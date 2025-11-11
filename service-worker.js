self.addEventListener('install', function(event) {
    console.log('Service Worker installato');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker attivo');
    return self.clients.claim();
});

self.addEventListener('fetch', function(event) {
    // Qui puoi gestire caching se vuoi
});
