const CACHE_NAME = 'v1.4.17';
const ASSETS_TO_CACHE = ['/', '/book.css', '/book.js', '/bootstrap5.1.1.bundle.min.js', '/bootstrap5.1.1.min.css', '/index.css', '/index.js', '/jquery-3.7.0.min.js', '/login.js', '/main.js', '/manifest.json', '/robots.txt', '/signup.js', '/img/book_192.png', '/img/book_512.png', '/img/favicon.ico', '/img/home.png'];
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});