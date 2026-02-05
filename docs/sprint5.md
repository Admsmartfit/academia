# SPRINT 5: CRM E RETENÇÃO - VERSÃO CONCISA

## 📋 Objetivo
Implementar sistema de health score e dashboard de CRM em **4 passos práticos**.

---

## PASSO 1: Modelo de Health Score (5 min)

### Criar arquivo: `app/models/health_score.py`

```python
from app import db
from datetime import datetime

class StudentHealthScore(db.Model):
    __tablename__ = 'student_health_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Scores individuais (0-100)
    frequency_score = db.Column(db.Float, default=0)
    engagement_score = db.Column(db.Float, default=0) 
    financial_score = db.Column(db.Float, default=0)
    tenure_score = db.Column(db.Float, default=0)
    total_score = db.Column(db.Float, nullable=False, index=True)
    
    # Risk: LOW, MEDIUM, HIGH, CRITICAL
    risk_level = db.Column(db.String(20), nullable=False, index=True)
    requires_attention = db.Column(db.Boolean, default=False, index=True)
    
    user = db.relationship('User', backref='health_scores')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'calculated_at', name='_user_date_uc'),
    )
```

### Migration:
```bash
flask db migrate -m "Add health score model"
flask db upgrade
```

---

## PASSO 2: Calculador de Score (10 min)

### Criar arquivo: `app/services/health_calculator.py`

```python
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import User, Booking, StudentHealthScore
from app import db

class HealthCalculator:
    
    def calculate_all(self):
        """Calcula score de todos alunos ativos"""
        students = User.query.filter_by(role='student', is_active=True).all()
        
        for student in students:
            score = self.calculate_student(student.id)
            self._save_score(student.id, score)
        
        return len(students)
    
    def calculate_student(self, user_id):
        """Calcula score de um aluno"""
        # 1. Frequência (40 pontos)
        checkins = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == 'COMPLETED',
            Booking.checked_in_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        if checkins >= 12: freq_score = 40
        elif checkins >= 8: freq_score = 30
        elif checkins >= 4: freq_score = 20
        elif checkins >= 1: freq_score = 10
        else: freq_score = 0
        
        # 2. Engajamento (30 pontos) - simplificado
        eng_score = 30 if checkins > 0 else 0
        
        # 3. Financeiro (20 pontos) - simplificado
        fin_score = 20  # Assumir pagamento em dia
        
        # 4. Tenure (10 pontos)
        user = User.query.get(user_id)
        months = (datetime.utcnow() - user.created_at).days / 30
        
        if months >= 12: ten_score = 10
        elif months >= 6: ten_score = 7
        elif months >= 3: ten_score = 5
        else: ten_score = 0
        
        # Total e risco
        total = freq_score + eng_score + fin_score + ten_score
        
        if total >= 80: risk = 'LOW'
        elif total >= 60: risk = 'MEDIUM'
        elif total >= 40: risk = 'HIGH'
        else: risk = 'CRITICAL'
        
        return {
            'frequency_score': freq_score,
            'engagement_score': eng_score,
            'financial_score': fin_score,
            'tenure_score': ten_score,
            'total_score': total,
            'risk_level': risk
        }
    
    def _save_score(self, user_id, score_data):
        """Salva score no banco"""
        score = StudentHealthScore(
            user_id=user_id,
            frequency_score=score_data['frequency_score'],
            engagement_score=score_data['engagement_score'],
            financial_score=score_data['financial_score'],
            tenure_score=score_data['tenure_score'],
            total_score=score_data['total_score'],
            risk_level=score_data['risk_level'],
            requires_attention=(score_data['risk_level'] in ['HIGH', 'CRITICAL'])
        )
        db.session.add(score)
        db.session.commit()
```

### Testar:
```python
# No flask shell ou criar rota de teste
from app.services.health_calculator import HealthCalculator

calc = HealthCalculator()
calc.calculate_all()  # Calcula todos
```

---

## PASSO 3: Dashboard CRM (15 min)

### Criar arquivo: `app/routes/admin/crm.py`

```python
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.models import User, StudentHealthScore, Booking
from sqlalchemy import desc, func
from datetime import datetime, timedelta

bp = Blueprint('crm', __name__, url_prefix='/admin/crm')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Página do dashboard"""
    return render_template('admin/crm/dashboard.html')

@bp.route('/api/summary')
@login_required
def api_summary():
    """KPIs do dashboard"""
    total_students = User.query.filter_by(role='student', is_active=True).count()
    
    # Últimos scores
    latest_scores = db.session.query(
        StudentHealthScore.user_id,
        func.max(StudentHealthScore.calculated_at).label('max_date')
    ).group_by(StudentHealthScore.user_id).subquery()
    
    scores = StudentHealthScore.query.join(
        latest_scores,
        (StudentHealthScore.user_id == latest_scores.c.user_id) &
        (StudentHealthScore.calculated_at == latest_scores.c.max_date)
    ).all()
    
    at_risk = sum(1 for s in scores if s.risk_level in ['HIGH', 'CRITICAL'])
    critical = sum(1 for s in scores if s.risk_level == 'CRITICAL')
    avg_score = sum(s.total_score for s in scores) / len(scores) if scores else 0
    
    return jsonify({
        'total_students': total_students,
        'at_risk': at_risk,
        'critical': critical,
        'avg_score': round(avg_score, 1)
    })

@bp.route('/api/students-at-risk')
@login_required
def api_students_at_risk():
    """Lista alunos em risco"""
    # Pegar últimos scores de cada aluno
    latest_scores = db.session.query(
        StudentHealthScore.user_id,
        func.max(StudentHealthScore.calculated_at).label('max_date')
    ).group_by(StudentHealthScore.user_id).subquery()
    
    students_data = db.session.query(
        User, StudentHealthScore
    ).join(
        StudentHealthScore, User.id == StudentHealthScore.user_id
    ).join(
        latest_scores,
        (StudentHealthScore.user_id == latest_scores.c.user_id) &
        (StudentHealthScore.calculated_at == latest_scores.c.max_date)
    ).filter(
        StudentHealthScore.risk_level.in_(['HIGH', 'CRITICAL'])
    ).order_by(StudentHealthScore.total_score).all()
    
    result = []
    for user, score in students_data:
        # Último check-in
        last_booking = Booking.query.filter(
            Booking.user_id == user.id,
            Booking.status == 'COMPLETED'
        ).order_by(desc(Booking.checked_in_at)).first()
        
        # Frequência 30 dias
        freq_30d = Booking.query.filter(
            Booking.user_id == user.id,
            Booking.status == 'COMPLETED',
            Booking.checked_in_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar_url': user.avatar_url or '/static/img/default-avatar.png',
            'health_score': round(score.total_score, 1),
            'risk_level': score.risk_level,
            'last_checkin': last_booking.checked_in_at.isoformat() if last_booking else None,
            'frequency_30d': freq_30d,
            'days_since_checkin': (datetime.utcnow() - last_booking.checked_in_at).days if last_booking else 999
        })
    
    return jsonify(result)
```

### Registrar blueprint em `app/__init__.py`:
```python
from app.routes.admin import crm
app.register_blueprint(crm.bp)
```

---

## PASSO 4: Template do Dashboard (20 min)

### Criar arquivo: `templates/admin/crm/dashboard.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="container-fluid mt-4">
    <!-- KPIs -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card border-left-success">
                <div class="card-body">
                    <h3 id="total-students">0</h3>
                    <p class="text-muted">Total Alunos</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-left-warning">
                <div class="card-body">
                    <h3 id="at-risk">0</h3>
                    <p class="text-muted">Em Risco</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-left-danger">
                <div class="card-body">
                    <h3 id="critical">0</h3>
                    <p class="text-muted">Críticos</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-left-info">
                <div class="card-body">
                    <h3 id="avg-score">0</h3>
                    <p class="text-muted">Score Médio</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Tabela -->
    <div class="card">
        <div class="card-header">
            <h5>Alunos em Risco</h5>
        </div>
        <div class="card-body">
            <table class="table table-hover" id="students-table">
                <thead>
                    <tr>
                        <th>Aluno</th>
                        <th>Score</th>
                        <th>Último Check-in</th>
                        <th>Frequência (30d)</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody id="students-tbody">
                    <tr><td colspan="5" class="text-center">Carregando...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
.card {
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.border-left-success { border-left: 4px solid #28a745; }
.border-left-warning { border-left: 4px solid #ffc107; }
.border-left-danger { border-left: 4px solid #dc3545; }
.border-left-info { border-left: 4px solid #17a2b8; }

.badge-critical { background: #dc3545; }
.badge-high { background: #fd7e14; }
.badge-medium { background: #ffc107; color: #000; }
.badge-low { background: #28a745; }
</style>

<script>
$(document).ready(function() {
    loadDashboard();
    loadStudents();
});

async function loadDashboard() {
    try {
        const response = await fetch('/admin/crm/api/summary');
        const data = await response.json();
        
        $('#total-students').text(data.total_students);
        $('#at-risk').text(data.at_risk);
        $('#critical').text(data.critical);
        $('#avg-score').text(data.avg_score);
    } catch (err) {
        console.error('Erro ao carregar dashboard:', err);
    }
}

async function loadStudents() {
    try {
        const response = await fetch('/admin/crm/api/students-at-risk');
        const students = await response.json();
        
        const tbody = $('#students-tbody');
        tbody.empty();
        
        if (students.length === 0) {
            tbody.html('<tr><td colspan="5" class="text-center">Nenhum aluno em risco</td></tr>');
            return;
        }
        
        students.forEach(student => {
            const row = `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <img src="${student.avatar_url}" class="rounded-circle mr-2" width="40" height="40">
                            <div>
                                <strong>${student.name}</strong><br>
                                <small class="text-muted">${student.email}</small>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="badge badge-${student.risk_level.toLowerCase()}">
                            ${student.health_score.toFixed(0)}
                        </span>
                    </td>
                    <td>${formatDate(student.last_checkin)}</td>
                    <td>${student.frequency_30d} check-ins</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="sendRecoveryMessage(${student.id})">
                            <i class="fas fa-paper-plane"></i> Mensagem
                        </button>
                    </td>
                </tr>
            `;
            tbody.append(row);
        });
    } catch (err) {
        console.error('Erro ao carregar alunos:', err);
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '<span class="text-danger">Nunca</span>';
    
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Hoje';
    if (diffDays === 1) return 'Ontem';
    if (diffDays < 7) return `${diffDays} dias atrás`;
    return date.toLocaleDateString('pt-BR');
}

function sendRecoveryMessage(studentId) {
    // Integrar com WhatsApp aqui
    alert('Mensagem de recuperação enviada! (implementar integração WhatsApp)');
}
</script>
{% endblock %}
```

---

## PASSO 5: Agendar Cálculo Automático (5 min)

### Adicionar em `app/scheduler.py`:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.health_calculator import HealthCalculator
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def calculate_health_scores_job():
    """Job diário de health scores"""
    logger.info("Calculando health scores...")
    try:
        calc = HealthCalculator()
        total = calc.calculate_all()
        logger.info(f"✅ {total} health scores calculados")
    except Exception as e:
        logger.error(f"❌ Erro ao calcular scores: {e}")

def start_scheduler(app):
    """Inicia scheduler"""
    if not scheduler.running:
        with app.app_context():
            # Todo dia às 3h da manhã
            scheduler.add_job(
                calculate_health_scores_job,
                'cron',
                hour=3,
                minute=0,
                id='health_scores'
            )
            
            scheduler.start()
            logger.info("✅ Scheduler iniciado")
```

### Inicializar em `app/__init__.py`:

```python
def create_app():
    app = Flask(__name__)
    # ... outras configurações ...
    
    from app.scheduler import start_scheduler
    start_scheduler(app)
    
    return app
```

---

## 🧪 TESTAR TUDO

### 1. Calcular scores manualmente:
```bash
flask shell
>>> from app.services.health_calculator import HealthCalculator
>>> calc = HealthCalculator()
>>> calc.calculate_all()
```

### 2. Acessar dashboard:
```
http://localhost:5000/admin/crm/dashboard
```

### 3. Verificar dados:
```bash
flask shell
>>> from app.models import StudentHealthScore
>>> StudentHealthScore.query.all()
```

---

## ✅ CHECKLIST SPRINT 5

- [ ] Modelo StudentHealthScore criado
- [ ] Migration aplicada
- [ ] HealthCalculator funcionando
- [ ] API endpoints respondendo
- [ ] Dashboard renderizando
- [ ] KPIs sendo calculados
- [ ] Tabela mostrando alunos
- [ ] Scheduler configurado
- [ ] Job rodando às 3h

---

## 🚨 TROUBLESHOOTING

**Erro: "No such table: student_health_scores"**
```bash
flask db upgrade
```

**Scores sempre 0:**
```python
# Verificar se tem bookings com status COMPLETED
Booking.query.filter_by(status='COMPLETED').count()
```

**Dashboard não carrega:**
- Verificar se blueprint foi registrado
- Checar logs do Flask
- Inspecionar Network tab no browser

---

## 📊 PRÓXIMOS PASSOS

Agora que você tem CRM básico funcionando:

1. **Sprint 6:** Integrar WhatsApp (enviar mensagens de recuperação)
2. **Melhorar:** Adicionar mais métricas ao score
3. **Automatizar:** Réguas de relacionamento
4. **Dashboards:** Gráficos com Chart.js

---

**Tempo estimado:** 45 minutos total  
**Complexidade:** Média  
**Dependências:** Models User e Booking existentes

🎯 **Foco:** Código funcional direto, sem texto desnecessário!