Com base na sua auditoria e nas falhas relatadas, identifiquei uma desconexão entre o **Faturamento Global** (registado em pagamentos) e a **Receita do Split** (que depende da geração de entradas de comissão), além da falta de "atalhos" operacionais no dashboard.

Apresento o **PRD de Consolidação Financeira e Operacional** para o **Biohacking Studio**.

---

# PRD: Consolidação Financeira e Transparência Operacional

**Versão:** 3.3 (Finanças & UX Admin)
**Objetivo:** Criar rastreabilidade para alertas de atraso, unificar a receita da academia no módulo de split e implementar a remuneração de aulas gratuitas.

## 1. Problemas Identificados
1.  **Alertas "Cegos":** O dashboard informa números (ex: "5 atrasados"), mas não permite clicar para ver a lista.
2.  **Receita Zerada no Split:** O faturamento do mês no dashboard soma a tabela `Payment`, mas o módulo de Split só contabiliza receitas que geraram `CommissionEntry`.
3.  **Remuneração de Incentivo:** Instrutores não recebem automaticamente por aulas de XP/Experimentais no fluxo de split.

---

## 2. Etapa 1: Navegação de Alertas (Dashboard)

**Ação:** Alterar `app/templates/admin/dashboard.html` para transformar os alertas em links para rotas filtradas.

```html
<div class="row">
    <div class="col-md-6 col-lg-3">
        <a href="{{ url_for('admin_payments.overdue') }}" class="text-decoration-none">
            <div class="card bg-danger text-white mb-4 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="small text-white-50 fw-bold">PAGAMENTOS EM ATRASO</div>
                            <div class="h3 fw-bold">{{ pending_payments_count }}</div>
                        </div>
                        <i class="fas fa-exclamation-circle fa-2x opacity-50"></i>
                    </div>
                </div>
                <div class="card-footer d-flex align-items-center justify-content-between small">
                    <span class="text-white">Ver Lista de Devedores</span>
                    <i class="fas fa-angle-right"></i>
                </div>
            </div>
        </a>
    </div>

    <div class="col-md-6 col-lg-3">
        <a href="{{ url_for('admin_users.list_users', filter='expiring') }}" class="text-decoration-none">
            <div class="card bg-warning text-dark mb-4 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="small text-dark-50 fw-bold">EXPIRANDO EM 7 DIAS</div>
                            <div class="h3 fw-bold">{{ expiring_subscriptions_count }}</div>
                        </div>
                        <i class="fas fa-clock fa-2x opacity-50"></i>
                    </div>
                </div>
                <div class="card-footer d-flex align-items-center justify-content-between small">
                    <span class="text-dark">Ver Lista de Renovações</span>
                    <i class="fas fa-angle-right"></i>
                </div>
            </div>
        </a>
    </div>
</div>
```

---

## 3. Etapa 2: Unificação de Receita no Split (Backend)

O valor na Receita da Academia do Split está zerado porque as subscrições foram pagas mas os agendamentos (`Bookings`) ainda não foram marcados como `COMPLETED` ou `NO_SHOW`, que é o gatilho para gerar a comissão.

**Ação:** Atualizar a lógica de cálculo em `app/routes/admin/split.py` para mostrar tanto a receita "Realizada" (comissões processadas) quanto a receita "Bruta de Pagamentos".

```python
# app/routes/admin/split.py

@admin_split_bp.route('/')
@login_required
@admin_required
def dashboard():
    # ... (lógica existente) ...
    
    # CORREÇÃO: Buscar faturamento total da tabela Payment para comparação
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    receita_bruta_mes = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_at >= month_start
    ).scalar() or Decimal('0.00')

    # Receita que já passou pelo Split (já gerou comissão)
    receita_comissionada = db.session.query(func.sum(CommissionEntry.amount_academy)).filter(
        CommissionEntry.status == CommissionStatus.PAID,
        CommissionEntry.processed_at >= month_start
    ).scalar() or Decimal('0.00')

    return render_template('admin/split/dashboard.html',
                         receita_bruta_mes=receita_bruta_mes,
                         receita_comissionada=receita_comissionada,
                         # ... outros dados ...
                         )
```

---

## 4. Etapa 3: Regras de Remuneração para Aulas de Incentivo

Integramos agora a lógica onde o Studio subsidia a aula gratuita (XP ou Experimental) para o instrutor.

**Ação:** Atualizar `app/models/commission.py`.

```python
# app/models/commission.py

@classmethod
def create_from_booking(cls, booking, split_config=None):
    from app.models.commission import SplitSettings
    settings = SplitSettings.get_settings()
    
    # REGRA: Se o custo for 0 (Experimental/XP), usamos o valor nominal de Split
    # Isso garante que o instrutor receba, agindo como um custo de marketing para a academia.
    valor_referencia = booking.cost_at_booking
    is_incentive = False
    
    if valor_referencia == 0:
        valor_referencia = settings.credit_value_reais
        is_incentive = True
    
    schedule = booking.schedule
    professional = schedule.instructor
    
    if not split_config:
        split_config = schedule.split_config

    # Percentuais (Padrão ou Dinâmico)
    academy_pct = split_config.academy_percentage if split_config else Decimal('40.00')
    prof_pct = split_config.professional_percentage if split_config else Decimal('60.00')

    amount_professional = (valor_referencia * prof_pct / 100).quantize(Decimal('0.01'))
    amount_academy = (valor_referencia * academy_pct / 100).quantize(Decimal('0.01'))

    entry = cls(
        booking_id=booking.id,
        professional_id=professional.id,
        credit_value=valor_referencia,
        academy_percentage=academy_pct,
        professional_percentage=prof_pct,
        amount_academy=amount_academy, # Aqui a academia assume o custo
        amount_professional=amount_professional,
        booking_status=booking.status.value,
        status=CommissionStatus.PENDING,
        notes="Aula de Incentivo (Subsidiada)" if is_incentive else ""
    )
    return entry
```

---

## 5. Resumo das Correções
1.  **Links Diretos:** Ao ver "5 pagamentos em atraso" no painel, o administrador clica e vai direto para a lista de devedores.
2.  **Rastreio de Receita:** A "Receita da Academia" no Split agora diferencia o dinheiro que entrou (Bruto) do dinheiro que sobrou após pagar os instrutores (Líquido Comissionado).
3.  **Justiça com o Instrutor:** Aulas experimentais não geram "trabalho de graça" para o professor. O sistema calcula a comissão dele baseada no valor de mercado (R$ 15,00 por crédito, por exemplo) e debita da margem de lucro da academia como investimento.

**Nota Técnica:** Para que a receita do split apareça preenchida, certifique-se de que os instrutores estão a finalizar as aulas no painel (`COMPLETED`), pois é neste momento que a `CommissionEntry` é gerada. Se a aula estiver apenas agendada (`CONFIRMED`), a comissão ainda não existe para o financeiro.