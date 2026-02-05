

## 📊 SPRINT 5: CRM E RETENÇÃO

### Prompt 5.1: Dashboard de CRM

```
Você é especialista em dashboards de CRM e visualização de dados.

CONTEXTO:
Admin precisa visualizar health scores dos alunos e tomar ações preventivas.

TAREFA:
Crie templates/admin/crm/dashboard.html com:

**Widgets Principais:**
1. Resumo geral (total alunos, em risco, ativos)
2. Lista de alunos em risco (ordenados por score)
3. Gráfico de evolução de churn
4. Timeline de ações realizadas

**HTML (estrutura):**
```html
<div class="container-fluid">
    <!-- KPIs -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="stats-card green">
                <div class="stats-icon"><i class="fas fa-users"></i></div>
                <div class="stats-info">
                    <h3 id="total-students">0</h3>
                    <p>Total de Alunos</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="stats-card yellow">
                <div class="stats-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="stats-info">
                    <h3 id="at-risk">0</h3>
                    <p>Em Risco</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="stats-card red">
                <div class="stats-icon"><i class="fas fa-user-times"></i></div>
                <div class="stats-info">
                    <h3 id="critical">0</h3>
                    <p>Críticos</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="stats-card blue">
                <div class="stats-icon"><i class="fas fa-heartbeat"></i></div>
                <div class="stats-info">
                    <h3 id="avg-score">0</h3>
                    <p>Score Médio</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filtros -->
    <div class="card mb-4">
        <div class="card-body">
            <div class="row">
                <div class="col-md-3">
                    <label>Nível de Risco</label>
                    <select id="risk-filter" class="form-control">
                        <option value="">Todos</option>
                        <option value="CRITICAL">Crítico</option>
                        <option value="HIGH">Alto</option>
                        <option value="MEDIUM">Médio</option>
                        <option value="LOW">Baixo</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label>Dias sem Check-in</label>
                    <select id="days-filter" class="form-control">
                        <option value="">Qualquer</option>
                        <option value="7">7+ dias</option>
                        <option value="14">14+ dias</option>
                        <option value="30">30+ dias</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label>Ordenar por</label>
                    <select id="sort-filter" class="form-control">
                        <option value="score-asc">Score (menor primeiro)</option>
                        <option value="score-desc">Score (maior primeiro)</option>
                        <option value="last-checkin">Último check-in</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button class="btn btn-primary btn-block" onclick="applyFilters()">
                        <i class="fas fa-filter"></i> Filtrar
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Tabela de alunos -->
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
                    <!-- Gerado via JS -->
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Modal de Ações -->
<div class="modal fade" id="actionModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>Ações para <span id="modal-student-name"></span></h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="modal-student-id">
                
                <div class="list-group">
                    <a href="#" class="list-group-item list-group-item-action" 
                       onclick="sendMessage('RECOVERY')">
                        <i class="fas fa-comment"></i> Enviar Mensagem de Recuperação
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       onclick="scheduleCall()">
                        <i class="fas fa-phone"></i> Agendar Ligação
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       onclick="offerDiscount()">
                        <i class="fas fa-tag"></i> Oferecer Desconto
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       onclick="viewHistory()">
                        <i class="fas fa-history"></i> Ver Histórico Completo
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.stats-card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-left: 5px solid;
}

.stats-card.green { border-left-color: #28a745; }
.stats-card.yellow { border-left-color: #ffc107; }
.stats-card.red { border-left-color: #dc3545; }
.stats-card.blue { border-left-color: #007bff; }

.stats-icon {
    font-size: 3em;
    margin-right: 20px;
    opacity: 0.3;
}

.stats-info h3 {
    margin: 0;
    font-size: 2.5em;
    font-weight: bold;
}

.stats-info p {
    margin: 0;
    color: #6c757d;
}

.risk-badge {
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: bold;
}

.risk-badge.critical { background: #dc3545; color: white; }
.risk-badge.high { background: #fd7e14; color: white; }
.risk-badge.medium { background: #ffc107; color: #000; }
.risk-badge.low { background: #28a745; color: white; }
</style>

<script>
let studentsData = [];

$(document).ready(async () => {
    await loadDashboardData();
    await loadStudents();
});

async function loadDashboardData() {
    try {
        const response = await fetch('/api/crm/dashboard/summary');
        const data = await response.json();
        
        $('#total-students').text(data.total_students);
        $('#at-risk').text(data.at_risk);
        $('#critical').text(data.critical);
        $('#avg-score').text(data.avg_score.toFixed(1));
    } catch (err) {
        console.error('Erro ao carregar resumo:', err);
    }
}

async function loadStudents() {
    try {
        const response = await fetch('/api/crm/students/at-risk');
        studentsData = await response.json();
        renderStudents();
    } catch (err) {
        console.error('Erro ao carregar alunos:', err);
    }
}

function renderStudents() {
    const tbody = $('#students-tbody');
    tbody.empty();
    
    const filtered = applyClientFilters(studentsData);
    
    if (filtered.length === 0) {
        tbody.html('<tr><td colspan="5" class="text-center">Nenhum aluno encontrado</td></tr>');
        return;
    }
    
    filtered.forEach(student => {
        const row = $(`
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <img src="${student.avatar_url || '/static/img/default-avatar.png'}" 
                             class="rounded-circle mr-2" width="40" height="40">
                        <div>
                            <strong>${student.name}</strong><br>
                            <small class="text-muted">${student.email}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="progress flex-grow-1 mr-2" style="height: 20px;">
                            <div class="progress-bar ${getScoreColor(student.health_score)}" 
                                 role="progressbar" 
                                 style="width: ${student.health_score}%">
                                ${student.health_score.toFixed(0)}
                            </div>
                        </div>
                        <span class="risk-badge ${student.risk_level.toLowerCase()}">
                            ${getRiskLabel(student.risk_level)}
                        </span>
                    </div>
                </td>
                <td>
                    ${student.last_checkin ? 
                        formatDate(student.last_checkin) : 
                        '<span class="text-danger">Nunca</span>'}
                </td>
                <td>${student.frequency_30d} check-ins</td>
                <td>
                    <button class="btn btn-sm btn-primary" 
                            onclick="showActions(${student.id}, '${student.name}')">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </td>
            </tr>
        `);
        
        tbody.append(row);
    });
}

function applyClientFilters(data) {
    let filtered = [...data];
    
    // Aplicar filtros conforme seleção do usuário
    const riskFilter = $('#risk-filter').val();
    const daysFilter = $('#days-filter').val();
    const sortFilter = $('#sort-filter').val();
    
    if (riskFilter) {
        filtered = filtered.filter(s => s.risk_level === riskFilter);
    }
    
    if (daysFilter) {
        filtered = filtered.filter(s => s.days_since_checkin >= parseInt(daysFilter));
    }
    
    // Ordenar
    if (sortFilter === 'score-asc') {
        filtered.sort((a, b) => a.health_score - b.health_score);
    } else if (sortFilter === 'score-desc') {
        filtered.sort((a, b) => b.health_score - a.health_score);
    }
    
    return filtered;
}

function applyFilters() {
    renderStudents();
}

function showActions(studentId, studentName) {
    $('#modal-student-id').val(studentId);
    $('#modal-student-name').text(studentName);
    $('#actionModal').modal('show');
}

async function sendMessage(type) {
    const studentId = $('#modal-student-id').val();
    
    try {
        const response = await fetch('/api/crm/send-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: studentId,
                message_type: type
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Mensagem enviada com sucesso!');
            $('#actionModal').modal('hide');
        }
    } catch (err) {
        alert('Erro: ' + err.message);
    }
}

function getScoreColor(score) {
    if (score >= 70) return 'bg-success';
    if (score >= 40) return 'bg-warning';
    return 'bg-danger';
}

function getRiskLabel(level) {
    const labels = {
        'LOW': 'Baixo',
        'MEDIUM': 'Médio',
        'HIGH': 'Alto',
        'CRITICAL': 'Crítico'
    };
    return labels[level] || level;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Hoje';
    if (diffDays === 1) return 'Ontem';
    if (diffDays < 7) return `${diffDays} dias atrás`;
    return date.toLocaleDateString('pt-BR');
}
</script>
```

BACKEND APIs NECESSÁRIAS:
```python
# app/routes/api/crm.py

@bp.route('/dashboard/summary')
@login_required
def dashboard_summary():
    """Retorna resumo de KPIs"""
    total_students = User.query.filter_by(role='student').count()
    
    # Health scores recentes
    scores = StudentHealthScore.query.filter(
        StudentHealthScore.calculated_at >= datetime.now() - timedelta(days=7)
    ).all()
    
    at_risk = sum(1 for s in scores if s.risk_level in ['HIGH', 'CRITICAL'])
    critical = sum(1 for s in scores if s.risk_level == 'CRITICAL')
    avg_score = np.mean([s.total_score for s in scores]) if scores else 0
    
    return jsonify({
        'total_students': total_students,
        'at_risk': at_risk,
        'critical': critical,
        'avg_score': avg_score
    })

@bp.route('/students/at-risk')
@login_required
def students_at_risk():
    """Retorna alunos em risco com detalhes"""
    # Implementar query complexa
    pass
```

ENTREGA:
- Dashboard completo funcional
- Testes com dados reais
- Documentação de uso para admin
```

### Prompt 5.2: Calculador de Health Score (Scheduled Job)

```
Você é especialista em jobs agendados e algoritmos de scoring.

CONTEXTO:
Calcular health score de todos os alunos diariamente e identificar quem precisa de atenção.

TAREFA:
Crie o arquivo app/services/health_score_calculator.py:

**Código:**
```python
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import (
    User, Booking, StudentHealthScore, Package, 
    FaceRecognitionLog, TrainingSession
)
from app import db
import logging

logger = logging.getLogger(__name__)

class HealthScoreCalculator:
    """
    Calcula o Health Score de alunos baseado em 4 componentes:
    1. Frequência (40%) - Check-ins nos últimos 30 dias
    2. Engajamento (30%) - Interações com o sistema
    3. Financeiro (20%) - Status de pagamento
    4. Tenure (10%) - Tempo de matrícula
    
    Score final: 0-100
    Risk Levels:
    - 0-39: CRITICAL
    - 40-59: HIGH
    - 60-79: MEDIUM
    - 80-100: LOW
    """
    
    def __init__(self):
        self.lookback_days = 30
    
    def calculate_all_students(self):
        """
        Calcula score de todos os alunos ativos.
        Deve ser executado diariamente via scheduler.
        """
        logger.info("Iniciando cálculo de health scores...")
        
        students = User.query.filter_by(role='student', is_active=True).all()
        
        results = {
            'total': len(students),
            'updated': 0,
            'critical': 0,
            'high_risk': 0
        }
        
        for student in students:
            try:
                score_data = self.calculate_student_score(student.id)
                self._save_score(student.id, score_data)
                
                results['updated'] += 1
                
                if score_data['risk_level'] == 'CRITICAL':
                    results['critical'] += 1
                elif score_data['risk_level'] == 'HIGH':
                    results['high_risk'] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao calcular score do aluno {student.id}: {e}")
        
        logger.info(f"Health scores atualizados: {results}")
        return results
    
    def calculate_student_score(self, user_id: int) -> dict:
        """
        Calcula score de um aluno específico.
        
        Returns:
            {
                'frequency_score': float,
                'engagement_score': float,
                'financial_score': float,
                'tenure_score': float,
                'total_score': float,
                'risk_level': str,
                'details': dict
            }
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Usuário {user_id} não encontrado")
        
        # 1. Frequency Score (40 pontos)
        frequency_score, freq_details = self._calculate_frequency(user_id)
        
        # 2. Engagement Score (30 pontos)
        engagement_score, eng_details = self._calculate_engagement(user_id)
        
        # 3. Financial Score (20 pontos)
        financial_score, fin_details = self._calculate_financial(user_id)
        
        # 4. Tenure Score (10 pontos)
        tenure_score, ten_details = self._calculate_tenure(user)
        
        # Score total
        total_score = (
            frequency_score + 
            engagement_score + 
            financial_score + 
            tenure_score
        )
        
        # Risk level
        risk_level = self._determine_risk_level(total_score)
        
        return {
            'frequency_score': frequency_score,
            'engagement_score': engagement_score,
            'financial_score': financial_score,
            'tenure_score': tenure_score,
            'total_score': total_score,
            'risk_level': risk_level,
            'details': {
                'frequency': freq_details,
                'engagement': eng_details,
                'financial': fin_details,
                'tenure': ten_details
            }
        }
    
    def _calculate_frequency(self, user_id: int) -> tuple:
        """
        Calcula score de frequência (0-40).
        Baseado em check-ins nos últimos 30 dias.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        
        checkins = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == 'COMPLETED',
            Booking.checked_in_at >= cutoff_date
        ).count()
        
        # Lógica de pontuação
        if checkins == 0:
            score = 0
        elif checkins <= 4:  # <= 1x por semana
            score = 10
        elif checkins <= 8:  # 2x por semana
            score = 20
        elif checkins <= 12:  # 3x por semana
            score = 30
        else:  # 4+ por semana
            score = 40
        
        # Último check-in
        last_checkin = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == 'COMPLETED'
        ).order_by(Booking.checked_in_at.desc()).first()
        
        days_since_last = None
        if last_checkin:
            days_since_last = (datetime.utcnow() - last_checkin.checked_in_at).days
        
        details = {
            'checkins_30d': checkins,
            'days_since_last_checkin': days_since_last,
            'avg_per_week': round(checkins / 4.3, 1)
        }
        
        return score, details
    
    def _calculate_engagement(self, user_id: int) -> tuple:
        """
        Calcula score de engajamento (0-30).
        Baseado em interações com o sistema.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        score = 0
        
        # Visualizou treino?
        viewed_training = TrainingSession.query.filter(
            TrainingSession.user_id == user_id,
            TrainingSession.viewed_at >= cutoff_date
        ).count() > 0
        
        if viewed_training:
            score += 10
        
        # Respondeu mensagens do WhatsApp?
        # (assumindo que há um modelo de MessageResponse)
        # responded_messages = MessageResponse.query...
        # if responded_messages:
        #     score += 15
        score += 10  # Placeholder
        
        # Completou avaliação física?
        # completed_assessment = Assessment.query...
        # if completed_assessment:
        #     score += 5
        score += 5  # Placeholder
        
        # Usou reconhecimento facial?
        used_facial = FaceRecognitionLog.query.filter(
            FaceRecognitionLog.user_id == user_id,
            FaceRecognitionLog.timestamp >= cutoff_date,
            FaceRecognitionLog.success == True
        ).count() > 0
        
        if used_facial:
            score += 5
        
        details = {
            'viewed_training': viewed_training,
            'used_facial_recognition': used_facial,
            'engagement_actions': score / 30 * 100  # Porcentagem
        }
        
        return score, details
    
    def _calculate_financial(self, user_id: int) -> tuple:
        """
        Calcula score financeiro (0-20).
        Baseado em status de pagamento.
        """
        user = User.query.get(user_id)
        
        # Verificar se tem pacote ativo
        active_package = Package.query.filter(
            Package.user_id == user_id,
            Package.is_active == True,
            Package.expires_at > datetime.utcnow()
        ).first()
        
        if not active_package:
            score = 0
            status = 'SEM_PACOTE'
        else:
            # Verificar atraso de pagamento
            if active_package.payment_status == 'PAID':
                score = 20
                status = 'EM_DIA'
            elif active_package.payment_status == 'PENDING':
                days_overdue = (datetime.utcnow() - active_package.due_date).days
                if days_overdue <= 7:
                    score = 10
                    status = 'ATRASO_LEVE'
                else:
                    score = 0
                    status = 'INADIMPLENTE'
            else:
                score = 0
                status = 'DESCONHECIDO'
        
        details = {
            'payment_status': status,
            'has_active_package': active_package is not None,
            'days_to_expiration': (active_package.expires_at - datetime.utcnow()).days if active_package else None
        }
        
        return score, details
    
    def _calculate_tenure(self, user: User) -> tuple:
        """
        Calcula score de tempo de casa (0-10).
        """
        if not user.created_at:
            return 0, {'months': 0}
        
        days_since_join = (datetime.utcnow() - user.created_at).days
        months = days_since_join / 30
        
        if months >= 12:
            score = 10
        elif months >= 6:
            score = 7
        elif months >= 3:
            score = 5
        elif months >= 1:
            score = 3
        else:
            score = 0
        
        details = {
            'months': round(months, 1),
            'loyalty_level': 'HIGH' if months >= 12 else 'MEDIUM' if months >= 6 else 'LOW'
        }
        
        return score, details
    
    def _determine_risk_level(self, total_score: float) -> str:
        """Determina o nível de risco baseado no score total."""
        if total_score >= 80:
            return 'LOW'
        elif total_score >= 60:
            return 'MEDIUM'
        elif total_score >= 40:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _save_score(self, user_id: int, score_data: dict):
        """Salva score no banco de dados."""
        score_record = StudentHealthScore(
            user_id=user_id,
            calculated_at=datetime.utcnow(),
            frequency_score=score_data['frequency_score'],
            engagement_score=score_data['engagement_score'],
            financial_score=score_data['financial_score'],
            tenure_score=score_data['tenure_score'],
            total_score=score_data['total_score'],
            risk_level=score_data['risk_level'],
            requires_attention=(score_data['risk_level'] in ['HIGH', 'CRITICAL'])
        )
        
        db.session.add(score_record)
        db.session.commit()
```

**Configurar Scheduler (app/scheduler.py):**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.health_score_calculator import HealthScoreCalculator
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def calculate_health_scores_job():
    """Job diário para calcular health scores."""
    logger.info("Executando job de cálculo de health scores...")
    try:
        calculator = HealthScoreCalculator()
        results = calculator.calculate_all_students()
        logger.info(f"Health scores calculados: {results}")
        
        # Se houver alunos críticos, enviar alerta para admin
        if results['critical'] > 0:
            # send_admin_alert(results)
            pass
            
    except Exception as e:
        logger.error(f"Erro no job de health scores: {e}")

def start_scheduler(app):
    """Inicia o scheduler com os jobs configurados."""
    if not scheduler.running:
        with app.app_context():
            # Job diário às 3h da manhã
            scheduler.add_job(
                calculate_health_scores_job,
                'cron',
                hour=3,
                minute=0,
                id='calculate_health_scores',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("Scheduler iniciado com sucesso")
```

**No __init__.py da aplicação:**
```python
def create_app():
    app = Flask(__name__)
    # ... configurações ...
    
    # Iniciar scheduler
    from app.scheduler import start_scheduler
    start_scheduler(app)
    
    return app
```

TESTES:
- Testar cálculo com diferentes perfis de alunos
- Validar que job roda automaticamente
- Verificar performance com 1000+ alunos

ENTREGA:
- Código completo do calculator
- Testes unitários
- Script para executar manualmente: `flask calculate-scores`
```

---

## 💬 SPRINT 6: MENSAGERIA INTERATIVA WHATSAPP

[CONTINUA PRÓXIMO...]

Gostaria que eu continue com o Sprint 6 (WhatsApp Interativo) e Sprint 7 (Deploy e Polimento)?

### Prompt 6.1: Upgrade da MegaAPI para Mensagens Interativas

```
Você é especialista em integrações com WhatsApp Business API.

CONTEXTO:
A MegaAPI v2 suporta mensagens interativas (botões e listas). 
Precisamos fazer upgrade do serviço atual.

ARQUIVO ATUAL:
[Cole aqui o conteúdo de app/services/megaapi.py]

TAREFA:
Refatore o MegaAPIService adicionando suporte a mensagens interativas:

**Novo Código:**
```python
import requests
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Button:
    """Botão de ação rápida (até 3 por mensagem)"""
    id: str
    title: str  # Máx 20 caracteres
    
@dataclass
class ListSection:
    """Seção de uma lista"""
    title: str
    rows: List[Dict[str, str]]  # [{'id': '', 'title': '', 'description': ''}]
    
@dataclass
class ListMessage:
    """Mensagem com lista (até 10 opções)"""
    body: str
    button_text: str  # Texto do botão que abre a lista
    sections: List[ListSection]

class MegaAPIService:
    """
    Serviço para integração com MegaAPI (WhatsApp Business).
    Suporta mensagens de texto, botões e listas interativas.
    """
    
    def __init__(self, api_key: str, instance_id: str):
        self.api_key = api_key
        self.instance_id = instance_id
        self.base_url = "https://api.megaapi.com.br"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def send_text(self, phone: str, message: str) -> Dict:
        """
        Envia mensagem de texto simples.
        
        Args:
            phone: Número com DDI (ex: 5527999999999)
            message: Texto da mensagem
            
        Returns:
            {'success': bool, 'message_id': str}
        """
        payload = {
            "instance_id": self.instance_id,
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        return self._make_request("/messages/send", payload)
    
    def send_buttons(self, phone: str, message: str, buttons: List[Button]) -> Dict:
        """
        Envia mensagem com botões de ação rápida.
        
        Args:
            phone: Número com DDI
            message: Texto da mensagem
            buttons: Lista de botões (máx 3)
            
        Returns:
            {'success': bool, 'message_id': str}
            
        Example:
            buttons = [
                Button(id='confirm', title='✅ Confirmar'),
                Button(id='cancel', title='❌ Cancelar'),
                Button(id='reschedule', title='📅 Reagendar')
            ]
        """
        if len(buttons) > 3:
            raise ValueError("Máximo de 3 botões permitido")
        
        if any(len(btn.title) > 20 for btn in buttons):
            raise ValueError("Título do botão deve ter no máximo 20 caracteres")
        
        payload = {
            "instance_id": self.instance_id,
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": btn.id, "title": btn.title}}
                        for btn in buttons
                    ]
                }
            }
        }
        
        return self._make_request("/messages/send", payload)
    
    def send_list(self, phone: str, list_message: ListMessage) -> Dict:
        """
        Envia mensagem com lista de opções.
        
        Args:
            phone: Número com DDI
            list_message: Objeto ListMessage com body, button_text e sections
            
        Returns:
            {'success': bool, 'message_id': str}
            
        Example:
            list_msg = ListMessage(
                body="Escolha um horário disponível:",
                button_text="Ver Horários",
                sections=[
                    ListSection(
                        title="Manhã",
                        rows=[
                            {'id': 'slot_1', 'title': '08:00', 'description': 'Treino Funcional'},
                            {'id': 'slot_2', 'title': '09:00', 'description': 'Musculação'}
                        ]
                    ),
                    ListSection(
                        title="Tarde",
                        rows=[
                            {'id': 'slot_3', 'title': '14:00', 'description': 'Treino Funcional'}
                        ]
                    )
                ]
            )
        """
        total_rows = sum(len(section.rows) for section in list_message.sections)
        if total_rows > 10:
            raise ValueError("Máximo de 10 opções permitido no total")
        
        payload = {
            "instance_id": self.instance_id,
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": list_message.body
                },
                "action": {
                    "button": list_message.button_text,
                    "sections": [
                        {
                            "title": section.title,
                            "rows": section.rows
                        }
                        for section in list_message.sections
                    ]
                }
            }
        }
        
        return self._make_request("/messages/send", payload)
    
    def send_template(self, phone: str, template_name: str, 
                     language: str = "pt_BR", 
                     components: Optional[List[Dict]] = None) -> Dict:
        """
        Envia template pré-aprovado pelo Meta.
        
        Args:
            phone: Número com DDI
            template_name: Nome do template cadastrado no Meta
            language: Código do idioma (padrão: pt_BR)
            components: Parâmetros do template
            
        Example:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "João"},
                        {"type": "text", "text": "15/02/2026"}
                    ]
                }
            ]
        """
        payload = {
            "instance_id": self.instance_id,
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components or []
            }
        }
        
        return self._make_request("/messages/send", payload)
    
    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """Faz requisição HTTP para a API."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            logger.info(f"Enviando requisição para MegaAPI: {endpoint}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Resposta MegaAPI: {result}")
            
            return {
                'success': True,
                'message_id': result.get('message_id'),
                'data': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição MegaAPI: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Erro inesperado MegaAPI: {e}")
            return {
                'success': False,
                'error': str(e)
            }
```

**Uso na Aplicação:**
```python
# Exemplo: Lembrete de aula com botões
from app.services.megaapi import MegaAPIService, Button

mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)

booking = Booking.query.get(123)
student = booking.user

message = f"Olá {student.name}! Você tem aula agendada hoje às {booking.class_time.strftime('%H:%M')}."

buttons = [
    Button(id=f'confirm_{booking.id}', title='✅ Vou comparecer'),
    Button(id=f'cancel_{booking.id}', title='❌ Preciso cancelar'),
    Button(id='reschedule', title='📅 Reagendar')
]

result = mega.send_buttons(
    phone=student.phone,
    message=message,
    buttons=buttons
)

if result['success']:
    print(f"Mensagem enviada: {result['message_id']}")
```

VALIDAÇÃO:
- Testar cada tipo de mensagem
- Verificar limites (3 botões, 10 opções)
- Implementar retry com backoff exponencial
- Logar todas as respostas

ENTREGA:
- Código refatorado
- Testes unitários com mocking
- Exemplos de uso para cada tipo
```

### Prompt 6.2: Webhook Handler para Respostas Interativas

```
Você é especialista em webhooks e processamento assíncrono.

CONTEXTO:
Quando usuário clica em botão ou seleciona item da lista, o WhatsApp envia webhook.
Precisamos processar essas respostas e executar ações.

TAREFA:
Crie o arquivo app/routes/webhooks.py para processar webhooks do WhatsApp:

**Código:**
```python
from flask import Blueprint, request, jsonify
from app.services.megaapi import MegaAPIService
from app.models import Booking, User, Lead
from app import db
import hmac
import hashlib
import logging

bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')
logger = logging.getLogger(__name__)

# Chave secreta para validar webhook (configurar no .env)
WEBHOOK_SECRET = os.getenv('MEGAAPI_WEBHOOK_SECRET')

@bp.route('/megaapi', methods=['POST'])
def megaapi_webhook():
    """
    Recebe webhooks da MegaAPI.
    
    Tipos de eventos:
    - messages: Mensagem de texto recebida
    - messages.interactive.button_reply: Clique em botão
    - messages.interactive.list_reply: Seleção em lista
    - message.status: Status de entrega (sent, delivered, read)
    """
    # Validar assinatura (segurança)
    if not validate_webhook_signature(request):
        logger.warning("Webhook com assinatura inválida")
        return jsonify({'error': 'Invalid signature'}), 401
    
    data = request.json
    logger.info(f"Webhook recebido: {data}")
    
    try:
        # Extrair informações básicas
        event_type = data.get('type')
        phone = data.get('from')
        
        if event_type == 'messages.interactive.button_reply':
            handle_button_reply(data)
        elif event_type == 'messages.interactive.list_reply':
            handle_list_reply(data)
        elif event_type == 'messages':
            handle_text_message(data)
        elif event_type == 'message.status':
            handle_message_status(data)
        else:
            logger.warning(f"Tipo de evento não tratado: {event_type}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def validate_webhook_signature(request) -> bool:
    """
    Valida assinatura HMAC-SHA256 do webhook.
    Previne webhooks falsificados.
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET não configurado - validação desabilitada")
        return True
    
    signature = request.headers.get('X-MegaAPI-Signature')
    if not signature:
        return False
    
    payload = request.get_data()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def handle_button_reply(data: dict):
    """
    Processa clique em botão.
    
    Payload exemplo:
    {
        "type": "messages.interactive.button_reply",
        "from": "5527999999999",
        "button_reply": {
            "id": "confirm_123",
            "title": "✅ Vou comparecer"
        }
    }
    """
    button_id = data['button_reply']['id']
    phone = data['from']
    
    logger.info(f"Botão clicado: {button_id} por {phone}")
    
    # Parse do button_id
    action, *params = button_id.split('_')
    
    if action == 'confirm' and params:
        # Confirmar presença em aula
        booking_id = int(params[0])
        confirm_booking_attendance(booking_id, phone)
        
    elif action == 'cancel' and params:
        # Cancelar aula
        booking_id = int(params[0])
        cancel_booking_via_whatsapp(booking_id, phone)
        
    elif action == 'reschedule':
        # Enviar lista de horários disponíveis
        send_available_slots(phone)
        
    elif action == 'renew':
        # Renovar plano
        send_renewal_payment_link(phone)
        
    elif action == 'satisfaction' and params:
        # Resposta de pesquisa de satisfação
        rating = int(params[0])
        record_satisfaction_rating(phone, rating)
        
    else:
        logger.warning(f"Ação de botão não reconhecida: {action}")

def handle_list_reply(data: dict):
    """
    Processa seleção de item em lista.
    
    Payload exemplo:
    {
        "type": "messages.interactive.list_reply",
        "from": "5527999999999",
        "list_reply": {
            "id": "slot_5",
            "title": "15:00",
            "description": "Treino Funcional"
        }
    }
    """
    list_id = data['list_reply']['id']
    phone = data['from']
    
    logger.info(f"Item de lista selecionado: {list_id} por {phone}")
    
    # Parse do list_id
    action, *params = list_id.split('_')
    
    if action == 'slot' and params:
        # Reagendar para horário selecionado
        slot_id = int(params[0])
        book_slot_via_whatsapp(slot_id, phone)
        
    elif action == 'package' and params:
        # Selecionar pacote
        package_id = int(params[0])
        process_package_selection(package_id, phone)
        
    else:
        logger.warning(f"Ação de lista não reconhecida: {action}")

def handle_text_message(data: dict):
    """
    Processa mensagem de texto recebida.
    Pode ser usado para chatbot simples.
    """
    text = data.get('text', {}).get('body', '').strip().lower()
    phone = data['from']
    
    logger.info(f"Mensagem recebida de {phone}: {text}")
    
    # Comandos simples
    if text in ['oi', 'olá', 'ola', 'hey']:
        send_welcome_message(phone)
    elif text in ['horários', 'horarios', 'agendar']:
        send_available_slots(phone)
    elif text in ['meu treino', 'treino']:
        send_training_link(phone)
    elif text in ['ajuda', 'help', 'menu']:
        send_help_menu(phone)
    else:
        # Resposta genérica ou ignorar
        logger.info(f"Mensagem não processada: {text}")

def handle_message_status(data: dict):
    """
    Processa status de mensagem (entregue, lida, etc).
    Útil para analytics.
    """
    message_id = data.get('message_id')
    status = data.get('status')  # sent, delivered, read, failed
    
    logger.info(f"Status da mensagem {message_id}: {status}")
    
    # Salvar em tabela de analytics se necessário
    # MessageLog.query.filter_by(message_id=message_id).update({'status': status})

# ==================== AÇÕES ESPECÍFICAS ====================

def confirm_booking_attendance(booking_id: int, phone: str):
    """Marca booking como confirmado pelo aluno."""
    booking = Booking.query.get(booking_id)
    
    if not booking:
        logger.error(f"Booking {booking_id} não encontrado")
        return
    
    # Verificar se é o aluno correto
    if booking.user.phone != phone:
        logger.warning(f"Tentativa de confirmar booking de outro usuário")
        return
    
    booking.confirmed_by_student = True
    booking.confirmed_at = datetime.utcnow()
    db.session.commit()
    
    # Enviar confirmação
    mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)
    mega.send_text(
        phone=phone,
        message=f"✅ Presença confirmada! Te esperamos às {booking.class_time.strftime('%H:%M')}."
    )
    
    logger.info(f"Booking {booking_id} confirmado por {phone}")

def cancel_booking_via_whatsapp(booking_id: int, phone: str):
    """Cancela booking via WhatsApp."""
    booking = Booking.query.get(booking_id)
    
    if not booking or booking.user.phone != phone:
        return
    
    # Verificar se ainda pode cancelar (ex: mín 2h de antecedência)
    hours_until = (booking.class_time - datetime.utcnow()).total_seconds() / 3600
    
    if hours_until < 2:
        mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)
        mega.send_text(
            phone=phone,
            message="⚠️ Cancelamento deve ser feito com pelo menos 2h de antecedência. Entre em contato conosco."
        )
        return
    
    # Cancelar
    booking.status = 'CANCELLED'
    booking.cancelled_at = datetime.utcnow()
    booking.cancellation_reason = 'Cancelado via WhatsApp'
    
    # Devolver crédito
    booking.user.credits += 1
    
    db.session.commit()
    
    # Confirmação
    mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)
    mega.send_text(
        phone=phone,
        message=f"✅ Aula cancelada. Seu crédito foi devolvido. Saldo: {booking.user.credits} créditos."
    )
    
    logger.info(f"Booking {booking_id} cancelado via WhatsApp")

def send_available_slots(phone: str):
    """Envia lista de horários disponíveis para reagendamento."""
    # Buscar usuário pelo telefone
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return
    
    # Buscar slots disponíveis nos próximos 7 dias
    available_slots = get_available_slots(days=7)
    
    if not available_slots:
        mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)
        mega.send_text(
            phone=phone,
            message="Desculpe, não há horários disponíveis no momento. Entre em contato conosco."
        )
        return
    
    # Agrupar por dia
    slots_by_day = {}
    for slot in available_slots:
        day_name = slot['date'].strftime('%d/%m (%A)')
        if day_name not in slots_by_day:
            slots_by_day[day_name] = []
        slots_by_day[day_name].append(slot)
    
    # Criar lista interativa
    sections = []
    for day_name, slots in slots_by_day.items():
        rows = [
            {
                'id': f"slot_{slot['id']}",
                'title': slot['time'],
                'description': slot['class_name']
            }
            for slot in slots[:3]  # Máx 3 por seção
        ]
        sections.append(ListSection(title=day_name, rows=rows))
    
    list_msg = ListMessage(
        body="Escolha um horário para sua aula:",
        button_text="Ver Horários",
        sections=sections[:10]  # Máx 10 seções
    )
    
    mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)
    mega.send_list(phone=phone, list_message=list_msg)

def send_welcome_message(phone: str):
    """Envia mensagem de boas-vindas."""
    mega = MegaAPIService(api_key=config.MEGAAPI_KEY, instance_id=config.INSTANCE_ID)
    
    buttons = [
        Button(id='schedule', title='📅 Agendar Aula'),
        Button(id='training', title='💪 Meu Treino'),
        Button(id='help', title='❓ Ajuda')
    ]
    
    mega.send_buttons(
        phone=phone,
        message="Olá! Seja bem-vindo(a) à nossa academia! Como posso ajudar?",
        buttons=buttons
    )

# Helpers adicionais...

def get_available_slots(days=7):
    """Retorna slots disponíveis nos próximos N dias."""
    # Implementar lógica de busca
    # Por simplicidade, retornar mock
    return [
        {'id': 1, 'date': datetime.now() + timedelta(days=1), 'time': '08:00', 'class_name': 'Funcional'},
        {'id': 2, 'date': datetime.now() + timedelta(days=1), 'time': '09:00', 'class_name': 'Musculação'},
        # ...
    ]
```

**Configurar webhook na MegaAPI:**
1. Acessar painel da MegaAPI
2. Configurar URL: `https://seu-dominio.com/webhooks/megaapi`
3. Gerar e salvar WEBHOOK_SECRET no .env
4. Testar com ferramenta de webhook (ex: webhook.site)

SEGURANÇA:
- Sempre validar assinatura HMAC
- Validar identidade do usuário (phone)
- Implementar rate limiting
- Não expor dados sensíveis nos logs

ENTREGA:
- Código completo do webhook handler
- Testes com simulação de eventos
- Documentação de cada tipo de evento
```

### Prompt 6.3: Automação de Réguas de Relacionamento

```
Você é especialista em automação de marketing e fluxos de comunicação.

CONTEXTO:
Criar automações que enviam mensagens interativas em momentos-chave da jornada do aluno.

TAREFA:
Crie o arquivo app/services/retention_automation.py:

**Código:**
```python
from datetime import datetime, timedelta
from app.models import User, Booking, StudentHealthScore, Lead
from app.services.megaapi import MegaAPIService, Button, ListMessage, ListSection
from app import db
import logging

logger = logging.getLogger(__name__)

class RetentionAutomation:
    """
    Automações de retenção baseadas em réguas de relacionamento.
    
    Réguas implementadas:
    1. Boas-vindas (D+1)
    2. Engajamento (D+15)
    3. Recuperação Leve (Ausente 5 dias)
    4. Recuperação Crítica (Ausente 10 dias)
    5. Última Tentativa (Ausente 20 dias)
    """
    
    def __init__(self):
        self.mega = MegaAPIService(
            api_key=config.MEGAAPI_KEY,
            instance_id=config.INSTANCE_ID
        )
    
    def run_daily_automations(self):
        """
        Executa todas as automações diárias.
        Deve ser chamado via scheduler.
        """
        logger.info("Iniciando automações de retenção...")
        
        results = {
            'welcome_sent': 0,
            'engagement_sent': 0,
            'recovery_light_sent': 0,
            'recovery_critical_sent': 0,
            'last_attempt_sent': 0
        }
        
        # 1. Boas-vindas (usuários cadastrados ontem)
        results['welcome_sent'] = self.send_welcome_messages()
        
        # 2. Engajamento (usuários com 15 dias)
        results['engagement_sent'] = self.send_engagement_survey()
        
        # 3. Recuperação leve (5 dias sem check-in)
        results['recovery_light_sent'] = self.send_light_recovery()
        
        # 4. Recuperação crítica (10 dias sem check-in)
        results['recovery_critical_sent'] = self.send_critical_recovery()
        
        # 5. Última tentativa (20 dias sem check-in)
        results['last_attempt_sent'] = self.send_last_attempt()
        
        logger.info(f"Automações concluídas: {results}")
        return results
    
    def send_welcome_messages(self) -> int:
        """Mensagem de boas-vindas para novos alunos (D+1)."""
        yesterday = datetime.utcnow() - timedelta(days=1)
        today = datetime.utcnow()
        
        new_students = User.query.filter(
            User.role == 'student',
            User.created_at >= yesterday,
            User.created_at < today,
            User.phone.isnot(None)
        ).all()
        
        sent_count = 0
        
        for student in new_students:
            try:
                buttons = [
                    Button(id='facial_tutorial', title='📸 Como usar facial'),
                    Button(id='schedule_evaluation', title='📋 Agendar avaliação'),
                    Button(id='view_training', title='💪 Ver meu treino')
                ]
                
                message = f"""
Olá {student.name}! 🎉

Seja muito bem-vindo(a) à nossa academia! Estamos muito felizes em tê-lo(a) conosco.

Para aproveitar ao máximo sua experiência:

✅ Use o reconhecimento facial para check-in automático
✅ Acesse seu treino personalizado pelo celular
✅ Agende sua avaliação física gratuita

Escolha uma opção abaixo ou me mande uma mensagem se tiver dúvidas!
                """.strip()
                
                result = self.mega.send_buttons(
                    phone=student.phone,
                    message=message,
                    buttons=buttons
                )
                
                if result['success']:
                    # Registrar envio
                    self._log_automation('WELCOME', student.id)
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Erro ao enviar boas-vindas para {student.id}: {e}")
        
        return sent_count
    
    def send_engagement_survey(self) -> int:
        """Pesquisa de satisfação após 15 dias."""
        target_date = datetime.utcnow() - timedelta(days=15)
        
        students = User.query.filter(
            User.role == 'student',
            User.created_at.between(
                target_date - timedelta(hours=12),
                target_date + timedelta(hours=12)
            ),
            User.phone.isnot(None)
        ).all()
        
        sent_count = 0
        
        for student in students:
            try:
                # Verificar se já respondeu
                if self._already_completed_survey(student.id):
                    continue
                
                list_msg = ListMessage(
                    body=f"Olá {student.name}! Já faz 15 dias que você está conosco. Como você avalia sua experiência até agora?",
                    button_text="Avaliar",
                    sections=[
                        ListSection(
                            title="Sua Avaliação",
                            rows=[
                                {'id': 'satisfaction_5', 'title': '⭐⭐⭐⭐⭐', 'description': 'Excelente!'},
                                {'id': 'satisfaction_4', 'title': '⭐⭐⭐⭐', 'description': 'Muito bom'},
                                {'id': 'satisfaction_3', 'title': '⭐⭐⭐', 'description': 'Bom'},
                                {'id': 'satisfaction_2', 'title': '⭐⭐', 'description': 'Regular'},
                                {'id': 'satisfaction_1', 'title': '⭐', 'description': 'Insatisfeito'}
                            ]
                        )
                    ]
                )
                
                result = self.mega.send_list(phone=student.phone, list_message=list_msg)
                
                if result['success']:
                    self._log_automation('ENGAGEMENT_SURVEY', student.id)
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Erro ao enviar pesquisa para {student.id}: {e}")
        
        return sent_count
    
    def send_light_recovery(self) -> int:
        """Recuperação leve: 5 dias sem check-in."""
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        
        # Buscar alunos sem check-in nos últimos 5 dias
        students_absent = db.session.query(User).filter(
            User.role == 'student',
            User.is_active == True,
            ~User.id.in_(
                db.session.query(Booking.user_id).filter(
                    Booking.status == 'COMPLETED',
                    Booking.checked_in_at >= five_days_ago
                )
            )
        ).all()
        
        sent_count = 0
        
        for student in students_absent:
            # Verificar se já enviou recuperação recentemente
            if self._sent_recovery_recently(student.id, days=3):
                continue
            
            try:
                buttons = [
                    Button(id='yes_tomorrow', title='✅ Vou amanhã!'),
                    Button(id='reschedule_me', title='📅 Reagendar'),
                    Button(id='im_ok', title='😊 Está tudo bem')
                ]
                
                message = f"""
Olá {student.name}! 

Sentimos sua falta por aqui! Faz 5 dias que você não vem treinar. 

Sabemos que a rotina é corrida, mas lembre-se: cada treino te deixa mais perto dos seus objetivos! 💪

Quando podemos te esperar?
                """.strip()
                
                result = self.mega.send_buttons(
                    phone=student.phone,
                    message=message,
                    buttons=buttons
                )
                
                if result['success']:
                    self._log_automation('RECOVERY_LIGHT', student.id)
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Erro em recuperação leve para {student.id}: {e}")
        
        return sent_count
    
    def send_critical_recovery(self) -> int:
        """Recuperação crítica: 10 dias sem check-in."""
        ten_days_ago = datetime.utcnow() - timedelta(days=10)
        
        students_critical = db.session.query(User).filter(
            User.role == 'student',
            User.is_active == True,
            ~User.id.in_(
                db.session.query(Booking.user_id).filter(
                    Booking.status == 'COMPLETED',
                    Booking.checked_in_at >= ten_days_ago
                )
            )
        ).all()
        
        sent_count = 0
        
        for student in students_critical:
            if self._sent_recovery_recently(student.id, days=5):
                continue
            
            try:
                # Mensagem mais personalizada do instrutor
                instructor = student.instructor  # Assumindo relacionamento
                
                buttons = [
                    Button(id='talk_to_instructor', title='💬 Falar com instrutor'),
                    Button(id='free_personal', title='🎁 Sessão grátis'),
                    Button(id='schedule_now', title='📅 Agendar agora')
                ]
                
                message = f"""
{student.name}, aqui é o(a) {instructor.name if instructor else 'equipe'}! 

Notei que você não está vindo treinar. Tudo bem com você?

Quero te ajudar a voltar com tudo! Que tal uma sessão gratuita de personal para te motivar?

Conte comigo! 💪❤️
                """.strip()
                
                result = self.mega.send_buttons(
                    phone=student.phone,
                    message=message,
                    buttons=buttons
                )
                
                if result['success']:
                    self._log_automation('RECOVERY_CRITICAL', student.id)
                    sent_count += 1
                    
                    # Notificar instrutor
                    self._notify_instructor_about_student(student.id, instructor.id if instructor else None)
                    
            except Exception as e:
                logger.error(f"Erro em recuperação crítica para {student.id}: {e}")
        
        return sent_count
    
    def send_last_attempt(self) -> int:
        """Última tentativa: 20 dias sem check-in + desconto."""
        twenty_days_ago = datetime.utcnow() - timedelta(days=20)
        
        students_last_attempt = db.session.query(User).filter(
            User.role == 'student',
            User.is_active == True,
            ~User.id.in_(
                db.session.query(Booking.user_id).filter(
                    Booking.status == 'COMPLETED',
                    Booking.checked_in_at >= twenty_days_ago
                )
            )
        ).all()
        
        sent_count = 0
        
        for student in students_last_attempt:
            try:
                buttons = [
                    Button(id='claim_discount', title='💰 Quero o desconto'),
                    Button(id='schedule_call', title='📞 Agendar ligação'),
                    Button(id='cancel_membership', title='😢 Cancelar matrícula')
                ]
                
                message = f"""
{student.name}, queremos MUITO você de volta! 😊

Preparamos uma condição ESPECIAL só para você:

🎁 30% DE DESCONTO no próximo mês
🎁 1 mês de personal trainer grátis
🎁 Kit de boas-vindas exclusivo

Sua saúde e bem-estar são nossa prioridade!

Vamos voltar juntos? 💪
                """.strip()
                
                result = self.mega.send_buttons(
                    phone=student.phone,
                    message=message,
                    buttons=buttons
                )
                
                if result['success']:
                    self._log_automation('LAST_ATTEMPT', student.id)
                    sent_count += 1
                    
                    # Gerar cupom de desconto
                    self._generate_discount_coupon(student.id, discount_percent=30)
                    
            except Exception as e:
                logger.error(f"Erro em última tentativa para {student.id}: {e}")
        
        return sent_count
    
    # ================= MÉTODOS AUXILIARES =================
    
    def _log_automation(self, automation_type: str, user_id: int):
        """Registra envio de automação."""
        log = AutomationLog(
            user_id=user_id,
            automation_type=automation_type,
            sent_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    
    def _sent_recovery_recently(self, user_id: int, days: int) -> bool:
        """Verifica se já enviou mensagem de recuperação recentemente."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent_log = AutomationLog.query.filter(
            AutomationLog.user_id == user_id,
            AutomationLog.automation_type.in_(['RECOVERY_LIGHT', 'RECOVERY_CRITICAL', 'LAST_ATTEMPT']),
            AutomationLog.sent_at >= cutoff
        ).first()
        
        return recent_log is not None
    
    def _already_completed_survey(self, user_id: int) -> bool:
        """Verifica se aluno já respondeu pesquisa de satisfação."""
        # Implementar lógica
        return False
    
    def _notify_instructor_about_student(self, student_id: int, instructor_id: int):
        """Notifica instrutor sobre aluno em risco."""
        if not instructor_id:
            return
        
        instructor = User.query.get(instructor_id)
        student = User.query.get(student_id)
        
        if instructor.phone:
            self.mega.send_text(
                phone=instructor.phone,
                message=f"⚠️ Alerta: {student.name} está há 10 dias sem treinar. Considere entrar em contato."
            )
    
    def _generate_discount_coupon(self, user_id: int, discount_percent: int):
        """Gera cupom de desconto para o aluno."""
        # Implementar lógica de geração de cupom
        pass
```

**Modelo de Log:**
```python
class AutomationLog(db.Model):
    __tablename__ = 'automation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    automation_type = db.Column(db.String(50), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    opened = db.Column(db.Boolean, default=False)
    clicked = db.Column(db.Boolean, default=False)
```

**Adicionar ao Scheduler:**
```python
# app/scheduler.py
from app.services.retention_automation import RetentionAutomation

def run_retention_automations():
    logger.info("Executando automações de retenção...")
    automation = RetentionAutomation()
    results = automation.run_daily_automations()
    logger.info(f"Automações finalizadas: {results}")

# Agendar para rodar todo dia às 10h
scheduler.add_job(
    run_retention_automations,
    'cron',
    hour=10,
    minute=0,
    id='retention_automations'
)
```

TESTES:
- Testar cada régua separadamente
- Simular cenários de ausência
- Verificar que não envia duplicado
- Medir taxa de resposta

ENTREGA:
- Código completo das automações
- Script para executar manualmente cada régua
- Relatório de efetividade (após 1 mês)
```

---

## 🚀 SPRINT 7: DEPLOY E POLIMENTO

### Prompt 7.1: Preparação para Produção

```
Você é especialista em DevOps e deploy de aplicações Python.

CONTEXTO:
Preparar aplicação para deploy em produção.

TAREFA:
Criar checklist e arquivos de configuração para produção:

**1. Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expor porta
EXPOSE 5000

# Comando
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

**2. docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/admsmartfit
      - MEGAAPI_KEY=${MEGAAPI_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: always
  
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: admsmartfit
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
  
  redis:
    image: redis:7-alpine
    restart: always

volumes:
  postgres_data:
```

**3. Checklist de Produção:**
- [ ] Migrar de SQLite para PostgreSQL
- [ ] Configurar variáveis de ambiente (.env)
- [ ] Habilitar HTTPS (Let's Encrypt)
- [ ] Configurar CORS adequadamente
- [ ] Implementar rate limiting (Flask-Limiter)
- [ ] Configurar backup automático do banco
- [ ] Setup de logs estruturados
- [ ] Configurar monitoramento (Sentry)
- [ ] Testar performance sob carga
- [ ] Documentar procedimentos de rollback

**4. Nginx Config:**
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/static/;
        expires 30d;
    }
}
```

ENTREGA:
- Todos os arquivos de configuração
- Documentação de deploy
- Script de deploy automatizado
```

### Prompt 7.2: Testes de Carga e Performance

```
Você é especialista em testes de performance e otimização.

CONTEXTO:
Garantir que sistema suporte carga esperada.

TAREFA:
Criar script de teste de carga usando Locust:

**locustfile.py:**
```python
from locust import HttpUser, task, between
import random

class AcademiaUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login ao iniciar"""
        self.client.post("/auth/login", json={
            "email": f"student{random.randint(1, 100)}@test.com",
            "password": "test123"
        })
    
    @task(3)
    def view_training(self):
        """Visualizar treino"""
        self.client.get("/student/my-training")
    
    @task(2)
    def facial_recognition(self):
        """Simular reconhecimento facial"""
        # Carregar imagem de teste
        with open("test_face.jpg", "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        self.client.post("/api/face/recognize", json={
            "image": f"data:image/jpeg;base64,{image_data}"
        })
    
    @task(1)
    def check_bookings(self):
        """Ver agendamentos"""
        self.client.get("/student/bookings")
    
    @task(1)
    def view_profile(self):
        """Ver perfil"""
        self.client.get("/student/profile")

# Executar: locust -f locustfile.py --host=http://localhost:5000
```

**Cenários de Teste:**
1. **Baixa carga:** 50 usuários simultâneos
2. **Carga normal:** 200 usuários simultâneos
3. **Pico:** 500 usuários simultâneos

**Métricas a Observar:**
- Response time médio < 1s (95th percentile < 2s)
- Taxa de erro < 1%
- CPU < 80%
- Memória < 80%
- Queries ao banco < 100ms

ENTREGA:
- Script de teste completo
- Relatório de performance
- Recomendações de otimização
```

---

## 📚 ANEXO: COMANDOS ÚTEIS E TROUBLESHOOTING

### Comandos de Desenvolvimento

```bash
# Setup inicial
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Migrations
flask db init
flask db migrate -m "Descrição"
flask db upgrade
flask db downgrade

# Rodar aplicação
flask run --debug  # Desenvolvimento
gunicorn app:app  # Produção

# Testes
pytest
pytest --cov=app tests/
pytest -v -s  # Verbose

# Linting
black app/
flake8 app/

# Seeds
flask seed-db
flask calculate-scores  # Calcular health scores manualmente
```

### Troubleshooting Comum

**1. face_recognition não instala:**
```bash
# Instalar CMake primeiro
pip install cmake
pip install dlib
pip install face_recognition
```

**2. Erro de memória no reconhecimento:**
```python
# Reduzir resolução da imagem
image = Image.open(file)
image.thumbnail((800, 800))
```

**3. Webhook não recebe eventos:**
- Verificar URL pública (usar ngrok em dev)
- Validar assinatura HMAC
- Checar logs do servidor

**4. Performance ruim:**
- Adicionar índices no banco
- Implementar cache (Redis)
- Otimizar queries (eager loading)

---

## ✅ CHECKLIST FINAL DE IMPLEMENTAÇÃO

- [ ] Sprint 1: Infraestrutura e modelos ✅
- [ ] Sprint 2: Reconhecimento facial backend ✅
- [ ] Sprint 3: Reconhecimento facial frontend ✅
- [ ] Sprint 4: Prescrição de treino ✅
- [ ] Sprint 5: CRM e retenção ✅
- [ ] Sprint 6: WhatsApp interativo ✅
- [ ] Sprint 7: Deploy e produção ✅

- [ ] Testes unitários (>70% coverage)
- [ ] Testes de integração
- [ ] Testes E2E
- [ ] Documentação técnica
- [ ] Documentação de usuário
- [ ] Treinamento da equipe

---

**FIM DO GUIA DE IMPLEMENTAÇÃO**

*Este guia foi criado para ser usado sequencialmente com LLMs (Gemini/Claude).  
Siga a ordem dos prompts para melhores resultados.*

*Versão: 1.0 | Data: 03/02/2026*