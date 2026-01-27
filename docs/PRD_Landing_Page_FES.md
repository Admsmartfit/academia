# PRD: Landing Page - Centro de Biohacking & Alta Performance

**Versao:** 2.0
**Status:** Aprovado para Implementacao
**Data:** Janeiro 2026
**Foco Principal:** Conversao para Planos de Eletroestimulacao (FES/EMS)

---

## 1. Visao Geral

### 1.1 Objetivo
Transformar a landing page publica em uma vitrine de **Biohacking e Alta Performance**, posicionando a academia como referencia em tecnologia de eletroestimulacao FES. O objetivo e aumentar conversoes atraves de:

- Diferenciacao tecnologica clara
- Autoridade cientifica acessivel
- Urgencia baseada em eficiencia de tempo
- Jornada de conversao otimizada

### 1.2 Publico-Alvo
| Segmento | Dor Principal | Gatilho de Conversao |
|----------|---------------|----------------------|
| Executivos 30-50 | | "40 min = 1h30 de treino" |
| Atletas amadores | Platô de resultados | "Recrute fibras que voce nunca ativou" |
| Pos-fisioterapia | Recuperacao muscular | "Tecnologia de reabilitacao de elite" |
| Estetica/Wellness | Tonificacao rapida | "Resultados visiveis em 4 semanas" |

---

## 2. Estrutura da Landing Page

### 2.1 Arquitetura de Secoes

```
[NAVBAR] - Fixo, transparente -> solido ao scroll
    |
[HERO] - Video/Imagem FES + CTA Principal
    |
[SOCIAL PROOF] - Logos de parceiros/certificacoes
    |
[PROBLEMA/SOLUCAO] - "Por que treinos comuns falham"
    |
[CIENCIA FES] - Explicacao visual da tecnologia
    |
[COMPARATIVO] - FES vs Treino Tradicional
    |
[MODALIDADES] - Grid de todas as modalidades (FES destacado)
    |
[SIMULADOR] - Calculadora de creditos interativa
    |
[PLANOS] - Cards de pacotes (hibridos FES)
    |
[DEPOIMENTOS] - Casos de sucesso reais
    |
[RANKING] - Hall da Fama (gamificacao)
    |
[FAQ] - Perguntas frequentes sobre FES
    |
[CTA FINAL] - Sessao experimental gratuita
    |
[FOOTER]
```

---

## 3. Especificacoes por Secao

### 3.1 HERO Section

**Objetivo:** Capturar atencao em 3 segundos e comunicar proposta de valor unica.

```
Layout:
+--------------------------------------------------+
|  [VIDEO/IMAGEM BACKGROUND - Atleta com FES]      |
|                                                  |
|  "O FUTURO DA HIPERTROFIA CHEGOU"               |
|  ________________________________________        |
|  | Tecnologia FES: Recrute 90% Mais      |      |
|  | Fibras em Treinos de Apenas 20 Min    |      |
|  |_______________________________________|      |
|                                                  |
|  [AGENDAR SESSAO EXPERIMENTAL]  [CONHECER PLANOS]|
|                                                  |
|  * 500+ alunos ativos  * 4.9/5 avaliacao        |
+--------------------------------------------------+
```

**Elementos:**
- **Titulo Principal:** "O Futuro da Hipertrofia Chegou"
- **Subtitulo:** "Tecnologia FES: Recrute 90% mais fibras musculares em treinos de apenas 20 minutos. A ciencia da fisioterapia de elite aplicada ao seu ganho de massa."
- **CTA Primario:** "Agendar Sessao Experimental" -> `/register?trial=fes`
- **CTA Secundario:** "Conhecer Planos" -> `#planos`
- **Trust Badges:** Numero de alunos, avaliacao media, certificacoes

**Especificacoes Tecnicas:**
- Video WebM/MP4 com autoplay muted loop (fallback para imagem)
- Overlay gradient: `linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.6))`
- Mobile: Video substitui por imagem estatica para performance

---

### 3.2 Secao PROBLEMA/SOLUCAO (NOVA)

**Objetivo:** Criar conexao emocional identificando a dor do cliente.

```
Layout:
+--------------------------------------------------+
|  "POR QUE SEUS TREINOS NAO ESTAO FUNCIONANDO"   |
|                                                  |
|  [Icon Clock]     [Icon Muscle]    [Icon Brain] |
|  Falta de         Plato de         Fibras       |
|  Tempo            Resultados       Dormentes    |
|                                                  |
|  "Seu corpo tem fibras musculares que NUNCA     |
|   foram ativadas por treinos convencionais"     |
|                                                  |
|  [DESCOBRIR A SOLUCAO ->]                       |
+--------------------------------------------------+
```

**Copy:**
- "Voce treina, se esforça, mas os resultados pararam?"
- "O problema nao e dedicacao - e ATIVACAO."
- "95% das pessoas usam apenas 30% do potencial muscular"

---

### 3.3 Secao CIENCIA FES (NOVA - Principal)

**Objetivo:** Estabelecer autoridade cientifica de forma visual e acessivel.

```
Layout:
+--------------------------------------------------+
|  "A CIENCIA POR TRAS DO SHAPE PERFEITO"         |
|                                                  |
|  +-------------------+  +-------------------+    |
|  | TREINO COMUM      |  | TREINO COM FES    |    |
|  |                   |  |                   |    |
|  | [Animacao fibras] |  | [Animacao fibras] |    |
|  | 30% ativacao      |  | 90% ativacao      |    |
|  | Fibras Tipo I     |  | Fibras Tipo I+II  |    |
|  +-------------------+  +-------------------+    |
|                                                  |
|  COMO FUNCIONA:                                  |
|  1. Impulsos eletricos controlados              |
|  2. Bypassa limitacao do sistema nervoso        |
|  3. Ativa fibras profundas Tipo II              |
|  4. Contracao tetanica = hipertrofia maxima     |
|                                                  |
|  [Certificacao ANVISA] [Usado em Fisioterapia]  |
+--------------------------------------------------+
```

**Elementos Visuais:**
- Animacao SVG comparando ativacao muscular
- Icones com microinteracoes (hover pulse)
- Badges de certificacao e seguranca
- Infografico: "20 min FES = 1h30 Musculacao"

**Copy Tecnico (Simplificado):**
- "O FES (Functional Electrical Stimulation) envia impulsos eletricos que 'enganam' seu sistema nervoso"
- "Resultado: fibras musculares profundas que voce NUNCA conseguiria ativar sozinho"
- "Mesma tecnologia usada na reabilitacao de atletas olimpicos"

---

### 3.4 Secao COMPARATIVO (NOVA)

**Objetivo:** Facilitar decisao com comparacao direta.

```
+--------------------------------------------------+
|           TREINO COMUM    vs    TREINO FES      |
+--------------------------------------------------+
| Tempo por sessao    1h30              20 min    |
| Ativacao muscular   30%               90%       |
| Resultados visiveis 12 semanas        4 semanas |
| Risco de lesao      Medio             Minimo    |
| Recrutamento Tipo II Parcial          Total     |
+--------------------------------------------------+
|                                                  |
|  [QUERO EXPERIMENTAR FES]                       |
+--------------------------------------------------+
```

---

### 3.5 Secao MODALIDADES (Atualizada)

**Objetivo:** Mostrar variedade com destaque para FES.

**Grid Layout:**
- Card FES: 2x maior, com animacao de pulso eletrico
- Badge "TECNOLOGIA EXCLUSIVA" no card FES
- Ordenacao: FES primeiro, depois por popularidade

**Dados da Modalidade FES:**
```python
{
    "name": "Eletroestimulacao FES",
    "description": "Treino hibrido com corrente FES para hipertrofia maxima e recrutamento de fibras tipo II. Sessoes de 20 minutos com resultados equivalentes a 1h30 de treino convencional.",
    "color": "#FF6B35",
    "icon": "⚡",
    "credits_cost": 30,
    "is_featured": True,
    "badge": "TECNOLOGIA EXCLUSIVA"
}
```

---

### 3.6 Secao SIMULADOR (Atualizada)

**Objetivo:** Engajar usuario e mostrar economia com FES.

**Melhorias:**
1. Incluir slider para "Eletroestimulacao FES"
2. Ao adicionar FES, mostrar mensagem:
   > "Com FES, voce alcanca seu objetivo **X meses mais rapido** comparado ao treino tradicional"
3. Calcular e exibir: "Tempo economizado por semana: X horas"
4. Destacar pacotes que incluem FES no resultado

---

### 3.7 Secao PLANOS (Atualizada)

**Objetivo:** Conversao direta com opcoes claras.

**Novos Planos Sugeridos:**

| Plano | Creditos | Preco | Destaque | Inclui FES |
|-------|----------|-------|----------|------------|
| Starter | 30 | R$ 197 | - | 1 sessao FES |
| FES-Hyper Solo | 60 | R$ 397 | - | 2 sessoes FES |
| Performance Hibrida | 120 | R$ 697 | MAIS VENDIDO | 4 sessoes FES + Livre |
| Bio-Boost VIP | 200 | R$ 997 | PREMIUM | FES ilimitado |

**Card Destaque (Performance Hibrida):**
```
+----------------------------------+
|  [MAIS VENDIDO]                  |
|  PERFORMANCE HIBRIDA             |
|  ________________________________|
|  R$ 697 /mes                     |
|  ________________________________|
|  * 120 creditos                  |
|  * 4 sessoes FES inclusas        |
|  * Acesso livre musculacao       |
|  * Avaliacao corporal mensal     |
|  * +150 XP de boas-vindas        |
|  ________________________________|
|  "O melhor dos dois mundos:      |
|   Peso Livre + FES"              |
|  ________________________________|
|  [ASSINAR AGORA]                 |
|  ________________________________|
|  12% de economia vs avulso       |
+----------------------------------+
```

---

### 3.8 Secao DEPOIMENTOS (Atualizada)

**Objetivo:** Prova social com foco em resultados FES.

**Formato:**
- Carrossel com fotos antes/depois (com permissao)
- Video testimonials curtos (15-30s)
- Metricas concretas: "Ganhei 4kg de massa em 6 semanas"

**Depoimentos Sugeridos (Templates):**
1. **Executivo:** "Com 20 minutos por sessao, finalmente consigo manter a rotina"
2. **Atleta:** "Sai do plato apos 3 anos. O FES ativou musculos que eu nem sabia que existiam"
3. **Pos-Lesao:** "Recuperei a forca da perna operada em metade do tempo previsto"

---

### 3.9 Secao FAQ (NOVA)

**Objetivo:** Eliminar objecoes e duvidas sobre FES.

**Perguntas Essenciais:**
1. "O FES doi?" -> Nao, a sensacao e de formigamento e contracao involuntaria
2. "E seguro?" -> Sim, aprovado pela ANVISA, usado em hospitais
3. "Substitui a musculacao?" -> Complementa. O ideal e o treino hibrido
4. "Quanto tempo para ver resultados?" -> Mudancas visiveis em 4-6 semanas
5. "Posso fazer se tiver marca-passo?" -> Nao, ha contraindicacoes especificas

---

### 3.10 CTA Final

**Objetivo:** Ultima chance de conversao.

```
+--------------------------------------------------+
|  PRONTO PARA EXPERIMENTAR O FUTURO?             |
|                                                  |
|  Agende sua Sessao de Ativacao FES              |
|  100% GRATUITA - Sem compromisso                |
|                                                  |
|  [AGENDAR MINHA SESSAO GRATUITA]                |
|                                                  |
|  * Avaliacao corporal inclusa                   |
|  * Sessao supervisionada por especialista       |
|  * Sem cartao de credito necessario             |
+--------------------------------------------------+
```

---

## 4. Requisitos Tecnicos

### 4.1 Backend - Seed Data

**Arquivo:** `scripts/seed_data.py`

```python
# Adicionar modalidade FES
{
    "name": "Eletroestimulacao FES",
    "description": "Treino hibrido com corrente FES para hipertrofia maxima e recrutamento de fibras tipo II. Sessoes de 20 minutos equivalentes a 1h30 de treino convencional.",
    "color": "#FF6B35",
    "icon": "⚡",
    "credits_cost": 30,
    "is_featured": True
}

# Novos pacotes hibridos
packages_fes = [
    {
        "name": "FES-Hyper Solo",
        "description": "Ativacao profunda localizada com tecnologia FES.",
        "credits": 60,
        "price": Decimal("397.00"),
        "validity_days": 30,
        "color": "#FF6B35",
        "is_featured": False,
        "welcome_xp_bonus": 50,
        "extra_benefits": ["2 sessoes FES/mes", "Avaliacao inicial"]
    },
    {
        "name": "Performance Hibrida",
        "description": "O melhor dos dois mundos: Peso Livre + FES.",
        "credits": 120,
        "price": Decimal("697.00"),
        "validity_days": 30,
        "color": "#FFD700",
        "is_featured": True,
        "welcome_xp_bonus": 150,
        "extra_benefits": ["4 sessoes FES/mes", "Musculacao ilimitada", "Avaliacao mensal"]
    },
    {
        "name": "Bio-Boost VIP",
        "description": "Sessoes ilimitadas com foco em pontos fracos.",
        "credits": 200,
        "price": Decimal("997.00"),
        "validity_days": 30,
        "color": "#E5E5E5",
        "is_featured": False,
        "welcome_xp_bonus": 300,
        "extra_benefits": ["FES ilimitado", "Personal incluso 2x/semana", "Suplementacao orientada"]
    }
]
```

### 4.2 Frontend - Template Updates

**Arquivo:** `app/templates/marketing/index.html`

**Novas CSS Variables:**
```css
:root {
    /* Existing */
    --bg-dark: #0f172a;
    --bg-card: #1e293b;
    --accent: #ff6b35;

    /* New - FES Theme */
    --fes-glow: rgba(255, 107, 53, 0.6);
    --fes-pulse: rgba(255, 107, 53, 0.3);
    --gradient-tech: linear-gradient(135deg, #ff6b35 0%, #ff8c5a 100%);
}
```

**Animacao Pulse FES:**
```css
@keyframes fes-pulse {
    0%, 100% { box-shadow: 0 0 0 0 var(--fes-pulse); }
    50% { box-shadow: 0 0 20px 10px var(--fes-glow); }
}

.fes-card {
    animation: fes-pulse 2s infinite;
}
```

### 4.3 Parametro Trial

**Rota de Registro:** `app/routes/auth.py`

```python
@auth_bp.route('/register')
def register():
    trial_type = request.args.get('trial')  # 'fes' ou None

    return render_template('auth/register.html',
        trial_type=trial_type,
        show_fes_banner=(trial_type == 'fes')
    )
```

### 4.4 Performance Requirements

| Metrica | Target | Ferramenta |
|---------|--------|------------|
| LCP (Largest Contentful Paint) | < 2.5s | Lighthouse |
| FID (First Input Delay) | < 100ms | Lighthouse |
| CLS (Cumulative Layout Shift) | < 0.1 | Lighthouse |
| Mobile Score | > 90 | PageSpeed Insights |

**Otimizacoes Obrigatorias:**
- [ ] Lazy loading em imagens abaixo da dobra
- [ ] WebP com fallback JPG
- [ ] Critical CSS inline no `<head>`
- [ ] Defer em scripts nao-criticos
- [ ] Preconnect para Google Fonts

---

## 5. Metricas de Sucesso

### 5.1 KPIs Primarios

| Metrica | Baseline | Meta 30 dias | Meta 90 dias |
|---------|----------|--------------|--------------|
| Taxa de Conversao (Registro) | 2% | 4% | 6% |
| Cliques em "Sessao Experimental" | - | 100/sem | 300/sem |
| Tempo na Pagina | 45s | 90s | 120s |
| Scroll Depth > 75% | 20% | 40% | 50% |

### 5.2 KPIs Secundarios

- Bounce Rate: < 50%
- Cliques no Simulador: > 30% dos visitantes
- Compartilhamentos Sociais: > 5% dos visitantes
- Plano mais vendido: Performance Hibrida (meta 40% das vendas)

---

## 6. Cronograma de Implementacao

### Fase 1: Fundacao (Semana 1)
- [ ] Criar modalidade FES no banco
- [ ] Criar pacotes hibridos
- [ ] Atualizar seed_data.py

### Fase 2: Hero + Ciencia (Semana 2)
- [ ] Redesenhar Hero Section
- [ ] Criar secao "Ciencia FES"
- [ ] Implementar animacoes

### Fase 3: Conversao (Semana 3)
- [ ] Atualizar Simulador com FES
- [ ] Redesenhar cards de Planos
- [ ] Criar secao Comparativo

### Fase 4: Prova Social (Semana 4)
- [ ] Secao Depoimentos com foco FES
- [ ] FAQ sobre eletroestimulacao
- [ ] CTA Final otimizado

### Fase 5: Otimizacao (Semana 5)
- [ ] Testes A/B no CTA principal
- [ ] Otimizacao de performance
- [ ] Ajustes baseados em analytics

---

## 7. Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| FES desconhecido pelo publico | Alta | Medio | Secao educativa robusta |
| Preco alto dos planos FES | Media | Alto | Destacar ROI de tempo |
| Contraindicacoes medicas | Baixa | Alto | FAQ claro + disclaimer |
| Performance mobile ruim | Media | Alto | Mobile-first development |

---

## 8. Aprovacoes

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | - | - | Pendente |
| Tech Lead | - | - | Pendente |
| Design Lead | - | - | Pendente |
| Marketing | - | - | Pendente |

---

## Anexo A: Wireframes de Referencia

*(Adicionar links para Figma/wireframes quando disponiveis)*

## Anexo B: Copy Completo

*(Documento separado com todos os textos finais)*

## Anexo C: Assets Necessarios

- [ ] Video hero (WebM + MP4, 1920x1080, < 5MB)
- [ ] Imagem fallback hero (WebP + JPG, 1920x1080)
- [ ] Icones SVG das modalidades
- [ ] Fotos antes/depois (com permissao)
- [ ] Badges de certificacao (ANVISA, etc)
- [ ] Animacao SVG fibras musculares
