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

  // ---- 導覽列 NEW：有新內容才亮，點進那一頁看過就消失，之後又有新內容會再亮 ----
  // 營收佈告欄：月份或「已公布家數」變了就算新（月初公司陸續公布，每多幾家都會亮）
  // 個股報告：最新一份報告的日期或檔數變了就算新
  var REV_META = "https://raw.githubusercontent.com/wowwow3100-ctrl/daily-report/data/revenue/meta.json";
  function navNew(href, key, getSig, red) {
    var a = document.querySelector('nav.bnav a[href="' + href + '"]');
    if (!a) return;
    var here = location.pathname.split("/").pop() === href;
    getSig().then(function (sig) {
      if (!sig) return;
      var seen = "";
      try { seen = localStorage.getItem(key) || ""; } catch (e) {}
      if (here) { try { localStorage.setItem(key, sig); } catch (e) {} return; }
      if (seen === sig || a.querySelector(".newdot,.revdot")) return;
      var b = document.createElement("span");
      b.className = red ? "revdot" : "newb newdot";
      b.textContent = "NEW";
      a.appendChild(b);
    }).catch(function () {});
  }
  function revSig() {
    return fetch(REV_META).then(function (r) { return r.json(); }).then(function (m) { return m && m.ym ? m.ym + ":" + m.n : ""; });
  }
  function stockSig() {
    return fetch("stocks.json").then(function (r) { return r.json(); }).then(function (j) {
      var mx = "", n = 0;
      (j.stocks || []).forEach(function (s) {
        n += (s.files || []).length;
        if (s.rec && s.rec > mx) mx = s.rec;
        (s.files || []).forEach(function (f) { var m = String(f).match(/^(\d{6})_/); if (m) { var d = "20" + m[1].slice(0, 2) + "-" + m[1].slice(2, 4) + "-" + m[1].slice(4, 6); if (d > mx) mx = d; } });
      });
      return mx + ":" + n;
    });
  }
  function revDot() {
    navNew("revenue.html", "wl_rev_sig", revSig, true);
    navNew("stocks.html", "wl_stk_sig", stockSig, false);
  }


  // ---- 浮誇主題：切過去的那一下撒一陣 🍍 ----
  function pineRain(){
    if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    for (var i = 0; i < 28; i++) (function(i){
      setTimeout(function(){
        var p = document.createElement("span");
        p.className = "fx-pine"; p.textContent = "🍍";
        p.style.left = (Math.random() * 96) + "vw";
        p.style.fontSize = (18 + Math.random() * 22) + "px";
        p.style.animationDuration = (2.2 + Math.random() * 2.2) + "s";
        document.body.appendChild(p);
        setTimeout(function(){ p.remove(); }, 5000);
      }, i * 60);
    })(i);
  }
  try {
    var lastTh = document.documentElement.getAttribute("data-theme");
    new MutationObserver(function(){
      var t = document.documentElement.getAttribute("data-theme");
      if (t === "fx" && lastTh !== "fx") pineRain();
      lastTh = t;
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  } catch (e) {}
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { apply(); revDot(); });
  else { apply(); revDot(); }
  // 有些區塊是資料載入後才畫出來的，稍後再補掛一次
  setTimeout(apply, 1500);
})();
