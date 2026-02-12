// Service Worker - Biohacking Studio PWA
const CACHE_NAME = 'biostudio-v1';
const OFFLINE_URL = '/offline';

// Assets to pre-cache on install
const PRECACHE_ASSETS = [
    '/',
    '/offline',
    '/static/css/landing.css',
    '/static/js/gamification.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

// Install: pre-cache essential assets
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(PRECACHE_ASSETS);
        }).then(function() {
            return self.skipWaiting();
        })
    );
});

// Activate: clean old caches
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.filter(function(name) {
                    return name !== CACHE_NAME;
                }).map(function(name) {
                    return caches.delete(name);
                })
            );
        }).then(function() {
            return self.clients.claim();
        })
    );
});

// Fetch: network-first for API/pages, cache-first for static assets
self.addEventListener('fetch', function(event) {
    var request = event.request;

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip admin routes (always fresh)
    if (request.url.includes('/admin/')) return;

    var url = new URL(request.url);

    // Static assets: cache-first
    if (url.pathname.startsWith('/static/') ||
        url.hostname === 'cdn.jsdelivr.net' ||
        url.hostname === 'cdnjs.cloudflare.com') {
        event.respondWith(
            caches.match(request).then(function(cached) {
                if (cached) return cached;
                return fetch(request).then(function(response) {
                    if (response.ok) {
                        var responseClone = response.clone();
                        caches.open(CACHE_NAME).then(function(cache) {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }

    // HTML pages: network-first with offline fallback
    if (request.headers.get('Accept') && request.headers.get('Accept').includes('text/html')) {
        event.respondWith(
            fetch(request).then(function(response) {
                // Cache successful page responses
                if (response.ok) {
                    var responseClone = response.clone();
                    caches.open(CACHE_NAME).then(function(cache) {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            }).catch(function() {
                // Try cache, then offline page
                return caches.match(request).then(function(cached) {
                    return cached || caches.match(OFFLINE_URL);
                });
            })
        );
        return;
    }

    // API/other: network-first, silent fail
    event.respondWith(
        fetch(request).then(function(response) {
            if (response.ok) {
                var responseClone = response.clone();
                caches.open(CACHE_NAME).then(function(cache) {
                    cache.put(request, responseClone);
                });
            }
            return response;
        }).catch(function() {
            return caches.match(request);
        })
    );
});

// Push notifications
self.addEventListener('push', function(event) {
    var data = { title: 'Biohacking Studio', body: 'Voce tem uma notificacao!', icon: '/static/icons/icon-192x192.png' };

    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    var options = {
        body: data.body || data.message || '',
        icon: data.icon || '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/student/dashboard'
        },
        actions: []
    };

    // Add contextual actions based on notification type
    if (data.type === 'class_reminder') {
        options.actions = [
            { action: 'view', title: 'Ver Agendamento' },
            { action: 'dismiss', title: 'Dispensar' }
        ];
    } else if (data.type === 'xp_earned') {
        options.actions = [
            { action: 'view', title: 'Ver XP' },
            { action: 'dismiss', title: 'OK' }
        ];
    }

    event.waitUntil(
        self.registration.showNotification(data.title || 'Biohacking Studio', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    var url = '/student/dashboard';
    if (event.notification.data && event.notification.data.url) {
        url = event.notification.data.url;
    }

    if (event.action === 'dismiss') return;

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            // Focus existing window if available
            for (var i = 0; i < clientList.length; i++) {
                if (clientList[i].url.includes(url) && 'focus' in clientList[i]) {
                    return clientList[i].focus();
                }
            }
            // Open new window
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
