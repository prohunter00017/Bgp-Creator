// Service Worker for Slither Io
// Progressive Web App caching strategy with automatic cache management

const CACHE_NAME = 'slither-io-v1';
const urlsToCache = [
  '/',
  '/offline.html',
  '/404.html',
  '/assets/css/styles.css',
  '/assets/js/main.js',
  '/logo.png',
  '/favicon.ico'
];

// Install event - cache initial assets
self.addEventListener('install', (event) => {
  // Skip waiting to activate immediately
  self.skipWaiting();
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete all old caches that don't match current version
          if (cacheName !== CACHE_NAME && cacheName.startsWith('slither-io-')) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Take control of all pages immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache or network with offline fallback
self.addEventListener('fetch', (event) => {
  // Only handle HTTP/HTTPS requests
  if (!event.request.url.startsWith('http')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // For CSS files, always try to fetch fresh first
        if (event.request.url.includes('.css')) {
          return fetch(event.request)
            .then((networkResponse) => {
              // Cache the fresh CSS for next time
              if (networkResponse && networkResponse.status === 200) {
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(event.request, responseToCache);
                });
              }
              return networkResponse;
            })
            .catch(() => {
              // If network fails, return cached version or empty CSS
              return response || new Response('/* Offline - CSS unavailable */', {
                headers: { 'Content-Type': 'text/css' }
              });
            });
        }
        
        // For navigation requests (HTML pages)
        if (event.request.mode === 'navigate') {
          return response || fetch(event.request)
            .then((networkResponse) => {
              // Cache successful responses
              if (networkResponse && networkResponse.status === 200) {
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(event.request, responseToCache);
                });
              }
              return networkResponse;
            })
            .catch(() => {
              // Return offline page for failed navigation requests
              return caches.match('/offline.html')
                .then((offlineResponse) => {
                  if (offlineResponse) {
                    return offlineResponse;
                  }
                  // Fallback if offline page is not cached
                  return new Response('You are offline', {
                    status: 503,
                    statusText: 'Service Unavailable',
                    headers: { 'Content-Type': 'text/html' }
                  });
                });
            });
        }
        
        // For all other requests
        return response || fetch(event.request)
          .catch(() => {
            // Return appropriate fallback for different resource types
            if (event.request.url.endsWith('.js')) {
              return new Response('// Offline - JavaScript unavailable', {
                headers: { 'Content-Type': 'application/javascript' }
              });
            }
            if (event.request.url.match(/\.(png|jpg|jpeg|gif|webp|svg|ico)$/i)) {
              // Return a transparent 1x1 pixel for images
              return new Response('', {
                headers: { 'Content-Type': 'image/gif' }
              });
            }
            // Default offline response
            return new Response('Resource unavailable offline', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});