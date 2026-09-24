/* =====================================================================
   旺來新聞站 · NEW 標記 wl-new.js
   ---------------------------------------------------------------------
   在新功能旁邊掛一個金色「NEW」小徽章，到期日一過就自動不顯示，
   不用再回來手動拿掉。用「找元素＋比對文字」的方式掛上去，
   所以排程每天重寫資料區塊也不會把標記洗掉。
   要加新標記：在 RULES 加一行 {sel:"CSS 選擇器", text:"要包含的字", until:"YYYY-MM-DD"}
   ===================================================================== */
(function () {
  "use strict";
  var RULES = [
    // 09/24 上線：自選股
    { sel: "h2#watch", until: "2026-10-08" },
    { sel: '.vtab[data-v="watch"]', until: "2026-10-08" },
    { sel: 'nav.bnav a[href="stocks.html"]', until: "2026-10-08", dot: true },
    // 09/24 上線：本週行事曆、資料交集
    { sel: "h2#cal", until: "2026-10-01" },
    { sel: "h2#overlap", until: "2026-10-01" },
    // 09/23 上線：上市櫃月營收、擔保維持率、信用風險戶數
    { sel: ".sect-head", text: "上市櫃月營收", until: "2026-10-01" },
    { sel: ".mkt .lbl", text: "擔保維持率", until: "2026-10-01" },
    { sel: ".mkt .lbl", text: "信用風險戶數", until: "2026-10-01" }
  ];

  function today() {
    var d = new Date(), m = d.getMonth() + 1, dd = d.getDate();
    return d.getFullYear() + "-" + (m < 10 ? "0" : "") + m + "-" + (dd < 10 ? "0" : "") + dd;
  }

  function badge(dot) {
    var b = document.createElement("span");
    b.className = dot ? "newb newdot" : "newb";
    b.textContent = "NEW";
    return b;
  }

  function apply() {
    var t = today();
    RULES.forEach(function (r) {
      if (r.until && t > r.until) return;
      document.querySelectorAll(r.sel).forEach(function (el) {
        if (r.text && el.textContent.indexOf(r.text) < 0) return;
        if (el.querySelector(".newb")) return;
        var b = badge(r.dot);
        var sub = el.tagName === "H2" ? el.querySelector(".muted") : null;
        if (sub) el.insertBefore(b, sub); else el.appendChild(b);
      });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
  // 有些區塊是資料載入後才畫出來的，稍後再補掛一次
  setTimeout(apply, 1500);
})();
