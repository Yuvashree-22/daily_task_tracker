const CACHE_NAME = 'task-tracker-cache-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/dashboard/home',
  '/task/entry',
  '/task/history',
  '/task/pending',
  '/task/completed',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Install SW
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
});

// Fetch cache
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(resp => {
      return resp || fetch(event.request);
    })
  );
});