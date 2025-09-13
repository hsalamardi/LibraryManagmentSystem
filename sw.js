self.addEventListener('install', function(event) {
  console.log('Service Worker installing.');
});

self.addEventListener('activate', function(event) {
  console.log('Service Worker activating.');
});

self.addEventListener('fetch', function(event) {
  // This is a basic service worker. For now, it just passes requests through.
  // You can add caching logic here later.
  event.respondWith(fetch(event.request));
});