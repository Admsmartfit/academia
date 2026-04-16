Compreendo perfeitamente. O problema de contraste ocorreu porque a nova variável Ciano Elétrico (`#00f2ff`) que aplicámos na identidade visual foi herdada por elementos de texto da tabela (como as horas). Como a tabela tem um fundo branco (padrão do Bootstrap no Admin), o texto ciano tornou-se ilegível.

Além disso, a adição de um botão de **Aprovação em Massa** é essencial para a eficiência do gestor, permitindo validar múltiplos horários sugeridos pelos professores de uma só vez.

Abaixo, apresento o **PRD de Correção UI/UX e Nova Funcionalidade**, acompanhado do código completo.

---

# PRD: Correção de Contraste e Aprovação em Massa

**Versão:** 2.3 (UI Fix & Admin Efficiency)
**Módulo:** Gestão de Horários (Admin)
**Arquivos Afetados:** `app/routes/admin/schedules.py` e `app/templates/admin/schedules/list.html`

## 1. Melhoria de Contraste (UI)
* **Problema:** Texto das horas em azul claro sobre fundo branco é ilegível.
* **Solução:** Transformar as horas numa *badge* (etiqueta) escura e sólida (`bg-dark` com texto `white`). Isso não apenas resolve o problema de acessibilidade instantaneamente, como confere um visual mais estruturado à tabela de horários.

## 2. Nova Ação em Massa: "Aprovar Selecionados"
* **Backend:** Criação de um novo endpoint (`/api/availability/bulk-approve`) para alterar o status `is_approved = True` em lote.
* **Frontend:** Adição de um botão verde ("Aprovar") ao lado do botão vermelho ("Eliminar") que aparece apenas quando há 1 ou mais itens selecionados.

---

## Passo 1: Atualização do Backend (`schedules.py`)

Adicione a nova rota `api_bulk_approve` no final do arquivo `app/routes/admin/schedules.py`. Certifique-se de manter a rota de `api_bulk_delete` que criámos anteriormente.

```python
# app/routes/admin/schedules.py (Adicionar no final do arquivo)

@schedules_bp.route('/api/availability/bulk-approve', methods=['POST'])
@login_required
@admin_required
def api_bulk_approve():
    """Endpoint para aprovação em massa via AJAX"""
    data = request.get_json()
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({'success': False, 'message': 'Nenhum ID fornecido'}), 400

    try:
        # Busca as grades selecionadas e atualiza o status de aprovação
        schedules = ClassSchedule.query.filter(ClassSchedule.id.in_(ids)).all()
        
        for s in schedules:
            s.is_approved = True
            
        db.session.commit()
        return jsonify({'success': True, 'message': f'{len(ids)} horários aprovados com sucesso.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
```

---

## Passo 2: Atualização do Frontend (`list.html`)

Substitua completamente o código do arquivo `app/templates/admin/schedules/list.html`. 
*Neste arquivo, fixei as horas dentro de `badges` de alto contraste e implementei os dois botões e as respetivas lógicas de comunicação em massa.*

```html
{% extends "admin/base.html" %}

{% block title %}Gestão de Horários | Biohacking Studio{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="mb-0 fw-bold">Gestão de Horários</h2>
            <p class="text-muted">Agrupamento inteligente por dia da semana.</p>
        </div>
        <div>
            <button id="btnBulkApprove" class="btn btn-outline-success d-none me-2" onclick="handleBulkApprove()">
                <i class="fas fa-check me-2"></i>Aprovar (<span id="countApprove">0</span>)
            </button>
            <button id="btnBulkDelete" class="btn btn-outline-danger d-none me-2" onclick="handleBulkDelete()">
                <i class="fas fa-trash me-2"></i>Eliminar (<span id="countSelected">0</span>)
            </button>
            
            <a href="{{ url_for('admin_schedules.create') }}" class="btn btn-primary text-dark fw-bold">
                <i class="fas fa-plus me-2"></i>Novo Horário
            </a>
        </div>
    </div>

    <div class="card mb-4 border-0 shadow-sm">
        <div class="card-body p-2">
            <div class="input-group">
                <span class="input-group-text bg-transparent border-0"><i class="fas fa-search text-muted"></i></span>
                <input type="text" id="scheduleSearch" class="form-control border-0" placeholder="Filtrar por modalidade, professor ou status..." onkeyup="filterSchedules()">
            </div>
        </div>
    </div>

    {% set weekdays = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'] %}
    {% set grouped = schedules | groupby('weekday') %}

    <div class="accordion" id="accordionSchedules">
        {% for weekday_idx, day_items in grouped %}
        <div class="accordion-item mb-3 border-0 shadow-sm rounded">
            <h2 class="accordion-header">
                <button class="accordion-button bg-white text-dark fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#day-{{ weekday_idx }}">
                    <i class="fas fa-calendar-day me-2 text-primary"></i> {{ weekdays[weekday_idx] }}
                    <span class="badge bg-light text-dark border ms-3">{{ day_items | length }} slots</span>
                </button>
            </h2>
            <div id="day-{{ weekday_idx }}" class="accordion-collapse collapse show">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th style="width: 50px;" class="text-center">
                                    <input type="checkbox" class="form-check-input" onchange="toggleDaySelection('{{ weekday_idx }}', this)">
                                </th>
                                <th>Horário</th>
                                <th>Modalidade</th>
                                <th>Instrutor</th>
                                <th>Status</th>
                                <th class="text-end">Ações</th>
                            </tr>
                        </thead>
                        <tbody class="day-group-{{ weekday_idx }}">
                            {% for schedule in day_items %}
                            <tr class="schedule-row" data-searchable="{{ schedule.modality.name }} {{ schedule.instructor.name }}">
                                <td class="text-center">
                                    <input type="checkbox" class="form-check-input row-checkbox" value="{{ schedule.id }}" onchange="updateBulkUI()">
                                </td>
                                <td><span class="badge bg-dark text-white px-3 py-2 fs-6">{{ schedule.start_time.strftime('%H:%M') }}</span></td>
                                <td class="text-dark fw-medium">{{ schedule.modality.name }}</td>
                                <td class="text-secondary">{{ schedule.instructor.name }}</td>
                                <td>
                                    {% if schedule.is_approved %}
                                    <span class="badge bg-success-subtle text-success">Aprovado</span>
                                    {% else %}
                                    <span class="badge bg-warning-subtle text-warning">Pendente</span>
                                    {% endif %}
                                </td>
                                <td class="text-end">
                                    {% if not schedule.is_approved %}
                                    <form action="{{ url_for('admin_schedules.approve_schedule', id=schedule.id) }}" method="POST" class="d-inline">
                                        <button class="btn btn-sm btn-link text-success text-decoration-none"><i class="fas fa-check"></i> Aprovar</button>
                                    </form>
                                    {% endif %}
                                    <form action="{{ url_for('admin_schedules.reject_schedule', id=schedule.id) }}" method="POST" class="d-inline" onsubmit="return confirm('Eliminar este horário permanentemente?');">
                                        <button class="btn btn-sm btn-link text-danger text-decoration-none"><i class="fas fa-times"></i> Rejeitar</button>
                                    </form>
                                    <a href="{{ url_for('admin_schedules.edit', id=schedule.id) }}" class="btn btn-sm btn-light"><i class="fas fa-edit"></i></a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<script>
    // 1. Busca Dinâmica
    function filterSchedules() {
        let input = document.getElementById('scheduleSearch').value.toLowerCase();
        let rows = document.querySelectorAll('.schedule-row');
        rows.forEach(row => {
            let text = row.getAttribute('data-searchable').toLowerCase();
            row.style.display = text.includes(input) ? '' : 'none';
        });
    }

    // 2. Seleção por Dia
    function toggleDaySelection(dayIdx, master) {
        let checkboxes = document.querySelectorAll('.day-group-' + dayIdx + ' .row-checkbox');
        checkboxes.forEach(cb => cb.checked = master.checked);
        updateBulkUI();
    }

    // 3. Interface de Ações em Massa (Mostra botões de Excluir e Aprovar)
    function updateBulkUI() {
        let selected = document.querySelectorAll('.row-checkbox:checked');
        let btnDelete = document.getElementById('btnBulkDelete');
        let btnApprove = document.getElementById('btnBulkApprove');
        
        document.getElementById('countSelected').innerText = selected.length;
        document.getElementById('countApprove').innerText = selected.length;
        
        if(selected.length > 0) {
            btnDelete.classList.remove('d-none');
            btnApprove.classList.remove('d-none');
        } else {
            btnDelete.classList.add('d-none');
            btnApprove.classList.add('d-none');
        }
    }

    // 4. Lógica de Eliminação (AJAX)
    async function handleBulkDelete() {
        let ids = Array.from(document.querySelectorAll('.row-checkbox:checked')).map(cb => cb.value);
        if(!confirm(`Deseja eliminar permanentemente ${ids.length} horários?`)) return;

        try {
            // Utilizando o Jinja url_for para garantir a rota correta do blueprint
            const response = await fetch('{{ url_for("admin_schedules.api_bulk_delete") }}', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ids: ids})
            });
            const result = await response.json();
            if(result.success) location.reload();
            else alert("Erro: " + result.message);
        } catch (e) {
            alert("Erro na comunicação com o servidor.");
        }
    }

    // 5. Lógica de Aprovação em Massa (AJAX)
    async function handleBulkApprove() {
        let ids = Array.from(document.querySelectorAll('.row-checkbox:checked')).map(cb => cb.value);
        if(!confirm(`Deseja aprovar ${ids.length} horários selecionados?`)) return;

        try {
            const response = await fetch('{{ url_for("admin_schedules.api_bulk_approve") }}', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ids: ids})
            });
            const result = await response.json();
            if(result.success) location.reload();
            else alert("Erro: " + result.message);
        } catch (e) {
            alert("Erro na comunicação com o servidor.");
        }
    }
</script>
{% endblock %}
```

Com estas alterações:
1. O horário passará a estar encapsulado num quadrado preto com letras brancas (`<span class="badge bg-dark text-white...">`), tornando a identificação imediata e perfeitamente legível.
2. O botão de "Aprovar" verde aparecerá ao lado do "Eliminar" e processará a aprovação múltipla de uma só vez, enviando os dados de forma limpa para a API que acabou de adicionar.