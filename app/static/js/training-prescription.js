// training-prescription.js - Instructor training prescription interface

var currentStep = 1;
var sessions = [];
var exercisesLibrary = [];
var selectedStudent = null;
var sessionCounter = 0;

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    loadExercisesLibrary();
    setupAutocomplete();
    setupFilters();
    checkInitialStudent();
    checkInitialTemplate();
    setupTemplateNameListener();
});

function setupTemplateNameListener() {
    var templateNameInput = document.getElementById('templateName');
    if (templateNameInput) {
        templateNameInput.addEventListener('input', function () {
            updatePreview();
        });
    }
}

function checkInitialTemplate() {
    var step1 = document.getElementById('step1');
    if (step1 && step1.dataset.loadTemplate) {
        loadTemplate(parseInt(step1.dataset.loadTemplate));
    }
}

// Check if a student was passed from the backend
function checkInitialStudent() {
    var container = document.getElementById('studentContainer');
    if (container && container.dataset.initialId) {
        selectStudent({
            id: parseInt(container.dataset.initialId),
            name: container.dataset.initialName,
            email: container.dataset.initialEmail
        });
    }
}

// Load exercises library from API
async function loadExercisesLibrary() {
    try {
        var response = await fetch('/api/training/exercises/list');
        exercisesLibrary = await response.json();
        renderExercisesLibrary();
    } catch (err) {
        console.error('Erro ao carregar exercicios:', err);
        document.getElementById('exercises-library').innerHTML =
            '<p class="text-danger">Erro ao carregar exercicios.</p>';
    }
}

// Render exercise library with filters
function renderExercisesLibrary() {
    var container = document.getElementById('exercises-library');
    if (!container) return;

    var muscleFilterEl = document.getElementById('muscleFilter');
    var exerciseSearchEl = document.getElementById('exerciseSearch');

    var muscleFilter = muscleFilterEl ? muscleFilterEl.value : '';
    var searchTerm = (exerciseSearchEl ? exerciseSearchEl.value : '').toLowerCase();

    var filtered = exercisesLibrary.filter(function (ex) {
        var matchMuscle = !muscleFilter || ex.muscle_group === muscleFilter;
        var matchSearch = !searchTerm || ex.name.toLowerCase().indexOf(searchTerm) !== -1;
        return matchMuscle && matchSearch;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">Nenhum exercicio encontrado.</p>';
        return;
    }

    var html = '';
    filtered.forEach(function (exercise) {
        html += '<div class="card mb-2 exercise-library-item" data-exercise-id="' + exercise.id + '" onclick="addExerciseToSession(' + exercise.id + ')">' +
            '<div class="card-body p-2">' +
            '<div class="d-flex justify-content-between align-items-center">' +
            '<div>' +
            '<strong>' + exercise.name + '</strong><br>' +
            '<small class="text-muted">' + (exercise.muscle_group_label || exercise.muscle_group) + '</small>' +
            (exercise.equipment_needed ? ' <small class="text-muted">| ' + exercise.equipment_needed + '</small>' : '') +
            '</div>' +
            '<div>' +
            (exercise.video_url ? '<span class="badge bg-info"><i class="fas fa-video"></i></span> ' : '') +
            '<button class="btn btn-sm btn-primary"><i class="fas fa-plus"></i></button>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
    });

    container.innerHTML = html;
}

// Setup filters
function setupFilters() {
    var muscleFilter = document.getElementById('muscleFilter');
    var exerciseSearch = document.getElementById('exerciseSearch');

    if (muscleFilter) {
        muscleFilter.addEventListener('change', renderExercisesLibrary);
    }

    if (exerciseSearch) {
        var searchTimeout;
        exerciseSearch.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(renderExercisesLibrary, 300);
        });
    }
}

// Student autocomplete
function setupAutocomplete() {
    var searchInput = document.getElementById('studentSearch');
    var timeout;

    searchInput.addEventListener('focus', function () {
        if (this.value.length >= 2) {
            triggerSearch(this.value);
        }
    });

    searchInput.addEventListener('keyup', function () {
        clearTimeout(timeout);
        var query = this.value;

        if (query.length < 2) {
            document.getElementById('studentResults').style.display = 'none';
            document.getElementById('clearStudent').style.display = query.length > 0 ? 'block' : 'none';
            return;
        }

        document.getElementById('clearStudent').style.display = 'block';

        timeout = setTimeout(function () {
            triggerSearch(query);
        }, 300);
    });

    async function triggerSearch(query) {
        try {
            var response = await fetch('/api/training/users/search?q=' + encodeURIComponent(query) + '&role=student');
            var students = await response.json();

            var results = document.getElementById('studentResults');
            results.innerHTML = '';

            if (students.length === 0) {
                results.innerHTML = '<div class="dropdown-item disabled">Nenhum aluno encontrado</div>';
            }

            students.forEach(function (student) {
                var item = document.createElement('a');
                item.className = 'dropdown-item d-flex justify-content-between align-items-center py-2';
                item.href = '#';
                item.innerHTML = '<div>' +
                    '<div class="fw-bold">' + student.name + '</div>' +
                    '<small class="text-muted">' + student.email + '</small>' +
                    '</div>' +
                    '<i class="fas fa-chevron-right text-muted small"></i>';

                item.addEventListener('click', function (e) {
                    e.preventDefault();
                    selectStudent(student);
                });
                results.appendChild(item);
            });

            results.style.display = 'block';
        } catch (err) {
            console.error('Erro ao buscar alunos:', err);
        }
    }

    // Clear button
    document.getElementById('clearStudent').addEventListener('click', function () {
        searchInput.value = '';
        this.style.display = 'none';
        document.getElementById('studentResults').style.display = 'none';
        searchInput.focus();
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function (e) {
        if (!e.target.closest('#studentSearch') && !e.target.closest('#studentResults')) {
            document.getElementById('studentResults').style.display = 'none';
        }
    });
}

function selectStudent(student) {
    selectedStudent = student;
    var searchInput = document.getElementById('studentSearch');
    searchInput.value = student.name;
    searchInput.disabled = true;
    document.getElementById('selectedStudentId').value = student.id;
    document.getElementById('studentResults').style.display = 'none';
    document.getElementById('clearStudent').style.display = 'none';

    var info = document.getElementById('selectedStudentInfo');
    info.style.display = '';
    document.getElementById('studentBadge').textContent = student.name;

    updatePreview();
}

function resetStudent() {
    selectedStudent = null;
    var searchInput = document.getElementById('studentSearch');
    searchInput.value = '';
    searchInput.disabled = false;
    document.getElementById('selectedStudentId').value = '';
    document.getElementById('selectedStudentInfo').style.display = 'none';
    document.getElementById('clearStudent').style.display = 'none';
    searchInput.focus();
    updatePreview();
}

// Step navigation
function goToStep(step) {
    var isTemplateMode = !!document.querySelector('#step1[data-mode="template"]');

    // Validate before advancing
    if (step === 2 && !isTemplateMode && !selectedStudent) {
        showPrescriptionAlert('Selecione um aluno primeiro.', 'warning');
        return;
    }

    // For templates, ensure name is provided before step 2
    if (step === 2 && isTemplateMode) {
        var templateName = document.getElementById('templateName').value;
        if (!templateName) {
            showPrescriptionAlert('Digite o nome do modelo primeiro.', 'warning');
            return;
        }
    }

    if (step === 3 && sessions.length === 0) {
        showPrescriptionAlert('Adicione pelo menos uma sessao de treino.', 'warning');
        return;
    }

    document.querySelectorAll('.prescription-step').forEach(function (el) {
        el.classList.remove('active');
    });
    document.getElementById('step' + step).classList.add('active');

    // Update step indicators
    for (var i = 1; i <= 3; i++) {
        var ind = document.getElementById('stepInd' + i);
        var conn = document.getElementById('conn' + (i - 1));
        ind.classList.remove('active', 'completed');
        if (conn) conn.classList.remove('completed');

        if (i < step) {
            ind.classList.add('completed');
            if (conn) conn.classList.add('completed');
        } else if (i === step) {
            ind.classList.add('active');
        }
    }

    // Update target session dropdown when entering step 3
    if (step === 3) {
        updateTargetSessionDropdown();
    }

    currentStep = step;
}

// Session management
function addSession() {
    sessionCounter++;
    var sessionId = 'session-' + sessionCounter;
    var defaultName = 'Treino ' + String.fromCharCode(64 + sessionCounter);

    sessions.push({
        id: sessionId,
        name: defaultName,
        day_of_week: null,
        exercises: []
    });

    var container = document.getElementById('sessions-container');
    var emptyMsg = document.getElementById('emptySessionsMsg');
    if (emptyMsg) emptyMsg.style.display = 'none';

    var card = document.createElement('div');
    card.className = 'card mb-3 session-card';
    card.setAttribute('data-session-id', sessionId);
    card.innerHTML =
        '<div class="card-header d-flex justify-content-between align-items-center">' +
        '<div class="d-flex gap-2 flex-wrap align-items-center">' +
        '<input type="text" class="form-control form-control-sm bg-transparent text-white border-light" ' +
        'style="width: 200px;" placeholder="Nome da sessao" value="' + defaultName + '" ' +
        'onchange="updateSessionName(\'' + sessionId + '\', this.value)">' +
        '<select class="form-select form-select-sm bg-transparent text-white border-light" style="width: 150px;" ' +
        'onchange="updateSessionDay(\'' + sessionId + '\', this.value)">' +
        '<option value="">Sistema ABC</option>' +
        '<option value="0">Segunda</option>' +
        '<option value="1">Terca</option>' +
        '<option value="2">Quarta</option>' +
        '<option value="3">Quinta</option>' +
        '<option value="4">Sexta</option>' +
        '<option value="5">Sabado</option>' +
        '<option value="6">Domingo</option>' +
        '</select>' +
        '</div>' +
        '<button class="btn btn-sm btn-outline-light" onclick="removeSession(\'' + sessionId + '\')">' +
        '<i class="fas fa-trash"></i>' +
        '</button>' +
        '</div>' +
        '<div class="card-body">' +
        '<div class="exercises-list" id="exercises-' + sessionId + '">' +
        '<p class="text-muted small mb-0">Nenhum exercicio adicionado. Va para o passo 3 para adicionar.</p>' +
        '</div>' +
        '</div>';

    container.appendChild(card);
    updatePreview();
}

function removeSession(sessionId) {
    if (!confirm('Remover esta sessao e todos os seus exercicios?')) return;

    sessions = sessions.filter(function (s) { return s.id !== sessionId; });
    var card = document.querySelector('.session-card[data-session-id="' + sessionId + '"]');
    if (card) card.remove();

    if (sessions.length === 0) {
        var emptyMsg = document.getElementById('emptySessionsMsg');
        if (emptyMsg) emptyMsg.style.display = 'block';
    }

    updatePreview();
}

function updateSessionName(sessionId, name) {
    var session = sessions.find(function (s) { return s.id === sessionId; });
    if (session) session.name = name;
    updatePreview();
}

function updateSessionDay(sessionId, value) {
    var session = sessions.find(function (s) { return s.id === sessionId; });
    if (session) session.day_of_week = value === '' ? null : parseInt(value);
}

// Exercise management
function addExerciseToSession(exerciseId) {
    var targetSelect = document.getElementById('targetSession');
    var targetSessionId = targetSelect.value;

    if (!targetSessionId) {
        showPrescriptionAlert('Selecione uma sessao de destino primeiro.', 'warning');
        return;
    }

    var session = sessions.find(function (s) { return s.id === targetSessionId; });
    if (!session) return;

    var exercise = exercisesLibrary.find(function (ex) { return ex.id === exerciseId; });
    if (!exercise) return;

    // Check duplicate
    var duplicate = session.exercises.find(function (ex) { return ex.exercise_id === exerciseId; });
    if (duplicate) {
        showPrescriptionAlert('Este exercicio ja foi adicionado a esta sessao.', 'warning');
        return;
    }

    var workoutExercise = {
        exercise_id: exerciseId,
        name: exercise.name,
        muscle_group_label: exercise.muscle_group_label,
        sets: 3,
        reps: '10-12',
        rest: 60,
        weight: '',
        notes: ''
    };

    session.exercises.push(workoutExercise);
    renderSessionExercises(targetSessionId);
    renderStep3Exercises();
    updatePreview();
    showPrescriptionAlert(exercise.name + ' adicionado a ' + session.name, 'success');
}

function renderSessionExercises(sessionId) {
    var session = sessions.find(function (s) { return s.id === sessionId; });
    if (!session) return;

    var container = document.getElementById('exercises-' + sessionId);
    if (!container) return;

    if (session.exercises.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">Nenhum exercicio adicionado.</p>';
        return;
    }

    var html = '';
    session.exercises.forEach(function (ex, idx) {
        html += '<div class="exercise-item mb-3 shadow-sm" data-index="' + idx + '">' +
            '<div class="d-flex justify-content-between align-items-center mb-2">' +
            '<div class="d-flex align-items-center gap-2">' +
            '<span class="badge bg-secondary rounded-circle" style="width:24px; height:24px; display:flex; align-items:center; justify-content:center;">' + (idx + 1) + '</span>' +
            '<strong>' + ex.name + '</strong>' +
            '<small class="text-muted">(' + ex.muscle_group_label + ')</small>' +
            '</div>' +
            '<button class="btn btn-sm btn-outline-danger border-0" ' +
            'onclick="removeExerciseFromSession(\'' + sessionId + '\',' + idx + ')">' +
            '<i class="fas fa-trash-alt"></i>' +
            '</button>' +
            '</div>' +
            '<div class="row g-2">' +
            '<div class="col-md-2 col-4">' +
            '<label class="small text-muted mb-0">Series</label>' +
            '<input type="number" class="form-control form-control-sm" value="' + ex.sets + '" min="1" max="20" ' +
            'oninput="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'sets\',this.value)">' +
            '</div>' +
            '<div class="col-md-3 col-8">' +
            '<label class="small text-muted mb-0">Repeticoes</label>' +
            '<input type="text" class="form-control form-control-sm" value="' + ex.reps + '" placeholder="Ex: 10-12 ou Max" ' +
            'oninput="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'reps\',this.value)">' +
            '</div>' +
            '<div class="col-md-2 col-4">' +
            '<label class="small text-muted mb-0">Desc.(s)</label>' +
            '<input type="number" class="form-control form-control-sm" value="' + ex.rest + '" step="10" ' +
            'oninput="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'rest\',this.value)">' +
            '</div>' +
            '<div class="col-md-2 col-8">' +
            '<label class="small text-muted mb-0">Carga/Peso</label>' +
            '<input type="text" class="form-control form-control-sm" value="' + (ex.weight || '') + '" placeholder="Ex: 20kg" ' +
            'oninput="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'weight\',this.value)">' +
            '</div>' +
            '<div class="col-md-3 col-12">' +
            '<label class="small text-muted mb-0">Notas</label>' +
            '<input type="text" class="form-control form-control-sm" value="' + (ex.notes || '') + '" placeholder="Opcional" ' +
            'oninput="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'notes\',this.value)">' +
            '</div>' +
            '</div>' +
            '</div>';
    });

    container.innerHTML = html;
}

function updateExerciseField(sessionId, exerciseIndex, field, value) {
    var session = sessions.find(function (s) { return s.id === sessionId; });
    if (session && session.exercises[exerciseIndex]) {
        session.exercises[exerciseIndex][field] = value;
        updatePreview();
    }
}

function removeExerciseFromSession(sessionId, exerciseIndex) {
    var session = sessions.find(function (s) { return s.id === sessionId; });
    if (session) {
        session.exercises.splice(exerciseIndex, 1);
        renderSessionExercises(sessionId);
        renderStep3Exercises();
        updatePreview();
    }
}

// Render exercises in the Step 3 visible panel
function renderStep3Exercises() {
    var container = document.getElementById('step3-exercises-list');
    if (!container) return;

    var targetSelect = document.getElementById('targetSession');
    var targetSessionId = targetSelect ? targetSelect.value : '';
    var session = sessions.find(function (s) { return s.id === targetSessionId; });

    if (!session || session.exercises.length === 0) {
        container.innerHTML =
            '<div class="text-center py-4 border rounded bg-light" id="step3EmptyMsg">' +
            '<i class="fas fa-arrow-left fa-2x text-muted mb-2 d-block"></i>' +
            '<p class="text-muted mb-0">Selecione exercicios da biblioteca ao lado</p>' +
            '<small class="text-muted">Aqui voce podera ajustar series, repeticoes e carga</small>' +
            '</div>';
        return;
    }

    var html = '';
    session.exercises.forEach(function (ex, idx) {
        html += '<div class="exercise-item mb-3 shadow-sm" data-index="' + idx + '">' +
            '<div class="d-flex justify-content-between align-items-center mb-2">' +
            '<div class="d-flex align-items-center gap-2">' +
            '<span class="badge bg-secondary rounded-circle" style="width:24px; height:24px; display:flex; align-items:center; justify-content:center;">' + (idx + 1) + '</span>' +
            '<strong class="small">' + ex.name + '</strong>' +
            '<small class="text-muted">(' + ex.muscle_group_label + ')</small>' +
            '</div>' +
            '<button class="btn btn-sm btn-outline-danger border-0" ' +
            'onclick="removeExerciseFromSession(\'' + targetSessionId + '\',' + idx + ')">' +
            '<i class="fas fa-trash-alt"></i>' +
            '</button>' +
            '</div>' +
            '<div class="row g-2">' +
            '<div class="col-4 col-md-2">' +
            '<label class="small text-muted mb-0">Series</label>' +
            '<input type="number" class="form-control form-control-sm" value="' + ex.sets + '" min="1" max="20" ' +
            'oninput="updateExerciseFieldStep3(\'' + targetSessionId + '\',' + idx + ',\'sets\',this.value)">' +
            '</div>' +
            '<div class="col-8 col-md-3">' +
            '<label class="small text-muted mb-0">Repeticoes</label>' +
            '<input type="text" class="form-control form-control-sm" value="' + ex.reps + '" placeholder="Ex: 10-12" ' +
            'oninput="updateExerciseFieldStep3(\'' + targetSessionId + '\',' + idx + ',\'reps\',this.value)">' +
            '</div>' +
            '<div class="col-4 col-md-2">' +
            '<label class="small text-muted mb-0">Desc.(s)</label>' +
            '<input type="number" class="form-control form-control-sm" value="' + ex.rest + '" step="10" ' +
            'oninput="updateExerciseFieldStep3(\'' + targetSessionId + '\',' + idx + ',\'rest\',this.value)">' +
            '</div>' +
            '<div class="col-8 col-md-2">' +
            '<label class="small text-muted mb-0">Carga</label>' +
            '<input type="text" class="form-control form-control-sm" value="' + (ex.weight || '') + '" placeholder="20kg" ' +
            'oninput="updateExerciseFieldStep3(\'' + targetSessionId + '\',' + idx + ',\'weight\',this.value)">' +
            '</div>' +
            '<div class="col-12 col-md-3">' +
            '<label class="small text-muted mb-0">Notas</label>' +
            '<input type="text" class="form-control form-control-sm" value="' + (ex.notes || '') + '" placeholder="Opcional" ' +
            'oninput="updateExerciseFieldStep3(\'' + targetSessionId + '\',' + idx + ',\'notes\',this.value)">' +
            '</div>' +
            '</div>' +
            '</div>';
    });

    container.innerHTML = html;
}

function updateExerciseFieldStep3(sessionId, exerciseIndex, field, value) {
    updateExerciseField(sessionId, exerciseIndex, field, value);
    // Also sync the step 2 card
    renderSessionExercises(sessionId);
}

function updateTargetSessionDropdown() {
    var select = document.getElementById('targetSession');
    select.innerHTML = '';

    if (sessions.length === 0) {
        select.innerHTML = '<option value="">Nenhuma sessao criada</option>';
        return;
    }

    sessions.forEach(function (session) {
        var option = document.createElement('option');
        option.value = session.id;
        option.textContent = session.name + ' (' + session.exercises.length + ' exercicios)';
        select.appendChild(option);
    });

    // Listen for changes to refresh step 3 exercises
    select.onchange = function () {
        renderStep3Exercises();
    };

    // Render current session exercises
    renderStep3Exercises();
}

// Save prescription
async function savePrescription() {
    if (!selectedStudent) {
        showPrescriptionAlert('Selecione um aluno', 'warning');
        return;
    }

    if (sessions.length === 0) {
        showPrescriptionAlert('Adicione pelo menos uma sessao', 'warning');
        return;
    }

    // Check at least one session has exercises
    var hasExercises = sessions.some(function (s) { return s.exercises.length > 0; });
    if (!hasExercises) {
        showPrescriptionAlert('Adicione exercicios a pelo menos uma sessao', 'warning');
        return;
    }

    var saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Salvando...';

    var data = {
        user_id: selectedStudent.id,
        goal: document.getElementById('goal').value,
        validity_days: parseInt(document.getElementById('validity').value),
        notes: document.getElementById('planNotes').value,
        sessions: sessions.map(function (session) {
            return {
                name: session.name,
                day_of_week: session.day_of_week,
                exercises: session.exercises.map(function (ex) {
                    return {
                        exercise_id: ex.exercise_id,
                        sets: parseInt(ex.sets),
                        reps: ex.reps,
                        rest: parseInt(ex.rest),
                        weight: ex.weight,
                        notes: ex.notes
                    };
                })
            };
        })
    };

    try {
        var response = await fetch('/api/training/prescribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        var result = await response.json();

        if (result.success) {
            showPrescriptionAlert('Prescricao salva com sucesso!', 'success');
            setTimeout(function () {
                window.location.href = '/instructor/training/list';
            }, 1500);
        } else {
            showPrescriptionAlert('Erro: ' + result.error, 'danger');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Salvar Prescricao';
        }
    } catch (err) {
        showPrescriptionAlert('Erro de conexao: ' + err.message, 'danger');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Salvar Prescricao';
    }
}

async function loadTemplate(templateId) {
    try {
        var response = await fetch('/api/training/templates/' + templateId);
        var template = await response.json();

        // Populate basic info
        document.getElementById('goal').value = template.goal;

        // Clear current sessions
        sessions = [];
        document.getElementById('sessions-container').innerHTML = '';
        sessionCounter = 0;

        // Add sessions from template
        template.sessions.forEach(function (sData) {
            sessionCounter++;
            var sessionId = 'session-' + sessionCounter;

            var session = {
                id: sessionId,
                name: sData.name,
                day_of_week: null,
                exercises: sData.exercises.map(function (e) {
                    return {
                        exercise_id: e.exercise_id,
                        name: e.name,
                        muscle_group_label: e.muscle_group_label,
                        sets: e.sets,
                        reps: e.reps,
                        rest: e.rest,
                        weight: e.weight || '',
                        notes: e.notes || ''
                    };
                })
            };
            sessions.push(session);

            // Render session card
            renderSessionCard(session);
        });

        updatePreview();
        showPrescriptionAlert('Modelo "' + template.name + '" carregado!', 'success');

    } catch (err) {
        console.error('Erro ao carregar template:', err);
        showPrescriptionAlert('Erro ao carregar modelo.', 'danger');
    }
}

function renderSessionCard(session) {
    var container = document.getElementById('sessions-container');
    var card = document.createElement('div');
    card.className = 'card mb-3 session-card';
    card.setAttribute('data-session-id', session.id);
    card.innerHTML =
        '<div class="card-header d-flex justify-content-between align-items-center">' +
        '<div class="d-flex gap-2 flex-wrap align-items-center">' +
        '<input type="text" class="form-control form-control-sm bg-transparent text-white border-light" ' +
        'style="width: 200px;" placeholder="Nome da sessao" value="' + session.name + '" ' +
        'onchange="updateSessionName(\'' + session.id + '\', this.value)">' +
        '<select class="form-select form-select-sm bg-transparent text-white border-light" style="width: 150px;" ' +
        'onchange="updateSessionDay(\'' + session.id + '\', this.value)">' +
        '<option value="">Sistema ABC</option>' +
        '<option value="0">Segunda</option>' +
        '<option value="1">Terca</option>' +
        '<option value="2">Quarta</option>' +
        '<option value="3">Quinta</option>' +
        '<option value="4">Sexta</option>' +
        '<option value="5">Sabado</option>' +
        '<option value="6">Domingo</option>' +
        '</select>' +
        '</div>' +
        '<button class="btn btn-sm btn-outline-light" onclick="removeSession(\'' + session.id + '\')">' +
        '<i class="fas fa-trash"></i>' +
        '</button>' +
        '</div>' +
        '<div class="card-body">' +
        '<div class="exercises-list" id="exercises-' + session.id + '">' +
        '</div>' +
        '</div>';

    container.appendChild(card);
    renderSessionExercises(session.id);
}

async function saveAsTemplate() {
    var name = document.getElementById('templateName').value;
    if (!name) {
        showPrescriptionAlert('Digite um nome para o modelo.', 'warning');
        return;
    }

    if (sessions.length === 0 || !sessions.some(s => s.exercises.length > 0)) {
        showPrescriptionAlert('O modelo deve ter pelo menos uma sessao com exercicios.', 'warning');
        return;
    }

    var saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Salvando...';

    var data = {
        name: name,
        description: document.getElementById('templateDescription').value,
        goal: document.getElementById('goal').value,
        is_public: true,
        sessions: sessions.map(function (s) {
            return {
                name: s.name,
                exercises: s.exercises.map(function (ex) {
                    return {
                        exercise_id: ex.exercise_id,
                        sets: parseInt(ex.sets),
                        reps: ex.reps,
                        rest: parseInt(ex.rest),
                        weight: ex.weight,
                        notes: ex.notes
                    };
                })
            };
        })
    };

    try {
        var response = await fetch('/api/training/templates/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        var result = await response.json();

        if (result.success) {
            showPrescriptionAlert('Modelo salvo com sucesso!', 'success');
            setTimeout(function () {
                window.location.href = '/instructor/training/templates';
            }, 1500);
        } else {
            showPrescriptionAlert('Erro: ' + result.error, 'danger');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Salvar Modelo';
        }
    } catch (err) {
        console.error('Erro ao salvar modelo:', err);
        showPrescriptionAlert('Erro de conexao.', 'danger');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Salvar Modelo';
    }
}

// Update preview panel
function updatePreview() {
    var preview = document.getElementById('prescription-preview');

    // Check if we are in template mode
    var step1 = document.getElementById('step1');
    var isTemplateMode = step1 && step1.dataset.mode === 'template';

    if (!isTemplateMode && !selectedStudent) {
        preview.innerHTML = '<p class="text-muted">Selecione um aluno para comecar...</p>';
        return;
    }

    var goalSelect = document.getElementById('goal');
    var goalText = goalSelect.options[goalSelect.selectedIndex].text;
    var validity = document.getElementById('validity').value;

    var headerHtml = '';
    if (isTemplateMode) {
        var templateName = document.getElementById('templateName').value || 'Novo Modelo';
        headerHtml = '<strong>Modelo:</strong> ' + templateName + '<br>';
    } else {
        headerHtml = '<strong>Aluno:</strong> ' + selectedStudent.name + '<br>' +
            '<strong>Validade:</strong> ' + validity + ' dias' + '<br>';
    }

    var html = '<div class="mb-3">' +
        headerHtml +
        '<strong>Objetivo:</strong> ' + goalText +
        '</div>';

    if (sessions.length > 0) {
        html += '<hr><h6>Sessoes (' + sessions.length + ')</h6>';

        sessions.forEach(function (session, idx) {
            html += '<div class="mb-2 p-2 bg-light rounded">' +
                '<strong>' + session.name + '</strong>';

            if (session.exercises.length > 0) {
                html += '<ul class="list-unstyled mb-0 mt-1">';
                session.exercises.forEach(function (ex) {
                    html += '<li><small>' + ex.name + ' - ' + ex.sets + 'x' + ex.reps + '</small></li>';
                });
                html += '</ul>';
            } else {
                html += '<br><small class="text-muted">Sem exercicios</small>';
            }

            html += '</div>';
        });
    }

    var totalExercises = sessions.reduce(function (sum, s) { return sum + s.exercises.length; }, 0);
    html += '<hr><small class="text-muted">Total: ' + sessions.length + ' sessao(oes), ' + totalExercises + ' exercicio(s)</small>';

    preview.innerHTML = html;
}

// Alert helper
function showPrescriptionAlert(message, type) {
    var container = document.getElementById('prescriptionAlerts');
    if (!container) return;

    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    container.appendChild(alertDiv);

    setTimeout(function () {
        if (alertDiv.parentNode) alertDiv.remove();
    }, 4000);
}
