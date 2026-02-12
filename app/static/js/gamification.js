/**
 * Gamification Visual Effects
 * - XP Conversion: violet particle animation
 * - Payment Confirmed: confetti + checkmark
 * - Fibras Ativadas: counter animation
 */

// ==========================================
// XP CONVERSION PARTICLES
// ==========================================
function showXPConversionAnimation(targetElement) {
    var container = document.createElement('div');
    container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;overflow:hidden;';
    document.body.appendChild(container);

    var rect = targetElement ? targetElement.getBoundingClientRect() : { left: window.innerWidth / 2, top: window.innerHeight / 2 };
    var targetX = rect.left + (rect.width || 0) / 2;
    var targetY = rect.top + (rect.height || 0) / 2;

    // Create 30 violet particles
    var particles = [];
    for (var i = 0; i < 30; i++) {
        var p = document.createElement('div');
        var startX = Math.random() * window.innerWidth;
        var startY = Math.random() * window.innerHeight;
        var size = 4 + Math.random() * 8;

        p.style.cssText = 'position:absolute;border-radius:50%;pointer-events:none;' +
            'width:' + size + 'px;height:' + size + 'px;' +
            'left:' + startX + 'px;top:' + startY + 'px;' +
            'background:' + (Math.random() > 0.5 ? '#8B5CF6' : '#a78bfa') + ';' +
            'box-shadow:0 0 ' + (size * 2) + 'px ' + (Math.random() > 0.5 ? '#8B5CF6' : '#a78bfa') + ';' +
            'opacity:0;' +
            'transition:all 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);';

        container.appendChild(p);
        particles.push({ el: p, startX: startX, startY: startY });
    }

    // Phase 1: particles appear
    requestAnimationFrame(function() {
        particles.forEach(function(p) {
            p.el.style.opacity = '1';
        });

        // Phase 2: converge to target
        setTimeout(function() {
            particles.forEach(function(p) {
                p.el.style.left = targetX + 'px';
                p.el.style.top = targetY + 'px';
                p.el.style.opacity = '0.8';
                p.el.style.width = '3px';
                p.el.style.height = '3px';
            });

            // Phase 3: flash and cleanup
            setTimeout(function() {
                // Gold flash at target
                var flash = document.createElement('div');
                flash.style.cssText = 'position:absolute;border-radius:50%;' +
                    'width:60px;height:60px;' +
                    'left:' + (targetX - 30) + 'px;top:' + (targetY - 30) + 'px;' +
                    'background:radial-gradient(circle,#FFD700,rgba(255,215,0,0));' +
                    'animation:xp-flash 0.6s ease-out forwards;';
                container.appendChild(flash);

                // Gold credit icon
                var icon = document.createElement('div');
                icon.innerHTML = '<i class="fas fa-coins" style="color:#FFD700;font-size:2rem;"></i>';
                icon.style.cssText = 'position:absolute;' +
                    'left:' + (targetX - 16) + 'px;top:' + (targetY - 16) + 'px;' +
                    'animation:xp-icon-pop 0.8s ease-out forwards;';
                container.appendChild(icon);

                // Cleanup
                setTimeout(function() {
                    container.remove();
                }, 1000);
            }, 1200);
        }, 300);
    });
}

// ==========================================
// CONFETTI FOR PAYMENT
// ==========================================
function showPaymentConfetti() {
    var container = document.createElement('div');
    container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;overflow:hidden;';
    document.body.appendChild(container);

    var colors = ['#FF6B35', '#10B981', '#06B6D4', '#8B5CF6', '#FFD700', '#F43F5E'];
    var confettiCount = 60;

    for (var i = 0; i < confettiCount; i++) {
        var c = document.createElement('div');
        var color = colors[Math.floor(Math.random() * colors.length)];
        var x = Math.random() * window.innerWidth;
        var size = 6 + Math.random() * 8;
        var delay = Math.random() * 0.5;
        var duration = 2 + Math.random() * 2;
        var rotation = Math.random() * 360;
        var isRect = Math.random() > 0.5;

        c.style.cssText = 'position:absolute;' +
            'left:' + x + 'px;top:-20px;' +
            'width:' + (isRect ? size * 2 : size) + 'px;' +
            'height:' + size + 'px;' +
            'background:' + color + ';' +
            'border-radius:' + (isRect ? '2px' : '50%') + ';' +
            'opacity:1;' +
            'transform:rotate(' + rotation + 'deg);' +
            'animation:confetti-fall ' + duration + 's ease-in ' + delay + 's forwards;';

        container.appendChild(c);
    }

    // Checkmark overlay
    var check = document.createElement('div');
    check.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);' +
        'width:100px;height:100px;border-radius:50%;' +
        'background:rgba(16,185,129,0.15);border:3px solid #10B981;' +
        'display:flex;align-items:center;justify-content:center;' +
        'animation:check-pop 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;' +
        'opacity:0;';
    check.innerHTML = '<i class="fas fa-check" style="color:#10B981;font-size:3rem;"></i>';
    container.appendChild(check);

    setTimeout(function() {
        check.style.opacity = '1';
    }, 200);

    setTimeout(function() {
        container.style.transition = 'opacity 0.5s';
        container.style.opacity = '0';
        setTimeout(function() { container.remove(); }, 500);
    }, 3000);
}

// ==========================================
// FIBRAS ATIVADAS COUNTER
// ==========================================
function animateCounter(element, target, duration) {
    if (!element) return;
    var start = 0;
    var startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        var current = Math.floor(eased * target);
        element.textContent = current.toLocaleString('pt-BR');
        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            element.textContent = target.toLocaleString('pt-BR');
        }
    }

    requestAnimationFrame(step);
}

// ==========================================
// CSS ANIMATIONS (injected dynamically)
// ==========================================
(function injectAnimationStyles() {
    var style = document.createElement('style');
    style.textContent = '' +
        '@keyframes xp-flash {' +
        '  0% { transform: scale(0); opacity: 1; }' +
        '  100% { transform: scale(3); opacity: 0; }' +
        '}' +
        '@keyframes xp-icon-pop {' +
        '  0% { transform: scale(0) rotate(-30deg); opacity: 0; }' +
        '  50% { transform: scale(1.3) rotate(5deg); opacity: 1; }' +
        '  100% { transform: scale(1) rotate(0deg); opacity: 0; }' +
        '}' +
        '@keyframes confetti-fall {' +
        '  0% { top: -20px; opacity: 1; }' +
        '  80% { opacity: 1; }' +
        '  100% { top: 110vh; opacity: 0; transform: rotate(720deg); }' +
        '}' +
        '@keyframes check-pop {' +
        '  0% { transform: translate(-50%,-50%) scale(0); }' +
        '  60% { transform: translate(-50%,-50%) scale(1.1); }' +
        '  100% { transform: translate(-50%,-50%) scale(1); }' +
        '}';
    document.head.appendChild(style);
})();
