# 📄 PRD: Upgrade de Vendas e Pagamentos Automatizados

**Versão:** 1.0
**Data:** 23 de Janeiro de 2026
**Status:** Em Análise
**Autor:** Equipe de Produto

---

## 📋 Índice

1. [Resumo Executivo](#1-resumo-executivo)
2. [Contexto e Problema](#2-contexto-e-problema)
3. [Objetivos e Métricas de Sucesso](#3-objetivos-e-métricas-de-sucesso)
4. [Escopo do Projeto](#4-escopo-do-projeto)
5. [Requisitos Funcionais](#5-requisitos-funcionais)
6. [Requisitos Técnicos](#6-requisitos-técnicos)
7. [Arquitetura Proposta](#7-arquitetura-proposta)
8. [Plano de Implementação](#8-plano-de-implementação)
9. [Riscos e Mitigações](#9-riscos-e-mitigações)
10. [Critérios de Aceite](#10-critérios-de-aceite)

---

## 1. Resumo Executivo

### Visão do Produto

Transformar o sistema atual de gestão de academia em uma **Plataforma de Experiência e Vendas Self-Service** de alta conversão. O aluno deve ser capaz de:

> Ver o valor da academia → Simular seu uso → Comprar via PIX/Recorrente → Receber acesso imediato

**Sem intervenção humana.**

### Mudança de Paradigma

| Antes (Atual) | Depois (Proposto) |
|---------------|-------------------|
| Sistema de gestão interno | Plataforma de vendas e experiência |
| Upload manual de comprovante | Checkout automatizado NuPay |
| Aprovação manual de pagamentos | Liberação instantânea via webhook |
| Sem página de vendas | Landing page de alta conversão |
| Cobrança única por pacote | PIX único + Recorrência mensal |

---

## 2. Contexto e Problema

### 2.1 Situação Atual

O sistema atual (`app/routes/shop.py`) oferece:
- Listagem de pacotes em `/shop/`
- Checkout que cria `Subscription` + `Payment` records
- Upload manual de comprovante (`/shop/payment/<id>/upload`)
- Aprovação manual pelo admin (`/admin/payments/approve/<id>`)

**Fluxo atual de compra:**
```
[Aluno vê pacote] → [Checkout] → [Upload comprovante] → [Admin aprova] → [Créditos liberados]
                                        ↓
                            Tempo médio: 2-24 horas
```

### 2.2 Problemas Identificados

| Problema | Impacto | Evidência no Código |
|----------|---------|---------------------|
| **Fricção no checkout** | Abandono de carrinho | `shop.py:checkout()` cria subscription sem pagamento confirmado |
| **Delay na liberação** | Frustração do cliente | `payments.py:approve()` é processo manual |
| **Sem página de vendas** | Zero conversão orgânica | `/` redireciona direto para login |
| **Sem recorrência real** | Inadimplência e churn | `Package.installments` é apenas divisão, não cobrança automática |
| **CPF não coletado** | Impossibilita NuPay | `User` model não tem campo `cpf` |

### 2.3 Oportunidade de Mercado

A integração com NuPay permite:
- **PIX instantâneo** com QR Code e Deep Link
- **Cobrança recorrente** (CIBA/OAuth2) autorizada pelo cliente
- **Conciliação automática** via webhooks em tempo real

---

## 3. Objetivos e Métricas de Sucesso

### 3.1 Objetivos de Negócio

| Objetivo | Meta | Prazo |
|----------|------|-------|
| Aumentar conversão de visitantes | +40% | 90 dias |
| Reduzir tempo de liberação de créditos | < 5 segundos | Launch |
| Eliminar trabalho manual de aprovação | 100% automático | Launch |
| Reduzir inadimplência | -30% | 180 dias |

### 3.2 Métricas de Sucesso (KPIs)

**Métricas de Aquisição:**
- Taxa de conversão landing page → checkout
- Taxa de conclusão do checkout
- Tempo médio até primeira aula

**Métricas de Retenção:**
- Taxa de renovação automática (recorrência)
- Churn rate mensal
- LTV por tipo de pacote

**Métricas Operacionais:**
- Pagamentos aprovados automaticamente vs manual
- Tempo médio de liberação de créditos
- Taxa de falha de webhook

---

## 4. Escopo do Projeto

### 4.1 Incluído no Escopo (MVP)

| Componente | Descrição | Prioridade |
|------------|-----------|------------|
| **Landing Page** | Página de vendas pública com hero, planos e CTA | P0 |
| **Simulador de Créditos** | Calculadora interativa de pacotes | P0 |
| **Integração NuPay PIX** | Checkout com PIX instantâneo | P0 |
| **Webhooks NuPay** | Liberação automática de créditos | P0 |
| **Campo CPF no User** | Requisito obrigatório para NuPay | P0 |
| **Recorrência NuPay** | Cobrança mensal automática (CIBA) | P1 |
| **Social Proof** | Hall da Fama anônimo na landing | P1 |
| **Bônus XP de Boas-vindas** | Gamificação na compra | P2 |

### 4.2 Fora do Escopo (Futuro)

- Integração com outras formas de pagamento (cartão de crédito)
- App mobile nativo
- Sistema de indicação (referral)
- Integração com redes sociais
- A/B testing nativo

### 4.3 Dependências Externas

| Dependência | Responsável | Status |
|-------------|-------------|--------|
| Conta NuPay Business | Admin da Academia | Pendente |
| Credenciais API (X-Merchant-Key/Token) | NuPay | Pendente |
| Cadastro de URL de webhook | NuPay Business Panel | Pendente |
| Servidor com HTTPS (produção) | DevOps | Existente |

---

## 5. Requisitos Funcionais

### 5.1 Landing Page Moderna (RF-001)

**Descrição:** Criar página pública de vendas em `/` substituindo o redirecionamento para login.

#### 5.1.1 Hero Section

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo]                    Planos  |  Modalidades  |  [Entrar]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     Transforme seu corpo                                        │
│     com flexibilidade total.                                    │
│                                                                 │
│     Pague apenas pelas aulas que frequentar.                    │
│     Sem mensalidade fixa. Sem multa de cancelamento.            │
│                                                                 │
│              [ COMEÇAR AGORA ]  ←── CTA Principal               │
│                                                                 │
│     [Imagem de alta qualidade da academia]                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Regras de Negócio:**
- Menu transparente que fica sólido ao rolar (sticky)
- CTA rola suavemente até seção de planos
- Hero image: foto real da academia ou instrutores
- Responsivo para mobile

#### 5.1.2 Seção de Modalidades

**Origem dos dados:** `Modality` model existente

```python
# Query existente em shop.py que pode ser reaproveitada
modalities = Modality.query.filter_by(is_active=True).all()
```

**Layout:**
- Grid de cards com `modality.icon`, `modality.name`, `modality.description`
- Cor de fundo: `modality.color`
- Custo em créditos: `modality.credits_cost`

#### 5.1.3 Seção de Planos (Pacotes)

**Origem dos dados:** `Package` model existente

```python
# Query existente
packages = Package.query.filter_by(is_active=True).order_by(Package.display_order).all()
```

**Layout para cada card:**
```
┌───────────────────────────────┐
│  [Destaque] ← se is_featured  │
│                               │
│  PACOTE SILVER                │
│  "Para quem treina 3x/semana" │
│                               │
│  R$ 199,00                    │
│  ou 3x de R$ 69,90            │
│                               │
│  ✓ 50 créditos                │
│  ✓ Válido por 30 dias         │
│  ✓ Todas as modalidades       │
│  ✓ {extra_benefits JSON}      │
│                               │
│     [ ASSINAR AGORA ]         │
│                               │
│  Economia de 15% vs avulso    │
└───────────────────────────────┘
```

**Cálculos exibidos:**
- Economia: `package.discount_percent` (já existe no model)
- Preço por crédito: `package.price_per_credit` (já existe)

#### 5.1.4 Simulador de Créditos Interativo (RF-002)

**Descrição:** Calculadora que ajuda o cliente a escolher o pacote ideal.

**Interface:**
```
┌─────────────────────────────────────────────────────────────────┐
│  📊 SIMULADOR DE TREINO                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Quantas vezes por semana você pretende treinar cada           │
│  modalidade?                                                    │
│                                                                 │
│  Musculação (1 crédito/aula)                                   │
│  [━━━━━━●━━━━━━━━━━━━━━] 3x/semana                              │
│                                                                 │
│  Yoga (1 crédito/aula)                                         │
│  [━━●━━━━━━━━━━━━━━━━━━] 1x/semana                              │
│                                                                 │
│  Spinning (2 créditos/aula)                                    │
│  [━━━━━━━━━●━━━━━━━━━━━] 2x/semana                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  📈 RESULTADO                                                   │
│                                                                 │
│  Você precisa de: 28 créditos/mês                              │
│                                                                 │
│  ✅ Recomendado: PACOTE SILVER (50 créditos)                   │
│     R$ 199,00 - sobram 22 créditos para experimentar!          │
│                                                                 │
│  ⚠️ Alternativa: PACOTE BRONZE (30 créditos)                   │
│     R$ 129,00 - margem apertada, sem folga                     │
│                                                                 │
│              [ COMPRAR SILVER ]                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Lógica de cálculo:**
```python
# Pseudo-código
total_credits_needed = sum(
    modality.credits_cost * weekly_frequency * 4  # 4 semanas/mês
    for modality, weekly_frequency in selections
)

# Encontrar pacote ideal
recommended = Package.query.filter(
    Package.credits >= total_credits_needed,
    Package.is_active == True
).order_by(Package.price).first()
```

#### 5.1.5 Social Proof - Hall da Fama (RF-003)

**Descrição:** Exibir ranking de XP de forma anônima para criar desejo.

**Origem dos dados:** Query existente em `student.py:ranking()`

```python
# Adaptar query existente
top_users = User.query.filter_by(role='student', is_active=True)\
    .order_by(User.xp.desc()).limit(10).all()
```

**Exibição:**
```
┌─────────────────────────────────────────────────────────────────┐
│  🏆 HALL DA FAMA - TOP 10                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1º  🥇  A****a  ████████████████████  2.450 XP  Nível 25      │
│  2º  🥈  R****o  ███████████████████   2.180 XP  Nível 22      │
│  3º  🥉  M****a  ██████████████████    1.920 XP  Nível 20      │
│  4º      C****s  █████████████████     1.750 XP  Nível 18      │
│  5º      J****a  ████████████████      1.580 XP  Nível 16      │
│  ...                                                            │
│                                                                 │
│  "Nossos alunos já acumularam 45.000+ XP este mês!"            │
│                                                                 │
│              [ QUERO ENTRAR NO RANKING ]                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Regras de Anonimização:**
- Nome: primeira letra + asteriscos + última letra (ex: "Ana" → "A**a")
- Sem foto do usuário
- Sem link para perfil

---

### 5.2 Integração NuPay - PIX Instantâneo (RF-004)

**Descrição:** Substituir upload manual por checkout NuPay.

#### 5.2.1 Fluxo de Checkout Atualizado

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Aluno     │    │   Backend   │    │   NuPay     │    │   Webhook   │
│  escolhe    │───▶│   cria      │───▶│   gera      │    │   confirma  │
│  pacote     │    │  Subscription│    │   PIX       │    │   pagamento │
└─────────────┘    │  + Payment   │    │             │    │             │
                   └─────────────┘    └──────┬──────┘    └──────┬──────┘
                                             │                   │
                         ┌───────────────────┘                   │
                         ▼                                       │
                   ┌─────────────┐                               │
                   │   Aluno     │                               │
                   │   escaneia  │──────────────────────────────▶│
                   │   QR Code   │    (Paga via app Nubank)      │
                   │   ou clica  │                               │
                   │   deep link │                               │
                   └─────────────┘                               │
                                                                 │
                   ┌─────────────┐    ┌─────────────┐            │
                   │  Créditos   │◀───│   Backend   │◀───────────┘
                   │  liberados  │    │   processa  │
                   │  INSTANTÂNEO│    │   webhook   │
                   └─────────────┘    └─────────────┘
```

#### 5.2.2 Novo Campo: CPF no User (RF-005)

**Alteração no modelo `User` (`app/models/user.py`):**

```python
# Adicionar campo
cpf = db.Column(db.String(14), nullable=True)  # Formato: 123.456.789-00

# Adicionar validação
@staticmethod
def validate_cpf(cpf):
    """Valida CPF usando algoritmo oficial."""
    # Implementar validação de dígitos verificadores
    pass
```

**Alteração no registro (`app/routes/auth.py`):**
- Adicionar campo CPF no formulário de registro
- Tornar obrigatório para novos usuários
- Validar formato e dígitos verificadores

**Alteração no checkout (`app/routes/shop.py`):**
- Se usuário antigo não tem CPF, solicitar antes do checkout
- Modal ou etapa intermediária

#### 5.2.3 Página de Checkout com PIX (RF-006)

**Nova interface `/shop/checkout/<package_id>`:**

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar                                    CHECKOUT SEGURO 🔒 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RESUMO DO PEDIDO                                               │
│  ─────────────────                                              │
│  Pacote Silver - 50 créditos                                   │
│  Validade: 30 dias                                             │
│                                                                 │
│  Subtotal:                              R$ 199,00              │
│  ─────────────────────────────────────────────                 │
│  TOTAL:                                 R$ 199,00              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FORMA DE PAGAMENTO                                             │
│  ─────────────────────                                          │
│                                                                 │
│  ○ PIX à vista (Recomendado)                                   │
│    Pagamento instantâneo via Nubank                            │
│                                                                 │
│  ○ PIX Parcelado (3x de R$ 69,90)                              │
│    Primeira parcela agora, demais no vencimento                │
│                                                                 │
│  ○ Recorrência Mensal (R$ 199,00/mês)                          │
│    Renovação automática - cancele quando quiser                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│              [ GERAR PIX ]                                     │
│                                                                 │
│  Ao continuar, você concorda com os Termos de Uso              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 5.2.4 Tela de Pagamento PIX (RF-007)

**Após gerar PIX, exibir:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGUARDANDO PAGAMENTO                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────────┐                          │
│                    │                 │                          │
│                    │   [QR CODE]     │   ← Escaneie com         │
│                    │                 │     seu app de banco     │
│                    │                 │                          │
│                    └─────────────────┘                          │
│                                                                 │
│                    ou                                           │
│                                                                 │
│    [ ABRIR APP NUBANK ]  ← Deep link (mobile)                  │
│                                                                 │
│    PIX Copia e Cola:                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 00020126580014br.gov.bcb.pix...            │ [Copiar]     │
│    └─────────────────────────────────────────────┘             │
│                                                                 │
│    Valor: R$ 199,00                                            │
│    Expira em: 14:32 (15 minutos)                               │
│                                                                 │
│    ⏳ Aguardando confirmação do pagamento...                    │
│       (A página atualiza automaticamente)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Comportamento:**
- Polling a cada 5 segundos para verificar status
- Ou WebSocket para atualização instantânea
- Timeout de 15 minutos (configurável)
- Ao confirmar: redireciona para página de sucesso

#### 5.2.5 Página de Sucesso (RF-008)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                         ✅                                      │
│                                                                 │
│              PAGAMENTO CONFIRMADO!                              │
│                                                                 │
│    Seus 50 créditos já estão disponíveis.                      │
│                                                                 │
│    ┌─────────────────────────────────────────┐                 │
│    │  📊 RESUMO                              │                 │
│    │                                         │                 │
│    │  Pacote: Silver                         │                 │
│    │  Créditos: 50                           │                 │
│    │  Válido até: 22/02/2026                 │                 │
│    │  Bônus XP: +100 XP de boas-vindas!      │                 │
│    └─────────────────────────────────────────┘                 │
│                                                                 │
│    🎯 Próximo passo: Agende sua primeira aula!                 │
│                                                                 │
│           [ VER HORÁRIOS ]    [ IR PARA DASHBOARD ]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 5.3 Webhook NuPay - Liberação Automática (RF-009)

**Descrição:** Endpoint para receber notificações de pagamento.

#### 5.3.1 Endpoint do Webhook

**Rota:** `POST /webhooks/nupay/callback`

**Payload esperado (baseado em OpenAPI):**

```json
{
  "pspReferenceId": "NUPAY_123456789",
  "merchantReferenceId": "PAYMENT_42",
  "status": "COMPLETED",
  "amount": {
    "value": 199.00,
    "currency": "BRL"
  },
  "paymentMethod": {
    "type": "nupay"
  },
  "timestamp": "2026-01-23T14:30:00Z"
}
```

#### 5.3.2 Lógica de Processamento

```python
@webhooks_bp.route('/nupay/callback', methods=['POST'])
def nupay_callback():
    # 1. Validar assinatura do webhook (HMAC)
    if not validate_nupay_signature(request):
        return jsonify({"error": "Invalid signature"}), 401

    data = request.get_json()
    merchant_reference = data.get('merchantReferenceId')
    status = data.get('status')

    # 2. Buscar payment pelo reference
    payment = Payment.query.filter_by(nupay_reference_id=merchant_reference).first()

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # 3. Processar conforme status
    if status == 'COMPLETED':
        payment.mark_as_paid()  # Método existente

        # 4. Desbloquear subscription se estava bloqueada
        if payment.subscription.is_blocked:
            payment.subscription.unblock()

        # 5. Aplicar bônus XP de boas-vindas (se primeiro pagamento)
        if payment.installment_number == 1:
            xp_bonus = payment.subscription.package.welcome_xp_bonus or 0
            if xp_bonus > 0:
                payment.subscription.user.add_xp(xp_bonus)

        # 6. Notificar via WhatsApp
        megaapi.send_template_message(
            phone=payment.subscription.user.phone,
            template_code='payment_confirmed',
            variables={
                'nome': payment.subscription.user.name.split()[0],
                'creditos': payment.subscription.credits_remaining,
                'validade': payment.subscription.end_date.strftime('%d/%m/%Y')
            }
        )

        db.session.commit()

    elif status == 'FAILED':
        payment.status = 'FAILED'
        # Notificar falha
        megaapi.send_custom_message(
            payment.subscription.user.phone,
            "❌ Ops! Seu pagamento não foi processado. Tente novamente ou entre em contato."
        )
        db.session.commit()

    return jsonify({"status": "ok"}), 200
```

#### 5.3.3 Validação de Assinatura (Segurança)

```python
import hmac
import hashlib

def validate_nupay_signature(request):
    """Valida HMAC-SHA256 do webhook NuPay."""
    signature = request.headers.get('X-NuPay-Signature')
    if not signature:
        return False

    secret = current_app.config['NUPAY_WEBHOOK_SECRET']
    payload = request.get_data()

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

---

### 5.4 Pagamento Recorrente - CIBA (RF-010)

**Descrição:** Cobrança mensal automática via PIX pré-autorizado.

#### 5.4.1 Fluxo CIBA (Client-Initiated Backchannel Authentication)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Aluno     │    │   Backend   │    │   NuPay     │    │   Nubank    │
│  autoriza   │───▶│   inicia    │───▶│   envia     │───▶│   notifica  │
│  recorrência│    │   CIBA      │    │   auth req  │    │   cliente   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                   ┌─────────────────────────────────────────────┘
                   ▼
             ┌─────────────┐
             │   Cliente   │
             │   aprova    │  (Push no app Nubank)
             │   no Nubank │
             └─────────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │   Cobranças mensais   │  (Automáticas no vencimento)
       │   até cancelamento    │
       └───────────────────────┘
```

#### 5.4.2 Alterações no Modelo Package

```python
# app/models/package.py - Novos campos
class Package(db.Model):
    # ... campos existentes ...

    # Novos campos para recorrência e gamificação
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_interval_days = db.Column(db.Integer, default=30)  # Intervalo entre cobranças
    welcome_xp_bonus = db.Column(db.Integer, default=0)  # Bônus XP na primeira compra
```

#### 5.4.3 Alterações no Modelo Subscription

```python
# app/models/subscription.py - Novos campos
class Subscription(db.Model):
    # ... campos existentes ...

    # Campos para recorrência NuPay
    is_recurring = db.Column(db.Boolean, default=False)
    nupay_subscription_id = db.Column(db.String(100), nullable=True)  # ID da assinatura na NuPay
    recurring_status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, PAUSED, CANCELLED
    next_billing_date = db.Column(db.Date, nullable=True)
    last_billing_date = db.Column(db.Date, nullable=True)
```

#### 5.4.4 Cancelamento de Recorrência

**Rota:** `POST /student/subscription/<id>/cancel-recurring`

```python
@student_bp.route('/subscription/<int:id>/cancel-recurring', methods=['POST'])
@login_required
def cancel_recurring(id):
    subscription = Subscription.query.get_or_404(id)

    if subscription.user_id != current_user.id:
        abort(403)

    if not subscription.is_recurring:
        flash('Esta assinatura não é recorrente.', 'warning')
        return redirect(url_for('student.subscriptions'))

    # Cancelar na NuPay
    nupay = NuPayService()
    result = nupay.cancel_subscription(subscription.nupay_subscription_id)

    if result.get('success'):
        subscription.recurring_status = 'CANCELLED'
        subscription.is_recurring = False
        db.session.commit()

        flash('Recorrência cancelada. Você pode usar os créditos restantes até o vencimento.', 'success')
    else:
        flash('Erro ao cancelar recorrência. Tente novamente.', 'error')

    return redirect(url_for('student.subscription_detail', id=id))
```

---

### 5.5 Melhorias no Admin - Criação de Pacotes (RF-011)

**Descrição:** Permitir configuração de recorrência e bônus XP.

#### 5.5.1 Formulário de Criação/Edição

**Novos campos em `/admin/packages/form.html`:**

```html
<!-- Seção: Tipo de Cobrança -->
<div class="form-section">
    <h3>💳 Tipo de Cobrança</h3>

    <div class="form-group">
        <label class="toggle-label">
            <input type="checkbox" name="is_recurring" id="is_recurring"
                   {{ 'checked' if package.is_recurring else '' }}>
            <span class="toggle-switch"></span>
            Habilitar Cobrança Recorrente
        </label>
        <small>Quando ativado, o cliente será cobrado automaticamente a cada período.</small>
    </div>

    <div id="recurring-options" style="display: none;">
        <div class="form-group">
            <label for="recurring_interval_days">Intervalo de Cobrança (dias)</label>
            <input type="number" name="recurring_interval_days" id="recurring_interval_days"
                   value="{{ package.recurring_interval_days or 30 }}" min="7" max="365">
        </div>
    </div>
</div>

<!-- Seção: Gamificação -->
<div class="form-section">
    <h3>🎮 Gamificação</h3>

    <div class="form-group">
        <label for="welcome_xp_bonus">Bônus XP de Boas-vindas</label>
        <input type="number" name="welcome_xp_bonus" id="welcome_xp_bonus"
               value="{{ package.welcome_xp_bonus or 0 }}" min="0" max="1000">
        <small>XP concedido ao cliente na primeira compra deste pacote.</small>
    </div>
</div>
```

---

## 6. Requisitos Técnicos

### 6.1 Novo Serviço: NuPayService

**Arquivo:** `app/services/nupay.py`

```python
"""
Serviço de integração com API NuPay (Nubank Business).
Baseado na especificação OpenAPI fornecida.
"""

import requests
import hmac
import hashlib
from flask import current_app
from datetime import datetime, timedelta


class NuPayService:
    """Cliente para API NuPay."""

    def __init__(self):
        self.base_url = current_app.config.get('NUPAY_BASE_URL', 'https://api.spinpay.com.br')
        self.headers = {
            'X-Merchant-Key': current_app.config['NUPAY_MERCHANT_KEY'],
            'X-Merchant-Token': current_app.config['NUPAY_MERCHANT_TOKEN'],
            'Content-Type': 'application/json'
        }

    def create_pix_payment(self, payment, user):
        """
        Cria um pagamento PIX instantâneo.

        Args:
            payment: Payment model instance
            user: User model instance

        Returns:
            dict com pspReferenceId, paymentUrl, qrCode, pixCopyPaste
        """
        url = f"{self.base_url}/v1/checkouts/payments"

        payload = {
            "referenceId": f"PAYMENT_{payment.id}",
            "amount": {
                "value": float(payment.amount),
                "currency": "BRL"
            },
            "paymentMethod": {
                "type": "nupay",
                "authorizationType": "manually_authorized"
            },
            "shopper": {
                "firstName": user.name.split()[0],
                "lastName": " ".join(user.name.split()[1:]) or user.name,
                "document": user.cpf.replace('.', '').replace('-', ''),
                "email": user.email,
                "phone": user.phone
            },
            "paymentFlow": {
                "returnUrl": f"{current_app.config['BASE_URL']}/shop/checkout/success",
                "cancelUrl": f"{current_app.config['BASE_URL']}/shop/checkout/cancel"
            },
            "expiresAt": (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()

    def create_recurring_subscription(self, subscription, user):
        """
        Cria uma assinatura recorrente (CIBA flow).

        Args:
            subscription: Subscription model instance
            user: User model instance

        Returns:
            dict com subscriptionId, authorizationUrl
        """
        url = f"{self.base_url}/v1/subscriptions"

        payload = {
            "referenceId": f"SUB_{subscription.id}",
            "amount": {
                "value": float(subscription.package.price),
                "currency": "BRL"
            },
            "interval": {
                "unit": "day",
                "length": subscription.package.recurring_interval_days or 30
            },
            "shopper": {
                "firstName": user.name.split()[0],
                "document": user.cpf.replace('.', '').replace('-', ''),
                "email": user.email,
                "phone": user.phone
            },
            "paymentFlow": {
                "returnUrl": f"{current_app.config['BASE_URL']}/student/subscription/{subscription.id}",
                "cancelUrl": f"{current_app.config['BASE_URL']}/student/subscriptions"
            }
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()

    def cancel_subscription(self, nupay_subscription_id):
        """
        Cancela uma assinatura recorrente.

        Args:
            nupay_subscription_id: ID da assinatura na NuPay

        Returns:
            dict com status do cancelamento
        """
        url = f"{self.base_url}/v1/subscriptions/{nupay_subscription_id}/cancel"

        response = requests.post(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        return response.json()

    def get_payment_status(self, psp_reference_id):
        """
        Consulta status de um pagamento.

        Args:
            psp_reference_id: ID do pagamento na NuPay

        Returns:
            dict com status atual
        """
        url = f"{self.base_url}/v1/checkouts/payments/{psp_reference_id}"

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        return response.json()

    def refund_payment(self, psp_reference_id, amount=None):
        """
        Estorna um pagamento (total ou parcial).

        Args:
            psp_reference_id: ID do pagamento na NuPay
            amount: Valor a estornar (None = total)

        Returns:
            dict com status do estorno
        """
        url = f"{self.base_url}/v1/checkouts/payments/{psp_reference_id}/refund"

        payload = {}
        if amount:
            payload["amount"] = {"value": float(amount), "currency": "BRL"}

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()
```

### 6.2 Novas Configurações

**Adicionar ao `config.py`:**

```python
class Config:
    # ... configs existentes ...

    # NuPay Configuration
    NUPAY_BASE_URL = os.environ.get('NUPAY_BASE_URL', 'https://api.spinpay.com.br')
    NUPAY_MERCHANT_KEY = os.environ.get('NUPAY_MERCHANT_KEY')
    NUPAY_MERCHANT_TOKEN = os.environ.get('NUPAY_MERCHANT_TOKEN')
    NUPAY_WEBHOOK_SECRET = os.environ.get('NUPAY_WEBHOOK_SECRET')

    # Base URL for callbacks
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
```

**Adicionar ao `.env`:**

```env
# NuPay Credentials
NUPAY_BASE_URL=https://api.spinpay.com.br
NUPAY_MERCHANT_KEY=sua-merchant-key
NUPAY_MERCHANT_TOKEN=seu-merchant-token
NUPAY_WEBHOOK_SECRET=seu-webhook-secret

# Application URL
BASE_URL=https://suaacademia.com.br
```

### 6.3 Alterações no Modelo Payment

```python
# app/models/payment.py - Novos campos
class Payment(db.Model):
    # ... campos existentes ...

    # Campos NuPay
    nupay_reference_id = db.Column(db.String(100), nullable=True)  # merchantReferenceId
    nupay_psp_reference_id = db.Column(db.String(100), nullable=True)  # pspReferenceId
    nupay_payment_url = db.Column(db.String(500), nullable=True)  # URL para pagamento
    nupay_qr_code = db.Column(db.Text, nullable=True)  # QR Code base64
    nupay_pix_copy_paste = db.Column(db.Text, nullable=True)  # Código PIX
    payment_method = db.Column(db.String(20), default='manual')  # manual, nupay_pix, nupay_recurring
```

### 6.4 Migrations Necessárias

```python
# migrations/versions/xxxx_add_nupay_fields.py

def upgrade():
    # User - CPF
    op.add_column('users', sa.Column('cpf', sa.String(14), nullable=True))

    # Package - Recorrência e XP
    op.add_column('packages', sa.Column('is_recurring', sa.Boolean(), default=False))
    op.add_column('packages', sa.Column('recurring_interval_days', sa.Integer(), default=30))
    op.add_column('packages', sa.Column('welcome_xp_bonus', sa.Integer(), default=0))

    # Subscription - Recorrência NuPay
    op.add_column('subscriptions', sa.Column('is_recurring', sa.Boolean(), default=False))
    op.add_column('subscriptions', sa.Column('nupay_subscription_id', sa.String(100), nullable=True))
    op.add_column('subscriptions', sa.Column('recurring_status', sa.String(20), default='ACTIVE'))
    op.add_column('subscriptions', sa.Column('next_billing_date', sa.Date(), nullable=True))
    op.add_column('subscriptions', sa.Column('last_billing_date', sa.Date(), nullable=True))

    # Payment - NuPay fields
    op.add_column('payments', sa.Column('nupay_reference_id', sa.String(100), nullable=True))
    op.add_column('payments', sa.Column('nupay_psp_reference_id', sa.String(100), nullable=True))
    op.add_column('payments', sa.Column('nupay_payment_url', sa.String(500), nullable=True))
    op.add_column('payments', sa.Column('nupay_qr_code', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('nupay_pix_copy_paste', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('payment_method', sa.String(20), default='manual'))


def downgrade():
    op.drop_column('users', 'cpf')
    op.drop_column('packages', 'is_recurring')
    op.drop_column('packages', 'recurring_interval_days')
    op.drop_column('packages', 'welcome_xp_bonus')
    op.drop_column('subscriptions', 'is_recurring')
    op.drop_column('subscriptions', 'nupay_subscription_id')
    op.drop_column('subscriptions', 'recurring_status')
    op.drop_column('subscriptions', 'next_billing_date')
    op.drop_column('subscriptions', 'last_billing_date')
    op.drop_column('payments', 'nupay_reference_id')
    op.drop_column('payments', 'nupay_psp_reference_id')
    op.drop_column('payments', 'nupay_payment_url')
    op.drop_column('payments', 'nupay_qr_code')
    op.drop_column('payments', 'nupay_pix_copy_paste')
    op.drop_column('payments', 'payment_method')
```

---

## 7. Arquitetura Proposta

### 7.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Landing Page   │  │   Shop/Checkout │  │  Student Portal │             │
│  │  (marketing/)   │  │   (shop/)       │  │  (student/)     │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
└───────────┼────────────────────┼────────────────────┼───────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (Flask)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ROUTES (Blueprints)                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │   │
│  │  │marketing│ │  shop   │ │ student │ │  admin  │ │  webhooks   │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           SERVICES                                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │   │
│  │  │ NuPay   │ │ MegaAPI │ │ Payment │ │   XP    │ │ Achievement │   │   │
│  │  │ Service │ │ Service │ │Processor│ │ Manager │ │   Checker   │   │   │
│  │  └────┬────┘ └────┬────┘ └─────────┘ └─────────┘ └─────────────┘   │   │
│  └───────┼───────────┼─────────────────────────────────────────────────┘   │
│          │           │                                                      │
└──────────┼───────────┼──────────────────────────────────────────────────────┘
           │           │
           ▼           ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│     NuPay API    │  │   MegaAPI        │  │   PostgreSQL     │
│  (Pagamentos)    │  │   (WhatsApp)     │  │   (Database)     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### 7.2 Fluxo de Dados - Checkout Completo

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO DE CHECKOUT PIX                                  │
└──────────────────────────────────────────────────────────────────────────────┘

[1] SELEÇÃO DO PACOTE
    User → GET /shop/package/5 → Renderiza detalhes do pacote

[2] INÍCIO DO CHECKOUT
    User → POST /shop/checkout/5
    │
    ├── Valida: User tem CPF? Se não, solicita
    ├── Cria: Subscription (status=PENDING)
    ├── Cria: Payment (status=PENDING)
    └── Retorna: Formulário de pagamento

[3] GERAR PIX
    User → POST /shop/generate-pix/payment_id
    │
    ├── Backend → NuPayService.create_pix_payment()
    │             │
    │             └── POST api.spinpay.com.br/v1/checkouts/payments
    │                 │
    │                 └── Returns: pspReferenceId, qrCode, pixCopyPaste
    │
    ├── Atualiza: Payment com dados NuPay
    └── Retorna: Página com QR Code e timer

[4] PAGAMENTO
    User → Escaneia QR ou abre app Nubank → Paga

[5] WEBHOOK CONFIRMAÇÃO
    NuPay → POST /webhooks/nupay/callback
    │
    ├── Valida: Assinatura HMAC
    ├── Busca: Payment pelo merchantReferenceId
    ├── Atualiza: Payment.status = PAID
    ├── Atualiza: Subscription.status = ACTIVE
    ├── Aplica: XP Bonus (se configurado)
    ├── Notifica: WhatsApp via MegaAPI
    └── Retorna: 200 OK

[6] POLLING/REDIRECT
    Frontend polling cada 5s → GET /shop/payment-status/payment_id
    │
    ├── Se PAID: Redirect → /shop/checkout/success
    └── Se PENDING: Continua aguardando

[7] SUCESSO
    User → Vê página de sucesso com créditos liberados
```

### 7.3 Estrutura de Arquivos (Novos/Modificados)

```
app/
├── models/
│   ├── user.py              [MODIFICAR] Adicionar campo CPF
│   ├── package.py           [MODIFICAR] Adicionar is_recurring, welcome_xp_bonus
│   ├── subscription.py      [MODIFICAR] Adicionar campos recorrência
│   └── payment.py           [MODIFICAR] Adicionar campos NuPay
│
├── routes/
│   ├── marketing.py         [NOVO] Landing page pública
│   ├── shop.py              [MODIFICAR] Integrar NuPay checkout
│   └── webhooks.py          [MODIFICAR] Adicionar endpoint NuPay
│
├── services/
│   └── nupay.py             [NOVO] Cliente API NuPay
│
├── templates/
│   ├── marketing/
│   │   └── index.html       [NOVO] Landing page
│   ├── shop/
│   │   ├── checkout.html    [MODIFICAR] Novo fluxo PIX
│   │   ├── pix_payment.html [NOVO] Tela aguardando pagamento
│   │   └── success.html     [NOVO] Confirmação
│   └── components/
│       └── simulator.html   [NOVO] Componente simulador
│
└── static/
    └── js/
        └── simulator.js     [NOVO] Lógica do simulador
```

---

## 8. Plano de Implementação

### 8.1 Fases do Projeto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 1: FUNDAÇÃO (Semana 1-2)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Criar migration para novos campos (CPF, NuPay fields)                    │
│  □ Implementar validação de CPF no modelo User                              │
│  □ Criar NuPayService básico (create_pix_payment, get_status)               │
│  □ Configurar variáveis de ambiente NuPay                                   │
│  □ Criar endpoint webhook básico                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 2: CHECKOUT PIX (Semana 3-4)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Refatorar rota /shop/checkout para integrar NuPay                        │
│  □ Criar template pix_payment.html com QR Code                              │
│  □ Implementar polling de status                                            │
│  □ Implementar webhook completo com notificação WhatsApp                    │
│  □ Criar página de sucesso                                                  │
│  □ Testes end-to-end com sandbox NuPay                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 3: LANDING PAGE (Semana 5-6)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Criar blueprint marketing                                                │
│  □ Desenvolver template landing page (hero, planos, modalidades)            │
│  □ Implementar simulador de créditos (JS interativo)                        │
│  □ Adicionar social proof (Hall da Fama anônimo)                            │
│  □ Otimizar para mobile                                                     │
│  □ SEO básico (meta tags, structured data)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 4: RECORRÊNCIA (Semana 7-8)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Implementar create_recurring_subscription no NuPayService                │
│  □ Adicionar campos recorrência no formulário de pacotes                    │
│  □ Fluxo de autorização CIBA                                                │
│  □ Webhook para renovação automática                                        │
│  □ Interface para cancelamento de recorrência                               │
│  □ Testes com ciclos de cobrança                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 5: GAMIFICAÇÃO E POLISH (Semana 9-10)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  □ Implementar XP de boas-vindas por pacote                                 │
│  □ Integrar gamificação na landing page                                     │
│  □ Ajustes de UX baseados em feedback                                       │
│  □ Otimização de performance                                                │
│  □ Documentação final                                                       │
│  □ Deploy em produção                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Checklist de Tarefas Detalhado

#### Fase 1: Fundação

- [ ] **Database Changes**
  - [ ] Criar arquivo de migration
  - [ ] Adicionar `cpf` ao modelo User
  - [ ] Adicionar campos NuPay ao modelo Payment
  - [ ] Adicionar campos recorrência ao Subscription
  - [ ] Adicionar campos gamificação ao Package
  - [ ] Executar migration em desenvolvimento

- [ ] **Validação CPF**
  - [ ] Implementar algoritmo de validação de CPF
  - [ ] Adicionar método `validate_cpf()` no User model
  - [ ] Criar formatação automática (123.456.789-00)

- [ ] **NuPayService Básico**
  - [ ] Criar `app/services/nupay.py`
  - [ ] Implementar `__init__` com headers
  - [ ] Implementar `create_pix_payment()`
  - [ ] Implementar `get_payment_status()`
  - [ ] Adicionar tratamento de erros

- [ ] **Configuração**
  - [ ] Adicionar variáveis ao `config.py`
  - [ ] Atualizar `.env.example`
  - [ ] Documentar processo de obtenção de credenciais

#### Fase 2: Checkout PIX

- [ ] **Rotas Shop**
  - [ ] Refatorar `checkout()` para suportar NuPay
  - [ ] Criar rota `generate_pix()`
  - [ ] Criar rota `payment_status()` para polling
  - [ ] Criar rota `checkout_success()`
  - [ ] Criar rota `checkout_cancel()`

- [ ] **Templates**
  - [ ] Atualizar `checkout.html` com opções de pagamento
  - [ ] Criar `pix_payment.html` com QR Code
  - [ ] Criar `success.html`
  - [ ] Adicionar JavaScript para polling

- [ ] **Webhook**
  - [ ] Criar rota `POST /webhooks/nupay/callback`
  - [ ] Implementar validação HMAC
  - [ ] Processar status COMPLETED
  - [ ] Processar status FAILED
  - [ ] Integrar notificação WhatsApp

- [ ] **Testes**
  - [ ] Configurar sandbox NuPay
  - [ ] Testar fluxo completo PIX
  - [ ] Testar webhook com ngrok
  - [ ] Testar cenários de erro

#### Fase 3: Landing Page

- [ ] **Blueprint Marketing**
  - [ ] Criar `app/routes/marketing.py`
  - [ ] Registrar blueprint no `__init__.py`
  - [ ] Configurar rota `/` para landing
  - [ ] Manter redirecionamento para login em `/login`

- [ ] **Template Landing**
  - [ ] Criar estrutura base `marketing/index.html`
  - [ ] Desenvolver Hero Section
  - [ ] Desenvolver seção de modalidades
  - [ ] Desenvolver seção de planos/pacotes
  - [ ] Adicionar footer com links

- [ ] **Simulador de Créditos**
  - [ ] Criar componente HTML
  - [ ] Desenvolver `static/js/simulator.js`
  - [ ] Implementar sliders por modalidade
  - [ ] Calcular créditos necessários
  - [ ] Sugerir pacote ideal

- [ ] **Social Proof**
  - [ ] Criar query para ranking anônimo
  - [ ] Implementar anonimização de nomes
  - [ ] Adicionar seção Hall da Fama
  - [ ] Mostrar estatísticas agregadas

#### Fase 4: Recorrência

- [ ] **NuPayService Recorrência**
  - [ ] Implementar `create_recurring_subscription()`
  - [ ] Implementar `cancel_subscription()`
  - [ ] Implementar `pause_subscription()`

- [ ] **Admin**
  - [ ] Adicionar campos no form de pacotes
  - [ ] Validar intervalo de recorrência
  - [ ] Preview de como aparece para cliente

- [ ] **Student Portal**
  - [ ] Mostrar status de recorrência
  - [ ] Botão para cancelar recorrência
  - [ ] Histórico de cobranças

- [ ] **Webhooks Recorrência**
  - [ ] Processar evento de renovação
  - [ ] Criar novo Payment automaticamente
  - [ ] Renovar créditos na Subscription
  - [ ] Notificar via WhatsApp

#### Fase 5: Gamificação e Polish

- [ ] **XP de Boas-vindas**
  - [ ] Aplicar bônus no webhook de pagamento
  - [ ] Mostrar na página de sucesso
  - [ ] Registrar achievement se aplicável

- [ ] **UX Improvements**
  - [ ] Loading states
  - [ ] Error messages amigáveis
  - [ ] Animações sutis
  - [ ] Feedback visual de ações

- [ ] **Performance**
  - [ ] Lazy loading de imagens
  - [ ] Minificação de assets
  - [ ] Cache de queries frequentes

- [ ] **Deploy**
  - [ ] Configurar variáveis produção
  - [ ] Registrar webhook URL na NuPay
  - [ ] Teste de smoke em produção
  - [ ] Monitoramento de erros

---

## 9. Riscos e Mitigações

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|---------------|---------|-----------|
| 1 | **Credenciais NuPay demoram** | Média | Alto | Iniciar processo de cadastro NuPay Business imediatamente. Desenvolver com sandbox. |
| 2 | **Webhook não recebe callbacks** | Média | Alto | Usar ngrok para testes locais. Implementar retry manual. Log detalhado de tentativas. |
| 3 | **Usuários antigos sem CPF** | Alta | Médio | Modal obrigatório no primeiro checkout. Campanha de atualização de cadastro. |
| 4 | **Conversão landing page baixa** | Média | Médio | A/B testing do hero. Heatmaps. Iteração baseada em dados. |
| 5 | **Falha na recorrência CIBA** | Baixa | Alto | Fallback para PIX manual. Notificação proativa de falha. Retry automático. |
| 6 | **Fraude em pagamentos** | Baixa | Alto | Validação de CPF. Limites por usuário. Monitoramento de padrões. |
| 7 | **Indisponibilidade NuPay** | Baixa | Alto | Circuit breaker. Fallback para modo manual temporário. Alertas de falha. |

---

## 10. Critérios de Aceite

### 10.1 Landing Page

- [ ] Página carrega em menos de 3 segundos (mobile 4G)
- [ ] Responsiva em todas as resoluções (320px - 1920px)
- [ ] Hero section exibe proposta de valor clara
- [ ] Seção de planos mostra todos os pacotes ativos
- [ ] Simulador calcula créditos corretamente
- [ ] CTA principal leva ao checkout
- [ ] Social proof exibe ranking anônimo

### 10.2 Checkout PIX

- [ ] Usuário consegue completar checkout sem ter conta prévia
- [ ] CPF é validado antes de gerar PIX
- [ ] QR Code é exibido corretamente
- [ ] PIX Copia e Cola funciona
- [ ] Deep link abre app Nubank (mobile)
- [ ] Polling atualiza status a cada 5 segundos
- [ ] Pagamento confirmado em menos de 10 segundos após PIX
- [ ] Créditos são liberados instantaneamente
- [ ] WhatsApp de confirmação é enviado
- [ ] Página de sucesso mostra resumo correto

### 10.3 Webhook

- [ ] Endpoint responde em menos de 500ms
- [ ] Assinatura HMAC é validada
- [ ] Pagamentos duplicados são ignorados (idempotência)
- [ ] Falhas são logadas para debug
- [ ] Retry não causa duplicação de créditos

### 10.4 Recorrência

- [ ] Admin consegue criar pacote recorrente
- [ ] Cliente consegue autorizar recorrência
- [ ] Cobrança automática funciona no vencimento
- [ ] Cliente consegue cancelar recorrência
- [ ] Créditos são renovados automaticamente
- [ ] WhatsApp de renovação é enviado

### 10.5 Admin

- [ ] Novo campo "Tipo de Cobrança" no form de pacotes
- [ ] Campo "Bônus XP de Boas-vindas" funciona
- [ ] Dashboard mostra métricas de conversão NuPay
- [ ] Relatório de pagamentos inclui método (manual vs NuPay)

---

## Anexos

### A. Referências da API NuPay

- **Documentação:** OpenAPI spec fornecido (`openapi.json`)
- **Base URL Produção:** `https://api.spinpay.com.br`
- **Autenticação:** Headers `X-Merchant-Key` e `X-Merchant-Token`

### B. Templates WhatsApp Necessários

| Código | Trigger | Conteúdo |
|--------|---------|----------|
| `payment_confirmed` | Webhook COMPLETED | "Olá {nome}! Seu pagamento foi confirmado. Você tem {creditos} créditos disponíveis até {validade}." |
| `payment_failed` | Webhook FAILED | "Olá {nome}, houve um problema com seu pagamento. Por favor, tente novamente." |
| `subscription_renewed` | Webhook recorrência | "Olá {nome}! Sua assinatura foi renovada. +{creditos} créditos adicionados!" |
| `subscription_cancelled` | Cancelamento | "Olá {nome}, sua recorrência foi cancelada. Você ainda pode usar seus {creditos} créditos restantes." |

### C. Paleta de Cores Sugerida (Landing Page)

```css
:root {
  /* Cores principais */
  --primary-dark: #1a1a2e;      /* Fundo principal */
  --primary-accent: #FF6B35;    /* CTAs e destaques */
  --primary-light: #f8f9fa;     /* Texto sobre escuro */

  /* Cores secundárias */
  --secondary-dark: #16213e;    /* Cards */
  --secondary-accent: #0f3460;  /* Hover states */

  /* Feedback */
  --success: #10b981;           /* Sucesso */
  --warning: #f59e0b;           /* Alerta */
  --error: #ef4444;             /* Erro */
}
```

---

**Fim do Documento**

*Última atualização: 23 de Janeiro de 2026*
