

⚡


**BIOHACKING STUDIO**

**MANAGEMENT PLATFORM**


Product Requirements Document

Versao 3.0  |  Fevereiro 2026  |  Confidencial


*"Onde Ciencia, Tecnologia e Performance se encontram."*


| **Conceito** | Cyber-Wellness / Clean-Tech |
| - | - |
| **Diferencial** | Eletroestimulacao FES + IA Preditiva |
| **Mercado** | Academias Studio (Brasil) |
| **Stack** | Flask + face\_recognition + NuPay + MegaAPI |
| **Estimativa** | 12 sprints / 188 horas |

# Sumario




# 1. A Visao: O Futuro do Fitness Chegou


| **MANIFESTO DE PRODUTO** Em 2026, treinar nao e mais sobre quantidade de horas — e sobre qualidade de ativacao. O Biohacking Studio e a primeira plataforma que integra eletroestimulacao funcional (FES), reconhecimento facial biometrico, inteligencia preditiva de retencao e pagamentos invisíveis numa unica experiencia fluida. Nao vendemos aulas. Vendemos a versao mais avancada de voce. |
| - |


## 1.1 O Problema que Resolvemos

O mercado fitness brasileiro possui mais de 34.500 academias (ACAD 2024), mas enfrenta tres crises simultaneas que destroem valor:


| **Crise** | **Dados** | **Consequencia** |
| - | - | - |
| **Evasao** | 70% dos novos alunos abandonam em 90 dias (IHRSA 2024) | Academias operam em ciclo permanente de captacao, nunca retencao |
| **Friccao** | Check-in manual consome 40% do tempo do instrutor | Instrutores focam em administracao ao inves de coaching |
| **Invisibilidade** | Taxa de resposta a mensagens de texto: 5% | Comunicacao passiva nao gera acao — alunos somem silenciosamente |


## 1.2 A Solucao: Quatro Pilares Tecnologicos

A plataforma se sustenta em quatro pilares integrados que, juntos, criam um ecossistema onde cada interacao do aluno gera dados que retroalimentam a experiencia:


|  | **PILAR 1** **Biometria Sem Friccao** Reconhecimento facial elimina filas. Check-in em 2 segundos. Dados 100% confiaveis. |  | **PILAR 2** **Treino Inteligente** FES ativa 90% das fibras. Prescricao digital com video. Progresso automatico. |  | **PILAR 3** **Retencao Preditiva** Health Score detecta risco 15 dias antes do churn. CRM aciona reguas automaticas. |  | **PILAR 4** **Conversao Invisivel** PIX instantaneo via NuPay. Recorrencia CIBA. WhatsApp interativo com botoes. |  |
| - | - | - | - | - | - | - | - | - |


## 1.3 Publico-Alvo e Persona

| **Persona** | **Dor Central** | **Mensagem-Chave** | **Plano Ideal** |
| - | - | - | - |
| **Executivo(a) 30-50** | *"Nao tenho tempo para treinar 1h por dia"* | 20 min de FES = 1h30 de treino convencional | **Performance Hibrida** |
| **Atleta Amador** | *"Estou no plato ha meses, nada muda"* | Recrute fibras tipo II que nunca foram ativadas | **Bio-Boost VIP** |
| **Pos-Fisioterapia** | *"Preciso recuperar forca com seguranca"* | Tecnologia de reabilitacao de elite, supervisionada | **FES-Hyper Solo** |
| **Wellness/Estetica** | *"Quero tonificar sem virar 'rato de academia'"* | Resultados visiveis em 4 semanas, ambiente tech-premium | **Starter + Eletrolipolise** |


## 1.4 Metricas de Impacto Estrategico

| **Metrica** | **Baseline** | **Meta 3 Meses** | **Meta 6 Meses** |
| - | - | - | - |
| Taxa de Churn (90 dias) | 45% | **35%** | **20%** |
| Tempo de Check-in | 45s (manual) | **10s** | **\< 3s** |
| Taxa Resposta WhatsApp | 5% | **25%** | **40%** |
| Conversao Landing \> Checkout | 2% | **4%** | **6%** |
| Tempo Liberacao de Creditos | 2-24 horas | **\< 5 segundos** | **\< 5 segundos** |
| NPS (Net Promoter Score) | 35 | **50** | **65** |
| Health Score Medio | N/A | **65** | **75** |
| Conversao Lead \> Aluno | 15% | **20%** | **25%** |


# 2. Design Language: A Estetica Cyber-Wellness


A identidade visual da plataforma comunica tres atributos simultaneos: tecnologia de ponta (heranca da engenharia biomedica), confianca clinica (ambiente seguro e supervisionado) e premium acessivel (nao e hospital, nao e academia generica). Toda interface segue o principio Dark Mode por padrao, com acentos de cor que guiam a atencao.


## 2.1 Paleta de Cores

| **Nome** | **Hex** | **Funcao** | **Uso Principal** |
| - | - | - | - |
| **Charcoal** | \#0F172A | Fundo Primario | Background de todas as telas em dark mode, sensacao de profundidade e tecnologia |
| **Slate** | \#1E293B | Fundo Secundario | Cards, modais, paineis laterais — cria hierarquia visual sobre o charcoal |
| **Neon Orange** | \#FF6B35 | Acao / CTA | Botoes primarios, destaque FES, badges de urgencia, preco de planos |
| **Neon Cyan** | \#06B6D4 | Tecnologia / Dados | Graficos do Health Score, indicadores biometricos, badges de nivel |
| **Bio-Green** | \#10B981 | Sucesso / Saude | Confirmacoes, check-in realizado, pagamento aprovado, status 'Apto' |
| **Rose** | \#F43F5E | Alerta / Critico | Bloqueios de saude, alunos criticos no CRM, pagamento falhou |
| **Violet** | \#8B5CF6 | Gamificacao / Premium | XP, conquistas, nivel do aluno, planos VIP, elementos de reward |


## 2.2 Tipografia e Espacamento

Fonte primaria: Inter (corpo) e Space Grotesk (titulos e numeros). Fallback universal: Arial. Tamanhos: H1 = 32px, H2 = 24px, H3 = 18px, Body = 16px, Caption = 12px. Line-height padrao: 1.5. Espacamento entre secoes: 32px. Border-radius padrao: 12px para cards, 8px para botoes, 24px para modais.


## 2.3 Principios de Interface por Contexto

| **Interface** | **Dispositivo** | **Principios de Design** |
| - | - | - |
| **Aluno** | Mobile-first (PWA) | Cards grandes, gestos de swipe, notificacoes push. Treino do dia como hero card. XP e nivel sempre visiveis no header. Dark mode padrao. |
| **Instrutor** | Tablet / Mobile | Layout de lista com acoes rapidas (check-in em 1 tap). Prescricao de treino com drag-and-drop de exercicios. Registro de parametros EMS em formulario compacto. |
| **Admin** | Desktop-first | Dashboard com KPIs em grid. CRM com tabelas filtráveis e acoes em lote. Graficos de tendencia (Chart.js). Sidebar de navegacao permanente. |
| **Totem** | Kiosk (Fullscreen) | Zero interacao manual: camera ativa em loop, reconhecimento automatico. Saudacao personalizada com nome e info do treino. Animacao de pulso eletrico no sucesso. |
| **Landing Page** | Responsivo | Scroll linear narrativo. Video hero com autoplay muted. Animacoes SVG na secao de ciencia FES. Simulador interativo. CTAs de alto contraste (Neon Orange). |


## 2.4 Micro-Interacoes e Feedback Sensorial

Check-in facial bem-sucedido: animacao de pulso eletrico (ondas concentricas em Neon Cyan) com saudacao por nome e informacao do treino do dia (exemplo: "Bem-vindo, Rafael. Seu treino de Bio-Boost esta pronto.").

Conversao de XP: animacao de particulas violeta convergindo para um icone de credito dourado, com contador numerico incrementando em tempo real.

Pagamento PIX confirmado: transicao suave de QR Code para checkmark verde com confetti sutil e mensagem de creditos liberados.

Health Score pulsante no dashboard do aluno: anel circular que muda de cor dinamicamente (Verde \> Amarelo \> Vermelho) conforme o score varia, com heartbeat animation sutil.


# 3. The Biohacking Journey: Modulos do Sistema


Cada modulo da plataforma corresponde a uma etapa da jornada do aluno — desde o primeiro contato ate a fidelizacao de longo prazo. Nao sao funcionalidades isoladas; sao fases de uma experiencia integrada onde cada interacao gera dados que retroalimentam e personalizam a proxima.


## 3.1 Primeiro Contato: Landing Page de Alta Conversao

A landing page e a vitrine digital do studio. Seu objetivo e educar sobre FES, criar desejo atraves de prova social gamificada, e converter visitantes em alunos atraves de uma jornada narrativa de scroll. Nao e uma pagina institucional — e uma maquina de conversao baseada em valor.


### Arquitetura de Secoes (Scroll Narrativo)

| **\#** | **Secao** | **Proposito e Gatilho Mental** |
| - | - | - |
| **1** | **Hero + Video FES** | Captura em 3 segundos. Proposta de valor: "20 min = 1h30". CTA primario para sessao experimental gratuita. Trust badges (alunos ativos, avaliacao, certificacoes). |
| **2** | **Problema / Solucao** | Conexao emocional: "Por que seus treinos nao funcionam". Tres dores (tempo, plato, fibras dormentes). Transicao para a solucao. |
| **3** | **Ciencia FES** | Autoridade cientifica acessivel. Animacao SVG comparando 30% vs 90% de ativacao muscular. Badge ANVISA. "Mesma tecnologia da fisioterapia olimpica." |
| **4** | **Comparativo Visual** | Tabela FES vs Treino Tradicional: tempo, ativacao, resultados, risco de lesao. Decisao facilitada com dados concretos. |
| **5** | **Modalidades (Grid)** | Card FES 2x maior com animacao de pulso eletrico e badge "Tecnologia Exclusiva". Demais modalidades em grid padrao. |
| **6** | **Simulador Interativo** | Calculadora de creditos com sliders por modalidade. Mostra economia de tempo com FES. Sugere pacote ideal automaticamente. Gatilho: engajamento ativo. |
| **7** | **Planos e Precos** | Cards com hierarquia clara: Starter, FES-Hyper, Performance Hibrida (destacado), Bio-Boost VIP. CTA por plano. Economia vs avulso. |
| **8** | **Depoimentos + Resultados** | Prova social: video testimonials 15-30s, metricas concretas ("4kg de massa em 6 semanas"). Formato carrossel. |
| **9** | **Hall da Fama (Gamificacao)** | Ranking XP anonimizado dos top 10 alunos. Contador em tempo real: "X fibras ativadas hoje no studio". Prova social gamificada. |
| **10** | **FAQ sobre FES** | Eliminacao de objecoes: doi? E seguro? Substitui musculacao? Marca-passo? Resultados em quanto tempo? |
| **11** | **CTA Final** | Urgencia: "Agende sua Sessao de Ativacao FES — 100% Gratuita". Avaliacao corporal inclusa. Sem cartao necessario. |


### Performance e SEO

Targets obrigatorios: LCP \< 2.5s, FID \< 100ms, CLS \< 0.1, Mobile Score Lighthouse \> 90. Otimizacoes: video WebM com fallback JPG (lazy load abaixo da dobra), critical CSS inline, preconnect Google Fonts, structured data para rich snippets.


## 3.2 Onboarding: Da Curiosidade a Primeira Aula

### Triagem de Saude: "Seguranca com Sorriso"

Antes de qualquer atividade, o aluno responde questionarios de triagem projetados para proteger sem assustar. O tom e acolhedor, com linguagem acessivel e emojis estrategicos. O fluxo e adaptativo conforme a modalidade escolhida.


| **Modalidade** | **Questionario** | **Perguntas** | **Validade** | **Logica de Resultado** |
| - | - | - | - | - |
| Musculacao, Yoga, etc. | PAR-Q Cardiovascular | 7 (Sim/Nao) | 12 meses | Todas NAO = Apto. Qualquer SIM = Upload de atestado |
| FES / Eletroestimulacao | PAR-Q + Anamnese EMS | 7 + 9 | 12 + 6 meses | 3 contraindicacoes absolutas (marcapasso, gestacao, epilepsia) = Bloqueio total |
| Eletrolipolise | Anamnese Eletro | 9 | 6 meses | Checklist pre-sessao obrigatorio: hidratacao, nao jejum, 48h entre areas |


Fluxo de bloqueio humano: contraindicacoes absolutas apresentam mensagem empatica ("Este procedimento nao e indicado para voce, mas temos muitas outras modalidades incriveis!") com botao para ver alternativas. Contraindicacoes relativas solicitam upload de atestado com aprovacao pelo admin.

Renovacao proativa: notificacoes automaticas em 15, 7 e 1 dia antes do vencimento via WhatsApp e banner no dashboard. Apos vencer: soft-block amigavel com renovacao em 2 minutos.


### Cadastro Facial e Primeiro Check-in

O aluno envia foto pelo perfil (resolucao minima 640x480, exatamente 1 face detectada). O sistema gera um face encoding de 128 dimensoes sem armazenar a imagem original (conformidade LGPD). No primeiro check-in, a saudacao no totem cria o "momento wow" que define a percepcao de tecnologia premium.


### Checkout e Ativacao Instantanea

Fluxo self-service completo: escolher pacote na landing/loja, validar CPF, gerar PIX via NuPay (QR Code + copia-e-cola + deep link Nubank), polling de status a cada 5 segundos, webhook HMAC-SHA256 confirma pagamento, creditos liberados instantaneamente, WhatsApp de confirmacao com resumo. Tempo total: menos de 60 segundos do clique ao acesso.

Modalidades de pagamento: PIX a vista (recomendado), PIX parcelado (primeira parcela imediata), e Recorrencia Mensal CIBA (cliente autoriza via push no Nubank, cobranças automaticas no vencimento, cancelamento a qualquer momento pelo app).


## 3.3 O Treino: Performance Maximizada

### Prescricao Digital Mobile-First

O instrutor prescreve treinos em interface digital com biblioteca de exercicios (integracao Wger API para milhares de exercicios categorizados com imagens). Cada exercicio inclui video demonstrativo (YouTube embed inline), series, repeticoes, tempo de descanso e observacoes personalizadas. O aluno abre o celular e ve o "Treino do Dia" como hero card, sem carregar papel, sem depender do instrutor.

Progressao: historico dos ultimos 7 treinos com datas, badge de streak motivacional, e botao para reportar dor/desconforto (notifica instrutor imediatamente). A conclusao do treino e inferida automaticamente pelo check-in facial — zero confirmacao manual.


### Sessoes FES: Protocolo Controlado

Cada sessao de eletroestimulacao possui registro obrigatorio de parametros tecnicos pelo instrutor: frequencia (Hz), intensidade (mA), duracao (minutos), area tratada, e checkbox de desconforto relatado. Esse log alimenta o historico do aluno e permite ao admin analisar padroes de uso, medias de parametros e taxas de desconforto.

Regras de seguranca automatizadas: bloqueio de agendamento de Eletrolipolise na mesma area com menos de 48h de intervalo, exigencia de autorizacao parental para menores de 18, lembrete de hidratacao via WhatsApp 30 minutos antes da sessao.


### Check-in Biometrico: Zero Friccao

Totem em modo kiosk com camera ativa em loop (captura a cada 2 segundos via WebRTC). Ao reconhecer o aluno (threshold configuravel, padrao 0.6, tempo \< 2s), o sistema busca booking ativo em janela de +/- 30 minutos, marca como COMPLETED, concede XP, verifica conquistas, atualiza streak, e opcionalmente envia confirmacao via WhatsApp.

Fallback: QR Code dinamico unico por aluno para situacoes de iluminacao inadequada. Rate limit: 10 tentativas/minuto por IP. Metricas: acuracia \> 95% em 3 meses, \> 98% em 6 meses. Suporte a ate 50 reconhecimentos simultaneos.


## 3.4 Engajamento Continuo: Gamificacao e Recompensas

### Sistema de XP, Niveis e Conquistas

XP e a moeda de engajamento da plataforma. E acumulado por check-in, streaks de dias consecutivos, conquistas especiais (primeiro treino FES, 10 aulas no mes, 3 meses sem faltar), e bonus de boas-vindas por pacote. O XP total historico determina o nivel do aluno (visivel em todas as interfaces) e alimenta o Hall da Fama da landing page.


### Conversao XP para Creditos: Recompensa Tangivel

O admin configura regras de conversao (exemplo: 500 XP = 5 creditos validos por 30 dias). O XP disponivel para conversao opera em janela rolling de 3 meses — XP mais antigo sai da janela mas continua no ranking. A conversao pode ser manual (aluno escolhe) ou automatica (trigger ao atingir meta), com cooldown e limite de usos configuraveis.

Creditos convertidos possuem validade configuravel e sao consumidos em logica FIFO (First In, First Out) por data de vencimento. O sistema mostra preview de quais creditos serao debitados antes do aluno confirmar o agendamento. Notificacoes proativas de vencimento iminente em 7 dias e 1 dia.


### Health Score como "Moeda Social"

O Health Score (0-100) nao e apenas um numero no painel admin — e um elemento visual pulsante no dashboard do aluno. Um anel circular que muda de cor dinamicamente (Bio-Green \> Amber \> Rose) conforme a saude da relacao do aluno com o studio varia. Alunos com score alto podem desbloquear recompensas exclusivas: creditos raros, acesso a horarios VIP, ou convites para eventos especiais.


## 3.5 Retencao Inteligente: CRM Preditivo

### Algoritmo de Health Score

Calculado diariamente pelo scheduler, o score pondera quatro dimensoes: Frequencia Semanal (40% — baseada em check-ins dos ultimos 30 dias), Engajamento (30% — resposta a mensagens, visualizacao de treino, avaliacao fisica), Financeiro (20% — status de pagamento), e Historico (10% — tempo de matricula).


### Segmentacao e Acoes Automatizadas

| **Segmento** | **Score** | **Regua de Relacionamento Automatizada** |
| - | - | - |
| **Saudavel** | \>= 70 | Incentivo positivo: sugestao de nova modalidade, upsell para plano superior, convite para trazer amigo. Mensagem de parabens por consistencia. |
| **Em Risco** | 40-69 | D+5 ausente: "Sentimos sua falta!" com sugestao de horarios alternativos. D+10: mensagem personalizada do instrutor. D+15: oferta de sessao gratuita com personal. |
| **Critico** | \< 40 | D+15: questionamento sobre barreiras. D+20: ligacao telefonica da recepcao + desconto de 30% no proximo mes. D+25: convite para evento especial da academia. |
| **Churn** | Cancelou | Campanha win-back: desconto agressivo, convite para reavalicao corporal gratuita, highlight de novidades desde a saida. Cadencia de 30, 60 e 90 dias. |


### Dashboard CRM para Admin

Tela principal com 4 KPIs em destaque (total alunos, em risco, criticos, score medio), tabela de alunos em risco ordenada por score com foto, ultimo check-in, frequencia 30 dias, e acoes rapidas (enviar mensagem WhatsApp, agendar ligacao, oferecer desconto, ver historico completo). Filtros por nivel de risco, dias sem check-in, e ordenacao customizavel.


### Funil de Leads

Status de lead: NEW (captado via landing) \> CONTACTED (primeiro contato) \> VISITED (visitou o studio) \> TRIAL (sessao experimental) \> PROPOSAL (proposta comercial) \> WON/LOST. Cada transicao de estagio pode acionar mensagem WhatsApp automatica configuravel pelo admin.


## 3.6 Comunicacao: WhatsApp como Canal Primario

### Mensageria Interativa (MegaAPI v2)

A integracao com MegaAPI v2 permite tres tipos de mensagens nativas do WhatsApp Business: Button Messages (ate 3 botoes de acao rapida), List Messages (menu com ate 10 opcoes), e Template Messages (mensagens pre-aprovadas pelo Meta). Mensagens com botoes apresentam taxa de resposta 8x superior a texto simples.


### Fluxos Interativos Principais

| **Fluxo** | **Mensagem** | **Botoes / Opcoes** |
| - | - | - |
| **Lembrete de Aula (2h antes)** | "Voce tem aula de \[Modalidade\] hoje as \[Hora\]!" | \[Vou comparecer\] \[Cancelar\] \[Reagendar\] |
| **Renovacao de Plano (3 dias)** | "Seu plano vence em 3 dias. Renove e continue evoluindo!" | \[Renovar agora via PIX\] \[Falar com consultor\] \[Lembrar amanha\] |
| **Pesquisa NPS** | "Como voce avalia sua experiencia este mes?" | Lista: Excelente / Boa / Regular / Ruim (Ruim aciona alerta para gerente) |
| **Recuperacao (D+10)** | "Oi \[Nome\], tudo bem? Notamos que voce nao treinou esta semana." | \[Agendar aula agora\] \[Preciso de ajuda\] \[Pausar meu plano\] |
| **Hidratacao Eletrolipolise** | "Lembrete: beba 500ml de agua agora! Sua sessao comeca em 30 min." | Mensagem simples (sem botao) |
| **Pagamento Confirmado** | "Pagamento confirmado! Voce tem \[X\] creditos ate \[Data\]." | \[Ver horarios\] \[Agendar primeira aula\] |


### Webhook Bidirecional

Respostas dos alunos sao processadas automaticamente: clicar "Cancelar" libera a vaga e sugere reagendamento; clicar "Renovar agora" gera link de pagamento PIX; respostas negativas no NPS acionam alerta para gerente e agendam ligacao em 24h. O admin configura credenciais e testa envios pelo painel sem editar arquivos.


## 3.7 Motor Financeiro: Conversao Invisivel

### Planos e Precificacao

| **Plano** | **Creditos** | **Preco** | **Destaque** | **XP Bonus** | **FES Incluso** |
| - | - | - | - | - | - |
| **Starter** | 30 | R$ 197 | - | +50 | 1 sessao experimental |
| **FES-Hyper Solo** | 60 | R$ 397 | - | +50 | 2 sessoes FES/mes |
| **Performance Hibrida** | 120 | R$ 697 | **MAIS VENDIDO** | +150 | 4 sessoes FES + musculacao livre |
| **Bio-Boost VIP** | 200 | R$ 997 | **PREMIUM** | +300 | FES ilimitado + personal 2x/sem |


### Simulador de Creditos

Ferramenta interativa na landing page e loja: sliders por modalidade ("Quantas vezes por semana?"), calculo automatico de creditos mensais necessarios (frequencia x custo x 4 semanas), sugestao do pacote ideal com destaque visual, comparativo de economia de tempo com FES vs treino convencional. Gatilho de conversao: engajamento ativo gera comprometimento psicologico.


### Inadimplencia e Controle Financeiro

Regras automatizadas: 15 dias de atraso = bloqueio de agendamento (soft-block com mensagem amigavel e link de pagamento). 90 dias = cancelamento automatico com campanha win-back. Aprovacao manual de pagamentos substituida por webhook NuPay com validacao HMAC. Dashboard financeiro com metrica de pagamentos automaticos vs manuais.


# 4. Modelo de Dados: Entidades Principais


A base de dados e composta por 15 entidades principais com relacionamentos ORM, migrations versionadas e backup automatico diario. Abaixo, a visao conceitual de cada entidade sem detalhes de implementacao:


| **Entidade** | **Responsabilidade e Atributos Conceituais** |
| - | - |
| **User** | Identidade central. Armazena dados pessoais (nome, email, telefone, CPF), credenciais de acesso, papel (admin/instrutor/aluno), face encoding biometrico, metricas de gamificacao (XP total, nivel, streak), e status de atividade. |
| **Modality** | Define cada tipo de atividade oferecida pelo studio (Musculacao, Yoga, FES, Eletrolipolise). Inclui custo em creditos, cor visual, icone, e flag de destaque na landing page. |
| **Package** | Plano comercial com quantidade de creditos, preco, validade, opcao de recorrencia, bonus XP de boas-vindas, badge de marketing, e lista de beneficios extras. |
| **Subscription** | Vinculo ativo entre aluno e pacote. Controla creditos totais, usados, datas de inicio/fim, status de recorrencia NuPay, e proxima data de cobranca. |
| **Booking** | Reserva individual de aula. Registra aluno, horario, data, status (confirmado/completado/cancelado), custo no momento da reserva, timestamp de check-in, e XP ganho. |
| **RecurringBooking** | Agendamento automatico (ex: toda segunda 18h). Limitado pela validade do pacote e saldo de creditos. Processado diariamente pelo scheduler. |
| **Payment** | Registro financeiro vinculado a subscription. Armazena valor, metodo (manual/PIX/recorrencia), referencias NuPay (QR code, copia-e-cola, webhook IDs), e status. |
| **HealthScreening** | Questionario de triagem (PAR-Q ou Anamnese EMS). Guarda respostas em formato estruturado, resultado (apto/pendente/bloqueado), assinatura digital (IP + timestamp), validade, e link de atestado medico. |
| **EMSSessionLog** | Registro tecnico obrigatorio apos cada sessao FES/Eletrolipolise. Parametros: frequencia, intensidade, duracao, area tratada, desconforto relatado, observacoes. |
| **Exercise** | Catalogo de exercicios com nome, grupo muscular, URL de video demonstrativo, instrucoes de execucao, e equipamento necessario. |
| **TrainingPlan** | Prescricao do instrutor para o aluno. Define objetivo (hipertrofia/emagrecimento/forca/saude), periodo de validade, e organiza sessoes de treino (A/B/C). |
| **StudentHealthScore** | Snapshot diario do score de saude do aluno (0-100). Decomposto em frequencia, engajamento, financeiro e historico. Classifica nivel de risco. |
| **ConversionRule** | Regra admin de conversao XP \> creditos. Define XP necessario, creditos gerados, validade, modo (manual/automatico), limite de usos, e cooldown. |
| **CreditWallet** | "Carteira" individual de creditos com origem (compra/conversao/bonus/estorno), quantidade, data de criacao, e data de expiracao. Consumo FIFO. |
| **FaceRecognition** | Log de auditoria de cada tentativa de reconhecimento facial. Registra usuario identificado, confianca do match, IP de origem, e resultado (sucesso/falha). |


# 5. Seguranca, Privacidade e Conformidade LGPD


| **PRINCIPIO ZERO: PRIVACY BY DESIGN** Dados biometricos (face encodings) sao dados sensiveis pela LGPD (Lei 13.709/2018). O sistema NUNCA armazena imagens faciais — apenas vetores numericos de 128 dimensoes que nao podem ser revertidos em foto. Cada aluno deve fornecer consentimento expresso, especifico e revogavel para coleta biometrica. |
| - |


## 5.1 Protecoes Implementadas

| **Dominio** | **Medidas de Seguranca** |
| - | - |
| **Dados em Repouso** | Criptografia AES-256 para face encodings e dados sensiveis. Chaves gerenciadas via variaveis de ambiente com rotacao a cada 90 dias. |
| **Dados em Transito** | HTTPS obrigatorio (TLS 1.3) com certificado Let's Encrypt. Headers HSTS habilitados em producao. |
| **Autenticacao** | Senhas com hash bcrypt (cost factor 12). Session timeout de 30 minutos. Rate limit de 5 tentativas de login por minuto. RBAC granular por papel. |
| **Webhooks** | Validacao HMAC-SHA256 em todos os callbacks NuPay. Idempotencia para prevenir duplicacao de creditos. Log de cada tentativa. |
| **Auditoria** | Todos os acessos a dados faciais e financeiros logados com timestamp, IP e identidade. Retencao de 12 meses. Alertas para padroes anomalos. |
| **Backup** | Automatico diario (scheduler 3h da manha). Regra 3-2-1 (3 copias, 2 midias, 1 off-site). Testes de restauracao mensais. RTO de 4 horas. |
| **LGPD Compliance** | Consentimento expresso para biometria, transparencia de finalidade, direito de exclusao imediata, anonimizacao de backups antigos (\>1 ano), DPO designado. |
| **Formularios** | Protecao CSRF em todos os formularios. Validacao server-side de todos os inputs. Sanitizacao contra XSS e SQL injection via ORM. |


# 6. Plano de Implementacao


## 6.1 Cronograma: 12 Sprints em 12 Semanas

Metodologia: entregas incrementais semanais, testes automatizados (coverage \> 70%), code review obrigatorio, deploy em staging antes de producao. Equipe recomendada: 1 Backend Developer + 1 Frontend Developer. Total estimado: 188 horas.


| **Sprint** | **Modulo** | **Entregas** | **Horas** |
| - | - | - | - |
| **1** | **Fundacao e Creditos** | Setup, migrations, creditos variaveis por modalidade, admin | 16h |
| **2** | **Reconhecimento Facial (Backend)** | FaceService, enrollment, API recognize, testes | 16h |
| **3** | **Reconhecimento Facial (Frontend)** | Upload de foto, Totem kiosk, WebRTC, QR Code fallback | 12h |
| **4** | **Triagem de Saude** | PAR-Q, Anamnese EMS, bloqueios, upload atestado, checkpoints | 16h |
| **5** | **Prescricao Digital de Treino** | Catalogo exercicios (Wger), interface instrutor, tela aluno | 16h |
| **6** | **CRM e Retencao** | Health Score, dashboard, reguas automatizadas, funil leads | 20h |
| **7** | **WhatsApp Interativo** | Botoes e listas MegaAPI, webhook handlers, fluxos | 16h |
| **8** | **Pagamentos NuPay (PIX)** | CPF, NuPayService, checkout PIX, webhook, liberacao | 16h |
| **9** | **Pagamentos NuPay (Recorrencia)** | CIBA flow, renovacao automatica, cancelamento | 12h |
| **10** | **Landing Page FES** | Hero, ciencia, comparativo, simulador, planos, FAQ, CTA | 16h |
| **11** | **Gamificacao Avancada** | ConversionRules, CreditWallet, FIFO, interface, automacao | 16h |
| **12** | **Polimento e Deploy** | Navegacao global, testes E2E, performance, docs, deploy | 16h |


## 6.2 Priorizacao Estrategica

| **Nivel** | **Modulos** | **Justificativa** |
| - | - | - |
| **P0 — Critico** | Creditos, PAR-Q (MVP), Checkout NuPay, Landing Page | Requisitos minimos para operar comercialmente e gerar receita |
| **P1 — Alto** | Reconhecimento Facial, CRM, WhatsApp, Prescricao Digital | Diferenciais competitivos que justificam o posicionamento premium |
| **P2 — Medio** | Recorrencia NuPay, XP \> Creditos, Totem Facial | Automacao avancada e engajamento de longo prazo |
| **P3 — Futuro** | App nativo, wearables, telemedicina, IA generativa | Roadmap de expansao apos validacao do MVP em mercado |


# 7. Riscos e Estrategias de Mitigacao


| **Risco** | **Prob.** | **Impacto** | **Mitigacao** |
| - | - | - | - |
| Baixa acuracia facial (iluminacao) | Media | Alto | Cameras IR no totem; fallback QR Code; threshold configuravel pelo admin; teste em condicoes reais antes do deploy |
| Credenciais NuPay demoram | Media | Alto | Iniciar cadastro NuPay Business imediatamente; todo desenvolvimento em sandbox; fallback para checkout manual |
| Resistencia do aluno ao facial | Alta | Medio | Campanha educativa LGPD; incentivo +50 XP pelo cadastro; opcao QR Code permanente; termo de consentimento claro |
| FES desconhecido pelo publico | Alta | Medio | Secao educativa robusta na landing; sessao experimental gratuita; depoimentos com metricas concretas |
| Preco alto dos planos FES | Media | Alto | Simulador com ROI de tempo; trial gratis; plano Starter acessivel; destaque de economia vs personal trainer |
| Contraindicacoes medicas FES | Baixa | Alto | Triagem rigorosa com 3 niveis de bloqueio; disclaimer legal; registro de parametros; seguro de responsabilidade |
| Sobrecarga em horarios de pico | Baixa | Alto | Cache de face encodings; queue com Celery para picos; rate limiting; monitoring com alertas |
| WhatsApp API rate limits | Media | Medio | Backoff exponencial; priorizacao de mensagens criticas (pagamento/saude); batch processing em horarios ociosos |


# 8. Referencias Tecnicas e Documentacao de Apoio


| **Tecnologia** | **Documentacao de Referencia** |
| - | - |
| **Face Recognition** | Biblioteca Python baseada em dlib (ResNet-34). Documentacao: face-recognition.readthedocs.io. Acuracia: 99.38% no LFW dataset. |
| **MegaAPI (WhatsApp)** | API WhatsApp Business para mensagens interativas. Documentacao: mega-api.app.br/documentacao/business. Suporte a botoes, listas e templates. |
| **NuPay for Business** | Pagamentos PIX e recorrencia via Nubank. Documentacao: spinpay.zendesk.com. Integração CIBA para cobranças automaticas. |
| **Wger API** | Base de dados open-source de exercicios com categorias e imagens. Documentacao: wger.readthedocs.io/en/2.0. Util para popular catalogo inicial. |
| **Flask 3.0** | Framework web Python. Documentacao: flask.palletsprojects.com. Ecosistema: Flask-Login, Flask-Migrate, Flask-SQLAlchemy. |
| **IHRSA 2024** | The 2024 Global Health Club Report. Dados de churn e retencao em academias globais. |
| **ACAD Brasil 2024** | Panorama do Mercado Brasileiro de Academias. 34.500+ unidades, 12% com tech avancada. |
| **LGPD (Lei 13.709/2018)** | Lei Geral de Protecao de Dados. Especificamente Art. 11 sobre dados biometricos como dados sensiveis. |


# 9. Aprovacoes


| **Papel** | **Nome** | **Data** | **Status** |
| - | - | - | - |
| **Product Owner** | - | - | Pendente |
| **Tech Lead** | - | - | Pendente |
| **Design Lead** | - | - | Pendente |
| **Financeiro** | - | - | Pendente |
| **Juridico (LGPD)** | - | - | Pendente |


| **NOTA FINAL** Este PRD consolida requisitos de 12 documentos de especificacao em uma visao unica e estrategica. Cada modulo foi projetado para funcionar independentemente (deploy incremental) mas gerar maximo valor quando integrado ao ecossistema completo. O diferencial competitivo nao esta em nenhuma feature isolada — esta na integracao total entre biometria, gamificacao, retencao preditiva e pagamentos invisiveis num unico produto coeso. |
| - |
