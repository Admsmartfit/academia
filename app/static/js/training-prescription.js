// training-prescription.js - Instructor training prescription interface

var currentStep = 1;
var sessions = [];
var exercisesLibrary = [];
var selectedStudent = null;
var sessionCounter = 0;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadExercisesLibrary();
    setupAutocomplete();
    setupFilters();
});

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
    var muscleFilter = document.getElementById('muscleFilter').value;
    var searchTerm = (document.getElementById('exerciseSearch').value || '').toLowerCase();

    var filtered = exercisesLibrary.filter(function(ex) {
        var matchMuscle = !muscleFilter || ex.muscle_group === muscleFilter;
        var matchSearch = !searchTerm || ex.name.toLowerCase().indexOf(searchTerm) !== -1;
        return matchMuscle && matchSearch;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Nenhum exercicio encontrado.</p>';
        return;
    }

    var html = '';
    filtered.forEach(function(exercise) {
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
    document.getElementById('muscleFilter').addEventListener('change', renderExercisesLibrary);
    var searchInput = document.getElementById('exerciseSearch');
    var searchTimeout;
    searchInput.addEventListener('keyup', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(renderExercisesLibrary, 300);
    });
}

// Student autocomplete
function setupAutocomplete() {
    var searchInput = document.getElementById('studentSearch');
    var timeout;

    searchInput.addEventListener('keyup', function() {
        clearTimeout(timeout);
        var query = this.value;

        if (query.length < 2) {
            document.getElementById('studentResults').style.display = 'none';
            return;
        }

        timeout = setTimeout(async function() {
            try {
                var response = await fetch('/api/training/users/search?q=' + encodeURIComponent(query) + '&role=student');
                var students = await response.json();

                var results = document.getElementById('studentResults');
                results.innerHTML = '';

                students.forEach(function(student) {
                    var item = document.createElement('a');
                    item.className = 'dropdown-item';
                    item.href = '#';
                    item.innerHTML = student.name + ' <small class="text-muted">(' + student.email + ')</small>';
                    item.addEventListener('click', function(e) {
                        e.preventDefault();
                        selectStudent(student);
                    });
                    results.appendChild(item);
                });

                results.style.display = students.length > 0 ? 'block' : 'none';
            } catch (err) {
                console.error('Erro ao buscar alunos:', err);
            }
        }, 300);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#studentSearch') && !e.target.closest('#studentResults')) {
            document.getElementById('studentResults').style.display = 'none';
        }
    });
}

function selectStudent(student) {
    selectedStudent = student;
    document.getElementById('studentSearch').value = student.name;
    document.getElementById('selectedStudentId').value = student.id;
    document.getElementById('studentResults').style.display = 'none';

    var info = document.getElementById('selectedStudentInfo');
    info.style.display = '';
    document.getElementById('studentBadge').textContent = student.name + ' (' + student.email + ')';

    updatePreview();
}

// Step navigation
function goToStep(step) {
    // Validate before advancing
    if (step === 2 && !selectedStudent) {
        showPrescriptionAlert('Selecione um aluno primeiro.', 'warning');
        return;
    }
    if (step === 3 && sessions.length === 0) {
        showPrescriptionAlert('Adicione pelo menos uma sessao de treino.', 'warning');
        return;
    }

    document.querySelectorAll('.prescription-step').forEach(function(el) {
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

    sessions = sessions.filter(function(s) { return s.id !== sessionId; });
    var card = document.querySelector('.session-card[data-session-id="' + sessionId + '"]');
    if (card) card.remove();
    updatePreview();
}

function updateSessionName(sessionId, name) {
    var session = sessions.find(function(s) { return s.id === sessionId; });
    if (session) session.name = name;
    updatePreview();
}

function updateSessionDay(sessionId, value) {
    var session = sessions.find(function(s) { return s.id === sessionId; });
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

    var session = sessions.find(function(s) { return s.id === targetSessionId; });
    if (!session) return;

    var exercise = exercisesLibrary.find(function(ex) { return ex.id === exerciseId; });
    if (!exercise) return;

    // Check duplicate
    var duplicate = session.exercises.find(function(ex) { return ex.exercise_id === exerciseId; });
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
    updatePreview();
    showPrescriptionAlert(exercise.name + ' adicionado a ' + session.name, 'success');
}

function renderSessionExercises(sessionId) {
    var session = sessions.find(function(s) { return s.id === sessionId; });
    if (!session) return;

    var container = document.getElementById('exercises-' + sessionId);
    if (!container) return;

    if (session.exercises.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">Nenhum exercicio adicionado.</p>';
        return;
    }

    var html = '';
    session.exercises.forEach(function(ex, idx) {
        html += '<div class="exercise-item mb-2" data-index="' + idx + '">' +
            '<div class="d-flex justify-content-between align-items-start">' +
            '<div class="flex-grow-1">' +
            '<strong>' + (idx + 1) + '. ' + ex.name + '</strong>' +
            ' <small class="text-muted">(' + ex.muscle_group_label + ')</small>' +
            '<div class="row g-2 mt-1">' +
            '<div class="col-3">' +
            '<input type="number" class="form-control form-control-sm" placeholder="Series" ' +
            'value="' + ex.sets + '" min="1" max="10" ' +
            'onchange="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'sets\',this.value)">' +
            '<small class="text-muted">Series</small>' +
            '</div>' +
            '<div class="col-3">' +
            '<input type="text" class="form-control form-control-sm" placeholder="Reps" ' +
            'value="' + ex.reps + '" ' +
            'onchange="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'reps\',this.value)">' +
            '<small class="text-muted">Reps</small>' +
            '</div>' +
            '<div class="col-3">' +
            '<input type="number" class="form-control form-control-sm" placeholder="Desc.(s)" ' +
            'value="' + ex.rest + '" ' +
            'onchange="updateExerciseField(\'' + sessionId + '\',' + idx + ',\'rest\',this.value)">' +
            '<small class="text-muted">Desc.(s)</small>' +
            '</div>' +
            '<div class="col-3 text-end">' +
            '<button class="btn btn-sm btn-outline-danger" ' +
            'onclick="removeExerciseFromSession(\'' + sessionId + '\',' + idx + ')">' +
            '<i class="fas fa-times"></i>' +
            '</button>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
    });

    container.innerHTML = html;
}

function updateExerciseField(sessionId, exerciseIndex, field, value) {
    var session = sessions.find(function(s) { return s.id === sessionId; });
    if (session && session.exercises[exerciseIndex]) {
        session.exercises[exerciseIndex][field] = value;
        updatePreview();
    }
}

function removeExerciseFromSession(sessionId, exerciseIndex) {
    var session = sessions.find(function(s) { return s.id === sessionId; });
    if (session) {
        session.exercises.splice(exerciseIndex, 1);
        renderSessionExercises(sessionId);
        updatePreview();
    }
}

function updateTargetSessionDropdown() {
    var select = document.getElementById('targetSession');
    select.innerHTML = '';

    if (sessions.length === 0) {
        select.innerHTML = '<option value="">Nenhuma sessao criada</option>';
        return;
    }

    sessions.forEach(function(session) {
        var option = document.createElement('option');
        option.value = session.id;
        option.textContent = session.name + ' (' + session.exercises.length + ' exercicios)';
        select.appendChild(option);
    });
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
    var hasExercises = sessions.some(function(s) { return s.exercises.length > 0; });
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
        sessions: sessions.map(function(session) {
            return {
                name: session.name,
                day_of_week: session.day_of_week,
                exercises: session.exercises.map(function(ex) {
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
            setTimeout(function() {
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

// Update preview panel
function updatePreview() {
    var preview = document.getElementById('prescription-preview');

    if (!selectedStudent) {
        preview.innerHTML = '<p class="text-muted">Selecione um aluno para comecar...</p>';
        return;
    }

    var goalSelect = document.getElementById('goal');
    var goalText = goalSelect.options[goalSelect.selectedIndex].text;
    var validity = document.getElementById('validity').value;

    var html = '<div class="mb-3">' +
        '<strong>Aluno:</strong> ' + selectedStudent.name + '<br>' +
        '<strong>Objetivo:</strong> ' + goalText + '<br>' +
        '<strong>Validade:</strong> ' + validity + ' dias' +
        '</div>';

    if (sessions.length > 0) {
        html += '<hr><h6>Sessoes (' + sessions.length + ')</h6>';

        sessions.forEach(function(session, idx) {
            html += '<div class="mb-2 p-2 bg-light rounded">' +
                '<strong>' + session.name + '</strong>';

            if (session.exercises.length > 0) {
                html += '<ul class="list-unstyled mb-0 mt-1">';
                session.exercises.forEach(function(ex) {
                    html += '<li><small>' + ex.name + ' - ' + ex.sets + 'x' + ex.reps + '</small></li>';
                });
                html += '</ul>';
            } else {
                html += '<br><small class="text-muted">Sem exercicios</small>';
            }

            html += '</div>';
        });
    }

    var totalExercises = sessions.reduce(function(sum, s) { return sum + s.exercises.length; }, 0);
    html += '<hr><small class="text-muted">Total: ' + sessions.length + ' sessao(oes), ' + totalExercises + ' exercicio(s)</small>';

    preview.innerHTML = html;
}

// Alert helper
function showPrescriptionAlert(message, type) {
    var container = document.getElementById('prescriptionAlerts');
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    container.appendChild(alertDiv);

    setTimeout(function() {
        if (alertDiv.parentNode) alertDiv.remove();
    }, 4000);
}
