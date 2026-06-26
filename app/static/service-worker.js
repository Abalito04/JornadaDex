const CACHE_NAME = "jornadadex-static-v13";
const STATIC_ASSETS = [
  "/static/css/app.css?v=20260626-supervisor-dashboard-tabs",
  "/static/js/app.js",
  "/static/js/pwa.js",
  "/static/img/favicon.svg",
  "/static/img/pwa-icon-192.png",
  "/static/img/pwa-icon-512.png",
  "/static/img/pwa-maskable-192.png",
  "/static/img/pwa-maskable-512.png",
  "/static/manifest.webmanifest"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      fetch(event.request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      }).catch(() => caches.match(event.request))
    );
    return;
  }

  event.respondWith(fetch(event.request));
});
