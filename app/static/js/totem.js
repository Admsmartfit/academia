// totem.js - Kiosk mode face recognition for gym entrance

(function() {
    'use strict';

    var video = document.getElementById('webcam');
    var canvas = document.getElementById('canvas');
    var context = canvas.getContext('2d');
    var stream = null;
    var isProcessing = false;
    var captureInterval = 2000; // 2 seconds
    var lastCaptureTime = 0;
    var fpsCounter = 0;
    var lastFpsTime = Date.now();

    // Initialize
    init();

    async function init() {
        try {
            await requestFullscreen();
            await startCamera();
            startCaptureLoop();
            startFpsCounter();
            setupKeyboardShortcuts();
            updateStatus('Sistema pronto. Aguardando reconhecimento...', 'info');
        } catch (err) {
            console.error('Erro ao inicializar:', err);
            updateStatus('Erro ao iniciar camera: ' + err.message, 'error');
            // Show fallback UI
            document.getElementById('camera-error').style.display = '';
            video.style.display = 'none';
            document.getElementById('face-overlay').style.display = 'none';
        }
    }

    async function startCamera() {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            }
        });

        video.srcObject = stream;

        return new Promise(function(resolve) {
            video.onloadedmetadata = function() {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                resolve();
            };
        });
    }

    function startCaptureLoop() {
        function loop() {
            var now = Date.now();

            if (!isProcessing && (now - lastCaptureTime) >= captureInterval) {
                captureAndRecognize();
                lastCaptureTime = now;
            }

            requestAnimationFrame(loop);
        }

        requestAnimationFrame(loop);
    }

    async function captureAndRecognize() {
        isProcessing = true;
        setOverlayState('detecting');

        // Capture frame
        context.drawImage(video, 0, 0);
        var imageData = canvas.toDataURL('image/jpeg', 0.8);

        // Update admin panel timestamp
        var lastCapture = document.getElementById('last-capture');
        if (lastCapture) lastCapture.textContent = new Date().toLocaleTimeString();

        try {
            var response = await fetch('/api/face/recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: imageData,
                    auto_checkin: true
                })
            });

            var result = await response.json();

            if (result.success && result.user) {
                onUserRecognized(result);
            } else {
                setOverlayState('idle');
            }

            var connStatus = document.getElementById('connection-status');
            if (connStatus) {
                connStatus.textContent = 'Conectado';
                connStatus.style.color = '#28a745';
            }
        } catch (err) {
            console.error('Erro no reconhecimento:', err);
            updateStatus('Erro de conexao. Tentando novamente...', 'error');
            var connStatus = document.getElementById('connection-status');
            if (connStatus) {
                connStatus.textContent = 'Erro';
                connStatus.style.color = 'red';
            }
        } finally {
            isProcessing = false;
        }
    }

    function onUserRecognized(result) {
        console.log('Usuario reconhecido:', result);

        setOverlayState('recognized');
        showSuccessCard(result);
        playSuccessSound();

        // Pause recognition for 5 seconds
        lastCaptureTime = Date.now() + 5000;
    }

    function showSuccessCard(result) {
        var card = document.getElementById('success-card');
        var user = result.user;
        var checkin = result.checkin;

        // Update name
        document.getElementById('user-name').textContent = user.name;

        // Build badges
        var badgesContainer = document.getElementById('success-badges');
        badgesContainer.innerHTML = '';

        if (checkin && checkin.xp_earned) {
            badgesContainer.innerHTML += '<span class="badge bg-success me-2">+' + checkin.xp_earned + ' XP</span>';
        }

        if (checkin && checkin.success) {
            badgesContainer.innerHTML += '<span class="badge bg-info">Check-in OK</span>';
        } else if (result.should_checkin) {
            badgesContainer.innerHTML += '<span class="badge bg-warning text-dark">Aula agendada</span>';
        }

        // Show card
        card.classList.add('show');

        // Hide after 4 seconds
        setTimeout(function() {
            card.classList.remove('show');
            setOverlayState('idle');
            updateStatus('Aguardando proximo aluno...', 'info');
        }, 4000);
    }

    function setOverlayState(state) {
        var overlay = document.getElementById('face-overlay');
        overlay.classList.remove('detecting', 'recognized');
        if (state !== 'idle') {
            overlay.classList.add(state);
        }
    }

    function updateStatus(message, type) {
        var statusEl = document.getElementById('status-message');
        var icons = {
            info: 'fa-user-circle',
            error: 'fa-exclamation-triangle',
            success: 'fa-check-circle'
        };

        statusEl.innerHTML = '<i class="fas ' + (icons[type] || icons.info) + '"></i> ' + message;
    }

    function playSuccessSound() {
        try {
            var audioContext = new (window.AudioContext || window.webkitAudioContext)();
            var oscillator = audioContext.createOscillator();
            var gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (e) {
            // Audio not available, ignore
        }
    }

    function startFpsCounter() {
        setInterval(function() {
            var now = Date.now();
            var elapsed = (now - lastFpsTime) / 1000;
            var fps = Math.round(fpsCounter / elapsed);

            var fpsEl = document.getElementById('fps');
            if (fpsEl) fpsEl.textContent = fps;

            fpsCounter = 0;
            lastFpsTime = now;
        }, 1000);

        // Increment counter
        function countFps() {
            fpsCounter++;
            requestAnimationFrame(countFps);
        }
        requestAnimationFrame(countFps);
    }

    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // 'A' to toggle admin panel
            if (e.key.toLowerCase() === 'a') {
                var panel = document.getElementById('admin-panel');
                panel.style.display = panel.style.display === 'none' ? '' : 'none';
            }

            // 'ESC' to exit fullscreen
            if (e.key === 'Escape') {
                exitTotem();
            }

            // 'R' to reload
            if (e.key.toLowerCase() === 'r') {
                location.reload();
            }
        });
    }

    async function requestFullscreen() {
        var elem = document.documentElement;
        try {
            if (elem.requestFullscreen) {
                await elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) {
                await elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) {
                await elem.msRequestFullscreen();
            }
        } catch (e) {
            // Fullscreen not available or denied, continue anyway
            console.warn('Fullscreen nao disponivel:', e.message);
        }
    }

    // Expose exit function globally
    window.exitTotem = function() {
        if (document.exitFullscreen) {
            document.exitFullscreen().catch(function() {});
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }

        if (stream) {
            stream.getTracks().forEach(function(track) { track.stop(); });
        }

        window.location.href = '/instructor/dashboard';
    };

})();
