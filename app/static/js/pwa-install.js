// PWA Install Prompt Handler
(function() {
    var deferredPrompt = null;
    var installBanner = null;

    // Capture the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', function(e) {
        e.preventDefault();
        deferredPrompt = e;
        showInstallBanner();
    });

    function showInstallBanner() {
        // Don't show if already dismissed this session
        if (sessionStorage.getItem('pwa-install-dismissed')) return;

        // Create install banner
        installBanner = document.createElement('div');
        installBanner.id = 'pwa-install-banner';
        installBanner.innerHTML =
            '<div style="position:fixed;bottom:0;left:0;right:0;z-index:1050;' +
            'background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);' +
            'padding:16px 20px;display:flex;align-items:center;gap:12px;' +
            'box-shadow:0 -4px 20px rgba(0,0,0,0.3);border-top:2px solid #FF6B35;">' +
                '<div style="flex-shrink:0;width:44px;height:44px;background:#FF6B35;' +
                'border-radius:10px;display:flex;align-items:center;justify-content:center;">' +
                    '<i class="fas fa-bolt" style="color:white;font-size:20px;"></i>' +
                '</div>' +
                '<div style="flex:1;min-width:0;">' +
                    '<div style="color:white;font-weight:600;font-size:0.95rem;">Instalar Biohacking Studio</div>' +
                    '<div style="color:#94A3B8;font-size:0.8rem;">Acesse rapido sem abrir o navegador</div>' +
                '</div>' +
                '<button id="pwa-install-btn" style="flex-shrink:0;padding:8px 20px;' +
                'background:#FF6B35;color:white;border:none;border-radius:8px;' +
                'font-weight:600;font-size:0.875rem;cursor:pointer;">Instalar</button>' +
                '<button id="pwa-dismiss-btn" style="flex-shrink:0;background:none;' +
                'border:none;color:#64748B;font-size:1.25rem;cursor:pointer;padding:4px 8px;">' +
                '&times;</button>' +
            '</div>';

        document.body.appendChild(installBanner);

        document.getElementById('pwa-install-btn').addEventListener('click', function() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(function(result) {
                    if (result.outcome === 'accepted') {
                        console.log('PWA installed');
                    }
                    deferredPrompt = null;
                    hideInstallBanner();
                });
            }
        });

        document.getElementById('pwa-dismiss-btn').addEventListener('click', function() {
            sessionStorage.setItem('pwa-install-dismissed', '1');
            hideInstallBanner();
        });
    }

    function hideInstallBanner() {
        if (installBanner && installBanner.parentNode) {
            installBanner.parentNode.removeChild(installBanner);
        }
    }

    // Hide banner when app is installed
    window.addEventListener('appinstalled', function() {
        hideInstallBanner();
        deferredPrompt = null;
    });

    // Push notification opt-in for student pages
    window.initPushOptIn = function() {
        if (!('Notification' in window)) return;
        if (Notification.permission !== 'default') return;

        var optIn = document.getElementById('push-optin');
        if (!optIn) return;

        optIn.style.display = 'block';
        var btn = optIn.querySelector('.push-enable-btn');
        if (btn) {
            btn.addEventListener('click', function() {
                if (typeof window.requestPushPermission === 'function') {
                    window.requestPushPermission().then(function(success) {
                        if (success) {
                            optIn.innerHTML =
                                '<div class="alert alert-success mb-0">' +
                                '<i class="fas fa-bell me-2"></i>Notificacoes ativadas!' +
                                '</div>';
                        }
                    });
                }
            });
        }
    };
})();
