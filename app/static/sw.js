// Выключатель. До 21.09.2026 на этом домене жила «Дорожная карта» со своим
// service worker и PWA. Браузеры посетителей до сих пор держат его и просят
// обновление по адресу /sw.js — отдаём вот это: чистим кэш, снимаем регистрацию,
// перезагружаем открытые вкладки. Портфолио service worker не нужен.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
    await self.registration.unregister();
    const tabs = await self.clients.matchAll({ type: 'window' });
    tabs.forEach((t) => t.navigate(t.url));
  })());
});
