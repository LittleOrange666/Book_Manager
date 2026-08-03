import os
import sys

template = """self.addEventListener('install', (e) => {
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
});"""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python prebuild.py <version>")
        sys.exit(1)
    version = sys.argv[1]
    print(f"Prebuilding service worker for version {version}")
    arr = ["/"]
    for dirname, _, files in os.walk("static"):
        for f in files:
            if f != "sw.js":
                rel = os.path.relpath(os.path.join(dirname, f), "static").replace("\\", "/")
                arr.append(f"/{rel}")
    a = "[\n  " + ",\n  ".join(repr(s) for s in arr) + "\n]"
    txt = f"const CACHE_NAME = '{version}';\nconst ASSETS_TO_CACHE = {a};\n\n" + template
    with open("static/sw.js", "w", encoding="utf-8") as f:
        f.write(txt)
    print("Service worker prebuilt successfully.")


