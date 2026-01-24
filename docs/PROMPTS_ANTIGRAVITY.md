# Prompts para Antigravity - Implementação do PRD NuPay

Este documento contém prompts sequenciais para implementar o PRD de Upgrade de Vendas e Pagamentos Automatizados. Execute cada prompt separadamente, em ordem, validando o resultado antes de prosseguir.

---

## FASE 1: FUNDAÇÃO (Database & Models)

### Prompt 1.1 - Campo CPF no User Model

```
Adicione o campo CPF ao modelo User existente em app/models/user.py.

TAREFAS:
1. Adicionar campo: cpf = db.Column(db.String(14), nullable=True)
2. Adicionar método estático validate_cpf(cpf) que:
   - Remove caracteres não numéricos
   - Valida se tem 11 dígitos
   - Valida os dígitos verificadores usando o algoritmo oficial do CPF
   - Retorna True/False
3. Adicionar método format_cpf(cpf) que formata para XXX.XXX.XXX-XX

NÃO modifique nenhum outro arquivo. Apenas app/models/user.py.
```

---

### Prompt 1.2 - Campos NuPay no Payment Model

```
Adicione campos NuPay ao modelo Payment existente em app/models/payment.py.

ADICIONAR ESTES CAMPOS:
- nupay_reference_id = db.Column(db.String(100), nullable=True)
- nupay_psp_reference_id = db.Column(db.String(100), nullable=True)
- nupay_payment_url = db.Column(db.String(500), nullable=True)
- nupay_qr_code = db.Column(db.Text, nullable=True)
- nupay_pix_copy_paste = db.Column(db.Text, nullable=True)
- payment_method = db.Column(db.String(20), default='manual')

O campo payment_method pode ser: 'manual', 'nupay_pix', 'nupay_recurring'

NÃO modifique nenhum outro arquivo. Apenas app/models/payment.py.
```

---

### Prompt 1.3 - Campos Recorrência no Package Model

```
Adicione campos de recorrência e gamificação ao modelo Package em app/models/package.py.

ADICIONAR ESTES CAMPOS:
- is_recurring = db.Column(db.Boolean, default=False)
- recurring_interval_days = db.Column(db.Integer, default=30)
- welcome_xp_bonus = db.Column(db.Integer, default=0)

NÃO modifique nenhum outro arquivo. Apenas app/models/package.py.
```

---

### Prompt 1.4 - Campos Recorrência no Subscription Model

```
Adicione campos de recorrência NuPay ao modelo Subscription em app/models/subscription.py.

ADICIONAR ESTES CAMPOS:
- is_recurring = db.Column(db.Boolean, default=False)
- nupay_subscription_id = db.Column(db.String(100), nullable=True)
- recurring_status = db.Column(db.String(20), default='ACTIVE')
- next_billing_date = db.Column(db.Date, nullable=True)
- last_billing_date = db.Column(db.Date, nullable=True)

O campo recurring_status pode ser: 'ACTIVE', 'PAUSED', 'CANCELLED'

NÃO modifique nenhum outro arquivo. Apenas app/models/subscription.py.
```

---

### Prompt 1.5 - Migration dos Novos Campos

```
Crie uma migration Alembic para adicionar todos os novos campos.

Execute os comandos:
1. flask db migrate -m "add_nupay_and_recurring_fields"
2. flask db upgrade

A migration deve incluir:
- users: cpf (String 14)
- payments: nupay_reference_id, nupay_psp_reference_id, nupay_payment_url, nupay_qr_code, nupay_pix_copy_paste, payment_method
- packages: is_recurring, recurring_interval_days, welcome_xp_bonus
- subscriptions: is_recurring, nupay_subscription_id, recurring_status, next_billing_date, last_billing_date

Verifique se a migration foi criada corretamente antes de fazer upgrade.
```

---

### Prompt 1.6 - Configurações NuPay

```
Adicione as configurações NuPay ao arquivo config.py.

ADICIONAR NA CLASSE Config:
    # NuPay Configuration
    NUPAY_BASE_URL = os.environ.get('NUPAY_BASE_URL', 'https://api.spinpay.com.br')
    NUPAY_MERCHANT_KEY = os.environ.get('NUPAY_MERCHANT_KEY')
    NUPAY_MERCHANT_TOKEN = os.environ.get('NUPAY_MERCHANT_TOKEN')
    NUPAY_WEBHOOK_SECRET = os.environ.get('NUPAY_WEBHOOK_SECRET')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

Também adicione ao arquivo .env (ou .env.example se existir):
    NUPAY_BASE_URL=https://api.spinpay.com.br
    NUPAY_MERCHANT_KEY=sua-merchant-key
    NUPAY_MERCHANT_TOKEN=seu-merchant-token
    NUPAY_WEBHOOK_SECRET=seu-webhook-secret
    BASE_URL=http://localhost:5000

NÃO modifique nenhum outro arquivo.
```

---

## FASE 2: SERVIÇO NUPAY

### Prompt 2.1 - NuPayService Básico

```
Crie o arquivo app/services/nupay.py com o serviço de integração NuPay.

O serviço deve ter:
1. Classe NuPayService com __init__ que configura:
   - self.base_url (de NUPAY_BASE_URL)
   - self.headers com X-Merchant-Key, X-Merchant-Token, Content-Type

2. Método create_pix_payment(self, payment, user) que:
   - Faz POST para {base_url}/v1/checkouts/payments
   - Envia payload com: referenceId, amount, paymentMethod, shopper, paymentFlow, expiresAt
   - Retorna response.json()
   - Usa timeout de 30 segundos

3. Método get_payment_status(self, psp_reference_id) que:
   - Faz GET para {base_url}/v1/checkouts/payments/{psp_reference_id}
   - Retorna response.json()

Use requests para as chamadas HTTP.
Adicione tratamento de erros com response.raise_for_status().

Crie APENAS o arquivo app/services/nupay.py.
```

---

### Prompt 2.2 - Métodos Adicionais NuPayService

```
Adicione mais métodos ao app/services/nupay.py:

1. create_recurring_subscription(self, subscription, user):
   - POST para {base_url}/v1/subscriptions
   - Payload com: referenceId, amount, interval, shopper, paymentFlow

2. cancel_subscription(self, nupay_subscription_id):
   - POST para {base_url}/v1/subscriptions/{id}/cancel

3. refund_payment(self, psp_reference_id, amount=None):
   - POST para {base_url}/v1/checkouts/payments/{id}/refund
   - Se amount for None, estorno total

Todos os métodos devem:
- Usar self.headers
- Ter timeout de 30 segundos
- Usar response.raise_for_status()
- Retornar response.json()

Modifique APENAS app/services/nupay.py.
```

---

## FASE 3: WEBHOOK NUPAY

### Prompt 3.1 - Função de Validação HMAC

```
Adicione ao arquivo app/routes/webhooks.py uma função para validar assinatura NuPay.

Adicione no topo do arquivo:
import hmac
import hashlib

Crie a função:
def validate_nupay_signature(request):
    """Valida HMAC-SHA256 do webhook NuPay."""
    signature = request.headers.get('X-NuPay-Signature')
    if not signature:
        return False

    secret = current_app.config.get('NUPAY_WEBHOOK_SECRET', '')
    if not secret:
        return True  # Se não configurou secret, aceita (dev mode)

    payload = request.get_data()
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)

NÃO adicione a rota do webhook ainda, apenas a função de validação.
```

---

### Prompt 3.2 - Rota Webhook NuPay

```
Adicione a rota do webhook NuPay em app/routes/webhooks.py.

Crie a rota POST /nupay/callback que:

1. Valida assinatura usando validate_nupay_signature()
2. Obtém JSON com: merchantReferenceId, status, pspReferenceId
3. Busca Payment pelo nupay_reference_id
4. Se status == 'COMPLETED':
   - Chama payment.mark_as_paid()
   - Se subscription.is_blocked, chama subscription.unblock()
   - Se installment_number == 1 e package.welcome_xp_bonus > 0:
     - Chama user.add_xp(welcome_xp_bonus)
   - Envia WhatsApp de confirmação via megaapi
   - db.session.commit()
5. Se status == 'FAILED':
   - Atualiza payment.status = 'FAILED'
   - Envia WhatsApp de falha
   - db.session.commit()
6. Retorna {"status": "ok"}, 200

Importe: Payment, db, megaapi (se existir o serviço)

Modifique APENAS app/routes/webhooks.py.
```

---

## FASE 4: CHECKOUT PIX

### Prompt 4.1 - Rota Generate PIX

```
Adicione novas rotas no arquivo app/routes/shop.py para o checkout PIX.

Adicione estas rotas:

1. POST /generate-pix/<int:payment_id>
   - Verifica se payment existe e pertence ao current_user
   - Verifica se user tem CPF (se não, retorna erro pedindo CPF)
   - Instancia NuPayService()
   - Chama nupay.create_pix_payment(payment, current_user)
   - Salva no payment: nupay_reference_id, nupay_psp_reference_id, nupay_qr_code, nupay_pix_copy_paste, payment_method='nupay_pix'
   - db.session.commit()
   - Retorna JSON com qr_code, pix_copy_paste, payment_url

2. GET /payment-status/<int:payment_id>
   - Verifica se payment pertence ao current_user
   - Retorna JSON com status atual do payment

Importe NuPayService de app.services.nupay

Modifique APENAS app/routes/shop.py.
```

---

### Prompt 4.2 - Rotas Success e Cancel

```
Adicione rotas de sucesso e cancelamento em app/routes/shop.py:

1. GET /checkout/success
   - Renderiza template shop/success.html
   - Passa subscription mais recente do usuário

2. GET /checkout/cancel
   - Flash message de cancelamento
   - Redireciona para /shop

Modifique APENAS app/routes/shop.py.
```

---

### Prompt 4.3 - Template PIX Payment

```
Crie o template app/templates/shop/pix_payment.html para exibir o QR Code PIX.

O template deve:
1. Estender base.html
2. Mostrar:
   - Título "Aguardando Pagamento"
   - QR Code (imagem base64 ou gerada)
   - Botão "Copiar código PIX" (com JavaScript para copiar)
   - Valor e tempo de expiração (15 minutos)
   - Mensagem "Aguardando confirmação..."

3. JavaScript para polling:
   - A cada 5 segundos, faz fetch para /shop/payment-status/{{ payment.id }}
   - Se status == 'PAID', redireciona para /shop/checkout/success
   - Mostra contador regressivo de 15 minutos

Variáveis disponíveis: payment, qr_code, pix_copy_paste

Crie APENAS o arquivo app/templates/shop/pix_payment.html.
```

---

### Prompt 4.4 - Template Success

```
Crie o template app/templates/shop/success.html para confirmação de pagamento.

O template deve:
1. Estender base.html
2. Mostrar:
   - Ícone de sucesso (checkmark verde)
   - "Pagamento Confirmado!"
   - Resumo: nome do pacote, créditos, validade
   - Se tiver welcome_xp_bonus: "Bônus: +X XP de boas-vindas!"
   - Botões: "Ver Horários" (link para /student/schedule) e "Ir para Dashboard" (link para /student/dashboard)

Variáveis disponíveis: subscription

Crie APENAS o arquivo app/templates/shop/success.html.
```

---

### Prompt 4.5 - Atualizar Template Checkout

```
Atualize o template app/templates/shop/checkout.html para incluir opção de PIX NuPay.

MODIFICAÇÕES:
1. Adicionar seção "Forma de Pagamento" com radio buttons:
   - PIX à vista (Recomendado)
   - Upload de comprovante (método atual)

2. Se PIX selecionado, botão "Gerar PIX" que:
   - Faz POST via JavaScript para /shop/generate-pix/{{ payment.id }}
   - Redireciona para página de PIX ou mostra QR inline

3. Verificar se usuário tem CPF:
   - Se não tem, mostrar campo para informar CPF antes de gerar PIX
   - Validar CPF no frontend (formato)

Mantenha a funcionalidade existente de upload de comprovante como alternativa.

Modifique APENAS app/templates/shop/checkout.html.
```

---

## FASE 5: LANDING PAGE

### Prompt 5.1 - Blueprint Marketing

```
Crie o blueprint de marketing em app/routes/marketing.py.

O arquivo deve:
1. Criar Blueprint('marketing', __name__)
2. Criar rota GET / que:
   - Busca packages ativos ordenados por display_order
   - Busca modalities ativas
   - Busca top 10 users por XP (para hall da fama)
   - Calcula total de XP de todos os alunos
   - Renderiza template marketing/index.html

3. Criar função auxiliar anonymize_name(name) que:
   - Retorna primeira letra + asteriscos + última letra
   - Ex: "Ana Silva" -> "A*****a"

Crie APENAS o arquivo app/routes/marketing.py.
```

---

### Prompt 5.2 - Registrar Blueprint Marketing

```
Registre o blueprint marketing no arquivo app/__init__.py.

ADICIONAR:
1. Import: from app.routes.marketing import marketing_bp
2. Registrar: app.register_blueprint(marketing_bp)

IMPORTANTE: O blueprint marketing deve ser registrado ANTES do blueprint auth,
para que a rota "/" do marketing tenha prioridade.

Se a rota "/" atual redireciona para login, remova ou comente essa lógica
para dar lugar à landing page.

Modifique APENAS app/__init__.py.
```

---

### Prompt 5.3 - Template Landing Page Base

```
Crie o template app/templates/marketing/index.html (parte 1 - estrutura base).

O template deve:
1. NÃO estender base.html (é uma página standalone)
2. Incluir HTML completo com:
   - DOCTYPE, html, head, body
   - Meta tags para SEO e mobile
   - Link para CSS (pode ser inline ou arquivo separado)

3. Estrutura do body:
   - <nav> com logo, links (Planos, Modalidades, Entrar) e fundo transparente
   - <section id="hero"> com espaço para conteúdo
   - <section id="modalidades"> vazio por enquanto
   - <section id="planos"> vazio por enquanto
   - <section id="ranking"> vazio por enquanto
   - <footer> básico

4. CSS básico:
   - Paleta: fundo #1a1a2e, accent #FF6B35, texto #f8f9fa
   - Fonte: system-ui ou Inter
   - Nav sticky com transição de transparente para sólido

Crie APENAS a estrutura. O conteúdo será adicionado nos próximos prompts.
```

---

### Prompt 5.4 - Hero Section da Landing

```
Adicione o conteúdo da Hero Section no template app/templates/marketing/index.html.

Dentro de <section id="hero">, adicione:
1. Container centralizado com max-width 1200px
2. Título grande: "Transforme seu corpo com flexibilidade total."
3. Subtítulo: "Pague apenas pelas aulas que frequentar. Sem mensalidade fixa. Sem multa de cancelamento."
4. Botão CTA: "COMEÇAR AGORA" que rola suavemente até #planos
5. Espaço para imagem de fundo ou hero image

CSS necessário:
- Hero com min-height 100vh
- Texto centralizado ou à esquerda com imagem à direita
- Botão com cor #FF6B35, hover com escurecimento
- Responsivo para mobile

Modifique APENAS a section#hero no template.
```

---

### Prompt 5.5 - Seção de Modalidades

```
Adicione a seção de modalidades no template app/templates/marketing/index.html.

Dentro de <section id="modalidades">, adicione:
1. Título: "Nossas Modalidades"
2. Grid de cards usando Jinja2 loop:
   {% for modality in modalities %}
   - Card com fundo {{ modality.color }}
   - Ícone {{ modality.icon }}
   - Nome {{ modality.name }}
   - Descrição {{ modality.description }}
   - Badge: "{{ modality.credits_cost }} crédito(s)/aula"
   {% endfor %}

CSS necessário:
- Grid responsivo: 4 colunas desktop, 2 tablet, 1 mobile
- Cards com border-radius, sombra suave
- Hover com leve elevação

Modifique APENAS a section#modalidades no template.
```

---

### Prompt 5.6 - Seção de Planos/Pacotes

```
Adicione a seção de planos no template app/templates/marketing/index.html.

Dentro de <section id="planos">, adicione:
1. Título: "Escolha seu Plano"
2. Grid de cards usando Jinja2:
   {% for package in packages %}
   - Badge "DESTAQUE" se package.is_featured
   - Nome {{ package.name }}
   - Descrição {{ package.description }}
   - Preço: R$ {{ package.price }}
   - Se tem installments: "ou {{ package.installments }}x de R$ {{ package.installment_price }}"
   - Lista de benefícios:
     * {{ package.credits }} créditos
     * Válido por {{ package.validity_days }} dias
     * Loop em package.extra_benefits (se for JSON)
   - Economia: "{{ package.discount_percent }}% de economia"
   - Botão: "ASSINAR AGORA" linkando para /shop/checkout/{{ package.id }}
   {% endfor %}

CSS necessário:
- Card destacado com borda #FF6B35 e scale maior
- Preço grande e bold
- Botão full-width no card

Modifique APENAS a section#planos no template.
```

---

### Prompt 5.7 - Hall da Fama (Ranking Anônimo)

```
Adicione a seção de ranking no template app/templates/marketing/index.html.

Dentro de <section id="ranking">, adicione:
1. Título: "Hall da Fama"
2. Subtítulo: "Nossos alunos mais dedicados"
3. Lista dos top 10:
   {% for i, user in enumerate(top_users, 1) %}
   - Posição (1º, 2º, 3º com emojis de medalha)
   - Nome anonimizado: {{ anonymize_name(user.name) }}
   - Barra de progresso proporcional ao XP
   - XP: {{ user.xp }} XP
   - Nível: Nível {{ user.level }}
   {% endfor %}

4. Estatística: "Nossos alunos já acumularam {{ total_xp|number_format }} XP!"
5. CTA: "QUERO ENTRAR NO RANKING" linkando para /register

CSS necessário:
- Lista estilizada sem bullets
- Medalhas dourada/prata/bronze para top 3
- Barra de progresso animada
- Fundo levemente diferente da seção anterior

Modifique APENAS a section#ranking no template.
```

---

## FASE 6: SIMULADOR DE CRÉDITOS

### Prompt 6.1 - Componente Simulador HTML

```
Adicione o simulador de créditos na landing page app/templates/marketing/index.html.

Criar nova <section id="simulador"> ANTES da seção de planos.

Conteúdo:
1. Título: "Simule seu Treino"
2. Subtítulo: "Descubra quantos créditos você precisa por mês"

3. Para cada modalidade, criar slider:
   <div class="simulator-row" data-modality="{{ modality.id }}" data-cost="{{ modality.credits_cost }}">
     <label>{{ modality.name }} ({{ modality.credits_cost }} crédito/aula)</label>
     <input type="range" min="0" max="7" value="0" class="modality-slider">
     <span class="frequency-display">0x/semana</span>
   </div>

4. Área de resultado:
   <div id="simulator-result">
     <p>Você precisa de: <strong id="total-credits">0</strong> créditos/mês</p>
     <div id="recommended-package"></div>
   </div>

5. Dados dos pacotes em JSON para JavaScript:
   <script>
     const packagesData = {{ packages|tojson }};
   </script>

Modifique APENAS adicionando a section#simulador no template.
```

---

### Prompt 6.2 - JavaScript do Simulador

```
Crie o arquivo app/static/js/simulator.js com a lógica do simulador.

O script deve:
1. Selecionar todos os sliders .modality-slider
2. Para cada slider, adicionar event listener 'input' que:
   - Atualiza o span .frequency-display com "Xx/semana"
   - Chama função calculateTotal()

3. Função calculateTotal():
   - Para cada .simulator-row, pega:
     - data-cost (custo em créditos)
     - valor do slider (frequência semanal)
   - Calcula: custo * frequência * 4 (semanas/mês)
   - Soma todos e atualiza #total-credits
   - Chama recommendPackage(total)

4. Função recommendPackage(totalNeeded):
   - Filtra packagesData onde credits >= totalNeeded
   - Ordena por preço
   - Pega o mais barato como recomendado
   - Atualiza #recommended-package com:
     - Nome do pacote recomendado
     - Preço
     - Créditos (e quantos sobram)
     - Botão "COMPRAR" linkando para checkout

5. Se totalNeeded == 0, mostrar mensagem "Selecione suas modalidades"

Crie APENAS o arquivo app/static/js/simulator.js.
```

---

### Prompt 6.3 - Incluir Script do Simulador

```
Adicione a inclusão do script do simulador no template da landing page.

No final do body de app/templates/marketing/index.html, adicione:
<script src="{{ url_for('static', filename='js/simulator.js') }}"></script>

Também adicione o CSS necessário para o simulador:
- Sliders estilizados com cor #FF6B35
- Área de resultado com fundo destacado
- Animação suave nas transições

Modifique APENAS app/templates/marketing/index.html.
```

---

## FASE 7: ADMIN - PACOTES RECORRENTES

### Prompt 7.1 - Formulário de Pacotes Atualizado

```
Atualize o template de formulário de pacotes em app/templates/admin/packages/form.html.

ADICIONAR após os campos existentes:

1. Seção "Tipo de Cobrança":
   <div class="form-section">
     <h3>Tipo de Cobrança</h3>
     <div class="form-group">
       <label>
         <input type="checkbox" name="is_recurring" {{ 'checked' if package.is_recurring }}>
         Habilitar Cobrança Recorrente
       </label>
       <small>O cliente será cobrado automaticamente a cada período.</small>
     </div>
     <div class="form-group" id="recurring-options">
       <label>Intervalo de Cobrança (dias)</label>
       <input type="number" name="recurring_interval_days"
              value="{{ package.recurring_interval_days or 30 }}" min="7" max="365">
     </div>
   </div>

2. Seção "Gamificação":
   <div class="form-section">
     <h3>Gamificação</h3>
     <div class="form-group">
       <label>Bônus XP de Boas-vindas</label>
       <input type="number" name="welcome_xp_bonus"
              value="{{ package.welcome_xp_bonus or 0 }}" min="0" max="1000">
       <small>XP concedido na primeira compra deste pacote.</small>
     </div>
   </div>

3. JavaScript para mostrar/esconder recurring-options baseado no checkbox.

Modifique APENAS o template de form de pacotes.
```

---

### Prompt 7.2 - Rota de Pacotes Atualizada

```
Atualize as rotas de criação/edição de pacotes em app/routes/admin/packages.py.

Na rota POST de criar e editar pacote, adicione:

1. Capturar novos campos do form:
   - is_recurring = 'is_recurring' in request.form
   - recurring_interval_days = request.form.get('recurring_interval_days', 30, type=int)
   - welcome_xp_bonus = request.form.get('welcome_xp_bonus', 0, type=int)

2. Salvar no objeto package:
   - package.is_recurring = is_recurring
   - package.recurring_interval_days = recurring_interval_days
   - package.welcome_xp_bonus = welcome_xp_bonus

Modifique APENAS app/routes/admin/packages.py.
```

---

## FASE 8: STUDENT - RECORRÊNCIA

### Prompt 8.1 - Cancelar Recorrência

```
Adicione rota para cancelar recorrência em app/routes/student.py.

Criar rota POST /subscription/<int:id>/cancel-recurring que:
1. Busca subscription pelo id
2. Verifica se pertence ao current_user (senão abort 403)
3. Verifica se is_recurring é True
4. Instancia NuPayService
5. Chama nupay.cancel_subscription(subscription.nupay_subscription_id)
6. Atualiza:
   - subscription.recurring_status = 'CANCELLED'
   - subscription.is_recurring = False
7. db.session.commit()
8. Flash message de sucesso
9. Redirect para subscription_detail

Adicione tratamento de erro se a chamada NuPay falhar.

Modifique APENAS app/routes/student.py.
```

---

### Prompt 8.2 - Template Subscription Detail Atualizado

```
Atualize o template app/templates/student/subscription_detail.html para mostrar info de recorrência.

ADICIONAR:
1. Se subscription.is_recurring:
   - Badge "Recorrência Ativa" ou "Recorrência Cancelada"
   - Mostrar próxima cobrança: subscription.next_billing_date
   - Mostrar última cobrança: subscription.last_billing_date
   - Botão "Cancelar Recorrência" que:
     - Abre modal de confirmação
     - Faz POST para /student/subscription/{{ subscription.id }}/cancel-recurring

2. Modal de confirmação com:
   - "Tem certeza que deseja cancelar a recorrência?"
   - "Você ainda poderá usar seus créditos até o vencimento."
   - Botões: "Manter Recorrência" e "Cancelar Recorrência"

Modifique APENAS o template subscription_detail.html.
```

---

## FASE 9: FORMULÁRIO DE CPF

### Prompt 9.1 - Campo CPF no Registro

```
Atualize o formulário de registro em app/templates/auth/register.html.

ADICIONAR campo CPF:
<div class="form-group">
  <label for="cpf">CPF *</label>
  <input type="text" id="cpf" name="cpf" required
         placeholder="000.000.000-00" maxlength="14">
  <small>Necessário para pagamentos via PIX</small>
</div>

ADICIONAR JavaScript para máscara de CPF:
- Formatar automaticamente enquanto digita: XXX.XXX.XXX-XX
- Aceitar apenas números
- Validar formato antes do submit

Modifique APENAS o template register.html.
```

---

### Prompt 9.2 - Rota de Registro Atualizada

```
Atualize a rota de registro em app/routes/auth.py para salvar CPF.

Na rota POST /register:
1. Capturar CPF do form: cpf = request.form.get('cpf')
2. Validar CPF usando User.validate_cpf(cpf)
3. Se inválido, flash error e retornar
4. Formatar CPF: cpf = User.format_cpf(cpf)
5. Salvar no user: user.cpf = cpf

Modifique APENAS app/routes/auth.py.
```

---

### Prompt 9.3 - Modal CPF no Checkout

```
Adicione modal para solicitar CPF no checkout se usuário não tiver.

Em app/templates/shop/checkout.html:

1. Verificar se current_user.cpf existe
2. Se não existe, mostrar modal ANTES de permitir gerar PIX:
   <div id="cpf-modal" class="modal">
     <h3>Informe seu CPF</h3>
     <p>Precisamos do seu CPF para gerar o PIX.</p>
     <form id="cpf-form">
       <input type="text" id="modal-cpf" placeholder="000.000.000-00" required>
       <button type="submit">Salvar e Continuar</button>
     </form>
   </div>

3. JavaScript que:
   - Faz POST via fetch para /student/update-cpf (criar essa rota)
   - Se sucesso, fecha modal e permite gerar PIX
   - Se erro, mostra mensagem de CPF inválido

Modifique APENAS o template checkout.html.
```

---

### Prompt 9.4 - Rota Update CPF

```
Crie rota para atualizar CPF em app/routes/student.py.

Criar rota POST /update-cpf que:
1. Requer login
2. Captura CPF do JSON: cpf = request.json.get('cpf')
3. Valida usando User.validate_cpf(cpf)
4. Se válido:
   - Formata: cpf = User.format_cpf(cpf)
   - Salva: current_user.cpf = cpf
   - db.session.commit()
   - Retorna JSON {"success": true}
5. Se inválido:
   - Retorna JSON {"success": false, "error": "CPF inválido"}, 400

Modifique APENAS app/routes/student.py.
```

---

## FASE 10: TESTES E AJUSTES FINAIS

### Prompt 10.1 - Testar Fluxo Completo

```
Faça uma revisão do fluxo completo e corrija erros.

VERIFICAR:
1. Landing page carrega sem erros
2. Simulador calcula corretamente
3. Registro com CPF funciona
4. Checkout exibe opção PIX
5. Se usuário não tem CPF, modal aparece
6. Webhook processa pagamentos (testar com dados fake)

CORRIGIR qualquer erro de:
- Import faltando
- Variáveis não definidas no template
- Rotas não registradas
- Campos não existentes no model

Liste os erros encontrados e corrija um por um.
```

---

### Prompt 10.2 - Criar Dados de Teste

```
Crie um script para popular dados de teste em scripts/seed_data.py.

O script deve criar:
1. 3 Modalidades: Musculação, Yoga, Spinning (com cores e custos diferentes)
2. 3 Pacotes: Bronze (30 créditos), Silver (50 créditos), Gold (100 créditos)
   - Gold deve ser is_featured=True
   - Silver deve ter welcome_xp_bonus=100
3. 1 Usuário admin
4. 5 Usuários estudantes com XP variado (para o ranking)

Execute com: python scripts/seed_data.py

Crie APENAS o arquivo scripts/seed_data.py.
```

---

## COMANDOS ÚTEIS

```bash
# Rodar migrations
flask db migrate -m "mensagem"
flask db upgrade

# Rodar servidor
flask run

# Testar webhook localmente (instalar ngrok)
ngrok http 5000
# Copiar URL https e configurar no painel NuPay

# Verificar erros de import
python -c "from app import create_app; app = create_app()"
```

---

## CHECKLIST FINAL

- [ ] Models atualizados (User, Payment, Package, Subscription)
- [ ] Migration executada
- [ ] Config atualizado com variáveis NuPay
- [ ] NuPayService criado e funcional
- [ ] Webhook NuPay implementado
- [ ] Rotas de checkout PIX funcionando
- [ ] Templates de PIX e sucesso criados
- [ ] Landing page completa
- [ ] Simulador funcionando
- [ ] Admin pode criar pacotes recorrentes
- [ ] Student pode cancelar recorrência
- [ ] CPF coletado no registro e checkout
- [ ] Testes básicos passando

---

**Dica:** Execute cada prompt em uma conversa separada se o Antigravity começar a se perder. Valide o resultado de cada prompt antes de prosseguir para o próximo.
