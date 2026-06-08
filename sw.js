const CACHE = 'vent-20260608-6';
const PRECACHE = [
  '/',
  '/catalog.html',
  '/critical.min.css?v=20260608-6',
  '/styles.min.css?v=20260608-6',
  '/catalog.min.css?v=20260608-6',
  '/fonts.min.css?v=20260608-6',
  '/icons.min.css?v=20260608-6',
  '/main.js?v=20260608-6',
  '/analytics.min.js?v=20260608-6',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => cached);

      return cached || network;
    }),
  );
});
