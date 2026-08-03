const CACHE_NAME = 'v1.6.0';
const ASSETS_TO_CACHE = [
  '/',
  '/book.css',
  '/book.js',
  '/bootstrap5.1.1.bundle.min.js',
  '/bootstrap5.1.1.min.css',
  '/index.css',
  '/index.js',
  '/jquery-3.7.0.min.js',
  '/login.js',
  '/main.js',
  '/manifest.json',
  '/robots.txt',
  '/signup.js',
  '/img/book_192.png',
  '/img/book_512.png',
  '/img/favicon.ico',
  '/img/home.png'
];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        ASSETS_TO_CACHE.map((url) =>
          fetch(url).then((response) => {
            if (response.ok) {
              return cache.put(url, response);
            }
          }).catch((err) => console.warn('Failed to cache:', url, err))
        )
      );
    })
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});