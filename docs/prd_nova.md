DOCUMENTO DE REQUISITOS DE PRODUTO
Sistema de Gestão de Academia v2.0
"Tech & Retention Platform"




Versão
2.0
Status
Planejamento Detalhado
Data
03 de February de 2026
Projeto
AdmSmartFit - Expansão Tecnológica
Autor
Equipe de Produto
Classificação
Confidencial
Validade
Q1-Q2 2026
Última Revisão
03/02/2026





Objetivo Estratégico
Transformar o sistema de gestão de academia em uma plataforma de alta tecnologia com foco em retenção de alunos através de reconhecimento facial, prescrição automatizada de treinos, CRM inteligente e engajamento via mensagens interativas no WhatsApp.

SUMÁRIO EXECUTIVO
Contexto do Projeto
O mercado de fitness apresenta taxas de churn (evasão) superiores a 50% ao ano, sendo que 70% dos novos alunos abandonam a academia nos primeiros 3 meses. Estudos da IHRSA (International Health, Racquet & Sportsclub Association) demonstram que academias com sistemas de acompanhamento digital apresentam 35% menos evasão.

Problema Identificado
Check-in manual consome 40% do tempo do instrutor
Falta de dados confiáveis sobre frequência real dos alunos
Ausência de alertas preventivos para alunos em risco de evasão
Comunicação passiva sem engajamento (taxa de resposta < 5%)
Prescrição de treino em papel dificulta acompanhamento e evolução

Solução Proposta
Implementação de quatro pilares tecnológicos integrados:
• Reconhecimento Facial Biométrico: Check-in automático via câmera, eliminando processos manuais e garantindo dados 100% confiáveis
• Prescrição Digital de Treino: Interface mobile-first para visualização do treino do dia, com vídeos e progressão automática
• CRM Inteligente de Retenção: Sistema preditivo que identifica alunos em risco e aciona réguas de relacionamento
• Mensageria Interativa WhatsApp: Comunicação bidirecional com botões e listas nativas, aumentando engajamento em 8x

Impacto Esperado
Métrica
Baseline Atual
Meta 6 Meses
Taxa de Churn (90 dias)
45%
20%
Taxa de Resposta Mensagens
5%
40%
Tempo Instrutor em Admin
40%
5%


1. ANÁLISE DE MERCADO E BENCHMARKING
1.1 Panorama do Mercado de Fitness Tech
O mercado global de fitness tech está projetado para alcançar US$ 59.23 bilhões até 2027 (CAGR 23.3%). No Brasil, segundo dados da ACAD (Associação Brasileira de Academias), existem mais de 34.500 academias, mas apenas 12% utilizam tecnologia de reconhecimento facial ou sistemas preditivos de retenção.

1.2 Análise Competitiva - Principais Soluções
Solução
Reconhecimento Facial
CRM Preditivo
WhatsApp Interativo
Tecnofit
❌ Não
⚠️ Básico
❌ Não
Nexur Wellness
✅ Sim
⚠️ Básico
⚠️ Parcial
Evolution
❌ Não
❌ Não
✅ Sim
AdmSmartFit v2.0
✅ Sim
✅ Avançado
✅ Sim


1.3 Diferenciais Competitivos
• Integração Total: Única solução que integra reconhecimento facial + prescrição digital + CRM preditivo + WhatsApp nativo
• Custo-Benefício: Implementação 60% mais econômica que soluções enterprise (Nexur, Tecnofit)
• Tecnologia Open-Source: Baseado em face_recognition (99.38% de acurácia, usado pelo FBI), Flask e SQLAlchemy
• Adaptação ao Mercado Brasileiro: Integração nativa com MegaAPI (WhatsApp Business) e NuPay (pagamentos)
• Escalabilidade: Arquitetura modular permite crescimento de 100 a 10.000 alunos sem reestruturação

2. ARQUITETURA TÉCNICA E STACK TECNOLÓGICO
2.1 Stack Tecnológico Atual
Backend: Python 3.11+ com Flask 3.0 — Framework web leve e modular
ORM: SQLAlchemy 2.0 — Gerenciamento de banco de dados com migrations Alembic
Database: SQLite (dev) / PostgreSQL (prod) — Fácil migração para produção
Frontend: Jinja2 Templates + Bootstrap 5 — Interface responsiva e moderna
Autenticação: Flask-Login + Werkzeug — Sistema de sessões seguro
Tarefas Agendadas: APScheduler — Cron jobs para automações
API Externa: MegaAPI v2 (WhatsApp) — Mensageria oficial do WhatsApp Business

2.2 Novas Dependências v2.0
Biblioteca
Versão
Propósito
Prioridade
face_recognition
1.3.0+
Biblioteca de reconhecimento facial (dlib + OpenCV)
CRÍTICO
opencv-python
4.8.0+
Processamento de imagem e câmera
CRÍTICO
numpy
1.24.0+
Operações matriciais para encodings
CRÍTICO
Pillow
10.0.0+
Manipulação de imagens
RECOMENDADO
scipy
1.11.0+
Cálculos de distância facial
OPCIONAL


2.3 Arquitetura em Camadas
A aplicação segue o padrão MVC (Model-View-Controller) com camada de serviços:

1. Camada de Apresentação (Views):
Templates Jinja2 responsivos
Rotas Flask organizadas por módulo (admin, instructor, student)
APIs REST para comunicação assíncrona
Interface do Totem (modo kiosk)
2. Camada de Controle (Routes):
app/routes/admin/ - Gestão administrativa e CRM
app/routes/instructor/ - Prescrição de treino e totem
app/routes/student/ - Dashboard do aluno
app/routes/webhooks.py - Recebimento de eventos WhatsApp
3. Camada de Serviços (Services):
app/services/face_service.py - Reconhecimento facial
app/services/megaapi.py - Integração WhatsApp
app/services/crm_service.py - Lógica de retenção
app/services/training_service.py - Prescrição de treino
4. Camada de Dados (Models):
app/models/user.py - Usuários e encodings faciais
app/models/training.py - Exercícios e prescrições
app/models/booking.py - Agendamentos e check-ins
app/models/crm.py - Leads e funil de vendas
5. Camada de Persistência:
SQLAlchemy ORM
Migrations Alembic versionadas
Backup automático diário

2.4 Fluxo de Dados - Reconhecimento Facial
1. Captura → Câmera do totem captura frame via getUserMedia() (WebRTC)
2. Envio → POST /instructor/totem com imagem base64
3. Processamento → FaceService.recognize() extrai encodings e compara com banco
4. Identificação → Se match > 0.4 (60% similaridade), retorna user_id
5. Check-in → Sistema busca Booking ativo e marca como COMPLETED
6. Gamificação → Atribui XP, verifica conquistas, atualiza streak
7. Notificação → Envia mensagem WhatsApp de confirmação (opcional)
8. Analytics → Registra log de acesso para CRM preditivo

3. MÓDULO 1: RECONHECIMENTO FACIAL BIOMÉTRICO
3.1 Visão Geral Técnica
O reconhecimento facial utiliza a biblioteca face_recognition (baseada em dlib), que implementa o modelo ResNet-34 treinado no dataset Labeled Faces in the Wild (LFW) com acurácia de 99.38%. O sistema converte faces em vetores de 128 dimensões (face encodings) e usa distância euclidiana para comparação.

3.2 Requisitos Funcionais Detalhados
RF-FR-001: Cadastro de Face (Enrollment)
O aluno DEVE poder enviar foto via upload no perfil
O sistema DEVE validar qualidade da imagem (resolução mín. 640x480)
O sistema DEVE detectar exatamente 1 face na imagem
O sistema DEVE gerar face_encoding de 128 dimensões
O encoding DEVE ser armazenado como BLOB ou TEXT no campo User.face_encoding
O sistema DEVE permitir re-cadastro (atualização) da face

RF-FR-002: Totem de Reconhecimento
Interface web DEVE acessar câmera via navigator.mediaDevices.getUserMedia()
DEVE capturar frame a cada 2 segundos automaticamente
DEVE enviar frame como base64 via POST para /api/recognize
DEVE exibir nome do aluno reconhecido em tempo real
DEVE funcionar em modo fullscreen (kiosk mode)
DEVE ter fallback para check-in manual via QR Code

RF-FR-003: Check-in Automático
Ao reconhecer face, DEVE buscar Booking ativo para ±30min do horário atual
Se encontrado, DEVE alterar status para COMPLETED
DEVE registrar timestamp exato do check-in
DEVE conceder XP configurado (padrão: 10 XP)
DEVE verificar e atribuir conquistas (ex: "3 dias seguidos")
Se não houver booking, DEVE verificar créditos e criar agendamento avulso

RF-FR-004: Tolerância e Segurança
Threshold padrão: 0.6 (valores menores = mais rigoroso)
DEVE permitir configuração do threshold por administrador
DEVE registrar confidence score de cada reconhecimento
DEVE impedir check-in duplicado no mesmo dia (configurable)
DEVE ter rate limit: máx 10 tentativas/minuto por IP

3.3 Requisitos Não Funcionais
ID
Categoria
Requisito
NFR-FR-001
Performance
Reconhecimento DEVE ocorrer em < 2 segundos (95th percentile)
NFR-FR-002
Escalabilidade
Suportar até 50 reconhecimentos simultâneos sem degradação
NFR-FR-003
Disponibilidade
Sistema de check-in DEVE ter uptime ≥ 99.5%
NFR-FR-004
Privacidade
Encodings DEVEM ser criptografados em repouso (AES-256)
NFR-FR-005
Auditoria
Todos os acessos DEVEM ser logados com timestamp e IP
NFR-FR-006
LGPD
Imagens originais NÃO DEVEM ser armazenadas, apenas encodings


3.4 Modelagem de Dados - Alterações no Schema
Alterações na tabela User:
class User(db.Model):
    # ... campos existentes ...
    
    # NOVO: Face encoding (128 dimensões)
    face_encoding = db.Column(db.LargeBinary, nullable=True)
    
    # NOVO: Metadados do cadastro facial
    face_registered_at = db.Column(db.DateTime, nullable=True)
    face_confidence_score = db.Column(db.Float, nullable=True)
    
    # NOVO: Histórico de reconhecimentos
    recognitions = db.relationship("FaceRecognition", backref="user")

Nova tabela FaceRecognition:
class FaceRecognition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    confidence = db.Column(db.Float)
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.String(200))
    success = db.Column(db.Boolean, default=True)

4. MÓDULO 2: PRESCRIÇÃO DIGITAL DE TREINO
4.1 Visão do Produto
Substituir a ficha de treino em papel por uma interface digital mobile-first, onde o instrutor prescreve exercícios com vídeos, e o aluno visualiza automaticamente o treino do dia sem necessidade de confirmação manual. A conclusão é inferida pelo reconhecimento facial no check-in.

4.2 User Stories
Como Instrutor, quero criar prescrição de treino, para que o aluno tenha um programa estruturado e evolua de forma controlada
[Prioridade: ALTA]

Como Instrutor, quero incluir vídeos de YouTube nos exercícios, para que o aluno execute com técnica correta mesmo sem supervisão
[Prioridade: MÉDIA]

Como Aluno, quero ver meu treino do dia no celular, para que não precise carregar papel e tenha acesso fácil às orientações
[Prioridade: ALTA]

Como Aluno, quero ver minha evolução (cargas e repetições), para que me motive a continuar e perceba meu progresso
[Prioridade: MÉDIA]

Como Sistema, quero marcar treino como realizado via facial, para que dados de frequência sejam 100% precisos
[Prioridade: ALTA]

4.3 Modelagem de Dados
Tabela: Exercise
• id: Integer (PK)
• name: String(100) - Nome do exercício
• muscle_group: Enum [CHEST, BACK, LEGS, SHOULDERS, ARMS, CORE]
• video_url: String(200) - Link YouTube/Vimeo
• description: Text - Instruções de execução
• equipment: String(50) - Ex: "Barra, Halteres"

Tabela: TrainingPlan
• id: Integer (PK)
• user_id: FK -> User
• instructor_id: FK -> User (instrutor que criou)
• goal: Enum [HYPERTROPHY, FAT_LOSS, STRENGTH, HEALTH]
• valid_from: Date
• valid_until: Date
• is_active: Boolean

Tabela: WorkoutSession
• id: Integer (PK)
• training_plan_id: FK -> TrainingPlan
• name: String(50) - Ex: "Treino A - Peito/Tríceps"
• day_of_week: Integer [0-6] ou NULL (se for ABC)
• order: Integer - Ordem de execução

Tabela: WorkoutExercise
• id: Integer (PK)
• workout_session_id: FK -> WorkoutSession
• exercise_id: FK -> Exercise
• sets: Integer
• reps: String(20) - Ex: "12-15", "máximo"
• rest_seconds: Integer
• notes: Text - Observações do instrutor
• order: Integer

4.4 Interface do Aluno (Mobile)
Rota: /student/my-training

✓ Card grande para cada exercício com imagem/thumbnail do vídeo
✓ Tap no card expande e exibe vídeo inline (sem sair da página)
✓ Exibição de séries, repetições e descanso de forma clara
✓ Indicador visual de "Treino de Hoje" baseado no dia da semana
✓ Histórico dos últimos 7 treinos realizados (com datas)
✓ Badge de streak: "🔥 5 dias seguidos"
✓ Botão para reportar dor/desconforto (envia notificação ao instrutor)

5. MÓDULO 3: CRM INTELIGENTE E RETENÇÃO
5.1 Fundamentos de Prevenção de Churn
Estudos demonstram que a intervenção precoce reduz churn em até 40%. O sistema deve identificar padrões comportamentais de risco (frequência decrescente, não-comparecimento em aulas agendadas) e acionar automaticamente réguas de relacionamento.

5.2 Algoritmo de Health Score
O Health Score é calculado semanalmente e varia de 0 a 100:

Frequência Semanal (peso 40%):
• 4+ check-ins = 40 pontos
• 3 check-ins = 30 pontos
• 2 check-ins = 20 pontos
• 1 check-in = 10 pontos
• 0 check-ins = 0 pontos

Engajamento (peso 30%):
• Respondeu mensagens = +15 pontos
• Visualizou treino = +10 pontos
• Completou avaliação física = +5 pontos

Financeiro (peso 20%):
• Pagamento em dia = 20 pontos
• Atraso < 7 dias = 10 pontos
• Atraso > 7 dias = 0 pontos

Histórico (peso 10%):
• Tempo de matrícula > 6 meses = +10 pontos

5.3 Segmentação de Alunos
Segmento
Health Score
Critério Adicional
Ação
🟢 Saudável
≥ 70
Frequência regular
Incentivo e upsell
🟡 Em Risco
40-69
Queda de frequência
Mensagem motivacional
🔴 Crítico
< 40
Ausente > 7 dias
Ligação + desconto
⚫ Churn
—
Cancelou plano
Win-back campaign


5.4 Réguas de Relacionamento Automatizadas
Boas-vindas (D+1):
→ Mensagem de boas-vindas com vídeo do proprietário
→ Tutorial de uso do reconhecimento facial
→ Link para agendamento de avaliação física

Engajamento (D+15):
→ Pesquisa de satisfação com 3 perguntas
→ Solicitação de feedback sobre instrutor
→ Oferta de aula experimental de nova modalidade

Recuperação Leve (Ausente 5 dias):
→ Mensagem: "Sentimos sua falta! Tudo bem?"
→ Sugestão de horários alternativos
→ Lembrança dos benefícios do treino regular

Recuperação Crítica (Ausente 10 dias):
→ Mensagem do instrutor pessoal
→ Oferta de sessão grátis com personal
→ Questionamento sobre dificuldades/barreiras

Última Tentativa (Ausente 20 dias):
→ Ligação telefônica da recepção
→ Desconto de 30% no próximo mês
→ Convite para evento especial da academia

5.5 Gestão de Leads e Funil de Vendas
Novos campos e status para controle do funil:

NEW → Lead captado (landing page, indicação)
CONTACTED → Primeiro contato realizado
VISITED → Visitou a academia
TRIAL → Agendou aula experimental
PROPOSAL → Recebeu proposta comercial
WON → Converteu em aluno
LOST → Não converteu

6. MÓDULO 4: MENSAGERIA INTERATIVA (WhatsApp)
6.1 Upgrade da Integração MegaAPI
A MegaAPI v2 (WhatsApp Business API oficial) suporta mensagens interativas com botões e listas. Estudos mostram que mensagens com botões têm taxa de resposta 8x maior que mensagens de texto simples (40% vs 5%).

6.2 Tipos de Mensagens Suportadas
Tipo
Descrição
Engajamento
Text Message
Mensagem de texto simples (já implementado)
Baixo
Button Message
Até 3 botões de ação rápida
Médio
List Message
Menu com até 10 opções
Alto
Template Message
Mensagens pré-aprovadas pelo Meta
Médio


6.3 Exemplos de Fluxos Interativos
Fluxo: Lembrete de Aula
Mensagem: "Você tem aula agendada hoje às 18h"
Botões:
  [✅ Vou comparecer]
  [❌ Preciso cancelar]
  [📅 Reagendar]

Se clicar "Cancelar":
  → Sistema libera vaga
  → Envia opções de reagendamento
Se clicar "Reagendar":
  → Exibe lista de horários disponíveis

Fluxo: Renovação de Plano
Mensagem: "Seu plano vence em 3 dias"
Botões:
  [💳 Renovar agora]
  [📞 Falar com consultor]
  [⏰ Lembrar amanhã]

Se clicar "Renovar agora":
  → Gera link de pagamento NuPay/Pix
  → Envia comprovante automático via webhook

Fluxo: Pesquisa de Satisfação
Mensagem: "Como você avalia sua experiência?"
Lista:
  1️⃣ Excelente - Recomendo!
  2️⃣ Boa - Satisfeito
  3️⃣ Regular - Pode melhorar
  4️⃣ Ruim - Insatisfeito

Se responder "Ruim":
  → Aciona alerta para gerente
  → Solicita feedback detalhado
  → Agenda ligação em 24h

6.4 Processamento de Webhooks
Arquivo: app/routes/webhooks.py

Tipo de Evento
Descrição
Payload Key
messages.interactive.button_reply
Usuário clicou em botão
event.button_reply.id
messages.interactive.list_reply
Usuário selecionou item da lista
event.list_reply.id
messages
Mensagem de texto recebida
event.text.body


7. PLANO DE IMPLEMENTAÇÃO DETALHADO
7.1 Metodologia e Princípios
✓ Desenvolvimento incremental com entregas semanais
✓ Testes automatizados para cada feature (coverage mín. 70%)
✓ Code review obrigatório antes de merge
✓ Documentação inline (docstrings) em todas as funções
✓ Versionamento semântico (SemVer 2.0)
✓ Deploy em staging antes de produção

7.2 Cronograma de Sprints (6 Semanas)
Sprint 1: Setup e Infraestrutura (Semana 1) (8h)
• Instalação de dependências (face_recognition, opencv)
• Criação de migrations para novos campos
• Setup de ambiente de testes
• Configuração de CI/CD básico

Sprint 2: Reconhecimento Facial - Backend (Semana 1-2) (16h)
• Implementação de FaceService.enroll()
• Implementação de FaceService.recognize()
• Criação de rotas /api/enroll e /api/recognize
• Testes unitários do módulo facial

Sprint 3: Reconhecimento Facial - Frontend (Semana 2) (12h)
• Interface de upload de foto no perfil
• Desenvolvimento do Totem (modo kiosk)
• Integração com câmera via WebRTC
• Testes de usabilidade

Sprint 4: Prescrição de Treino (Semana 3) (16h)
• Criação de modelos (Exercise, TrainingPlan, etc)
• Interface de prescrição para instrutor
• Tela de visualização para aluno
• Integração com YouTube Embed API

Sprint 5: CRM e Retenção (Semana 4-5) (20h)
• Implementação do algoritmo Health Score
• Dashboard de CRM para admin
• Criação das réguas de relacionamento
• Scheduler para processar automações

Sprint 6: WhatsApp Interativo (Semana 5-6) (16h)
• Upgrade de MegaAPI para buttons/lists
• Implementação de webhook handlers
• Criação de fluxos interativos
• Testes E2E de integração

Sprint 7: Polimento e Deploy (Semana 6) (12h)
• Correção de bugs reportados
• Otimização de performance
• Documentação de usuário final
• Deploy em produção

Total Estimado: 100 horas (~12 dias úteis)
Equipe Recomendada: 1 Backend Dev + 1 Frontend Dev

7.3 Análise de Riscos e Mitigação
Risco
Probabilidade
Impacto
Mitigação
Baixa acurácia facial em iluminação ruim
Média
Alto
Usar câmeras com IR; fallback para QR Code
Sobrecarga do servidor em horários de pico
Baixa
Alto
Implementar queue com Celery; cache de encodings
WhatsApp API rate limits
Média
Médio
Implementar backoff exponencial; priorizar mensagens
Resistência de usuários ao cadastro facial
Alta
Médio
Campanha educativa sobre privacidade; incentivos
Complexidade do algoritmo de Health Score
Baixa
Baixo
Começar com versão simplificada; iterar com dados reais


8. ESTRATÉGIA DE TESTES E MÉTRICAS
8.1 Pirâmide de Testes
Testes Unitários (70%)
• Funções puras de FaceService
• Cálculos de Health Score
• Validações de modelos
• Formatadores de mensagens

Testes de Integração (20%)
• Fluxo completo de enrollment
• Check-in via reconhecimento
• Envio de mensagem interativa
• Processamento de webhooks

Testes E2E (10%)
• Jornada completa do aluno novo
• Fluxo de CRM de recuperação
• Renovação via WhatsApp

8.2 Métricas de Sucesso (KPIs)
Métrica
Baseline
Meta 3M
Meta 6M
Taxa de Churn (90 dias)
45%
35%
20%
Tempo Médio Check-in
45s
10s
5s
Acurácia Reconhecimento Facial
—
95%
98%
Taxa Resposta WhatsApp
5%
25%
40%
Health Score Médio
—
65
75
Alunos com Plano Digital
0%
60%
90%
NPS (Net Promoter Score)
35
50
65
Tempo Cadastro Facial
—
2min
1min
Uptime Sistema Check-in
—
99%
99.5%
Conversão Lead → Aluno
15%
20%
25%


8.3 Ferramentas de Monitoramento
Application Performance: New Relic / Datadog — Monitorar latência de reconhecimento facial
Error Tracking: Sentry — Alertas em tempo real de exceções
Analytics: Mixpanel / Amplitude — Funil de conversão e engajamento
Infrastructure: Prometheus + Grafana — Métricas de servidor e banco de dados
User Feedback: Hotjar / FullStory — Gravação de sessões e heatmaps

9. SEGURANÇA, PRIVACIDADE E CONFORMIDADE
9.1 LGPD - Lei Geral de Proteção de Dados
Dados biométricos (face encodings) são considerados dados sensíveis pela LGPD. O sistema deve implementar as seguintes garantias:
✓ Consentimento expresso e específico para coleta de dados faciais
✓ Transparência total sobre finalidade (controle de acesso)
✓ Minimização de dados (não armazenar fotos, apenas encodings)
✓ Direito de exclusão (permitir remoção de dados biométricos)
✓ Segurança da informação (criptografia AES-256 em repouso)
✓ Logs de acesso auditáveis (quem acessou, quando, para quê)
✓ DPO (Data Protection Officer) designado
✓ Termo de Consentimento claro e acessível

9.2 Implementações Técnicas de Segurança
Criptografia de Dados em Repouso
• Face encodings armazenados com AES-256
• Chaves gerenciadas via environment variables
• Rotação de chaves a cada 90 dias

Criptografia de Dados em Trânsito
• HTTPS obrigatório (TLS 1.3)
• Certificado SSL Let's Encrypt
• HSTS headers habilitados

Autenticação e Autorização
• Senhas com hash bcrypt (cost factor 12)
• Session timeout de 30 minutos
• Rate limiting: 5 tentativas de login/min
• RBAC (Role-Based Access Control) granular

Auditoria e Logs
• Todos os acessos a dados faciais logados
• Logs armazenados em servidor separado
• Retenção de logs por 12 meses
• Alertas automáticos para acessos suspeitos

Backup e Disaster Recovery
• Backup diário automático do banco
• Armazenamento em 3 locais (3-2-1 rule)
• Testes de restauração mensais
• RTO (Recovery Time Objective) de 4 horas

9.3 Modelo de Termo de Consentimento
Eu, [NOME DO ALUNO], CPF [XXX.XXX.XXX-XX], autorizo expressamente a [NOME DA ACADEMIA] a coletar e processar meus dados biométricos (reconhecimento facial) exclusivamente para controle de acesso às instalações e registro de frequência. Estou ciente de que:

• Minha foto será convertida em um código numérico (face encoding) e a imagem original não será armazenada;
• Posso revogar este consentimento a qualquer momento através do meu perfil ou solicitando à recepção;
• Meus dados biométricos serão excluídos imediatamente após cancelamento da matrícula ou revogação do consentimento;
• A academia utiliza criptografia de nível bancário para proteger meus dados;
• Tenho direito de solicitar acesso, correção ou exclusão dos meus dados a qualquer momento.

10. APÊNDICES E REFERÊNCIAS
10.1 Glossário Técnico
Churn: Taxa de cancelamento/abandono de clientes
Face Encoding: Vetor numérico de 128 dimensões que representa características únicas de uma face
Threshold: Limiar de similaridade para considerar um match válido (padrão: 0.6)
Health Score: Pontuação de 0-100 que indica risco de evasão do aluno
Webhook: URL que recebe notificações automáticas de eventos externos
Rate Limit: Limite de requisições por período para prevenir abuso
RBAC: Role-Based Access Control - controle de acesso baseado em papéis
LGPD: Lei Geral de Proteção de Dados - legislação brasileira de privacidade
NPS: Net Promoter Score - métrica de satisfação do cliente
CAGR: Compound Annual Growth Rate - taxa de crescimento anual composta

10.2 Referências Bibliográficas e Técnicas
[1] IHRSA (2024). "The 2024 Global Health Club Report". International Health, Racquet & Sportsclub Association.
[2] King, D. E. (2009). "Dlib-ml: A Machine Learning Toolkit". Journal of Machine Learning Research.
[3] Schroff, F., Kalenichenko, D., & Philbin, J. (2015). "FaceNet: A Unified Embedding for Face Recognition". CVPR.
[4] ACAD Brasil (2023). "Panorama do Mercado Brasileiro de Academias".
[5] WhatsApp Business Platform Documentation (2024). Meta Platforms, Inc.
[6] Brasil. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD).
[7] Flask Documentation (2024). "Web Development, one drop at a time". Pallets Projects.
[8] SQLAlchemy Documentation (2024). "The Database Toolkit for Python".
[9] Reichheld, F. F. (2003). "The One Number You Need to Grow". Harvard Business Review.
[10] Grand View Research (2024). "Fitness App Market Size, Share & Trends Analysis Report".

10.3 Comandos Úteis para Desenvolvimento
Ação
Comando
Criar migration
flask db migrate -m "Add face recognition"
Aplicar migrations
flask db upgrade
Instalar dependências
pip install -r requirements.txt
Rodar testes
pytest tests/ -v --cov=app
Iniciar servidor dev
flask run --debug
Gerar face encoding
python scripts/generate_encoding.py photo.jpg
Backup banco de dados
python scripts/backup_db.py
Popular banco com dados de teste
flask seed-db


