/* =====================================================================
   旺來新聞站 · 資金流向即時補位 wl-sectors.js
   ---------------------------------------------------------------------
   GitHub Actions 每個交易日收盤後把證交所類股漲跌寫到 data 分支
   （tools/fetch_sectors.py）。這支程式讀那份資料，日期比頁面上的
   「資金流向 TOP 5（MM/DD 收盤）」新，就直接換成最新的。
   ===================================================================== */
(function () {
  "use strict";
  var URL = "https://raw.githubusercontent.com/wowwow3100-ctrl/daily-report/data/sectors/latest.json";
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function pct(p) {
    var cls = p > 0 ? ' class="up"' : (p < 0 ? ' class="down"' : "");
    return "<b" + cls + ">" + (p > 0 ? "+" : "") + p.toFixed(2) + "%</b>";
  }
  function md(s) { var m = String(s).match(/(\d{1,2})\/(\d{1,2})/); return m ? (+m[1]) * 100 + (+m[2]) : 0; }
  function run() {
    var heads = document.querySelectorAll(".sect-head"), head = null;
    for (var i = 0; i < heads.length; i++) if (/資金流向/.test(heads[i].textContent)) { head = heads[i]; break; }
    if (!head) return;
    var ol = head.nextElementSibling;
    if (!ol || !ol.classList.contains("sectlist")) return;
    fetch(URL + "?t=" + Math.floor(Date.now() / 300000)).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.top || !d.top.length || !d.label) return;
      var cur = head.textContent.match(/(\d{1,2}\/\d{1,2})\s*收盤/);
      if (cur && md(cur[1]) >= md(d.label)) return;
      head.innerHTML = head.innerHTML.replace(/\d{1,2}\/\d{1,2}(\s*收盤)/, d.label + "$1");
      ol.innerHTML = d.top.map(function (s, k) {
        return '<li><details class="stkbox"><summary><span class="sn">' + (k + 1) + '</span><span class="snm">' + esc(s.name) + "</span>" + pct(s.pct) + "</summary>" +
          '<ul class="stklist">' + (s.stocks || []).map(function (x) {
            return '<li><span class="stn">' + esc(x.n) + '</span><span class="stc">(' + esc(x.c) + ")</span>" + pct(x.p) + "</li>";
          }).join("") + "</ul></details></li>";
      }).join("");
      try { document.dispatchEvent(new CustomEvent("wl:sectors", { detail: d })); } catch (e) {}
    }).catch(function () {});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
