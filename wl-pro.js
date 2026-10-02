/* =====================================================================
   旺來台股情報站 · 體驗層 wl-pro.js
   ---------------------------------------------------------------------
   只在瀏覽器端「重新編排與加動態」，不改任何資料內容：
   1. 首頁 Masthead：從 DATA:MARKET 讀加權指數，配 market.csv 畫走勢線
   2. 把 h2／sect-head 起頭的內容包成 <section>，桌機（≥1100px）排成主欄＋側欄
   3. 區塊捲入畫面時淡入；數字跳動（有開「減少動態」就全部略過）
   4. 標題前的表情符號換成一致的線條圖示
   排程只會改 index.html 的 DATA: 區塊，這支檔案不受影響。
   ===================================================================== */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var reduce = (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) || document.visibilityState !== "visible";
  var wrap = doc.querySelector(".wrap");
  if (!wrap) return;
  root.classList.add("pro");

  /* ---------- 小工具 ---------- */
  function el(tag, cls, html) { var e = doc.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function num(s) { var m = String(s || "").replace(/,/g, "").match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : NaN; }
  var ICON = {
    fire: '<path d="M12 3c1 3.5 4.5 5 4.5 9.5A4.5 4.5 0 0 1 12 17a4.5 4.5 0 0 1-4.5-4.5c0-2 1-3.2 2-4.2.3 1.6 1.1 2.5 2 2.7C11 8.6 11 5.8 12 3z"/><path d="M8 21h8"/>',
    chart: '<path d="M4 19h16"/><path d="M6 15l4-4 3 3 5-6"/><path d="M15 8h3v3"/>',
    warn: '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.2v.3"/>'
  };
  function svg(k) { return '<svg class="pro-ic" viewBox="0 0 24 24" aria-hidden="true">' + ICON[k] + "</svg>"; }
  var EMOJI = /^[\u{1F300}-\u{1FAFF}☀-➿⭐⭕]️?\s*/u;

  /* ---------- 1. 標題前的表情符號 → 線條圖示 ---------- */
  doc.querySelectorAll(".sect-head").forEach(function (h) {
    var t = h.firstChild;
    if (t && t.nodeType === 3 && EMOJI.test(t.nodeValue)) {
      var k = /營收/.test(h.textContent) ? "chart" : "fire";
      t.nodeValue = t.nodeValue.replace(EMOJI, "");
      h.insertAdjacentHTML("afterbegin", svg(k));
    }
  });

  // sect-head 是排程寫的一整串字：「資金流向 TOP 5（09/22 收盤．…）．點族群看…」
  // 拆成「主標」＋下一行的說明，跟其他 h2 的節奏一致
  doc.querySelectorAll(".sect-head").forEach(function (h) {
    for (var i = 0; i < h.childNodes.length; i++) {
      var t = h.childNodes[i];
      if (t.nodeType !== 3) continue;
      var v = t.nodeValue, k = v.indexOf("（");
      if (k > 0) {
        t.nodeValue = v.slice(0, k).trim();
        var sub = el("span", "muted sh-sub"); sub.textContent = v.slice(k).replace(/^（/, "").replace(/）/, "・").replace(/．/g, "・").replace(/・{2,}/g, "・").replace(/・\s*$/, "");
        h.appendChild(sub);
      }
      break;
    }
  });

  /* ---------- 2. 分段：h2 / .sect-head 起頭的內容包成 section ---------- */
  var heads = [];
  Array.prototype.forEach.call(wrap.children, function (c) {
    if (c.tagName === "H2" || c.classList.contains("sect-head")) heads.push(c);
  });
  var secs = [];
  heads.forEach(function (h, i) {
    var s = el("section", "sec");
    var key = h.id || (/營收/.test(h.textContent) ? "rev" : /資金流向|最強族群/.test(h.textContent) ? "sectors" : "sec" + i);
    s.setAttribute("data-k", key);
    wrap.insertBefore(s, h);
    var n = h;
    while (n && n !== heads[i + 1] && !(n.tagName === "FOOTER")) {
      var nx = n.nextSibling; s.appendChild(n); n = nx;
    }
    secs.push(s);
  });
  // 章節編號（01、02…）：只給有 h2 的主要區塊，讓閱讀有節奏
  var idx = 0, isHome = doc.body.classList.contains("home");
  if (isHome) secs.forEach(function (s) {
    var h = s.firstElementChild;
    if (s.getAttribute("data-k") === "mkt") return;  // 大盤數字已移到最上方的脈動列
    if (h && (h.tagName === "H2" || h.classList.contains("sect-head"))) {
      idx++;
      h.insertAdjacentHTML("afterbegin", '<span class="sec-no" aria-hidden="true">' + (idx < 10 ? "0" : "") + idx + "</span>");
    }
  });

  /* ---------- 3. 桌機兩欄 ---------- */
  var RAIL = { mkt: 1, watch: 1, sectors: 1, rev: 1, cal: 1 };
  if (secs.length && doc.body.classList.contains("home")) {
    var grid = el("div", "pro-grid"), main = el("div", "pro-main"), rail = el("aside", "pro-rail");
    rail.setAttribute("aria-label", "市場數據");
    wrap.insertBefore(grid, secs[0]);
    grid.appendChild(rail); grid.appendChild(main);
    secs.forEach(function (s) { (RAIL[s.getAttribute("data-k")] ? rail : main).appendChild(s); });
  }

  /* ---------- 4. 首頁「市場脈動列」：六個指標一排，每個一樣大 ---------- */
  function buildHero() {
    var cards = doc.querySelectorAll(".mkt .m");
    if (!cards.length || !doc.body.classList.contains("home")) return;
    var mktSec = doc.querySelector('.sec[data-k="mkt"]');
    var noteEl = mktSec && mktSec.querySelector("h2 .muted");
    var note = noteEl ? noteEl.textContent.replace(/^（|）$/g, "") : "";
    var stamp = (doc.getElementById("updated") || {}).textContent || "";
    var SHORT = { "加權指數": "加權指數", "成交值（上市）": "成交值", "融資餘額（上市）": "融資餘額", "費城半導體 SOX": "費半 SOX", "全市場擔保維持率": "擔保維持率", "信用風險戶數": "信用風險戶" };
    var tiles = Array.prototype.map.call(cards, function (c, i) {
      var lbl = (c.querySelector(".lbl") || {}).textContent || "";
      lbl = lbl.replace(/NEW/g, "").trim();
      var v = (c.querySelector(".val") || {}).textContent || "";
      var ch = c.querySelector(".chg"), chT = ch ? ch.textContent.trim() : "";
      var dir = ch && ch.classList.contains("up") ? "up" : ch && ch.classList.contains("down") ? "down" : "";
      var tip = chT.match(/（(.*)）/), chShort = chT.replace(/（.*$/, "").replace(/^較前日\s*/, "").replace(/^單日\s*/, "");
      var sub = c.querySelector(".sub");
      // 加權：顯示漲跌幅（%），點數放提示；其他：直接顯示變化量，箭頭已表示方向就拿掉正負號
      var shown = (tip && /%$/.test(tip[1])) ? tip[1] : chShort;
      if (dir) shown = shown.replace(/^[+\-−]\s*/, "");
      if (tip && /%$/.test(tip[1])) tip = [0, chT.replace(/（.*$/, "") + " 點"];
      var spark = /加權/.test(lbl) ? "tx" : /成交值/.test(lbl) ? "vol" : "";
      return '<div class="pt ' + dir + '"' + (tip || sub ? ' title="' + ((tip ? tip[1] : "") + (sub ? " " + sub.textContent : "")).trim() + '"' : "") + ">" +
        '<span class="pk">' + (SHORT[lbl] || lbl) + "</span>" +
        '<b class="pv">' + v.trim() + "</b>" +
        '<span class="pc">' + (dir === "up" ? "▲ " : dir === "down" ? "▼ " : "") + shown + "</span>" +
        (spark ? '<svg class="ps" data-s="' + spark + '" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true"></svg>' : "") +
        "</div>";
    }).join("");
    var hero = el("section", "pulse");
    hero.setAttribute("aria-label", "今日盤勢");
    hero.innerHTML =
      '<div class="p-head"><span class="p-dot"></span><b>' + stamp + '</b><span class="p-lab">市場脈動</span></div>' +
      '<div class="p-grid">' + tiles + "</div>" +
      (note ? '<button class="p-note" type="button" aria-expanded="false">資料說明：' + note + "</button>" : "");
    if (mktSec) mktSec.classList.add("pulsed");
    var anchor = doc.querySelector(".pro-grid") || secs[0];
    if (anchor) anchor.parentNode.insertBefore(hero, anchor);
    var annc = doc.getElementById("annc");
    if (annc && anchor) anchor.parentNode.insertBefore(annc, anchor);
    var nb = hero.querySelector(".p-note");
    if (nb) nb.addEventListener("click", function () { var o = nb.classList.toggle("open"); nb.setAttribute("aria-expanded", o); });
    // 迷你走勢：加權、成交值（market.csv）
    fetch("market.csv", { cache: "no-store" }).then(function (r) { return r.ok ? r.text() : ""; }).then(function (t) {
      var rows = t.split(/\r?\n/).slice(1).filter(function (l) { return /^\d{4}-\d\d-\d\d,/.test(l); });
      var col = function (k) {
        return rows.map(function (l) {
          if (k === "tx") return parseFloat(l.split(",")[1]);
          var m = l.match(/"([\d,\.]+)\s*億"/); return m ? parseFloat(m[1].replace(/,/g, "")) : NaN;
        }).filter(function (x) { return !isNaN(x); }).slice(-20);
      };
      hero.querySelectorAll(".ps").forEach(function (s) {
        var ys = col(s.getAttribute("data-s")); if (ys.length < 2) { s.remove(); return; }
        var mn = Math.min.apply(null, ys), mx = Math.max.apply(null, ys), rg = (mx - mn) || 1;
        var d = ys.map(function (y, i) { return (i ? "L" : "M") + (i / (ys.length - 1) * 100).toFixed(1) + " " + (25 - (y - mn) / rg * 22).toFixed(1); }).join(" ");
        s.innerHTML = '<path d="' + d + ' L100 28 L0 28 Z" class="psa"/><path d="' + d + '" class="psl"/>';
      });
    }).catch(function () {});
  }
  buildHero();

  /* ---------- 5. 捲入淡入 ---------- */
  if (!reduce && "IntersectionObserver" in window) {
    var targets = doc.querySelectorAll(".sec, .pulse");
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.04 });
    targets.forEach(function (t) {
      var r = t.getBoundingClientRect();
      if (r.top < innerHeight) t.classList.add("in"); else { t.classList.add("rvl"); io.observe(t); }
    });
  }

  /* ---------- 6. 摺疊展開加一點過場 ---------- */
  doc.addEventListener("toggle", function (e) {
    var d = e.target; if (!d || d.tagName !== "DETAILS" || !d.open || reduce) return;
    var body = d.lastElementChild; if (!body || body.tagName === "SUMMARY") return;
    body.animate && body.animate([{ opacity: 0, transform: "translateY(-4px)" }, { opacity: 1, transform: "none" }], { duration: 220, easing: "ease-out" });
  }, true);
})();

/* ---------- 線上人數顯示：人少時只顯示瀏覽數（真實數字，不灌水） ---------- */
(function () {
  "use strict";
  var ol = document.getElementById("olnum");
  if (!ol) return;
  var box = ol.parentNode, vwrap = document.getElementById("vwrap");
  var on = document.createElement("span"); on.className = "ol-on";
  // 把「●線上 N 人」包起來，方便整段收起
  var n = box.firstChild, stop = vwrap || null;
  while (n && n !== stop) { var nx = n.nextSibling; on.appendChild(n); n = nx; }
  box.insertBefore(on, box.firstChild);
  var today = document.createElement("span"); today.className = "ol-today";
  today.innerHTML = '<i class="sep">｜</i>今日瀏覽 <b>—</b>';
  box.insertBefore(today, vwrap);
  var MIN = 0;  // 旺來大大要求：線上人數一律顯示，不收起
  function chk() { var v = parseInt(ol.textContent, 10); box.classList.toggle("ol-low", !(v >= MIN)); }
  chk();
  if ("MutationObserver" in window) new MutationObserver(chk).observe(ol, { childList: true, characterData: true, subtree: true });
  var d = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10).replace(/-/g, "");
  fetch("https://abacus.jasoncameron.dev/hit/wanglai-daily-report/day" + d)
    .then(function (r) { return r.json(); })
    .then(function (j) { if (j && j.value) today.querySelector("b").textContent = Number(j.value).toLocaleString(); else today.style.display = "none"; })
    .catch(function () { today.style.display = "none"; });
})();
