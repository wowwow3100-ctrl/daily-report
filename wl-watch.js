/* =====================================================================
   旺來新聞站 · 自選股 wl-watch.js
   ---------------------------------------------------------------------
   自選清單存在「使用者自己的裝置」（瀏覽器 localStorage），
   不需要註冊或登入，也不會上傳到任何伺服器。
   換手機／換瀏覽器／清除瀏覽資料，清單就會不見（這是無帳號的代價）。
   個股報告頁負責加入／移除，首頁「我的自選」負責顯示今天的相關資訊。
   ===================================================================== */
(function () {
  "use strict";
  var K = "wl_watch", MAX = 30;

  function get() {
    try {
      var a = JSON.parse(localStorage.getItem(K) || "[]");
      return Array.isArray(a) ? a.filter(function (x) { return /^\d{4}[A-Z]?$/.test(x); }) : [];
    } catch (e) { return []; }
  }
  function set(a) {
    try { localStorage.setItem(K, JSON.stringify(a)); } catch (e) {}
    try { window.dispatchEvent(new CustomEvent("wlwatch", { detail: a })); } catch (e) {}
  }

  window.WLW = {
    MAX: MAX,
    list: get,
    has: function (c) { return get().indexOf(c) >= 0; },
    toggle: function (c) {
      var a = get(), i = a.indexOf(c);
      if (i >= 0) { a.splice(i, 1); set(a); return { ok: true, on: false }; }
      if (a.length >= MAX) return { ok: false, on: false, msg: "自選最多 " + MAX + " 檔，先移除幾檔再加。" };
      a.unshift(c); set(a); return { ok: true, on: true };
    },
    STAR: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l2.5 5.2 5.7.8-4.1 4 1 5.6L12 16.4l-5.1 2.7 1-5.6-4.1-4 5.7-.8z"/></svg>'
  };
})();
