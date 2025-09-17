const CACHE_NAME = 'v1.3.2';
const ASSETS_TO_CACHE = ['/', '/book.css', '/book.js', '/index.css', '/index.js', '/main.js', '/manifest.json', '/robots.txt', '/img/book_192.png', '/img/book_512.png', '/img/favicon.ico', '/img/home.png'];
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