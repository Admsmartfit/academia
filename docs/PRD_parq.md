PRD COMPLETO: Sistema de Triagem de Saúde
Status: Pronto para Desenvolvimento | Versão: 2.0

Sistema: Academia Management System (Flask)

📌 Índice
Visão Geral
Módulo 1: PAR-Q (Musculação)
Módulo 2: Anamnese EMS/Eletrolipólise
Arquitetura Técnica
Plano de Implementação (Fases)
1. Visão Geral
Objetivo
Implementar dois sistemas de triagem de saúde complementares e amigáveis que garantam a segurança dos alunos antes de iniciar atividades físicas, cumprindo requisitos legais sem criar fricção no onboarding.

Quando Aplicar
Modalidade	Questionário	Validade	Checkpoint
Musculação, Yoga, Spinning, etc.	PAR-Q	12 meses	Antes do 1º pagamento
FES (Eletroestimulação)	PAR-Q + Anamnese EMS	12 + 6 meses	Antes do 1º pagamento + Antes de agendar FES
Eletrolipólise	Anamnese Eletro	6 meses	Antes de agendar Eletrolipólise
Princípio de Design
✅ "Segurança com Sorriso" - Proteger sem assustar, informar sem burocratizar

2. Módulo 1: PAR-Q (Musculação)
2.1. Objetivo
Triagem cardiovascular básica para atividades físicas gerais (musculação, aeróbicos, yoga, etc.)

2.2. Requisitos Funcionais
RF-PAR01: Questionário PAR-Q
Prioridade: P0 (Crítico)

7 Perguntas (formato SIM/NÃO com botões grandes):

Algum médico já disse que você possui algum problema de coração e recomendou que só fizesse atividade física sob prescrição médica?
Você sente dores no peito quando pratica atividade física?
No último mês, você sentiu dores no peito quando não estava praticando atividade física?
Você perde o equilíbrio em razão de tonturas ou já perdeu a consciência?
Você tem algum problema ósseo ou articular que poderia ser piorado pela atividade física?
Está tomando atualmente algum medicamento para pressão arterial ou problema cardíaco?
Sabe de alguma outra razão pela qual não deveria fazer atividade física?
Lógica:


if any(resposta == "SIM"):
    status = PENDENTE_MEDICO
    exibir_upload_atestado()
else:
    status = APTO
    liberar_compra()
RF-PAR02: Termo de Consentimento (Musculação)
Prioridade: P0 (Crítico)

Texto (exibido após as perguntas):


🏋️ TERMO DE RESPONSABILIDADE

Olá! Antes de começarmos sua jornada fitness, precisamos 
que você leia e concorde com alguns pontos importantes. 😊

Eu, [NOME], CPF [CPF], declaro que:

✅ Veracidade
   Confirmei que minhas respostas acima são verdadeiras.

✅ Conheço os Riscos
   Entendo que exercícios físicos envolvem riscos naturais 
   (como lesões musculares), e assumo responsabilidade por 
   condições de saúde não informadas.

✅ Orientação Médica
   Se respondi "SIM" a qualquer pergunta, sei que devo 
   consultar um médico antes de começar.

✅ Manterei Vocês Informados
   Vou avisar imediatamente se meu estado de saúde mudar 
   (cirurgias, diagnósticos, medicações novas).

✅ Privacidade (LGPD)
   Autorizo o uso dos meus dados de saúde apenas para 
   gestão de segurança da academia.

[ ] Li, entendi e concordo com tudo acima! 💪

[Confirmar e Continuar]
RF-PAR03: Upload de Atestado
Prioridade: P1 (Alto)

Quando: Se usuário responder SIM a qualquer pergunta

Tela Amigável:


⚠️ Ops! Precisamos de um documento médico

Detectamos que você precisa de uma avaliação médica 
antes de começar. Não se preocupe, é super normal! 🩺

Você pode:
📎 Fazer upload agora (PDF, JPG ou PNG - máx 5MB)
⏰ Enviar depois (pelo WhatsApp ou email)

[Upload de Arquivo] [Enviar Depois]

💡 Dica: Tire uma foto do atestado com seu celular!
RF-PAR04: Validade e Renovação
Prioridade: P1 (Alto)

Validade: 12 meses
Notificação 1: 15 dias antes (Email + WhatsApp)
Notificação 2: 7 dias antes
Notificação 3: 1 dia antes (Banner no dashboard)
Após vencer: Soft-block amigável
Mensagem de Soft-Block:


⏰ Hora de renovar seu PAR-Q!

Ei! Seu questionário de saúde expirou em [DATA]. 
Para sua segurança, precisamos que você renove. 
Leva só 2 minutos! 😊

[Renovar Agora] [Renovar Depois]
3. Módulo 2: Anamnese EMS/Eletrolipólise
3.1. Objetivo
Triagem rigorosa para procedimentos com correntes elétricas (FES/Eletrolipólise), bloqueando contraindicações críticas.

3.2. Quando Aplicar
Antes de agendar primeira aula de FES
Antes de agendar primeira sessão de Eletrolipólise
Mesmo que tenha PAR-Q válido (são questionários complementares)
3.3. Requisitos Funcionais
RF-EMS01: Anamnese Especializada
Prioridade: P0 (Crítico)

Perguntas Específicas (formato SIM/NÃO):

Bloco 1 - CONTRAINDICAÇÕES ABSOLUTAS (Bloqueiam imediatamente):

❌ Você possui marcapasso cardíaco ou desfibrilador implantado?
❌ Você está gestante ou há possibilidade de gravidez?
❌ Você possui epilepsia ou histórico de convulsões?
Bloco 2 - CONTRAINDICAÇÕES RELATIVAS (Precisam atestado):
4. ⚠️ Você tem implante metálico na região onde será aplicada a corrente?
5. ⚠️ Você tem trombose ou problemas graves de circulação?
6. ⚠️ Você tem insuficiência renal ou cardíaca?
7. ⚠️ Você tem alterações de sensibilidade na pele (feridas, queimaduras, cicatrizes recentes)?

Bloco 3 - INFORMAÇÕES COMPLEMENTARES (Eletrolipólise):
8. Você está em jejum neste momento? (apenas para Eletrolipólise)
9. Você bebeu pelo menos 500ml de água hoje? (apenas para Eletrolipólise)

Lógica de Bloqueio:


# CONTRAINDICAÇÕES ABSOLUTAS (q1, q2, q3)
if any([q1, q2, q3]) == "SIM":
    status = BLOQUEADO
    exibir_mensagem_bloqueio_total()
    
# CONTRAINDICAÇÕES RELATIVAS (q4, q5, q6, q7)
elif any([q4, q5, q6, q7]) == "SIM":
    status = PENDENTE_MEDICO
    exibir_upload_atestado_especializado()
    
else:
    status = APTO_EMS
    liberar_agendamento()
RF-EMS02: Mensagens de Bloqueio Amigáveis
Bloqueio Total (Contraindicações absolutas):


🚫 Importante: Este procedimento não é indicado para você

Por segurança, pessoas com marcapasso, gestantes ou 
com epilepsia não podem realizar procedimentos com 
corrente elétrica. 

Mas não se preocupe! Temos muitas outras modalidades 
incríveis para você:

[Ver Outras Modalidades] [Falar com Atendimento]

💡 Em caso de dúvidas, nossa equipe está aqui para ajudar!
Necessita Atestado (Contraindicações relativas):


🩺 Precisamos de um OK médico

Detectamos uma condição que requer autorização médica 
específica para procedimentos com corrente elétrica.

Você pode fazer upload de:
✅ Atestado médico liberando EMS/Eletroestimulação
✅ Laudo de exame recente
✅ Prescrição médica

[Upload de Documento] [Falar com Atendimento]

📞 Dúvidas? WhatsApp: (11) 9999-9999
RF-EMS03: Termo de Consentimento (EMS/Eletrolipólise)
Prioridade: P0 (Crítico)

Texto:


⚡ TERMO DE CONSENTIMENTO - ELETROESTIMULAÇÃO

Olá! Procedimentos com corrente elétrica são super eficazes, 
mas precisam de alguns cuidados especiais. 😊

Eu, [NOME], CPF [CPF], declaro que:

✅ Sem Dispositivos Eletrônicos
   Confirmo que NÃO uso marcapasso ou qualquer 
   dispositivo eletrônico implantado.

✅ Condições Físicas
   Confirmo que NÃO estou gestante e NÃO tenho 
   epilepsia, trombose ou insuficiência renal grave.

✅ Conheço os Riscos
   Entendo que posso sentir:
   • Formigamento ou contração muscular intensa
   • Leve vermelhidão na pele
   • Risco raro de queimadura (se houver má condução)

✅ Vou Comunicar Desconforto
   Me comprometo a avisar imediatamente o profissional 
   se sentir queimação ou desconforto.

✅ Orientações Específicas (Eletrolipólise)
   Seguirei as orientações de hidratação e atividade 
   física para melhores resultados.

[ ] Li, entendi e autorizo o procedimento! ⚡

[Confirmar e Continuar]
RF-EMS04: Checklist Pré-Sessão (Eletrolipólise)
Prioridade: P1 (Alto)

Modal antes de CADA sessão de Eletrolipólise:


💧 Checklist Rápido - Eletrolipólise

Antes de começarmos, confirme:

[ ] Estou bem hidratado(a) (tomei pelo menos 500ml de água)
[ ] NÃO estou em jejum
[ ] NÃO fiz eletrolipólise na mesma área há menos de 48h

✅ Tudo OK! [Confirmar e Iniciar]

❌ Se não puder confirmar, será necessário reagendar.
RF-EMS05: Registro de Parâmetros (Para o Instrutor/Esteticista)
Prioridade: P2 (Médio)

Tela do Profissional após a sessão:


📊 Registro da Sessão - [NOME DO ALUNO]

Modalidade: [FES / Eletrolipólise]
Data/Hora: [AUTO]

⚡ Parâmetros Utilizados:
━━━━━━━━━━━━━━━━━━━━
Frequência: [___] Hz
Intensidade: [___] mA
Duração: [___] minutos
Área tratada: [____________]

📝 Observações (opcional):
[_________________________________]

Aluno relatou desconforto? [ ] Sim [ ] Não

[Salvar Registro]
RF-EMS06: Regras de Negócio Específicas
RN-EMS01 - Periodicidade (Eletrolipólise):


# Bloquear agendamento na mesma área com < 48h
last_session = get_last_eletrolipo_session(user_id, area)
if last_session and (today - last_session.date) < timedelta(hours=48):
    block_with_message(
        "Para sua segurança, aguarde 48 horas entre "
        "sessões na mesma área. 😊"
    )
RN-EMS02 - Idade Mínima:


if user.age < 18 and not user.has_parental_consent:
    block_with_message(
        "Para menores de 18 anos, precisamos de "
        "autorização presencial dos pais. 📝"
    )
RN-EMS03 - Lembrete de Hidratação:


# 30 min antes da sessão
send_whatsapp_reminder(
    "🚰 Lembrete: Beba 500ml de água agora! "
    "Sua sessão começa em 30 minutos."
)
4. Arquitetura Técnica
4.1. Modelos de Banco de Dados
Modelo: HealthScreening (PAR-Q e Anamnese)

class ScreeningType(enum.Enum):
    PARQ = "parq"  # Musculação
    EMS = "ems"    # Eletroestimulação FES
    ELETROLIPO = "eletrolipo"  # Eletrolipólise

class ScreeningStatus(enum.Enum):
    APTO = "apto"
    PENDENTE_MEDICO = "pendente_medico"
    BLOQUEADO = "bloqueado"  # Contraindicação absoluta
    EXPIRADO = "expirado"

class HealthScreening(db.Model):
    __tablename__ = 'health_screenings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tipo de questionário
    screening_type = db.Column(db.Enum(ScreeningType), nullable=False)
    
    # Respostas
    responses = db.Column(db.JSON, nullable=False)
    # Ex PAR-Q: {q1: false, q2: false, ..., q7: false}
    # Ex EMS: {q1: false, q2: false, ..., q9: false}
    
    # Status
    status = db.Column(db.Enum(ScreeningStatus), nullable=False)
    
    # Assinatura Digital
    acceptance_ip = db.Column(db.String(45), nullable=False)
    acceptance_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_terms = db.Column(db.Boolean, default=True)
    
    # Validade
    expires_at = db.Column(db.DateTime, nullable=False)
    # PAR-Q: +12 meses
    # EMS/Eletro: +6 meses
    
    # Atestado (se necessário)
    medical_certificate_url = db.Column(db.String(500))
    medical_certificate_uploaded_at = db.Column(db.DateTime)
    
    # Aprovação manual
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    approval_notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='health_screenings')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
Modelo: EMSSessionLog (Registro de Parâmetros)

class EMSSessionLog(db.Model):
    __tablename__ = 'ems_session_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tipo de procedimento
    procedure_type = db.Column(db.Enum(ScreeningType), nullable=False)  # EMS ou ELETROLIPO
    
    # Parâmetros
    frequency_hz = db.Column(db.Integer)  # Frequência em Hz
    intensity_ma = db.Column(db.Integer)  # Intensidade em mA
    duration_minutes = db.Column(db.Integer)  # Duração
    treatment_area = db.Column(db.String(100))  # Área tratada
    
    # Feedback
    discomfort_reported = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    # Timestamps
    session_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    booking = db.relationship('Booking', backref='ems_logs')
    user = db.relationship('User', foreign_keys=[user_id])
    instructor = db.relationship('User', foreign_keys=[instructor_id])
4.2. Helper Methods no User Model

# Em app/models/user.py

def has_valid_screening(self, screening_type):
    """Verifica se usuário tem screening válido"""
    latest = HealthScreening.query.filter_by(
        user_id=self.id,
        screening_type=screening_type,
        status=ScreeningStatus.APTO
    ).filter(
        HealthScreening.expires_at > datetime.utcnow()
    ).order_by(HealthScreening.created_at.desc()).first()
    
    return latest is not None

def can_access_modality(self, modality):
    """Verifica se pode acessar uma modalidade específica"""
    # PAR-Q obrigatório para todos
    if not self.has_valid_screening(ScreeningType.PARQ):
        return False, "Preencha o questionário de saúde (PAR-Q)"
    
    # Se for FES, precisa também de anamnese EMS
    if modality.name == "Eletroestimulacao FES":
        if not self.has_valid_screening(ScreeningType.EMS):
            return False, "Preencha a anamnese de eletroestimulação"
    
    return True, "OK"

def get_screening_status(self, screening_type):
    """Retorna status do screening"""
    latest = HealthScreening.query.filter_by(
        user_id=self.id,
        screening_type=screening_type
    ).order_by(HealthScreening.created_at.desc()).first()
    
    if not latest:
        return None
    
    if latest.expires_at < datetime.utcnow():
        return ScreeningStatus.EXPIRADO
    
    return latest.status
4.3. Service: ScreeningService

# app/services/screening_service.py

class ScreeningService:
    
    @staticmethod
    def validate_parq_responses(responses):
        """Valida respostas do PAR-Q"""
        has_yes = any(responses.values())
        
        if has_yes:
            return ScreeningStatus.PENDENTE_MEDICO
        return ScreeningStatus.APTO
    
    @staticmethod
    def validate_ems_responses(responses):
        """Valida respostas da anamnese EMS"""
        # Q1, Q2, Q3: Contraindicações absolutas
        absolute_contraindications = [responses.get('q1'), responses.get('q2'), responses.get('q3')]
        
        if any(absolute_contraindications):
            return ScreeningStatus.BLOQUEADO
        
        # Q4-Q7: Contraindicações relativas
        relative_contraindications = [
            responses.get('q4'), responses.get('q5'), 
            responses.get('q6'), responses.get('q7')
        ]
        
        if any(relative_contraindications):
            return ScreeningStatus.PENDENTE_MEDICO
        
        return ScreeningStatus.APTO
    
    @staticmethod
    def can_book_ems_session(user_id, area, target_date):
        """Verifica se pode agendar sessão de eletrolipólise"""
        # Verificar 48h na mesma área
        last_session = EMSSessionLog.query.filter_by(
            user_id=user_id,
            procedure_type=ScreeningType.ELETROLIPO,
            treatment_area=area
        ).order_by(EMSSessionLog.session_date.desc()).first()
        
        if last_session:
            hours_since = (target_date - last_session.session_date).total_seconds() / 3600
            if hours_since < 48:
                return False, f"Aguarde {int(48 - hours_since)}h para nova sessão nesta área"
        
        return True, "OK"
5. Plano de Implementação (Fases)
📋 Fase 1: Fundação (Modelos e Infraestrutura)
Tempo estimado: Implementação base

Tarefas:
 1.1 Criar enum ScreeningType e ScreeningStatus
 1.2 Criar modelo HealthScreening
 1.3 Criar modelo EMSSessionLog
 1.4 Criar migration
 1.5 Adicionar helper methods no User
 1.6 Criar ScreeningService
 1.7 Testar models no console
Output: Estrutura de dados pronta

📋 Fase 2: PAR-Q (Musculação) - MVP
Tempo estimado: Formulário básico

Tarefas:
 2.1 Criar blueprint health_bp
 2.2 Rota GET /health/parq/fill - Formulário
 2.3 Template parq_form.html com:
Barra de progresso
7 perguntas com botões SIM/NÃO
Design mobile-first
 2.4 Rota POST /health/parq/fill - Submit
Capturar IP
Validar respostas
Salvar no banco
Calcular expires_at (+12 meses)
 2.5 Template parq_terms.html - Termo jurídico
 2.6 Lógica de aprovação automática (todas NÃO)
 2.7 Tela de sucesso amigável
Output: PAR-Q funcional (sem upload de atestado ainda)

📋 Fase 3: Upload de Atestado e Aprovação Admin
Tempo estimado: Sistema de upload

Tarefas:
 3.1 Sistema de upload de arquivo
Validação (PDF/JPG/PNG, máx 5MB)
Storage seguro
Nome único
 3.2 Rota POST /health/upload-certificate
 3.3 Painel Admin /admin/health/pending
Lista de PAR-Q pendentes
Visualizar respostas
Visualizar atestado
 3.4 Rotas Admin:
POST /admin/health/approve/<id>
POST /admin/health/reject/<id>
 3.5 Notificações ao aprovar/reprovar
 3.6 Template admin de aprovação
Output: Fluxo completo de atestado médico

📋 Fase 4: Integração com Compra (Checkpoint)
Tempo estimado: Bloqueio inteligente

Tarefas:
 4.1 Middleware/Decorator @requires_parq
 4.2 Aplicar checkpoint antes de /shop/checkout
Verificar se tem PAR-Q válido
Redirecionar para formulário se não tiver
Bloquear se PENDENTE_MEDICO
 4.3 Banner no dashboard quando PAR-Q expirado
 4.4 Template de soft-block amigável
 4.5 Link direto "Renovar PAR-Q"
 4.6 Testar fluxo completo
Output: PAR-Q integrado ao fluxo de compra

📋 Fase 5: Notificações e Renovação
Tempo estimado: Scheduler e mensagens

Tarefas:
 5.1 Job scheduler diário check_expiring_parq()
 5.2 Template WhatsApp: PAR-Q expirando (15 dias)
 5.3 Template Email: PAR-Q expirando
 5.4 Notificação 7 dias antes
 5.5 Notificação 1 dia antes
 5.6 Rota GET /health/parq/renew (pré-preenche dados)
 5.7 Atualizar status para EXPIRADO automaticamente
Output: Sistema de renovação automático

📋 Fase 6: Anamnese EMS (Eletroestimulação)
Tempo estimado: Segundo questionário

Tarefas:
 6.1 Rota GET /health/ems/fill
 6.2 Template ems_form.html
Dividir em 3 blocos visuais
Destacar perguntas críticas (Q1-Q3)
 6.3 Rota POST /health/ems/fill
Validação com bloqueio absoluto
Salvar screening_type=EMS
Expires_at (+6 meses)
 6.4 Template de bloqueio total (contraindicações absolutas)
Mensagem amigável mas firme
Sugerir outras modalidades
 6.5 Integração com upload de atestado especializado
 6.6 Termo jurídico específico EMS
Output: Anamnese EMS funcional

📋 Fase 7: Checkpoint EMS no Agendamento
Tempo estimado: Bloqueio por modalidade

Tarefas:
 7.1 Modificar book_class para verificar modalidade

if modality.name == "Eletroestimulacao FES":
    can_access, msg = user.can_access_modality(modality)
    if not can_access:
        flash(msg, 'warning')
        redirect('/health/ems/fill')
 7.2 Filtrar modalidades na tela de agendamento
Esconder/desabilitar FES se não tem anamnese
Badge "Requer Anamnese EMS"
 7.3 Modal explicativo antes de preencher EMS
 7.4 Testar fluxo: PAR-Q OK → Tentar agendar FES → Redirecionar para EMS
Output: FES bloqueado sem anamnese válida

📋 Fase 8: Checklist Pré-Sessão (Eletrolipólise)
Tempo estimado: Modal dinâmico

Tarefas:
 8.1 Criar modal de checklist pré-sessão
 8.2 Triggar modal ao clicar "Check-in" em aula de Eletrolipólise
 8.3 3 checkboxes obrigatórios:
Hidratação
Não jejum
48h respeitadas
 8.4 Validação antes de permitir check-in
 8.5 Lembrete WhatsApp 30 min antes (hidratação)
Output: Checklist funcional antes de cada sessão

📋 Fase 9: Registro de Parâmetros (Instrutor)
Tempo estimado: Interface do profissional

Tarefas:
 9.1 Rota GET /instructor/ems-log/<booking_id>
 9.2 Template de registro de parâmetros
Campos: frequência, intensidade, duração, área
Campo de observações
Checkbox "Desconforto relatado"
 9.3 Rota POST /instructor/ems-log/save
 9.4 Salvar em EMSSessionLog
 9.5 Visualização de histórico (admin e aluno)
 9.6 Painel admin: Analytics de EMS
Média de parâmetros
Taxa de desconforto
Output: Registro completo de sessões EMS

📋 Fase 10: Regras de Negócio EMS
Tempo estimado: Validações avançadas

Tarefas:
 10.1 Regra: Bloquear <48h na mesma área (Eletrolipólise)
Implementar em ScreeningService.can_book_ems_session()
Aplicar no agendamento
 10.2 Regra: Menores de 18 anos (autorização parental)
Adicionar campo parental_consent_url em User
Bloquear sem autorização
 10.3 Regra: Lembrete de hidratação
Job 30 min antes da sessão
WhatsApp automático
 10.4 Analytics: Frequência de uso EMS por usuário
Output: Regras de segurança implementadas

📋 Fase 11: Polimento e UX
Tempo estimado: Refinamento

Tarefas:
 11.1 Animações suaves entre perguntas
 11.2 Feedback visual ao responder
 11.3 Confirmação de salvamento
 11.4 Textos revisados (tom amigável)
 11.5 Ícones e emojis estratégicos
 11.6 Responsividade mobile testada
 11.7 Acessibilidade (WCAG)
Output: UX polida e amigável

📋 Fase 12: Testes e Lançamento
Tempo estimado: Validação final

Tarefas:
 12.1 Testes unitários (models, services)
 12.2 Testes de integração (fluxos completos)
 12.3 Teste mobile (Android/iOS)
 12.4 Teste de carga (uploads simultâneos)
 12.5 Auditoria de segurança
 12.6 Validação jurídica dos termos
 12.7 Treinamento da equipe
 12.8 Documentação interna
 12.9 Deploy em produção
 12.10 Monitoramento pós-lançamento
Output: Sistema em produção!

6. Resumo de Checkpoints
Ação do Usuário	Checkpoint	Questionário Requerido
Comprar pacote (qualquer)	✅ Antes do pagamento	PAR-Q
Agendar Musculação/Yoga	✅ Se PAR-Q vencido	PAR-Q renovado
Agendar FES pela 1ª vez	✅ Antes de agendar	PAR-Q + Anamnese EMS
Agendar Eletrolipólise	✅ Antes de agendar	PAR-Q + Anamnese Eletro
Check-in Eletrolipólise	✅ Modal pré-sessão	Checklist hidratação
Após sessão EMS (Instrutor)	✅ Registro obrigatório	Parâmetros técnicos
7. Priorização Final
🔥 MVP (Mínimo Viável):
Fase 1 (Modelos)
Fase 2 (PAR-Q básico)
Fase 4 (Checkpoint de compra)
🚀 Lançamento Completo:
Todas as fases até Fase 9
🎯 Melhorias Futuras:
Fase 11 (UX avançada)
Analytics avançado
Integração com telemedicina