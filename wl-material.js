/* =====================================================================
   旺來新聞站 · 個股重大訊息 wl-material.js
   ---------------------------------------------------------------------
   在「今日焦點」下面獨立放一區：平常只顯示最新 5 則，其餘摺疊；
   點開可搜尋股名／代號／關鍵字、只看上市或上櫃、只看我的自選。
   資料：證交所／櫃買中心 OpenAPI 每日重大訊息（推送守護每小時抓，
   存在 data 分支 material/latest.json，累積最近 7 天）。
   ===================================================================== */
(function () {
  "use strict";
  var URL = "https://raw.githubusercontent.com/wowwow3100-ctrl/daily-report/data/material/latest.json";
  var SHOW = 5;
  var HOT = /(法說|財報|營收|盈餘|增資|減資|合併|併購|收購|處分|取得|股利|配息|庫藏股|澄清|停工|火災|訴訟|董事會決議|解散|下市|私募|轉換公司債)/;
  function esc(s) { return String(s || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function watch() { try { return JSON.parse(localStorage.getItem("wl_watch") || "[]").map(String); } catch (e) { return []; } }
  function md(d) { return d ? (+d.slice(5, 7)) + "/" + (+d.slice(8, 10)) : ""; }

  function itemHTML(x, w) {
    var hot = HOT.exec(x.title), star = w.indexOf(x.c) >= 0;
    return '<details class="mt-it' + (star ? " star" : "") + '"><summary>' +
      '<span class="mt-tm">' + md(x.d) + (x.t ? " " + x.t : "") + "</span>" +
      '<a class="mt-co" href="stocks.html?code=' + esc(x.c) + '">' + (star ? "★ " : "") + esc(x.n) + '<i>' + esc(x.c) + "</i></a>" +
      (hot ? '<span class="mt-tag">' + esc(hot[1]) + "</span>" : "") +
      '<span class="mt-tt">' + esc(x.title) + "</span></summary>" +
      '<div class="mt-bd">' + (x.body ? esc(x.body) : "（公告沒有附說明）") +
      '<div class="mt-src">' + (x.m === "L" ? "上市" : "上櫃") + (x.rule ? "．" + esc(x.rule) : "") + "．資料來源：公開資訊觀測站重大訊息</div></div></details>";
  }

  function build(data) {
    var h2b = document.getElementById("broker");
    if (!h2b || document.getElementById("material")) return;
    var anchor = h2b.closest(".sec") || h2b;
    var items = data.items || [];
    var days = {}; items.forEach(function (x) { days[x.d] = 1; });
    var sec = document.createElement(anchor.tagName === "SECTION" ? "section" : "div");
    if (anchor.classList && anchor.classList.contains("sec")) { sec.className = "sec"; sec.setAttribute("data-k", "material"); }
    sec.innerHTML =
      '<h2 id="material">個股重大訊息<span class="muted" style="font-size:.75rem;letter-spacing:0;">（上市櫃公告．最近 ' + Object.keys(days).length + " 個公告日．共 " + items.length + " 則）</span></h2>" +
      '<div class="card mtbox">' +
      '<div class="mt-bar"><input type="search" class="mt-q" placeholder="搜尋股名、代號或關鍵字（例：法說、增資）">' +
      '<div class="mt-chips"><button type="button" class="on" data-m="">全部</button><button type="button" data-m="L">上市</button><button type="button" data-m="O">上櫃</button><button type="button" data-m="W">★ 我的自選</button></div></div>' +
      '<div class="mt-list"></div></div>';
    anchor.parentNode.insertBefore(sec, anchor);
    var q = sec.querySelector(".mt-q"), list = sec.querySelector(".mt-list"), mode = "";
    function render() {
      var w = watch(), kw = q.value.trim().toLowerCase();
      var arr = items.filter(function (x) {
        if (mode === "L" || mode === "O") { if (x.m !== mode) return false; }
        if (mode === "W" && w.indexOf(x.c) < 0) return false;
        if (kw && (x.n + x.c + x.title + (x.rule || "")).toLowerCase().indexOf(kw) < 0) return false;
        return true;
      });
      // 自選股排前面（同一天內）
      arr.sort(function (a, b) { return a.d !== b.d ? (a.d < b.d ? 1 : -1) : ((w.indexOf(b.c) >= 0) - (w.indexOf(a.c) >= 0)) || (a.t < b.t ? 1 : -1); });
      if (!arr.length) { list.innerHTML = '<div class="stkempty">' + (mode === "W" ? "你的自選股最近 7 天沒有重大訊息（自選在「個股報告」點 ☆ 加入）" : "沒有符合的重大訊息") + "</div>"; return; }
      var head = arr.slice(0, SHOW), rest = arr.slice(SHOW);
      list.innerHTML = head.map(function (x) { return itemHTML(x, w); }).join("") +
        (rest.length ? '<details class="more mt-more"' + (kw || mode ? " open" : "") + '><summary>▾ 看全部 ' + arr.length + " 則（再看 " + rest.length + " 則）</summary>" +
          rest.slice(0, 400).map(function (x) { return itemHTML(x, w); }).join("") + "</details>" : "");
    }
    q.addEventListener("input", render);
    sec.querySelectorAll(".mt-chips button").forEach(function (b) {
      b.addEventListener("click", function () {
        mode = b.getAttribute("data-m");
        sec.querySelectorAll(".mt-chips button").forEach(function (x) { x.classList.toggle("on", x === b); });
        render();
      });
    });
    render();
  }

  function run() {
    fetch(URL + "?t=" + Math.floor(Date.now() / 600000)).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.items && d.items.length) setTimeout(function () { build(d); }, 300);
    }).catch(function () {});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
