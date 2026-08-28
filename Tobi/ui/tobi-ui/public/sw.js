/**
 * TOBI Service Worker  (Phase 0 PWA)
 *
 * Strategy:
 *  - App shell (HTML, JS, CSS): Cache-first with background revalidation
 *  - API calls (/Tobi-api/**, /Tobi-ws): Network-only (never cache live data)
 *  - Icons / static assets: Cache-first (long TTL)
 *  - Reminders: Listen for push events and show native notifications
 *
 * Push notification payload format:
 *   { title: string, body: string, reminder_id?: number, tag?: string,
 *     audio_url?: string, playback_mode?: "own_voice"|"tobi_voice" }
 */

const CACHE_NAME = "tobi-shell-v1";
const STATIC_CACHE = "tobi-static-v1";

// App-shell files to pre-cache on install
const APP_SHELL = [
  "/",
  "/manifest.json",
  "/icon-192.png",
  "/icon-512.png",
  "/favicon.ico",
];

// ─────────────────────────── Install ─────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// ─────────────────────────── Activate ────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== STATIC_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ─────────────────────────── Fetch ───────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Never intercept API, WebSocket, or cross-origin requests
  if (
    url.pathname.startsWith("/Tobi-api/") ||
    url.pathname.startsWith("/Tobi-ws") ||
    url.protocol === "chrome-extension:" ||
    !url.origin.startsWith(self.location.origin.split("//")[0])
  ) {
    return; // fall through to network
  }

  // Static assets (icons, fonts): cache-first
  if (
    url.pathname.startsWith("/icon-") ||
    url.pathname === "/favicon.ico" ||
    url.pathname === "/manifest.json" ||
    url.pathname.match(/\.(png|jpg|jpeg|svg|webp|woff2?|ttf)$/)
  ) {
    event.respondWith(
      caches.open(STATIC_CACHE).then((cache) =>
        cache.match(request).then(
          (hit) =>
            hit ||
            fetch(request).then((res) => {
              cache.put(request, res.clone());
              return res;
            })
        )
      )
    );
    return;
  }

  // App shell (HTML / Next.js pages): stale-while-revalidate
  if (request.mode === "navigate" || request.headers.get("accept")?.includes("text/html")) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) =>
        cache.match(request).then((hit) => {
          const networkFetch = fetch(request).then((res) => {
            cache.put(request, res.clone());
            return res;
          });
          return hit || networkFetch;
        })
      )
    );
    return;
  }

  // Next.js compiled JS/CSS chunks: cache-first (they're content-hashed)
  if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(
      caches.open(STATIC_CACHE).then((cache) =>
        cache.match(request).then(
          (hit) =>
            hit ||
            fetch(request).then((res) => {
              cache.put(request, res.clone());
              return res;
            })
        )
      )
    );
    return;
  }

  // Everything else: network with cache fallback
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

// ─────────────────────────── Push notifications ───────────────────────────────
self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (_) {
    data = { title: "TOBI", body: event.data?.text() ?? "You have a reminder." };
  }

  const title = data.title || "TOBI Reminder";
  const options = {
    body: data.body || data.message || "Tap to open TOBI.",
    icon: "/icon-192.png",
    badge: "/icon-96.png",
    tag: data.tag || `reminder-${data.reminder_id ?? Date.now()}`,
    requireInteraction: Boolean(data.is_alarm),
    silent: false,
    data: {
      reminder_id: data.reminder_id ?? null,
      audio_url: data.audio_url ?? null,
      playback_mode: data.playback_mode ?? "tobi_voice",
      url: data.action_url ?? "/",
    },
    actions: [
      { action: "dismiss", title: "Dismiss" },
      { action: "snooze",  title: "Snooze 10 min" },
    ],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// ─────────────────────────── Notification click ───────────────────────────────
self.addEventListener("notificationclick", (event) => {
  const { notification, action } = event;
  const { reminder_id, url: targetUrl } = notification.data || {};

  notification.close();

  if (action === "snooze" && reminder_id) {
    // Tell any open TOBI client to snooze this reminder
    event.waitUntil(
      self.clients
        .matchAll({ type: "window", includeUncontrolled: true })
        .then((clients) => {
          if (clients.length > 0) {
            clients[0].postMessage({ type: "SNOOZE_REMINDER", reminder_id, minutes: 10 });
            return clients[0].focus();
          }
          return self.clients.openWindow(targetUrl || "/");
        })
    );
    return;
  }

  if (action === "dismiss" && reminder_id) {
    event.waitUntil(
      self.clients
        .matchAll({ type: "window", includeUncontrolled: true })
        .then((clients) => {
          if (clients.length > 0) {
            clients[0].postMessage({ type: "DISMISS_REMINDER", reminder_id });
            return clients[0].focus();
          }
          return self.clients.openWindow(targetUrl || "/");
        })
    );
    return;
  }

  // Default: open / focus the app
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients) => {
        for (const client of clients) {
          if ("focus" in client) {
            client.postMessage({ type: "REMINDER_FIRED", reminder_id });
            return client.focus();
          }
        }
        return self.clients.openWindow(targetUrl || "/");
      })
  );
});

// ─────────────────────────── Background sync (future) ────────────────────────
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-reminders") {
    // Placeholder for background reminder sync when back online
    event.waitUntil(Promise.resolve());
  }
});
