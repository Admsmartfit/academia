# PROMPT PARA IA: Sistema de Gestão de Academia

## 🎯 INSTRUÇÕES PARA A IA

Você é um desenvolvedor Python/Flask especializado. Vou fornecer o código de um sistema de gestão de academia e preciso que você implemente melhorias específicas seguindo as melhores práticas.

**Importante:**
- Mantenha o padrão de código existente
- Use apenas bibliotecas já instaladas (ou sugira instalação explícita)
- Teste cada mudança antes de prosseguir
- Forneça código completo e funcional
- Explique brevemente cada mudança

---

## 📁 CONTEXTO DO PROJETO

### Estrutura de Pastas
```
academia/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── user.py
│   │   ├── booking.py
│   │   ├── subscription.py
│   │   └── ...
│   ├── routes/
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── admin/
│   │   └── ...
│   ├── services/
│   │   ├── megaapi.py
│   │   └── ...
│   ├── templates/
│   └── utils/
├── config.py
├── requirements.txt
└── run.py
```

### Stack Tecnológica
- **Backend:** Flask 3.0.0
- **Banco:** SQLite (local)
- **Auth:** Flask-Login
- **Jobs:** APScheduler
- **WhatsApp:** MegaAPI (API REST)
- **Frontend:** Bootstrap 5 + Jinja2

### Modelos Principais
```python
User (id, name, email, phone, role, xp, level)
Booking (id, user_id, schedule_id, date, status, cost_at_booking)
Subscription (id, user_id, package_id, credits_total, credits_used)
ClassSchedule (id, modality_id, weekday, start_time, capacity)
Modality (id, name, credits_cost)
```

---

## 🚀 ETAPAS DE IMPLEMENTAÇÃO

Vou dividir em **5 prompts separados** que você pode usar um de cada vez. Copie cada seção abaixo e cole na IA quando estiver pronto para implementar aquela etapa.

---

# ═══════════════════════════════════════════════════════
# PROMPT 1: CONFIGURADOR MEGAAPI
# ═══════════════════════════════════════════════════════

**TAREFA:** Criar interface admin para configurar e testar integração WhatsApp (MegaAPI)

**ARQUIVOS A CRIAR:**
1. `app/routes/admin/megaapi_config.py` - Blueprint com rotas
2. `app/templates/admin/megaapi/settings.html` - Interface de configuração

**REQUISITOS:**

### 1.1 Blueprint (megaapi_config.py)
Crie um blueprint `admin_megaapi` com:

**Rota GET/POST `/admin/megaapi/`:**
- Buscar status da instância MegaAPI (GET request para `/instance/{instance_key}`)
- Exibir formulário com campos:
  * Host (URL da API)
  * Instance Key
  * Token (Bearer)
- Formulário de teste com:
  * Número de telefone
  * Mensagem de texto
- Ação "Salvar Config" atualiza `megaapi.token`, `megaapi.base_url`, `megaapi.instance_key` (em memória)
- Ação "Enviar Teste" usa `megaapi.send_custom_message()`
- Proteger com `@login_required` e `@admin_required`

**Template HTML:**
Criar interface Bootstrap 5 com 3 cards:
1. **Status da Conexão** - Verde/Vermelho com dados da instância
2. **Credenciais** - Formulário para editar Host/Key/Token
3. **Teste de Envio** - Form para testar envio de mensagem

**CÓDIGO BASE MEGAAPI:**
```python
# app/services/megaapi.py (já existe)
class MegapiService:
    def __init__(self):
        self.base_url = os.getenv('MEGAAPI_BASE_URL')
        self.token = os.getenv('MEGAAPI_TOKEN')
        self.instance_key = os.getenv('MEGAAPI_INSTANCE_KEY')
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def send_custom_message(self, phone: str, message: str, user_id=None):
        # Já implementado
        pass
```

**REGISTRAR BLUEPRINT:**
Em `app/__init__.py`, adicionar:
```python
from app.routes.admin.megaapi_config import megaapi_config_bp
app.register_blueprint(megaapi_config_bp)
```

**ADICIONAR AO MENU:**
Em `app/templates/admin/base.html`, adicionar link na sidebar:
```html
<li class="nav-item">
    <a href="{{ url_for('admin_megaapi.settings') }}" class="nav-link">
        <i class="fab fa-whatsapp"></i> Config WhatsApp
    </a>
</li>
```

**VALIDAÇÃO:**
- [ ] Rota `/admin/megaapi` acessível
- [ ] Status da conexão exibido
- [ ] Formulário permite editar credenciais
- [ ] Teste de envio funciona
- [ ] Flash messages aparecem

**FORNEÇA:**
1. Código completo do blueprint
2. Código completo do template
3. Instruções para registrar/testar

---

# ═══════════════════════════════════════════════════════
# PROMPT 2: MENSAGENS INTERATIVAS WHATSAPP
# ═══════════════════════════════════════════════════════

**TAREFA:** Implementar botões interativos (List Messages) no WhatsApp

**CONTEXTO:**
Atualmente os lembretes de aula enviam apenas texto com links. Queremos usar **List Messages** da MegaAPI para criar menus interativos.

**ARQUIVOS A MODIFICAR:**
1. `app/services/megaapi.py` - Adicionar método `send_list_message()`
2. `app/utils/scheduler.py` - Atualizar lembrete 2h para usar botões
3. `app/routes/webhooks.py` - Processar respostas dos usuários

**REQUISITOS:**

### 2.1 Implementar send_list_message

Adicionar na classe `MegapiService`:

```python
def send_list_message(
    self,
    phone: str,
    text: str,
    button_text: str,
    sections: List[dict],
    user_id: Optional[int] = None
) -> Dict:
    """
    Envia mensagem com menu interativo (List Message).
    
    Formato sections:
    [
        {
            "title": "Ações",
            "rows": [
                {
                    "title": "Confirmar",
                    "rowId": "confirm_123",
                    "description": "Garantir vaga"
                }
            ]
        }
    ]
    """
    phone = self._format_phone(phone)
    
    payload = {
        "messageData": {
            "to": phone,
            "text": text,
            "buttonText": button_text,
            "title": "Ação Necessária",
            "description": "Selecione uma opção",
            "sections": sections,
            "listType": 0
        }
    }
    
    # POST para /sendMessage/{instance_key}/listMessage
    # Usar self.base_url, self.headers
    # Logar com self._log_message()
    # Retornar response.json() ou None
```

### 2.2 Atualizar Scheduler

Em `app/utils/scheduler.py`, na função `class_reminders_2h()`:

**Substituir o envio de template por:**
```python
sections = [
    {
        "title": "Gerenciar Aula",
        "rows": [
            {
                "title": "✅ Confirmar Presença",
                "rowId": f"confirm_{booking.id}",
                "description": "Garante sua vaga"
            },
            {
                "title": "❌ Cancelar Aula",
                "rowId": f"cancel_{booking.id}",
                "description": "Libera vaga p/ outro"
            }
        ]
    }
]

text = f"""Olá {booking.user.name.split()[0]}! 🔔

Lembrete: Sua aula de *{booking.schedule.modality.name}* é daqui a 2 horas!

📅 {booking.date.strftime('%d/%m/%Y')}
⏰ {booking.schedule.start_time.strftime('%H:%M')}
👨‍🏫 {booking.schedule.instructor.name}"""

megaapi.send_list_message(
    phone=booking.user.phone,
    text=text,
    button_text="Opções",
    sections=sections,
    user_id=booking.user_id
)
```

### 2.3 Webhook para Respostas

Atualizar `app/routes/webhooks.py`, rota `/megaapi/incoming`:

```python
@webhooks_bp.route('/megaapi/incoming', methods=['POST'])
def megaapi_incoming():
    data = request.get_json()
    
    # Verificar se é resposta de lista
    message = data.get('message', {})
    if 'listResponseMessage' in message:
        response = message['listResponseMessage']
        row_id = response.get('singleSelectReply', {}).get('selectedRowId')
        
        if row_id:
            # Parsear "confirm_123" ou "cancel_123"
            action, booking_id = row_id.split('_')
            booking = Booking.query.get(int(booking_id))
            
            if action == 'cancel' and booking and booking.can_cancel:
                booking.cancel(reason="Cancelado via WhatsApp")
                
                # Enviar confirmação
                megaapi.send_custom_message(
                    booking.user.phone,
                    f"✅ Aula cancelada! Crédito estornado."
                )
    
    return jsonify({'status': 'ok'}), 200
```

**VALIDAÇÃO:**
- [ ] Método `send_list_message()` implementado
- [ ] Lembrete 2h usa botões interativos
- [ ] Webhook processa cliques
- [ ] Cancelamento via WhatsApp funciona

**FORNEÇA:**
1. Código completo do método
2. Código atualizado do scheduler
3. Código atualizado do webhook

---

# ═══════════════════════════════════════════════════════
# PROMPT 3: VALIDAÇÃO TELEFONE + BACKUP AUTOMÁTICO
# ═══════════════════════════════════════════════════════

**TAREFA:** Adicionar validação de telefone no cadastro e backup automático do banco

**ARQUIVOS A MODIFICAR/CRIAR:**
1. `app/routes/auth.py` - Validar telefone no registro
2. `app/utils/backup.py` (CRIAR) - Funções de backup
3. `app/utils/scheduler.py` - Adicionar job de backup

**REQUISITOS:**

### 3.1 Validação de Telefone

Em `app/routes/auth.py`, rota `/register`:

**Adicionar função de validação:**
```python
import re

def validate_phone(phone: str) -> str:
    """Valida e formata telefone para padrão 5511999999999"""
    clean = re.sub(r'\D', '', phone)
    
    if not clean.startswith('55'):
        clean = '55' + clean
    
    if len(clean) != 13:
        raise ValueError('Telefone inválido. Use: (11) 99999-9999')
    
    return clean
```

**Usar antes de criar usuário:**
```python
try:
    phone_formatted = validate_phone(phone)
except ValueError as e:
    flash(str(e), 'danger')
    return render_template('auth/register.html')

user = User(
    name=name,
    email=email,
    phone=phone_formatted,  # USAR FORMATADO
    ...
)
```

### 3.2 Backup Automático

**Criar arquivo `app/utils/backup.py`:**
```python
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """Cria backup do SQLite"""
    db_path = 'instance/academia.db'
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'academia_backup_{timestamp}.db'
    backup_path = backup_dir / backup_name
    
    shutil.copy2(db_path, backup_path)
    print(f"[BACKUP] Criado: {backup_path}")
    
    # Manter apenas 7 últimos
    backups = sorted(backup_dir.glob('academia_backup_*.db'))
    for old in backups[:-7]:
        old.unlink()
        print(f"[BACKUP] Removido: {old.name}")
    
    return True

def restore_database(backup_filename: str):
    """Restaura backup"""
    backup_path = Path('backups') / backup_filename
    db_path = 'instance/academia.db'
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup não encontrado: {backup_filename}")
    
    # Backup de emergência do atual
    if Path(db_path).exists():
        emergency = f'instance/academia_emergency_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(db_path, emergency)
    
    shutil.copy2(backup_path, db_path)
    return True
```

### 3.3 Adicionar ao Scheduler

Em `app/utils/scheduler.py`:

```python
from app.utils.backup import backup_database

@scheduler.scheduled_job(CronTrigger(hour=3, minute=0))
def daily_backup():
    with app.app_context():
        print("[SCHEDULER] Iniciando backup...")
        backup_database()
```

**CRIAR PASTA:**
```bash
mkdir backups
echo "backups/" >> .gitignore
```

**VALIDAÇÃO:**
- [ ] Telefone validado no cadastro (formato 5511999999999)
- [ ] Erro claro se inválido
- [ ] Backup criado às 3h da manhã
- [ ] Apenas 7 backups mantidos
- [ ] Pasta backups/ criada

**FORNEÇA:**
1. Código de validação de telefone
2. Código completo do backup.py
3. Instruções para testar manualmente

---

# ═══════════════════════════════════════════════════════
# PROMPT 4: PRESCRIÇÃO DE TREINO (OPCIONAL)
# ═══════════════════════════════════════════════════════

**TAREFA:** Instrutor pode criar fichas de treino para alunos

**ARQUIVOS A CRIAR:**
1. `app/models/training_plan.py` - Modelo de ficha
2. `app/routes/instructor.py` - Rotas (ou criar training.py)
3. `app/templates/instructor/training_form.html` - Form de criação
4. `app/templates/student/training_plans.html` - Visualização aluno

**REQUISITOS:**

### 4.1 Modelo TrainingPlan

```python
class TrainingPlan(db.Model):
    __tablename__ = 'training_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # "Treino A - Peito"
    description = db.Column(db.Text)
    exercises = db.Column(db.JSON)  # Lista de exercícios
    pdf_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='training_plans')
    instructor = db.relationship('User', foreign_keys=[instructor_id])

# Formato exercises:
# [
#     {
#         "name": "Supino Reto",
#         "sets": 4,
#         "reps": "10-12",
#         "rest": "90s",
#         "notes": "Controlar descida"
#     }
# ]
```

### 4.2 Rota Instrutor

```python
@instructor_bp.route('/training/create/<int:student_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_training_plan(student_id):
    student = User.query.get_or_404(student_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Processar exercícios (até 10)
        exercises = []
        for i in range(10):
            ex_name = request.form.get(f'exercise_name_{i}')
            if ex_name:
                exercises.append({
                    'name': ex_name,
                    'sets': request.form.get(f'exercise_sets_{i}'),
                    'reps': request.form.get(f'exercise_reps_{i}'),
                    'rest': request.form.get(f'exercise_rest_{i}'),
                    'notes': request.form.get(f'exercise_notes_{i}')
                })
        
        # Upload PDF (opcional)
        pdf_url = None
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file.filename:
                # Salvar em static/uploads/training/
                pdf_url = save_training_pdf(file, student_id)
        
        plan = TrainingPlan(
            user_id=student_id,
            instructor_id=current_user.id,
            name=name,
            description=description,
            exercises=exercises,
            pdf_url=pdf_url,
            is_active=True
        )
        
        db.session.add(plan)
        db.session.commit()
        
        flash('Ficha criada!', 'success')
        return redirect(url_for('instructor.dashboard'))
    
    return render_template('instructor/training_form.html', student=student)
```

### 4.3 Visualização Aluno

```python
@student_bp.route('/training')
@login_required
def my_training():
    plans = TrainingPlan.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(TrainingPlan.created_at.desc()).all()
    
    return render_template('student/training_plans.html', plans=plans)
```

**TEMPLATE (resumido):**
Form com campos repetíveis para exercícios + upload PDF + botão salvar.

**VALIDAÇÃO:**
- [ ] Modelo criado e migrado
- [ ] Instrutor cria ficha
- [ ] Aluno visualiza suas fichas
- [ ] PDF opcional funciona

**FORNEÇA:**
1. Código do modelo
2. Rotas completas
3. Template básico (estrutura HTML)

---

# ═══════════════════════════════════════════════════════
# PROMPT 5: QR CODE DE ACESSO (OPCIONAL)
# ═══════════════════════════════════════════════════════

**TAREFA:** Aluno mostra QR Code dinâmico que instrutor scaneia para check-in

**DEPENDÊNCIA:**
```bash
pip install qrcode[pil]==7.4.2 PyJWT==2.8.0
```

**ARQUIVOS A CRIAR:**
1. `app/utils/qrcode_generator.py` - Gerador de QR Code
2. `app/routes/access.py` - Rota de check-in via QR
3. `app/templates/student/qrcode.html` - Exibir QR Code

**REQUISITOS:**

### 5.1 Gerador de QR Code

```python
import qrcode
import io
import base64
from datetime import datetime, timedelta
import jwt

def generate_access_qrcode(user_id: int) -> str:
    """Gera QR Code válido por 2 minutos"""
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=2),
        'type': 'access'
    }
    
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    url = f"http://localhost:5000/access/checkin?token={token}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"
```

### 5.2 Rota de Check-in

```python
# app/routes/access.py
from flask import Blueprint, request, redirect, url_for, flash
import jwt

access_bp = Blueprint('access', __name__, url_prefix='/access')

@access_bp.route('/checkin')
def qrcode_checkin():
    token = request.args.get('token')
    
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        # Buscar aula de hoje
        today = datetime.now().date()
        booking = Booking.query.filter_by(
            user_id=user_id,
            date=today,
            status=BookingStatus.CONFIRMED
        ).first()
        
        if not booking:
            flash('Nenhuma aula agendada hoje', 'warning')
            return redirect(url_for('auth.login'))
        
        booking.checkin()
        flash(f'Check-in OK! +{booking.xp_earned} XP', 'success')
        return redirect(url_for('student.dashboard'))
        
    except jwt.ExpiredSignatureError:
        flash('QR Code expirado', 'warning')
        return redirect(url_for('auth.login'))
    except jwt.InvalidTokenError:
        flash('QR Code inválido', 'danger')
        return redirect(url_for('auth.login'))
```

### 5.3 Exibir QR Code

```python
@student_bp.route('/qrcode')
@login_required
def my_qrcode():
    from app.utils.qrcode_generator import generate_access_qrcode
    qr_code = generate_access_qrcode(current_user.id)
    return render_template('student/qrcode.html', qr_code=qr_code)
```

**TEMPLATE:**
```html
<div class="text-center">
    <h2>Meu QR Code</h2>
    <img src="{{ qr_code }}" class="img-fluid">
    <div class="alert alert-info">
        ⏱️ Expira em 2 minutos
    </div>
    <button onclick="location.reload()">🔄 Gerar Novo</button>
</div>
```

**VALIDAÇÃO:**
- [ ] QR Code gerado
- [ ] Expira em 2 minutos
- [ ] Check-in funciona ao scanear
- [ ] XP creditado

**FORNEÇA:**
1. Código do gerador
2. Código da rota de check-in
3. Instruções de teste

---

# ═══════════════════════════════════════════════════════
# DICAS GERAIS PARA TODAS AS ETAPAS
# ═══════════════════════════════════════════════════════

**QUANDO FORNECER CÓDIGO:**
1. ✅ Sempre forneça código completo e funcional
2. ✅ Mantenha imports organizados no topo
3. ✅ Use type hints quando possível
4. ✅ Adicione docstrings em funções importantes
5. ✅ Siga PEP 8 (formatação Python)

**QUANDO TESTAR:**
1. ✅ Após cada função implementada
2. ✅ Antes de commitar
3. ✅ Com dados reais (não mocks)

**SE ENCONTRAR ERRO:**
1. 🔍 Mostrar traceback completo
2. 🔍 Verificar logs do Flask
3. 🔍 Validar formato de dados
4. 🔍 Testar endpoint manualmente (Postman/curl)

**PADRÃO DE RESPOSTA ESPERADO:**

```markdown
## ✅ Implementação Concluída

### Arquivos Modificados:
- `app/routes/admin/megaapi_config.py` (CRIADO)
- `app/templates/admin/megaapi/settings.html` (CRIADO)
- `app/__init__.py` (atualizado linha 45)

### Código Principal:
[Inserir código aqui com comentários]

### Como Testar:
1. Reiniciar servidor Flask
2. Login como admin
3. Acessar /admin/megaapi
4. ...

### Possíveis Problemas:
- Se erro X: fazer Y
- Se erro Z: verificar W
```

---

# 📋 CHECKLIST FINAL

Após implementar todas as 5 etapas:

- [ ] **Etapa 1:** Configurador MegaAPI funcionando
- [ ] **Etapa 2:** Botões interativos no WhatsApp
- [ ] **Etapa 3:** Validação telefone + Backup diário
- [ ] **Etapa 4:** Prescrição de treino (opcional)
- [ ] **Etapa 5:** QR Code de acesso (opcional)

**Teste End-to-End:**
1. Cadastrar novo aluno
2. Comprar pacote
3. Agendar aula
4. Receber lembrete com botões
5. Fazer check-in
6. Verificar XP creditado
7. Verificar backup criado

---

**IMPORTANTE:** Use cada PROMPT (1-5) separadamente. Não tente implementar tudo de uma vez. Valide cada etapa antes de prosseguir para a próxima.

Boa implementação! 🚀