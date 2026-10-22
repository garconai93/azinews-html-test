// Service Worker pentru AziNews PWA
// Rețea întâi pentru pagină și ultimele știri; cache doar ca rezervă offline.
const CACHE_NAME = 'azinews-v5';
const OFFLINE_URLS = ['./', 'index.html', 'data/latest.json', 'data/horoscope.json', 'manifest.json', 'icon-192.png'];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(OFFLINE_URLS)).catch(() => {})
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const req = event.request;
    if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;
    const url = new URL(req.url);
    // arhiva și indexul de căutare nu se pun în cache (sunt mari și se cer rar)
    if (url.pathname.includes('/data/archive/') || url.pathname.includes('/data/search/')) return;

    event.respondWith(
        fetch(req)
            .then(response => {
                if (response.ok) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(req, copy));
                }
                return response;
            })
            .catch(() => caches.match(req).then(r => r || caches.match('index.html')))
    );
});
