// --- Service Worker base per Gestione Code ---
// Versione cache: cambia questo numero ogni volta che aggiorni il codice
const CACHE_NAME = "gestione-code-v1";

// File da mettere in cache (puoi aggiungerne altri)
const FILES_TO_CACHE = [
  "/",
  "https://raw.githubusercontent.com/dull235/Gestione-code/main/manifest.json",
];

// --- Installazione: carica i file nella cache ---
self.addEventListener("install", event => {
  console.log("[Service Worker] Installazione in corso...");
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log("[Service Worker] Caching app shell");
        return cache.addAll(FILES_TO_CACHE);
      })
  );
  self.skipWaiting();
});

// --- Attivazione: rimuove le vecchie cache ---
self.addEventListener("activate", event => {
  console.log("[Service Worker] Attivazione...");
  event.waitUntil(
    caches.keys().then(keyList => {
      return Promise.all(keyList.map(key => {
        if (key !== CACHE_NAME) {
          console.log("[Service Worker] Rimuovo vecchia cache:", key);
          return caches.delete(key);
        }
      }));
    })
  );
  self.clients.claim();
});

// --- Intercetta le richieste e serve la cache se offline ---
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});

