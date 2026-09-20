// 旺來新聞站 service worker (v1)
// 極簡版：只為了 PWA 可安裝性。不做快取（新聞站內容每天變，
// 快取舊聞比沒快取更糟），所有請求照常走網路。
self.addEventListener("install", function (e) { self.skipWaiting(); });
self.addEventListener("activate", function (e) { self.clients.claim(); });
self.addEventListener("fetch", function (e) { /* 交給瀏覽器預設網路行為 */ });
