# app/routes/admin/expenses.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.routes.admin.dashboard import admin_required
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract

expenses_bp = Blueprint('admin_expenses', __name__, url_prefix='/admin/expenses')


@expenses_bp.route('/')
@login_required
@admin_required
def list_expenses():
    """Lista de despesas com filtros."""
    from app.models.expense import Expense, ExpenseCategory

    # Filtros
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    category_filter = request.args.get('category', '')

    query = Expense.query.filter(
        extract('month', Expense.date) == month,
        extract('year', Expense.date) == year
    )

    if category_filter:
        query = query.filter(Expense.category == ExpenseCategory(category_filter))

    expenses = query.order_by(Expense.date.desc()).all()

    # Totais
    total = sum(float(e.amount) for e in expenses)
    total_recurring = sum(float(e.amount) for e in expenses if e.is_recurring)
    total_variable = total - total_recurring

    # Por categoria
    by_category = {}
    for e in expenses:
        cat = e.category.value
        by_category[cat] = by_category.get(cat, 0) + float(e.amount)

    categories = [{'value': c.value, 'label': c.label} for c in ExpenseCategory]

    # Meses disponiveis
    months_pt = ['', 'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

    return render_template('admin/expenses/list.html',
                           expenses=expenses,
                           total=total,
                           total_recurring=total_recurring,
                           total_variable=total_variable,
                           by_category=by_category,
                           categories=categories,
                           month=month,
                           year=year,
                           category_filter=category_filter,
                           months_pt=months_pt,
                           ExpenseCategory=ExpenseCategory)


@expenses_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_expense():
    """Criar despesa."""
    from app.models.expense import Expense, ExpenseCategory

    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'other')
        amount = request.form.get('amount', '0').replace(',', '.')
        expense_date = request.form.get('date', '')
        is_recurring = request.form.get('is_recurring') == 'on'
        recurring_day = request.form.get('recurring_day', type=int)
        notes = request.form.get('notes', '').strip()

        if not description or not amount:
            flash('Descricao e valor sao obrigatorios.', 'danger')
            return redirect(url_for('admin_expenses.create_expense'))

        try:
            amount_val = float(amount)
        except ValueError:
            flash('Valor invalido.', 'danger')
            return redirect(url_for('admin_expenses.create_expense'))

        try:
            parsed_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = date.today()

        expense = Expense(
            description=description,
            category=ExpenseCategory(category),
            amount=amount_val,
            date=parsed_date,
            is_recurring=is_recurring,
            recurring_day=recurring_day if is_recurring else None,
            notes=notes or None,
            created_by_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash(f'Despesa "{description}" cadastrada!', 'success')
        return redirect(url_for('admin_expenses.list_expenses'))

    categories = [{'value': c.value, 'label': c.label} for c in ExpenseCategory]
    return render_template('admin/expenses/form.html',
                           expense=None,
                           categories=categories)


@expenses_bp.route('/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_expense(expense_id):
    """Editar despesa."""
    from app.models.expense import Expense, ExpenseCategory

    expense = Expense.query.get_or_404(expense_id)

    if request.method == 'POST':
        expense.description = request.form.get('description', '').strip()
        expense.category = ExpenseCategory(request.form.get('category', 'other'))
        amount_str = request.form.get('amount', '0').replace(',', '.')
        try:
            expense.amount = float(amount_str)
        except ValueError:
            flash('Valor invalido.', 'danger')
            return redirect(url_for('admin_expenses.edit_expense', expense_id=expense_id))

        expense_date = request.form.get('date', '')
        try:
            expense.date = datetime.strptime(expense_date, '%Y-%m-%d').date()
        except ValueError:
            pass

        expense.is_recurring = request.form.get('is_recurring') == 'on'
        expense.recurring_day = request.form.get('recurring_day', type=int) if expense.is_recurring else None
        expense.notes = request.form.get('notes', '').strip() or None

        db.session.commit()
        flash('Despesa atualizada!', 'success')
        return redirect(url_for('admin_expenses.list_expenses'))

    categories = [{'value': c.value, 'label': c.label} for c in ExpenseCategory]
    return render_template('admin/expenses/form.html',
                           expense=expense,
                           categories=categories)


@expenses_bp.route('/<int:expense_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_expense(expense_id):
    """Deletar despesa."""
    from app.models.expense import Expense
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Despesa removida.', 'info')
    return redirect(url_for('admin_expenses.list_expenses'))


@expenses_bp.route('/summary')
@login_required
@admin_required
def monthly_summary():
    """Resumo mensal: receita vs despesas vs lucro."""
    from app.models.expense import Expense
    from app.models.payment import Payment, PaymentStatusEnum
    from app.models.commission import CommissionEntry, CommissionStatus

    today = date.today()
    # Ultimos 6 meses
    months_data = []
    for i in range(5, -1, -1):
        m_date = today.replace(day=1) - timedelta(days=i * 30)
        m_start = m_date.replace(day=1)
        if m_start.month == 12:
            m_end = m_start.replace(year=m_start.year + 1, month=1)
        else:
            m_end = m_start.replace(month=m_start.month + 1)

        # Receita (pagamentos aprovados)
        revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.status == PaymentStatusEnum.PAID,
            Payment.paid_date >= datetime.combine(m_start, datetime.min.time()),
            Payment.paid_date < datetime.combine(m_end, datetime.min.time())
        ).scalar()

        # Despesas
        total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.date >= m_start,
            Expense.date < m_end
        ).scalar()

        # Comissoes pagas
        commissions = db.session.query(func.coalesce(func.sum(CommissionEntry.net_amount), 0)).filter(
            CommissionEntry.status == CommissionStatus.PAID,
            CommissionEntry.created_at >= datetime.combine(m_start, datetime.min.time()),
            CommissionEntry.created_at < datetime.combine(m_end, datetime.min.time())
        ).scalar()

        revenue_f = float(revenue)
        expenses_f = float(total_expenses)
        commissions_f = float(commissions)
        profit = revenue_f - expenses_f - commissions_f

        months_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        months_data.append({
            'month': months_pt[m_start.month - 1],
            'year': m_start.year,
            'revenue': revenue_f,
            'expenses': expenses_f,
            'commissions': commissions_f,
            'profit': profit
        })

    # Resumo do mes atual
    current_month_start = today.replace(day=1)
    if current_month_start.month == 12:
        current_month_end = current_month_start.replace(year=current_month_start.year + 1, month=1)
    else:
        current_month_end = current_month_start.replace(month=current_month_start.month + 1)

    current_revenue = float(db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= datetime.combine(current_month_start, datetime.min.time()),
        Payment.paid_date < datetime.combine(current_month_end, datetime.min.time())
    ).scalar())

    current_expenses = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.date >= current_month_start,
        Expense.date < current_month_end
    ).scalar())

    current_commissions = float(db.session.query(func.coalesce(func.sum(CommissionEntry.net_amount), 0)).filter(
        CommissionEntry.status == CommissionStatus.PAID,
        CommissionEntry.created_at >= datetime.combine(current_month_start, datetime.min.time()),
        CommissionEntry.created_at < datetime.combine(current_month_end, datetime.min.time())
    ).scalar())

    # Previsao - assinaturas ativas * ticket medio
    from app.models.subscription import Subscription, SubscriptionStatus
    active_subs = Subscription.query.filter_by(status=SubscriptionStatus.ACTIVE).count()
    avg_ticket = current_revenue / active_subs if active_subs > 0 else 0
    forecast = active_subs * avg_ticket

    return render_template('admin/expenses/summary.html',
                           months_data=months_data,
                           current_revenue=current_revenue,
                           current_expenses=current_expenses,
                           current_commissions=current_commissions,
                           current_profit=current_revenue - current_expenses - current_commissions,
                           active_subs=active_subs,
                           avg_ticket=avg_ticket,
                           forecast=forecast)
