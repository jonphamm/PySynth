// PySynth service worker — handles incoming web push events and notification
// clicks. Registered from the main thread in src/lib/push.ts.

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { body: event.data ? event.data.text() : "" };
  }

  const title = data.title || "PySynth";
  const options = {
    body: data.body || "Time for today's Python session.",
    icon: "/icon-192.png",
    badge: "/icon-192.png",
    data: { url: data.url || "/" },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || "/";

  event.waitUntil(
    (async () => {
      const windowClients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      // Focus an existing PySynth window if one's open
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin) && "focus" in client) {
          await client.focus();
          if ("navigate" in client) await client.navigate(targetUrl);
          return;
        }
      }
      // Otherwise open a fresh window
      if (self.clients.openWindow) {
        await self.clients.openWindow(targetUrl);
      }
    })()
  );
});
