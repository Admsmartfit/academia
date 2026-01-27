# Prompts para Antigravity - Implementacao Landing Page FES

**Referencia:** PRD_Landing_Page_FES.md
**Total de Etapas:** 5 Fases
**Estimativa:** 5 semanas de implementacao

---

## FASE 1: FUNDACAO (Backend e Dados)

### Prompt 1.1 - Criar Modalidade FES no Banco

```
No projeto Flask em c:\Users\ralan\academia, preciso adicionar uma nova modalidade de treino.

Contexto:
- O modelo Modality ja existe em app/models/modality.py
- Existe um arquivo scripts/seed_data.py com dados iniciais

Tarefas:
1. Verifique a estrutura do modelo Modality
2. Atualize o seed_data.py adicionando a modalidade FES com estes dados:
   - name: "Eletroestimulacao FES"
   - description: "Treino hibrido com corrente FES para hipertrofia maxima e recrutamento de fibras tipo II. Sessoes de 20 minutos equivalentes a 1h30 de treino convencional."
   - color: "#FF6B35"
   - icon_url: "⚡"
   - credits_cost: 30 (se o campo existir)
   - is_featured: True (adicionar campo se nao existir)

3. Se o modelo nao tiver o campo "is_featured", adicione-o como Boolean default False
4. Crie uma migration se necessario
```

### Prompt 1.2 - Criar Pacotes Hibridos FES

```
No projeto Flask em c:\Users\ralan\academia, preciso criar novos pacotes de assinatura focados em FES.

Contexto:
- O modelo Package existe em app/models/package.py
- Seed data fica em scripts/seed_data.py

Tarefas:
1. Adicione os seguintes pacotes ao seed_data.py:

Pacote 1 - FES-Hyper Solo:
- name: "FES-Hyper Solo"
- description: "Ativacao profunda localizada com tecnologia FES."
- credits: 60
- price: 397.00
- validity_days: 30
- color: "#FF6B35"
- is_featured: False
- welcome_xp_bonus: 50

Pacote 2 - Performance Hibrida (MAIS VENDIDO):
- name: "Performance Hibrida"
- description: "O melhor dos dois mundos: Peso Livre + FES."
- credits: 120
- price: 697.00
- validity_days: 30
- color: "#FFD700"
- is_featured: True
- welcome_xp_bonus: 150
- badge: "MAIS VENDIDO"

Pacote 3 - Bio-Boost VIP:
- name: "Bio-Boost VIP"
- description: "Sessoes ilimitadas com foco em pontos fracos."
- credits: 200
- price: 997.00
- validity_days: 30
- color: "#E5E5E5"
- is_featured: False
- welcome_xp_bonus: 300

2. Se o modelo Package nao tiver campo "badge", adicione-o como String nullable
3. Garanta que o campo extra_benefits seja JSON/Text para armazenar lista de beneficios
```

### Prompt 1.3 - Parametro Trial no Registro

```
No projeto Flask, preciso que a rota de registro aceite um parametro "trial" para rastrear usuarios vindos da landing page FES.

Arquivo: app/routes/auth.py

Tarefas:
1. Modifique a rota GET /register para capturar o parametro ?trial=fes
2. Passe para o template: trial_type e show_fes_banner
3. Se trial_type == 'fes', mostrar banner especial no topo do formulario

Codigo base:
@auth_bp.route('/register')
def register():
    trial_type = request.args.get('trial')
    return render_template('auth/register.html',
        trial_type=trial_type,
        show_fes_banner=(trial_type == 'fes')
    )

4. No template register.html, adicione um banner condicional:
{% if show_fes_banner %}
<div class="alert alert-warning text-center">
    <strong>⚡ Sessao Experimental FES Reservada!</strong><br>
    Complete seu cadastro para confirmar sua sessao gratuita.
</div>
{% endif %}
```

---

## FASE 2: HERO + CIENCIA (Frontend Principal)

### Prompt 2.1 - Redesenhar Hero Section

```
No projeto Flask, preciso redesenhar a Hero Section da landing page focando em FES.

Arquivo: app/templates/marketing/index.html

Especificacoes do Hero:
- Titulo: "O FUTURO DA HIPERTROFIA CHEGOU"
- Subtitulo: "Tecnologia FES: Recrute 90% mais fibras musculares em treinos de apenas 20 minutos"
- CTA Primario: "Agendar Sessao Experimental" -> link para /register?trial=fes
- CTA Secundario: "Conhecer Planos" -> ancora #planos
- Trust Badges: "500+ alunos ativos" | "4.9/5 avaliacao"

CSS do Hero:
- Background com overlay gradient: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.6))
- Altura minima: 100vh
- Centralizado verticalmente
- Mobile-first responsivo

Adicione estas variaveis CSS:
:root {
    --fes-glow: rgba(255, 107, 53, 0.6);
    --fes-pulse: rgba(255, 107, 53, 0.3);
    --gradient-tech: linear-gradient(135deg, #ff6b35 0%, #ff8c5a 100%);
}

Botao primario deve ter animacao pulse:
@keyframes fes-pulse {
    0%, 100% { box-shadow: 0 0 0 0 var(--fes-pulse); }
    50% { box-shadow: 0 0 20px 10px var(--fes-glow); }
}
```

### Prompt 2.2 - Criar Secao Problema/Solucao

```
No arquivo app/templates/marketing/index.html, adicione uma nova secao logo apos o Hero.

Secao: PROBLEMA/SOLUCAO
Objetivo: Criar conexao emocional identificando a dor do cliente

Estrutura HTML:
- Titulo: "POR QUE SEUS TREINOS NAO ESTAO FUNCIONANDO"
- 3 cards com icones (FontAwesome):
  1. fa-clock - "Falta de Tempo" - "Horas na academia, resultados minimos"
  2. fa-dumbbell - "Plato de Resultados" - "Seu corpo se adaptou e parou de evoluir"
  3. fa-brain - "Fibras Dormentes" - "95% usam apenas 30% do potencial muscular"
- Texto destaque: "Seu corpo tem fibras musculares que NUNCA foram ativadas por treinos convencionais"
- CTA: "DESCOBRIR A SOLUCAO" -> ancora para proxima secao

Design:
- Background: #0f172a (escuro)
- Cards com borda sutil e hover effect
- Icones em cor laranja (#ff6b35)
- Responsivo: 3 colunas desktop, 1 coluna mobile
```

### Prompt 2.3 - Criar Secao Ciencia FES

```
No arquivo app/templates/marketing/index.html, crie a secao principal sobre FES.

Secao: CIENCIA FES
Objetivo: Estabelecer autoridade cientifica de forma visual

Estrutura:
1. Titulo: "A CIENCIA POR TRAS DO SHAPE PERFEITO"

2. Comparativo visual (2 cards lado a lado):
   Card 1 - Treino Comum:
   - Titulo: "TREINO COMUM"
   - "30% de ativacao muscular"
   - "Apenas fibras Tipo I"
   - Visual: cor cinza, opaco

   Card 2 - Treino FES:
   - Titulo: "TREINO COM FES"
   - "90% de ativacao muscular"
   - "Fibras Tipo I + II"
   - Visual: cor laranja, animacao pulse

3. Bloco "COMO FUNCIONA" com 4 passos:
   1. "Impulsos eletricos controlados"
   2. "Bypassa limitacao do sistema nervoso"
   3. "Ativa fibras profundas Tipo II"
   4. "Contracao tetanica = hipertrofia maxima"

4. Badges de credibilidade:
   - "Aprovado ANVISA"
   - "Usado em Fisioterapia de Elite"

5. Infografico: "20 min FES = 1h30 Musculacao"

CSS:
- Animacao SVG ou CSS para simular ativacao muscular
- Cards FES com borda brilhante e sombra laranja
```

### Prompt 2.4 - Criar Secao Comparativo

```
No arquivo app/templates/marketing/index.html, adicione tabela comparativa.

Secao: COMPARATIVO
Objetivo: Facilitar decisao com comparacao direta

Tabela com 2 colunas:
| Aspecto              | TREINO COMUM | TREINO FES |
|----------------------|--------------|------------|
| Tempo por sessao     | 1h30         | 20 min     |
| Ativacao muscular    | 30%          | 90%        |
| Resultados visiveis  | 12 semanas   | 4 semanas  |
| Risco de lesao       | Medio        | Minimo     |
| Recrutamento Tipo II | Parcial      | Total      |

Design:
- Coluna "Treino Comum": cinza, opaco
- Coluna "Treino FES": laranja, destacado, badge "RECOMENDADO"
- Linhas alternadas com cores sutis
- CTA ao final: "QUERO EXPERIMENTAR FES" -> /register?trial=fes
- Responsivo: tabela horizontal scroll em mobile OU cards empilhados
```

---

## FASE 3: CONVERSAO (Simulador e Planos)

### Prompt 3.1 - Atualizar Simulador com FES

```
No projeto Flask, atualize o Simulador de Creditos para incluir FES.

Arquivo: app/templates/marketing/index.html (secao simulador existente)

Modificacoes:
1. Adicionar slider para "Eletroestimulacao FES" com custo 30 creditos/sessao

2. Quando FES for adicionado, exibir mensagem especial:
   "Com FES, voce alcanca seu objetivo X meses mais rapido comparado ao treino tradicional"

3. Calcular e exibir: "Tempo economizado por semana: X horas"
   Formula: (sessoes_FES * 70min) / 60 = horas economizadas
   (Cada sessao FES de 20min substitui 1h30 = 70min de economia)

4. No resultado, destacar pacotes que incluem FES:
   - Badge "INCLUI FES" nos pacotes Performance Hibrida e Bio-Boost VIP

5. JavaScript: Atualizar calculos dinamicamente quando usuario interage
```

### Prompt 3.2 - Redesenhar Cards de Planos

```
No arquivo app/templates/marketing/index.html, redesenhe a secao de planos.

Secao: PLANOS (id="planos" para ancora)

4 Cards de Planos:

1. Starter (basico):
   - 30 creditos | R$ 197/mes
   - "1 sessao FES inclusa"
   - Cor: cinza

2. FES-Hyper Solo:
   - 60 creditos | R$ 397/mes
   - "2 sessoes FES/mes"
   - Cor: laranja (#FF6B35)

3. Performance Hibrida (DESTAQUE):
   - 120 creditos | R$ 697/mes
   - Badge: "MAIS VENDIDO"
   - Beneficios: "4 sessoes FES/mes", "Musculacao ilimitada", "Avaliacao mensal", "+150 XP boas-vindas"
   - Texto: "O melhor dos dois mundos: Peso Livre + FES"
   - Nota: "12% de economia vs avulso"
   - Cor: dourado (#FFD700)
   - Borda destacada, tamanho maior

4. Bio-Boost VIP (premium):
   - 200 creditos | R$ 997/mes
   - "FES ilimitado", "Personal 2x/semana"
   - Cor: prata/branco

Design:
- Card destaque (Performance Hibrida) 10% maior
- Hover: elevacao e sombra
- CTA em cada card: "ASSINAR AGORA" -> /shop/checkout/{package_id}
```

---

## FASE 4: PROVA SOCIAL (Depoimentos e FAQ)

### Prompt 4.1 - Secao Depoimentos FES

```
No arquivo app/templates/marketing/index.html, crie secao de depoimentos.

Secao: DEPOIMENTOS
Objetivo: Prova social com foco em resultados FES

Carrossel com 3 depoimentos:

1. Executivo:
   - Nome: "Carlos M., 42 anos"
   - Profissao: "Diretor de Vendas"
   - Foto: placeholder avatar
   - Depoimento: "Com 20 minutos por sessao, finalmente consigo manter a rotina. Perdi 8kg e ganhei definicao em 2 meses."
   - Resultado: "+8kg massa magra | -12% gordura"

2. Atleta:
   - Nome: "Fernanda L., 28 anos"
   - Profissao: "Triatleta Amadora"
   - Depoimento: "Sai do plato apos 3 anos. O FES ativou musculos que eu nem sabia que existiam. Meu tempo de prova melhorou 15%."
   - Resultado: "Plato quebrado | -15% tempo de prova"

3. Reabilitacao:
   - Nome: "Roberto S., 55 anos"
   - Profissao: "Empresario"
   - Depoimento: "Recuperei a forca da perna operada em metade do tempo previsto pelo medico. Tecnologia impressionante."
   - Resultado: "Recuperacao 2x mais rapida"

Design:
- Cards com foto circular, quote em italico
- Icones de estrelas (5/5)
- Autoplay com pause no hover
- Indicadores de navegacao (dots)
- Responsivo: 1 card por vez em mobile
```

### Prompt 4.2 - Secao FAQ sobre FES

```
No arquivo app/templates/marketing/index.html, crie FAQ sobre FES.

Secao: FAQ
Objetivo: Eliminar objecoes e duvidas

5 Perguntas em accordion (Bootstrap collapse):

1. "O FES doi?"
   Resposta: "Nao. A sensacao e de um formigamento leve seguido de contracao muscular involuntaria. A intensidade e ajustada ao seu conforto e aumenta gradualmente conforme voce se adapta."

2. "E seguro?"
   Resposta: "Sim. A tecnologia FES e aprovada pela ANVISA e usada ha decadas em hospitais para reabilitacao. Nossos equipamentos sao certificados e as sessoes sao supervisionadas por profissionais treinados."

3. "Substitui a musculacao tradicional?"
   Resposta: "Complementa. O FES potencializa seus treinos ativando fibras que exercicios convencionais nao alcancam. O ideal e o treino hibrido, combinando peso livre com sessoes de eletroestimulacao."

4. "Quanto tempo para ver resultados?"
   Resposta: "Mudancas visiveis aparecem entre 4-6 semanas com treinos regulares (2-3x por semana). Muitos alunos relatam melhora na forca e postura ja nas primeiras sessoes."

5. "Quem NAO pode fazer FES?"
   Resposta: "Existem contraindicacoes especificas: portadores de marca-passo, gestantes, pessoas com epilepsia nao controlada ou implantes metalicos na regiao tratada. Sempre consulte seu medico antes."

Design:
- Accordion com animacao suave
- Icone + e - para expandir/recolher
- Cores: titulo laranja, texto branco
- CTA ao final: "Ainda tem duvidas? Fale conosco" -> WhatsApp
```

### Prompt 4.3 - CTA Final Otimizado

```
No arquivo app/templates/marketing/index.html, crie CTA final antes do footer.

Secao: CTA FINAL
Objetivo: Ultima chance de conversao

Estrutura:
- Background: gradient laranja escuro
- Titulo: "PRONTO PARA EXPERIMENTAR O FUTURO?"
- Subtitulo: "Agende sua Sessao de Ativacao FES - 100% GRATUITA"
- CTA Grande: "AGENDAR MINHA SESSAO GRATUITA" -> /register?trial=fes

Trust elements (3 icones):
- fa-calendar-check: "Avaliacao corporal inclusa"
- fa-user-md: "Sessao supervisionada por especialista"
- fa-credit-card: "Sem cartao de credito necessario"

Extras:
- Contador fake de urgencia (opcional): "Restam X vagas esta semana"
- Animacao de pulse no botao CTA
- Garantia: "Sem compromisso. Cancele quando quiser."
```

---

## FASE 5: OTIMIZACAO (Performance e Analytics)

### Prompt 5.1 - Otimizacao de Performance

```
No projeto Flask, otimize a landing page para performance.

Arquivo principal: app/templates/marketing/index.html

Tarefas:

1. Lazy Loading de Imagens:
   - Adicione loading="lazy" em todas as tags <img> abaixo da dobra
   - Use placeholder blur enquanto carrega

2. Critical CSS:
   - Identifique CSS critico (above the fold)
   - Mova para tag <style> inline no <head>
   - Carregue resto do CSS com rel="preload"

3. Otimizacao de Scripts:
   - Adicione defer em scripts nao-criticos
   - Mova JavaScript para final do body
   - Minifique inline scripts

4. Fontes:
   - Adicione preconnect para Google Fonts:
   <link rel="preconnect" href="https://fonts.googleapis.com">
   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

5. Imagens:
   - Converta para WebP com fallback JPG usando <picture>
   - Defina width e height explicitos para evitar CLS

6. Verifique:
   - LCP < 2.5s
   - FID < 100ms
   - CLS < 0.1
```

### Prompt 5.2 - Implementar Analytics/Tracking

```
No projeto Flask, adicione tracking para medir conversao da landing page.

Tarefas:

1. Eventos de Clique (Google Analytics / Plausible):
   - Clique em "Agendar Sessao Experimental" (hero)
   - Clique em "Conhecer Planos" (hero)
   - Clique em qualquer CTA de plano
   - Clique em "Agendar Sessao Gratuita" (CTA final)
   - Interacao com simulador

2. Scroll Tracking:
   - Rastrear quando usuario passa 25%, 50%, 75%, 100% da pagina

3. Tempo na Pagina:
   - Rastrear tempo medio de permanencia

4. Criar dashboard ou endpoints para visualizar:
   - Taxa de conversao (registros / visitantes)
   - Plano mais clicado
   - Secao com maior abandono

5. Adicionar UTM support:
   - Capturar utm_source, utm_medium, utm_campaign da URL
   - Armazenar no registro do usuario para atribuicao
```

### Prompt 5.3 - Preparar Testes A/B

```
No projeto Flask, prepare infraestrutura para testes A/B.

Arquivo: app/routes/marketing.py

Tarefas:

1. Criar sistema simples de variantes:
   - Cookie ou session para manter usuario na mesma variante
   - 50/50 split entre variante A e B

2. Primeiro teste: CTA do Hero
   - Variante A: "Agendar Sessao Experimental"
   - Variante B: "Quero Minha Sessao Gratuita"

3. Passar variante para template:
   @marketing_bp.route('/')
   def index():
       variant = get_ab_variant(request, 'hero_cta')
       return render_template('marketing/index.html', ab_variant=variant)

4. No template, usar condicional:
   {% if ab_variant == 'A' %}
   Agendar Sessao Experimental
   {% else %}
   Quero Minha Sessao Gratuita
   {% endif %}

5. Logar qual variante converteu (no registro)
```

---

## Checklist de Validacao Final

Apos implementar todas as fases, valide:

### Backend
- [ ] Modalidade FES criada no banco
- [ ] 3 novos pacotes FES criados
- [ ] Parametro ?trial=fes funcionando no registro
- [ ] Migrations aplicadas sem erro

### Frontend
- [ ] Hero responsivo e animado
- [ ] Secao Problema/Solucao renderizando
- [ ] Secao Ciencia FES com comparativo visual
- [ ] Tabela comparativa legivel em mobile
- [ ] Simulador calculando FES corretamente
- [ ] Cards de planos com destaque no "Performance Hibrida"
- [ ] Depoimentos em carrossel funcionando
- [ ] FAQ accordion expandindo/recolhendo
- [ ] CTA final com botao pulsante

### Performance
- [ ] Lighthouse Mobile Score > 90
- [ ] LCP < 2.5s
- [ ] Sem erros no console do browser

### Conversao
- [ ] Todos os CTAs linkando corretamente
- [ ] Tracking de eventos funcionando
- [ ] UTMs sendo capturados

---

## Ordem de Execucao Recomendada

1. **Prompt 1.1** -> Depois **1.2** -> Depois **1.3** (dependencias de banco)
2. **Prompt 2.1** (Hero precisa existir primeiro)
3. **Prompts 2.2, 2.3, 2.4** (podem ser paralelos)
4. **Prompts 3.1, 3.2** (simulador e planos sao independentes)
5. **Prompts 4.1, 4.2, 4.3** (podem ser paralelos)
6. **Prompts 5.1, 5.2, 5.3** (otimizacao final)

---

*Documento gerado para uso com Antigravity AI*
*Referencia: docs/PRD_Landing_Page_FES.md*
