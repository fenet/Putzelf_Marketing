// Site Manager installability and a helpful fallback when navigating offline.
// The app's workflows require a live connection to save inspections and shifts.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || request.mode !== "navigate") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  const managerPaths = ["/site-manager", "/manager/inspections", "/schedule", "/admin/sites", "/admin/employees", "/admin/inspection-areas", "/resources"];
  if (!managerPaths.some((path) => url.pathname === path || url.pathname.startsWith(`${path}/`))) return;

  event.respondWith(
    fetch(request).catch(() => new Response(
      "<!doctype html><html lang='en'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Offline · Elf's Plan</title><body style='font:16px system-ui,sans-serif;background:#f5f7fb;color:#19233b;padding:2rem'><h1>You're offline</h1><p>Reconnect to manage sites, schedules, and inspections. Changes need an internet connection.</p></body></html>",
      { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } }
    ))
  );
});
