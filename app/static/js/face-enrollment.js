// face-enrollment.js - Face enrollment UI logic

let stream = null;
let capturedImageData = null;

// Toggle between upload and webcam
document.querySelectorAll('input[name="captureMethod"]').forEach(function(radio) {
    radio.addEventListener('change', function() {
        if (this.value === 'upload') {
            document.getElementById('uploadSection').style.display = '';
            document.getElementById('webcamSection').style.display = 'none';
            stopWebcam();
        } else {
            document.getElementById('uploadSection').style.display = 'none';
            document.getElementById('webcamSection').style.display = '';
        }
    });
});

// File upload handler
var fileInput = document.getElementById('fileInput');
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        var file = e.target.files[0];
        if (!file) return;

        // Validate size (5MB)
        if (file.size > 5 * 1024 * 1024) {
            showFaceAlert('Arquivo muito grande! Maximo 5MB.', 'danger');
            return;
        }

        // Validate type
        if (!file.type.startsWith('image/')) {
            showFaceAlert('Arquivo deve ser uma imagem (JPG, PNG).', 'danger');
            return;
        }

        // Preview
        var reader = new FileReader();
        reader.onload = function(e) {
            var img = document.getElementById('capturedImage');
            img.src = e.target.result;
            img.style.display = '';
            capturedImageData = e.target.result;
            document.getElementById('enrollBtn').disabled = false;
        };
        reader.readAsDataURL(file);
    });
}

// Start webcam
async function startWebcam() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }
        });

        var video = document.getElementById('webcam');
        video.srcObject = stream;
        video.style.display = '';

        document.getElementById('captureBtn').disabled = false;
        showFaceAlert('Camera iniciada! Posicione seu rosto e clique em Capturar.', 'info');
    } catch (err) {
        showFaceAlert('Erro ao acessar camera: ' + err.message, 'danger');
    }
}

// Stop webcam
function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(function(track) { track.stop(); });
        var video = document.getElementById('webcam');
        if (video) video.style.display = 'none';
        stream = null;
    }
}

// Capture photo from webcam
function capturePhoto() {
    var video = document.getElementById('webcam');
    var canvas = document.getElementById('canvas');
    var context = canvas.getContext('2d');

    // Draw current frame
    context.drawImage(video, 0, 0, 320, 240);

    // Convert to base64
    capturedImageData = canvas.toDataURL('image/jpeg');

    // Show preview
    var img = document.getElementById('capturedImage');
    img.src = capturedImageData;
    img.style.display = '';
    video.style.display = 'none';

    stopWebcam();
    document.getElementById('enrollBtn').disabled = false;
    showFaceAlert('Foto capturada! Clique em Cadastrar Face para enviar.', 'success');
}

// Enroll face
async function enrollFace() {
    var consentCheck = document.getElementById('consentCheck');
    if (!consentCheck.checked) {
        showFaceAlert('Voce precisa concordar com o termo de consentimento.', 'warning');
        return;
    }

    if (!capturedImageData) {
        showFaceAlert('Nenhuma imagem selecionada!', 'warning');
        return;
    }

    var enrollBtn = document.getElementById('enrollBtn');
    enrollBtn.disabled = true;
    enrollBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processando...';

    try {
        var response = await fetch('/api/face/enroll', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: capturedImageData
            })
        });

        var result = await response.json();

        if (result.success) {
            showFaceAlert('Face cadastrada com sucesso! Confianca: ' + result.confidence.toFixed(1) + '%', 'success');
            setTimeout(function() { location.reload(); }, 2000);
        } else {
            showFaceAlert('Erro: ' + (result.error || result.message), 'danger');
            enrollBtn.disabled = false;
            enrollBtn.innerHTML = '<i class="fas fa-check me-2"></i>Cadastrar Face';
        }
    } catch (err) {
        showFaceAlert('Erro de conexao: ' + err.message, 'danger');
        enrollBtn.disabled = false;
        enrollBtn.innerHTML = '<i class="fas fa-check me-2"></i>Cadastrar Face';
    }
}

// Remove face
async function removeFace() {
    if (!confirm('Tem certeza que deseja remover seus dados biometricos? Esta acao nao pode ser desfeita.')) {
        return;
    }

    try {
        var response = await fetch('/api/face/remove', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ confirm: true })
        });

        var result = await response.json();

        if (result.success) {
            showFaceAlert('Dados biometricos removidos com sucesso!', 'success');
            setTimeout(function() { location.reload(); }, 1500);
        } else {
            showFaceAlert('Erro: ' + (result.error || result.message), 'danger');
        }
    } catch (err) {
        showFaceAlert('Erro: ' + err.message, 'danger');
    }
}

// Show alert in the face enrollment card
function showFaceAlert(message, type) {
    var container = document.getElementById('faceAlerts');
    if (!container) return;

    container.innerHTML = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';

    // Auto-dismiss after 5 seconds for non-error alerts
    if (type !== 'danger') {
        setTimeout(function() {
            var alert = container.querySelector('.alert');
            if (alert) alert.remove();
        }, 5000);
    }
}
