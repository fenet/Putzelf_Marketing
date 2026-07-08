// Admin PWA disabled intentionally.
// Keep this worker lightweight and self-removing so only the employee app
// remains the installable/offline PWA experience.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      try {
        const names = await caches.keys();
        await Promise.all(names.map((name) => caches.delete(name)));
      } catch (_) {
        // no-op
      }
      await self.clients.claim();
      await self.registration.unregister();
    })()
  );
});
