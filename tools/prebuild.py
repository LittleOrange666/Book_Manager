import os
import sys
template = """self.addEventListener('install', (e) => {
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
});"""
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python prebuild.py <version>")
        sys.exit(1)
    version = sys.argv[1]
    print(f"Prebuilding service worker for version {version}")
    arr = ["/"]
    for f in os.listdir("static"):
        if f != "ws.js":
            arr.append(f"/{f}")
    a = "[" + ", ".join(repr(s) for s in arr) + "]"
    txt = f"const CACHE_NAME = '{version}';\nconst ASSETS_TO_CACHE = {a};\n"+template
    with open("static/ws.js", "w", encoding="utf-8") as f:
        f.write(txt)
    print("Service worker prebuilt successfully.")

