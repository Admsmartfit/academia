# PRD - Plano de Desenvolvimento por Etapas
## Sistema de Gestao de Academia

**Versao:** 2.0
**Data:** 19/02/2026
**Base:** Auditoria completa do codigo atual

---

## ESTADO ATUAL DO SISTEMA

### Funcionando (30+ modulos completos)
- Autenticacao (login, registro, recuperacao de senha)
- Dashboard do aluno (XP, creditos, agendamentos, ranking)
- Agendamento de aulas (avulso + recorrente + segregacao por genero)
- Loja de pacotes (checkout + PIX + aprovacao admin)
- Dashboard instrutor (presenca, cancelamento, no-show)
- Prescricao de treino (planos, sessoes, templates, exercicios)
- Admin completo (pacotes, modalidades, horarios, usuarios, pagamentos)
- Gamificacao (XP, niveis, conquistas, conversao XP->creditos)
- WhatsApp (MegaAPI com templates, botoes, listas, envio em massa)
- CRM (leads, pipeline, health score, retencao automatizada)
- Split bancario (comissoes, repasses, algoritmo dinamico)
- Triagem de saude (PAR-Q, EMS, eletrolopolise)
- Metricas e KPIs (dashboard operacional + financeiro)
- Backup automatico do banco de dados
- Reconhecimento facial (cadastro + API)
- 20+ tarefas agendadas (lembretes, cobranças, comissoes, etc.)

### Parcial ou Com Gaps
- Relato de dor do aluno (rota existe, sem template dedicado)
- Detalhes do health score do aluno (calculado, sem tela de detalhe)
- Historico detalhado de pagamentos (limitado)
- Reconhecimento facial (cadastro OK, verificacao limitada)
- Visualizacao do treino pelo aluno (basica)

---

## ETAPA 1 - POLIMENTO E CORRECOES (Fundacao)
**Objetivo:** Corrigir problemas existentes e polir a experiencia do usuario.
**Prioridade:** ALTA

### 1.1 Validacao de Telefone no Cadastro
**Onde:** `app/routes/auth.py`, `app/routes/admin/users.py`
**O que fazer:**
- Criar funcao `validate_phone()` que normaliza para formato `5511999999999`
- Aplicar no registro de aluno e no cadastro pelo admin
- Mascara no frontend (input com formato visual)
- Rejeitar numeros invalidos antes de salvar

### 1.2 Feedback Visual nas Acoes do Admin
**Onde:** Templates admin diversos
**O que fazer:**
- Garantir que todas as acoes mostram flash messages (sucesso/erro)
- Adicionar confirmacao em acoes destrutivas (deletar usuario, cancelar plano)
- Spinner/loading em botoes que fazem POST

### 1.3 Tratamento de Erros nas Paginas do Aluno
**Onde:** `app/routes/student.py`, templates student
**O que fazer:**
- Pagina 404 customizada
- Pagina 500 customizada
- Mensagens amigaveis quando nao tem agendamentos, creditos, etc.

### 1.4 Responsividade Mobile
**Onde:** Templates base, student, instructor
**O que fazer:**
- Testar e corrigir layout em telas pequenas
- Menu hamburger funcional no mobile
- Cards de exercicio/agendamento adaptaveis

---

## ETAPA 2 - EXPERIENCIA DO ALUNO (Retencao)
**Objetivo:** Melhorar o que o aluno ve e faz no sistema.
**Prioridade:** ALTA

### 2.1 Tela de Treino do Aluno Melhorada
**Onde:** `app/templates/student/my_training.html`
**O que fazer:**
- Mostrar plano atual com sessoes organizadas por dia (A/B/C/D)
- Para cada exercicio: nome, serie x repeticoes, carga, descanso
- Botao para ver video/imagem do exercicio (se tiver URL)
- Indicador visual de progresso (sessoes completadas na semana)

### 2.2 Historico e Evolucao do Aluno
**Onde:** Novo template `student/progress.html`
**O que fazer:**
- Rota `student.progress`
- Grafico de frequencia mensal (aulas agendadas vs realizadas)
- Historico de XP ganho por semana
- Conquistas desbloqueadas em timeline
- Streak atual e maior streak

### 2.3 Relato de Dor - Template Dedicado
**Onde:** `app/templates/student/report_pain.html` (novo)
**O que fazer:**
- Formulario visual com silhueta do corpo humano (selecionar area)
- Escala de dor (1-10)
- Campo de observacoes
- Historico de relatos anteriores
- Notificacao ao instrutor via WhatsApp (ja existe)

### 2.4 Notificacoes no Sistema
**Onde:** Novo modelo `Notification`, rota `student.notifications`
**O que fazer:**
- Sino de notificacoes no navbar do aluno
- Tipos: lembrete de aula, credito expirando, conquista desbloqueada, treino novo
- Marcar como lida
- Contador de nao lidas no icone

---

## ETAPA 3 - FERRAMENTAS DO INSTRUTOR (Produtividade)
**Objetivo:** Dar mais poder ao instrutor no dia-a-dia.
**Prioridade:** MEDIA-ALTA

### 3.1 Dashboard do Instrutor Melhorado
**Onde:** `app/templates/instructor/dashboard.html`
**O que fazer:**
- Cards com metricas do dia: total alunos, presencas, faltas, cancelamentos
- Lista de alunos do dia com status (confirmado, pendente, faltou)
- Acesso rapido ao perfil do aluno (treino, historico, saude)

### 3.2 Registro de Carga/Performance
**Onde:** Novo modelo `WorkoutLog`, rota instrutor
**O que fazer:**
- Instrutor registra carga usada pelo aluno em cada exercicio
- Historico de evolucao de carga por exercicio
- Aluno ve isso na tela de treino (read-only)
- Grafico simples de evolucao

### 3.3 Observacoes por Aluno
**Onde:** Novo campo ou modelo para anotacoes
**O que fazer:**
- Instrutor pode deixar observacoes no perfil do aluno
- Visivel para outros instrutores
- Tipos: restricao, progresso, comportamento
- Timeline de observacoes

### 3.4 QR Code para Check-in
**Onde:** `app/routes/instructor.py`, novo template
**O que fazer:**
- Gerar QR Code unico por aluno (com validade curta)
- Tela no instrutor para escanear (camera do celular/tablet)
- Registra check-in automatico ao escanear
- Alternativa ao check-in manual e ao reconhecimento facial

---

## ETAPA 4 - COMUNICACAO E CRM (Engajamento)
**Objetivo:** Melhorar a comunicacao automatizada e manual.
**Prioridade:** MEDIA

### 4.1 Webhook para Respostas do WhatsApp
**Onde:** `app/routes/webhooks.py`
**O que fazer:**
- Processar respostas de botoes/listas do WhatsApp
- Acoes automaticas: confirmar presenca, cancelar aula, reagendar
- Log de interacoes recebidas
- Resposta automatica de confirmacao

### 4.2 Campanhas de WhatsApp
**Onde:** Novo template `admin/whatsapp/campaigns.html`
**O que fazer:**
- Criar campanha com filtros (alunos inativos, aniversariantes, etc.)
- Agendar envio para data/hora especifica
- Usar templates aprovados ou mensagem customizada
- Relatorio de envio (enviados, entregues, erros)

### 4.3 CRM - Funil de Visitantes
**Onde:** `app/routes/admin/crm.py`, templates CRM
**O que fazer:**
- Cadastro rapido de visitante (nome + telefone)
- Status: Visitante -> Aula Experimental -> Matriculado -> Ativo
- Automacao: lembrete pos-visita, oferta de aula experimental
- Dashboard com taxa de conversao do funil

### 4.4 NPS e Feedback Automatizado
**Onde:** Scheduler + template de resultado
**O que fazer:**
- Pesquisa NPS mensal via WhatsApp (ja existe no scheduler)
- Tela admin para ver resultados consolidados
- Classificacao: promotores, neutros, detratores
- Alertas para detratores (notificar admin imediatamente)

---

## ETAPA 5 - FINANCEIRO AVANCADO (Controle)
**Objetivo:** Dar mais controle financeiro ao dono da academia.
**Prioridade:** MEDIA

### 5.1 Dashboard Financeiro Detalhado
**Onde:** `app/templates/admin/metrics/financeiro.html` (melhorar)
**O que fazer:**
- Receita mensal (total, por modalidade, por pacote)
- Grafico de receita vs despesas (comissoes)
- Taxa de inadimplencia com tendencia
- Previsao de receita proximos 30 dias (baseada em assinaturas ativas)

### 5.2 Controle de Despesas Basico
**Onde:** Novo modelo `Expense`, novas rotas admin
**O que fazer:**
- Cadastrar despesas fixas (aluguel, luz, agua, equipamentos)
- Despesas variaveis (manutencao, limpeza)
- Calcular lucro liquido (receita - comissoes - despesas)
- Relatorio mensal exportavel

### 5.3 Relatorio de Inadimplencia
**Onde:** Melhorar `admin/payments/overdue.html`
**O que fazer:**
- Lista com dias em atraso, valor, contato
- Botao para enviar cobranca via WhatsApp (individual ou em massa)
- Historico de tentativas de cobranca
- Filtros: faixa de atraso (15d, 30d, 60d, 90d+)

### 5.4 Recibos e Comprovantes
**Onde:** `app/services/pdf_generator.py` (melhorar)
**O que fazer:**
- Gerar recibo PDF apos aprovacao de pagamento
- Enviar recibo via WhatsApp automaticamente
- Historico de recibos do aluno

---

## ETAPA 6 - SEGURANCA E LGPD (Compliance)
**Objetivo:** Proteger dados e atender legislacao.
**Prioridade:** MEDIA-BAIXA (mas importante)

### 6.1 Termo de Consentimento LGPD
**Onde:** `app/routes/auth.py` (registro), novo modelo `ConsentLog`
**O que fazer:**
- Checkbox obrigatorio no cadastro
- Texto do termo de uso e privacidade
- Log de consentimento com data/hora/IP
- Opcao de revogar consentimento

### 6.2 Exclusao de Dados (Direito ao Esquecimento)
**Onde:** `app/routes/admin/users.py`
**O que fazer:**
- Botao "Anonimizar dados" no perfil do usuario
- Manter registros financeiros (obrigacao legal) mas anonimizar nome/telefone/CPF
- Log de anonimizacao

### 6.3 Log de Auditoria
**Onde:** Novo modelo `AuditLog`
**O que fazer:**
- Registrar acoes criticas: login, alteracao de dados, pagamentos, cancelamentos
- Quem fez, quando, o que mudou
- Tela admin para consultar logs
- Retencao de 1 ano

### 6.4 Rate Limiting
**Onde:** `app/__init__.py`
**O que fazer:**
- Limitar tentativas de login (5 por minuto)
- Limitar chamadas a API (100 por minuto)
- Usar Flask-Limiter
- Pagina de "muitas tentativas" amigavel

---

## ETAPA 7 - EXTRAS E DIFERENCIAIS (Nice to Have)
**Objetivo:** Funcionalidades que diferenciam de concorrentes.
**Prioridade:** BAIXA

### 7.1 Treino em Casa / Exercicios Offline
**O que fazer:**
- Aluno pode ver treino do dia sem internet (cache/PWA)
- Timer de descanso entre series
- Marcador de series completadas

### 7.2 Integracao com Wearables
**O que fazer:**
- Receber dados de frequencia cardiaca (via API Google Fit / Apple Health)
- Mostrar no perfil do aluno
- Usar como metrica de intensidade

### 7.3 Sistema de Indicacao
**O que fazer:**
- Aluno compartilha link de indicacao (ja tem `referral_code` no modelo User)
- Quem indicou ganha creditos bonus quando indicado se matricula
- Ranking de indicadores
- Dashboard admin com metricas de indicacao

### 7.4 Avaliacao Fisica
**Onde:** Novo modelo `PhysicalAssessment`
**O que fazer:**
- Formulario com medidas corporais (peso, altura, percentual de gordura, circunferencias)
- Fotos de evolucao (upload)
- Grafico de evolucao ao longo do tempo
- Comparativo entre avaliacoes
- Agendamento de reavaliacao periodica

---

## ORDEM DE IMPLEMENTACAO RECOMENDADA

```
ETAPA 1 (1-2 semanas)  -> Polimento e Correcoes
ETAPA 2 (2-3 semanas)  -> Experiencia do Aluno
ETAPA 3 (2-3 semanas)  -> Ferramentas do Instrutor
ETAPA 4 (1-2 semanas)  -> Comunicacao e CRM
ETAPA 5 (1-2 semanas)  -> Financeiro Avancado
ETAPA 6 (1 semana)     -> Seguranca e LGPD
ETAPA 7 (continuo)     -> Extras e Diferenciais
```

### Dependencias entre Etapas
- Etapa 2 depende parcialmente de Etapa 1 (erros corrigidos)
- Etapa 3.2 (registro de carga) alimenta Etapa 2.1 (tela de treino)
- Etapa 4.1 (webhook) melhora Etapa 4.2 (campanhas)
- Etapa 5 e independente
- Etapa 6 pode ser feita em paralelo com qualquer outra
- Etapa 7 depende de tudo anterior estar estavel

---

## MODELOS DE DADOS NOVOS NECESSARIOS

### Etapa 2
```
Notification(id, user_id, type, title, message, is_read, created_at)
```

### Etapa 3
```
WorkoutLog(id, user_id, session_exercise_id, sets_done, reps_done, weight_kg, date, notes)
InstructorNote(id, instructor_id, student_id, note_type, content, created_at)
```

### Etapa 5
```
Expense(id, description, category, amount, date, is_recurring, created_by_id)
Receipt(id, payment_id, pdf_path, sent_at)
```

### Etapa 6
```
ConsentLog(id, user_id, consent_type, accepted, ip_address, created_at)
AuditLog(id, user_id, action, entity_type, entity_id, old_value, new_value, created_at)
```

### Etapa 7
```
PhysicalAssessment(id, user_id, instructor_id, date, weight, height, body_fat, chest, waist, hips, arms, thighs, notes, photos)
Referral(id, referrer_id, referred_id, credits_awarded, created_at)
```

---

**Este PRD deve ser usado como guia. Cada etapa pode ser subdividida em tarefas menores conforme necessidade.**
