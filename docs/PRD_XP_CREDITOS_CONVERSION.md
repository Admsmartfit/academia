# PRD: Sistema de Conversao XP para Creditos

## Visao Geral

Sistema que permite ao administrador criar regras de conversao de XP (conquistas) em creditos para agendamento de aulas. Os creditos possuem validade configuravel e sao consumidos seguindo a logica FIFO (primeiro a vencer, primeiro a usar).

---

## Problema

Atualmente, o XP acumulado pelos alunos serve apenas para ranking e gamificacao. Nao ha incentivo tangivel para o acumulo de XP alem do status. Precisamos:

1. Dar valor real ao XP acumulado
2. Incentivar engajamento continuo
3. Premiar alunos dedicados com aulas extras
4. Criar ciclo virtuoso de fidelizacao

---

## Regras de Negocio

### 1. Acumulo de XP
- XP e **acumulativo em janela de 3 meses** (rolling window)
- XP mais antigo que 3 meses sai da janela de conversao (mas continua no historico total)
- O **XP total** (historico) continua visivel para manter o ranking do aluno

### 2. Conversao XP → Creditos
- Admin cria regras de conversao (ex: 1000 XP = 10 creditos)
- Aluno solicita conversao manualmente OU sistema converte automaticamente ao atingir meta
- XP usado em conversao e marcado como "convertido" e **nao pode ser usado novamente**
- XP convertido **continua contando para o ranking** (exibicao)

### 3. Creditos Convertidos
- Creditos ganhos por conversao tem **validade configuravel** (ex: 30, 60, 90 dias)
- Validade e definida na regra de conversao pelo admin
- Creditos expirados sao perdidos (com notificacao previa)

### 4. Consumo de Creditos (FIFO)
- Ao agendar aula, sistema debita creditos na ordem:
  1. **Primeiro**: Creditos com menor data de vencimento (proximos a expirar)
  2. **Segundo**: Em caso de empate, creditos mais antigos (FIFO por data de criacao)
- Sistema mostra ao aluno quais creditos serao usados antes de confirmar

### 5. Hierarquia de Creditos
- Creditos **comprados** (pacotes) tem prioridade de uso APOS creditos de conversao
- Logica: usar primeiro os creditos que vao expirar, preservando os comprados

---

## Modelos de Dados

### ConversionRule (Nova Tabela)
```
id: Integer (PK)
name: String(100)              -- "Bronze Reward", "Gold Achievement"
xp_required: Integer           -- XP necessario para conversao
credits_granted: Integer       -- Creditos concedidos
credit_validity_days: Integer  -- Validade dos creditos (dias)
is_active: Boolean             -- Regra ativa/inativa
is_automatic: Boolean          -- Conversao automatica ao atingir?
max_uses_per_user: Integer     -- Limite de usos por usuario (null = ilimitado)
cooldown_days: Integer         -- Dias de espera entre conversoes (null = sem cooldown)
created_at: DateTime
updated_at: DateTime
```

### CreditWallet (Nova Tabela)
```
id: Integer (PK)
user_id: Integer (FK → User)
credits: Integer               -- Quantidade de creditos
source_type: Enum              -- 'purchase', 'conversion', 'bonus', 'refund'
source_id: Integer             -- ID da compra ou conversao
expires_at: DateTime           -- Data de expiracao
created_at: DateTime
used_at: DateTime              -- Quando foi totalmente consumido (null se ainda tem saldo)
```

### XPConversion (Nova Tabela)
```
id: Integer (PK)
user_id: Integer (FK → User)
rule_id: Integer (FK → ConversionRule)
xp_spent: Integer              -- XP gasto nesta conversao
credits_granted: Integer       -- Creditos gerados
wallet_id: Integer (FK → CreditWallet)  -- Wallet criada
converted_at: DateTime
```

### XPLedger (Nova Tabela) - Controle granular de XP
```
id: Integer (PK)
user_id: Integer (FK → User)
xp_amount: Integer             -- Quantidade de XP (positivo)
source_type: String            -- 'class', 'achievement', 'bonus', 'streak'
source_id: Integer             -- ID da aula, conquista, etc
earned_at: DateTime            -- Quando foi ganho
expires_at: DateTime           -- Janela de 3 meses para conversao
converted_amount: Integer      -- Quanto deste XP ja foi convertido (default 0)
```

### Alteracoes em User
```
# Campos calculados (cached, atualizado por triggers)
xp_total: Integer              -- XP total historico (ranking)
xp_available: Integer          -- XP disponivel para conversao (janela 3 meses - convertido)
credits_balance: Integer       -- Total de creditos ativos (sum de wallets nao expiradas)
```

---

## Fluxos de Usuario

### Fluxo 1: Admin Cria Regra de Conversao

```
1. Admin acessa: Configuracoes → Regras de Conversao
2. Clica "Nova Regra"
3. Preenche formulario:
   - Nome: "Recompensa Dedicacao"
   - XP Necessario: 500
   - Creditos: 5
   - Validade: 30 dias
   - Conversao Automatica: Sim
   - Limite por Usuario: 2x/mes
   - Cooldown: 7 dias
4. Salva regra
5. Sistema ativa regra imediatamente
```

### Fluxo 2: Aluno Converte XP (Manual)

```
1. Aluno acessa: Minha Conta → Minhas Conquistas
2. Ve secao "Converter XP em Creditos"
3. Sistema mostra:
   - XP disponivel para conversao: 750 XP
   - Regras disponiveis:
     * [500 XP → 5 creditos] (30 dias validade) ✓ Disponivel
     * [1000 XP → 12 creditos] (60 dias validade) ✗ XP insuficiente
4. Aluno clica "Converter" na regra de 500 XP
5. Confirmacao: "Voce tera 5 creditos validos ate DD/MM/AAAA"
6. Aluno confirma
7. Sistema:
   - Debita 500 XP do saldo disponivel
   - Marca XP usado como "convertido" no ledger
   - Cria CreditWallet com 5 creditos
   - Atualiza cache do usuario
8. Feedback: "Conversao realizada! +5 creditos adicionados"
```

### Fluxo 3: Conversao Automatica

```
1. Aluno completa aula e ganha 100 XP
2. Sistema atualiza XPLedger
3. Trigger verifica regras automaticas ativas
4. Se XP disponivel >= XP de alguma regra automatica:
   - Verifica cooldown (ultima conversao)
   - Verifica limite de usos
   - Se OK: executa conversao automatica
   - Notifica aluno: "Parabens! Seu XP foi convertido em 5 creditos!"
```

### Fluxo 4: Agendamento com FIFO

```
1. Aluno agenda aula de Spinning (custo: 15 creditos)
2. Sistema consulta CreditWallet do usuario, ordenado por:
   - expires_at ASC (primeiro a vencer)
   - created_at ASC (mais antigo em caso de empate)
3. Carteiras do aluno:
   - Wallet A: 10 creditos, expira 10/02 (conversao)
   - Wallet B: 20 creditos, expira 15/02 (compra)
   - Wallet C: 5 creditos, expira 20/02 (conversao)
4. Sistema debita:
   - 10 creditos da Wallet A (zerada, marca used_at)
   - 5 creditos da Wallet B (resta 15)
5. Preview mostrado ao aluno antes de confirmar:
   "Serao usados:
    - 10 creditos (vencem 10/02)
    - 5 creditos (vencem 15/02)
    Total: 15 creditos"
6. Aluno confirma agendamento
```

### Fluxo 5: Visualizacao de XP (Ranking vs Disponivel)

```
Dashboard do Aluno mostra:

┌─────────────────────────────────────────────┐
│  SEU PROGRESSO                              │
├─────────────────────────────────────────────┤
│  XP Total (Ranking): 5.250 XP    Nivel 12   │
│  ████████████████████░░░░  750 XP p/ Lv 13  │
├─────────────────────────────────────────────┤
│  XP Disponivel p/ Conversao: 1.200 XP       │
│  (Acumulado nos ultimos 3 meses)            │
│                                             │
│  [Ver Regras de Conversao]                  │
├─────────────────────────────────────────────┤
│  Creditos Ativos: 25                        │
│  - 10 vencem em 5 dias ⚠️                   │
│  - 15 vencem em 20 dias                     │
└─────────────────────────────────────────────┘
```

---

## Interfaces Admin

### Tela: Lista de Regras de Conversao

```
┌─────────────────────────────────────────────────────────────────┐
│  REGRAS DE CONVERSAO XP → CREDITOS              [+ Nova Regra]  │
├─────────────────────────────────────────────────────────────────┤
│  Nome              │ XP    │ Creditos │ Validade │ Auto │ Status│
├─────────────────────────────────────────────────────────────────┤
│  Bronze Reward     │ 500   │ 5        │ 30 dias  │ Sim  │ ✓     │
│  Silver Reward     │ 1000  │ 12       │ 45 dias  │ Sim  │ ✓     │
│  Gold Reward       │ 2500  │ 35       │ 60 dias  │ Nao  │ ✓     │
│  Promocao Verao    │ 300   │ 5        │ 15 dias  │ Sim  │ ✗     │
├─────────────────────────────────────────────────────────────────┤
│  Estatisticas:                                                  │
│  - 156 conversoes este mes                                      │
│  - 1.872 creditos distribuidos                                  │
│  - Media: 12 creditos/usuario                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Tela: Criar/Editar Regra

```
┌─────────────────────────────────────────────────────────────────┐
│  NOVA REGRA DE CONVERSAO                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Nome da Regra:     [________________________]                  │
│                                                                 │
│  XP Necessario:     [______] XP                                 │
│                                                                 │
│  Creditos:          [______] creditos                           │
│                                                                 │
│  Validade:          [______] dias                               │
│                                                                 │
│  ☑ Conversao Automatica                                         │
│    (Converter automaticamente quando aluno atingir XP)          │
│                                                                 │
│  Limite por Usuario: [______] vezes (vazio = ilimitado)         │
│                                                                 │
│  Cooldown:          [______] dias entre conversoes              │
│                                                                 │
│  ☑ Regra Ativa                                                  │
│                                                                 │
│                              [Cancelar]  [Salvar Regra]         │
└─────────────────────────────────────────────────────────────────┘
```

### Tela: Relatorio de Conversoes

```
┌─────────────────────────────────────────────────────────────────┐
│  RELATORIO DE CONVERSOES                    Periodo: [Este Mes] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Resumo:                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     156      │  │    1.872     │  │    78.000    │          │
│  │  Conversoes  │  │   Creditos   │  │   XP Gasto   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  Por Regra:                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Bronze Reward    ████████████████████  89 (57%)         │   │
│  │ Silver Reward    ████████              42 (27%)         │   │
│  │ Gold Reward      █████                 25 (16%)         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Ultimas Conversoes:                                            │
│  │ Joao S.    │ Bronze │ 500 XP → 5 cred  │ 26/01 14:32 │      │
│  │ Maria L.   │ Silver │ 1000 XP → 12 cred│ 26/01 13:15 │      │
│  │ Carlos M.  │ Gold   │ 2500 XP → 35 cred│ 26/01 10:45 │      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Notificacoes

### Para Alunos

| Evento | Canal | Mensagem |
|--------|-------|----------|
| Conversao automatica | Push/Email | "🎉 Parabens! Seus 500 XP foram convertidos em 5 creditos! Validos ate DD/MM" |
| Creditos proximos a expirar (7 dias) | Push/Email | "⚠️ Voce tem 10 creditos que expiram em 7 dias. Use-os!" |
| Creditos proximos a expirar (1 dia) | Push | "🚨 ULTIMO DIA! 10 creditos expiram amanha!" |
| Creditos expiraram | Email | "Seus 10 creditos expiraram. Continue treinando para ganhar mais!" |
| Nova regra disponivel | Push | "📢 Nova recompensa disponivel! Converta 500 XP em 5 creditos" |
| XP proximo de regra | Push | "🔥 Faltam apenas 100 XP para voce ganhar 5 creditos!" |

### Para Admin

| Evento | Canal | Mensagem |
|--------|-------|----------|
| Muitas conversoes/dia | Email | "📊 Alerta: 50+ conversoes hoje. Verificar sustentabilidade." |
| Regra popular | Dashboard | "A regra 'Bronze' teve 100 usos esta semana" |

---

## API Endpoints

### Regras (Admin)
```
GET    /api/admin/conversion-rules         -- Listar regras
POST   /api/admin/conversion-rules         -- Criar regra
PUT    /api/admin/conversion-rules/:id     -- Atualizar regra
DELETE /api/admin/conversion-rules/:id     -- Desativar regra
GET    /api/admin/conversion-rules/stats   -- Estatisticas
```

### Conversao (Usuario)
```
GET    /api/user/xp/summary                -- XP total, disponivel, historico
GET    /api/user/xp/conversion-options     -- Regras disponiveis para o usuario
POST   /api/user/xp/convert                -- Executar conversao manual
GET    /api/user/xp/conversions            -- Historico de conversoes
```

### Creditos (Usuario)
```
GET    /api/user/credits/balance           -- Saldo total e por wallet
GET    /api/user/credits/wallets           -- Lista de wallets com vencimentos
GET    /api/user/credits/preview/:cost     -- Preview de quais creditos serao usados
```

---

## Fases de Implementacao

### Fase 1: Backend Core
1. Criar modelos: ConversionRule, CreditWallet, XPConversion, XPLedger
2. Migracoes de banco de dados
3. Implementar logica FIFO de consumo de creditos
4. Implementar janela de 3 meses para XP
5. Criar servico de conversao XP → Creditos
6. Atualizar agendamento para usar nova logica de creditos

### Fase 2: Admin Interface
1. CRUD de regras de conversao
2. Dashboard de estatisticas
3. Relatorio de conversoes
4. Configuracao de validade padrao

### Fase 3: Interface do Aluno
1. Tela de XP com distincao total vs disponivel
2. Lista de regras de conversao disponiveis
3. Fluxo de conversao manual
4. Preview de creditos no agendamento
5. Alerta de creditos proximos a expirar

### Fase 4: Automacao e Notificacoes
1. Conversao automatica (trigger)
2. Job de expiracao de creditos
3. Notificacoes push/email
4. Alertas de proximidade de metas

---

## Metricas de Sucesso

| Metrica | Meta | Medicao |
|---------|------|---------|
| Taxa de conversao | 40% dos usuarios elegíveis convertem | Mensal |
| Uso de creditos convertidos | 80% dos creditos usados antes de expirar | Mensal |
| Engajamento pos-conversao | +20% frequencia de treino | Comparativo |
| Retencao | +15% retencao de usuarios ativos | Trimestral |
| NPS | +10 pontos | Pesquisa |

---

## Consideracoes Tecnicas

### Performance
- Indexar `expires_at` em CreditWallet para queries FIFO rapidas
- Cache de `xp_available` e `credits_balance` no User
- Job noturno para recalcular caches e expirar creditos

### Consistencia
- Usar transacoes para conversao (debitar XP + criar wallet atomicamente)
- Lock otimista em wallets durante agendamento
- Auditoria completa de movimentacoes

### Escalabilidade
- XPLedger pode crescer muito - considerar particionamento por data
- Arquivar conversoes antigas (>1 ano)

---

## Glossario

| Termo | Definicao |
|-------|-----------|
| XP Total | Todo XP ganho historicamente (usado para ranking) |
| XP Disponivel | XP dos ultimos 3 meses que ainda nao foi convertido |
| XP Convertido | XP que foi usado em uma conversao (nao pode ser reusado) |
| Janela de 3 meses | Periodo rolling onde XP pode ser convertido |
| FIFO | First In First Out - primeiro a vencer, primeiro a usar |
| Wallet | "Carteira" individual de creditos com data de expiracao |
| Cooldown | Tempo minimo entre conversoes da mesma regra |

---

## Aprovacoes

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | | | Pendente |
| Tech Lead | | | Pendente |
| Financeiro | | | Pendente |

---

*Documento criado em: 26/01/2026*
*Versao: 1.0*
