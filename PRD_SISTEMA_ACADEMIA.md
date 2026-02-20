Com base na análise do código atual e nas dores identificadas, estruturei um plano de melhorias focado em **atrito zero** e uma interface moderna (Mobile-First).

Abaixo, apresento o **PRD (Documento de Requisitos do Produto)** seguido das sugestões visuais e lógicas para a atualização.

---

# 📄 PRD: Atualização do Sistema de Agendamento Inteligente (v2.0)

## 1. Visão Geral

Simplificar o fluxo de agendamento para alunos e a gestão de aula para instrutores, removendo cliques desnecessários e automatizando validações.

## 2. Problemas Identificados

* **Alunos:** Necessidade de selecionar assinatura manualmente a cada aula, validações de saúde (PAR-Q/EMS) ocorrem apenas no final do fluxo causando frustração, e recarregamento constante de página.
* **Instrutores:** Fluxo manual de "No-show" e preenchimento repetitivo de logs de EMS/Eletrolipólise.

## 3. Requisitos Funcionais (Melhorias Lógicas)

### 3.1. Agendamento em "Um Clique" (Smart Booking)

* **Seleção Automática:** Se o aluno tiver apenas uma assinatura ativa, o sistema deve selecioná-la automaticamente.
* **Reserva via AJAX:** O botão "Agendar" deve processar a reserva em segundo plano, alterando o estado do botão para "Agendado" sem recarregar a grade.
* **Validação Antecipada:** A grade de horários deve "desabilitar" ou sinalizar visualmente horários que o aluno não pode frequentar (ex: restrição de gênero ou falta de créditos) antes de ele clicar.

### 3.2. Dashboard do Instrutor "Mãos Livres"

* **Presença Automática:** Integrar o status de Reconhecimento Facial diretamente na lista de alunos do instrutor.
* **Log EMS Inteligente:** O sistema deve sugerir os valores de intensidade e frequência baseados na última sessão realizada pelo aluno.
* **Checklist pelo Aluno:** O checklist de hidratação/jejum deve ser enviado via Push/WhatsApp para o aluno 1 hora antes; o instrutor apenas vê o "check" verde no painel.

## 4. Requisitos de Interface (Visual)

### 4.1. Nova Grade de Horários (Aluno)

* **Visual de "Cards":** Substituir a tabela por cards empilhados no mobile com ícones grandes para modalidades.
* **Cores de Status:** * **Verde:** Disponível e compatível.
* **Amarelo:** Requer ação (ex: assinar PAR-Q).
* **Cinza:** Bloqueado (Gênero oposto ou sem créditos).


* **Navegação por Datas:** Barra horizontal de datas (scroll lateral) em vez de botões de "Semana Anterior/Próxima".

### 4.2. Dashboard "Live" (Instrutor)

* **Modo Fila:** Alunos organizados por ordem de chegada/reconhecimento facial.
* **Quick Actions:** Botões de ação rápida (Faltou/Log EMS) visíveis apenas ao expandir o nome do aluno para limpar o visual.

---

# 🎨 Proposta de Melhoria Visual e Implementação

### Sugestão para o `student/schedule.html`:

Em vez de uma tabela rígida, o uso de cards dinâmicos melhora a experiência mobile:

```html
<div class="class-card {% if not schedule.ems_ok or schedule.gender_restricted %}disabled-style{% endif %}">
    <div class="d-flex justify-content-between">
        <div>
            <span class="time">{{ schedule.start_time.strftime('%H:%M') }}</span>
            <h5 class="modality">{{ schedule.modality.name }}</h5>
            <small class="instructor">{{ schedule.instructor.name }}</small>
        </div>
        <div class="action-zone">
            {% if schedule.user_booked %}
                <button class="btn btn-success" disabled>✓ Agendado</button>
            {% else %}
                <button class="btn btn-primary btn-book-ajax" data-id="{{schedule.id}}">
                    Agendar (1cr)
                </button>
            {% endif %}
        </div>
    </div>
    {% if not parq_ok %}
        <div class="alert-mini">⚠️ Atualize seu PAR-Q para liberar esta aula.</div>
    {% endif %}
</div>

```

### Sugestão para o `instructor/dashboard.html`:

O instrutor ganha agilidade com indicadores visuais de quem já está na unidade:

* **Indicador de Presença:** Um anel luminoso ao redor do avatar do aluno.
* **Azul:** Agendado (esperado).
* **Verde Pulsante:** Reconhecido pela face no totem/entrada.
* **Vermelho:** Faltando (após 10min de aula).



### Benefícios Esperados:

1. **Redução de suporte:** Alunos entenderão por que não podem agendar antes de tentar.
2. **Agilidade:** O instrutor foca no treino e não em preencher formulários de Log.
3. **Conversão:** O fluxo de agendamento em um clique aumenta a ocupação das aulas.