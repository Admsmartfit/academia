Com base nas suas observações e nas imagens fornecidas, identifiquei perfeitamente os dois pontos de atrito:

1.  **Landing Page (Tela Inicial):** O overflow (tela maior que o monitor) geralmente é causado por margens negativas em elementos `.row` do Bootstrap que não estão contidos em um `.container-fluid` com `overflow-x: hidden`. O contraste ruim (fundo claro com letra branca) dificulta a leitura.
2.  **Gerenciamento de Grades (`/admin/schedules/`):** Uma lista plana de dezenas de horários torna-se insustentável. Precisamos agrupar os horários por **Dia da Semana** (usando *Accordions*), adicionar uma **Barra de Busca Dinâmica** e implementar a **Exclusão em Massa (Bulk Delete)** via checkboxes.

Abaixo está o **PRD Detalhado** com os códigos prontos para o assistente aplicar as melhorias no seu repositório.

---

# PRD: Melhorias de UX/UI - Landing Page e Gerenciamento de Grades

**Versão:** 1.3 (UX e Produtividade Admin)
**Módulos Afetados:** Marketing (Landing Page) e Admin (Schedules)

## Etapa 1: Correção Visual da Tela Inicial (Landing Page)

**Objetivo:** Eliminar a barra de rolagem horizontal (overflow) e melhorar o contraste do texto sobre o fundo azul.

### 1.1. Ajuste no CSS (`app/static/css/landing.css`)
Adicione ou substitua as seguintes regras no arquivo CSS da landing page para travar o eixo horizontal e adicionar uma camada de contraste ao texto.

```css
/* app/static/css/landing.css */

/* 1. Bloqueia a rolagem horizontal que faz a tela parecer maior */
html, body {
    overflow-x: hidden;
    max-width: 100vw;
}

/* 2. Melhora o contraste no bloco principal (Hero Section) */
/* Caso o fundo seja claro, adicionamos um leve sombreamento no texto ou escurecemos o overlay */
.hero-section {
    position: relative;
    /* Se usar imagem de fundo, adicione um overlay mais escuro: */
    /* background: linear-gradient(rgba(0, 50, 100, 0.7), rgba(0, 50, 100, 0.7)), url('../img/hero.png') center/cover; */
}

/* 3. Classe utilitária para garantir legibilidade do texto branco */
.text-contrast {
    color: #ffffff !important;
    text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.6), 0px 0px 10px rgba(0, 0, 0, 0.4);
}

/* 4. Alternativa: Mudar a cor do texto para um azul escuro se o fundo for muito claro */
.bg-light-blue .text-white {
    color: #0d233a !important; /* Azul marinho escuro ao invés de branco */
    text-shadow: none;
}
```
*Nota ao implementador:* Aplique a classe `.text-contrast` nos elementos `<h1>` e `<p>` do *Hero* no arquivo `app/templates/marketing/index.html`.

---

## Etapa 2: Refatoração da Lista de Horários do Admin

**Objetivo:** Transformar a lista plana em "Sanfonas" (Accordions) separadas por dias da semana, adicionar busca em tempo real e checkboxes para exclusão em lote.

### 2.1. Backend: Nova rota para Exclusão em Lote
Precisamos de um endpoint para receber os IDs selecionados e deletá-los de uma só vez.

* **Arquivo alvo:** `app/routes/admin/schedules.py`
* **Ação:** Adicione o seguinte código ao final do arquivo:

```python
# app/routes/admin/schedules.py

from flask import request, jsonify

@admin_schedules_bp.route('/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete():
    """Exclui múltiplos horários simultaneamente."""
    data = request.get_json()
    schedule_ids = data.get('ids', [])
    
    if not schedule_ids:
        return jsonify({'success': False, 'message': 'Nenhum horário selecionado.'}), 400

    try:
        # Busca os horários e os exclui
        # Obs: Se houver restrição de chave estrangeira com Bookings, 
        # pode ser necessário fazer deleção em cascata ou soft delete (is_active = False).
        ClassSchedule.query.filter(ClassSchedule.id.in_(schedule_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{len(schedule_ids)} horários foram excluídos com sucesso.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao excluir: {str(e)}'}), 500
```

### 2.2. Frontend: Novo Template da Lista (`list.html`)
Vamos reescrever a página para usar o componente Accordion do Bootstrap, agrupar via Jinja2 e adicionar a lógica JavaScript.

* **Arquivo alvo:** `app/templates/admin/schedules/list.html`
* **Ação:** Substitua o conteúdo pelo código abaixo:

```html
{% extends "admin/base.html" %}

{% block title %}Gerenciar Grades de Horários{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="mb-0"><i class="fas fa-calendar-alt text-primary me-2"></i>Grades de Horários</h2>
            <p class="text-muted">Gerencie os horários das aulas por dia da semana.</p>
        </div>
        <div>
            <button class="btn btn-outline-danger me-2 d-none" id="btnBulkDelete" onclick="deleteSelected()">
                <i class="fas fa-trash"></i> Excluir Selecionados (<span id="selectedCount">0</span>)
            </button>
            <a href="{{ url_for('admin_schedules.create') }}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Novo Horário
            </a>
        </div>
    </div>

    <div class="card mb-4 shadow-sm border-0">
        <div class="card-body p-3">
            <div class="input-group">
                <span class="input-group-text bg-white"><i class="fas fa-search text-muted"></i></span>
                <input type="text" id="searchInput" class="form-control" placeholder="Buscar por modalidade ou instrutor (Ex: Musculação, Carlos)..." onkeyup="filterSchedules()">
            </div>
        </div>
    </div>

    {% set days = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'] %}
    {% set grouped_schedules = schedules | groupby('weekday') %}

    <div class="accordion shadow-sm" id="schedulesAccordion">
        {% for weekday, day_schedules in grouped_schedules %}
        <div class="accordion-item border-0 border-bottom">
            <h2 class="accordion-header" id="heading{{ weekday }}">
                <button class="accordion-button bg-light fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ weekday }}" aria-expanded="true" aria-controls="collapse{{ weekday }}">
                    <i class="far fa-calendar-day me-2"></i> {{ days[weekday] }} 
                    <span class="badge bg-secondary rounded-pill ms-2">{{ day_schedules|length }} aulas</span>
                </button>
            </h2>
            <div id="collapse{{ weekday }}" class="accordion-collapse collapse show" aria-labelledby="heading{{ weekday }}">
                <div class="accordion-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0 schedule-table">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 40px; padding-left: 20px;">
                                        <input class="form-check-input select-all-day" type="checkbox" data-day="{{ weekday }}" onclick="toggleDay(this)">
                                    </th>
                                    <th>Horário</th>
                                    <th>Modalidade</th>
                                    <th>Instrutor</th>
                                    <th>Capacidade</th>
                                    <th>Status</th>
                                    <th class="text-end pe-4">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for schedule in day_schedules %}
                                <tr class="schedule-row">
                                    <td style="padding-left: 20px;">
                                        <input class="form-check-input schedule-checkbox" type="checkbox" value="{{ schedule.id }}" onchange="updateBulkButton()">
                                    </td>
                                    <td>
                                        <div class="fw-bold text-primary">
                                            <i class="far fa-clock me-1"></i>
                                            {{ schedule.start_time.strftime('%H:%M') }} - {{ schedule.end_time.strftime('%H:%M') }}
                                        </div>
                                    </td>
                                    <td class="search-target fw-semibold">{{ schedule.modality.name }}</td>
                                    <td class="search-target">{{ schedule.instructor.name }}</td>
                                    <td>{{ schedule.capacity }} vagas</td>
                                    <td>
                                        {% if schedule.is_active %}
                                            <span class="badge bg-success">Ativo</span>
                                        {% else %}
                                            <span class="badge bg-danger">Inativo</span>
                                        {% endif %}
                                    </td>
                                    <td class="text-end pe-4">
                                        <a href="{{ url_for('admin_schedules.edit', id=schedule.id) }}" class="btn btn-sm btn-outline-primary" title="Editar">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5 bg-white rounded shadow-sm">
            <i class="fas fa-calendar-times fa-3x text-muted mb-3"></i>
            <h5>Nenhuma grade de horário cadastrada.</h5>
            <p class="text-muted">Clique em "Novo Horário" para começar.</p>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Filtro de Busca em Tempo Real
    function filterSchedules() {
        const input = document.getElementById('searchInput').value.toLowerCase();
        const rows = document.querySelectorAll('.schedule-row');

        rows.forEach(row => {
            const targets = row.querySelectorAll('.search-target');
            let match = false;
            targets.forEach(target => {
                if (target.textContent.toLowerCase().includes(input)) {
                    match = true;
                }
            });
            row.style.display = match ? '' : 'none';
        });
    }

    // Selecionar todos de um dia específico
    function toggleDay(checkbox) {
        const day = checkbox.getAttribute('data-day');
        const collapseDiv = document.getElementById('collapse' + day);
        const childCheckboxes = collapseDiv.querySelectorAll('.schedule-checkbox');
        
        childCheckboxes.forEach(cb => {
            // Ignora os que estão escondidos pela busca
            if(cb.closest('tr').style.display !== 'none') {
                cb.checked = checkbox.checked;
            }
        });
        updateBulkButton();
    }

    // Atualiza visibilidade e contador do botão de Exclusão em Lote
    function updateBulkButton() {
        const selected = document.querySelectorAll('.schedule-checkbox:checked').length;
        const btn = document.getElementById('btnBulkDelete');
        const countSpan = document.getElementById('selectedCount');
        
        countSpan.textContent = selected;
        if (selected > 0) {
            btn.classList.remove('d-none');
        } else {
            btn.classList.add('d-none');
        }
    }

    // Função de Exclusão em Lote (AJAX)
    function deleteSelected() {
        const checkboxes = document.querySelectorAll('.schedule-checkbox:checked');
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));

        if (ids.length === 0) return;

        if (confirm(`Tem certeza que deseja excluir ${ids.length} horário(s) selecionado(s)? Esta ação não pode ser desfeita.`)) {
            
            fetch("{{ url_for('admin_schedules.bulk_delete') }}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ ids: ids })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    location.reload(); // Recarrega para atualizar a interface
                } else {
                    alert("Erro: " + data.message);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert("Ocorreu um erro ao processar a solicitação.");
            });
        }
    }
</script>
{% endblock %}
```

### O que isso resolve:
1. **Sanfonas por Dia:** Em vez de rolar infinitamente, o administrador vê os dias da semana. Ele pode encolher dias que não está trabalhando e focar, por exemplo, só na "Segunda-feira".
2. **Busca Rápida:** O script em JS (sem necessidade de plugins pesados) filtra as linhas da tabela instantaneamente ao digitar o nome do professor ou da aula.
3. **Exclusão Rápida:** O usuário pode clicar no checkbox do cabeçalho da "Segunda-feira" para selecionar todas as aulas da segunda, e clicar em **Excluir Selecionados** no topo da página. Simples e limpo.