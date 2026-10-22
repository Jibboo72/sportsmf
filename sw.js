/* SportsMF service worker.
   - The app page: network first, so every update shows up right away;
     the saved copy is only used when you're offline.
   - Fonts and team logos: served from the phone's cache after the first
     load, refreshed in the background.
   - Scores, odds and your data: never cached here; the app always asks
     for live data. */
const V = 'smf-v1';
const SHELL = ['./sportsmf.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V && k !== V + '-img').map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
async function trim(name, max){
  const c = await caches.open(name), ks = await c.keys();
  for (let i = 0; i < ks.length - max; i++) await c.delete(ks[i]);
}
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  /* the app itself */
  if (r.mode === 'navigate' || (u.origin === location.origin && /\/sportsmf\.html$/.test(u.pathname))){
    e.respondWith(fetch(r).then(res => {
      if (res.ok){ const cp = res.clone(); caches.open(V).then(c => c.put('./sportsmf.html', cp)); }
      return res;
    }).catch(() => caches.match('./sportsmf.html')));
    return;
  }
  /* the app's own icons and manifest: network, falling back to the saved copy */
  if (u.origin === location.origin && /\.(png|webmanifest)$/.test(u.pathname)){
    e.respondWith(fetch(r).catch(() => caches.match(r, {ignoreSearch: true})));
    return;
  }
  /* fonts and logos */
  const img = /(^|\.)espncdn\.com$/.test(u.hostname) && /\.(png|svg|jpg|jpeg|webp)/i.test(u.pathname);
  const font = u.hostname === 'fonts.googleapis.com' || u.hostname === 'fonts.gstatic.com';
  if (img || font){
    const name = img ? V + '-img' : V;
    e.respondWith(caches.open(name).then(async c => {
      const hit = await c.match(r);
      const net = fetch(r).then(res => { if (res && (res.ok || res.type === 'opaque')){ c.put(r, res.clone()); if (img) trim(name, 400); } return res; }).catch(() => hit);
      return hit || net;
    }));
  }
});
