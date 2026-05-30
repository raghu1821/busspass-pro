/* BusPass Pro — Service Worker (PWA offline support) */

const CACHE_NAME = 'buspass-v1';

// Files to cache for offline use (static assets only)
const STATIC_ASSETS = [
  '/static/style.css',
  '/static/toast.js',
  '/static/theme.js',
  '/static/manifest.json',
];

// ── Install: cache static assets ────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ── Activate: delete old caches ─────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: network first, fallback to cache ─────────────────
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // For static assets: cache first strategy
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        return cached || fetch(event.request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        });
      })
    );
    return;
  }

  // For pages: network first (so Flask data is always fresh)
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
