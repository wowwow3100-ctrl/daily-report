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
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
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
        var sub = el("span", "muted sh-sub"); sub.textContent = v.slice(k).replace(/^（/, "").replace(/）/, "・").replace(/．/g, "・").replace(/・$/, "");
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

  /* ---------- 4. 首頁 Masthead ---------- */
  function buildHero() {
    var cards = doc.querySelectorAll(".mkt .m");
    if (!cards.length || !doc.body.classList.contains("home")) return;
    var get = function (re) {
      for (var i = 0; i < cards.length; i++) {
        var l = cards[i].querySelector(".lbl");
        if (l && re.test(l.textContent)) return cards[i];
      }
      return null;
    };
    var tx = get(/加權/); if (!tx) return;
    var val = tx.querySelector(".val").textContent.trim();
    var chgEl = tx.querySelector(".chg"), chg = chgEl ? chgEl.textContent.trim() : "";
    var up = chgEl && chgEl.classList.contains("up"), dn = chgEl && chgEl.classList.contains("down");
    var stamp = (doc.getElementById("updated") || {}).textContent || "";
    var mini = [[/成交值/, "成交值"], [/融資/, "融資餘額"], [/費城|SOX/, "費半 SOX"]].map(function (p) {
      var c = get(p[0]); if (!c) return "";
      var ch = c.querySelector(".chg");
      return '<div class="hm"><span class="hk">' + p[1] + '</span><b>' + c.querySelector(".val").textContent.trim() +
        "</b>" + (ch ? '<i class="' + ch.className.replace("chg", "").trim() + '">' + ch.textContent.trim().replace(/（.*$/, "") + "</i>" : "") + "</div>";
    }).join("");
    // 已經放進 Masthead 的四張卡，在下方速覽區就不重複顯示
    [tx, get(/成交值/), get(/融資/), get(/費城|SOX/)].forEach(function (c) { if (c) c.classList.add("in-hero"); });
    var hero = el("section", "hero");
    hero.setAttribute("aria-label", "今日盤勢");
    hero.innerHTML =
      '<div class="h-l">' +
        '<div class="h-eye"><span class="dot' + (up ? " up" : dn ? " dn" : "") + '"></span>' + stamp + '</div>' +
        '<div class="h-title">加權指數</div>' +
        '<div class="h-num" data-v="' + num(val) + '">' + val + "</div>" +
        '<div class="h-chg ' + (up ? "up" : dn ? "down" : "") + '">' + chg + "</div>" +
      "</div>" +
      '<div class="h-r"><svg class="spark" viewBox="0 0 320 110" aria-hidden="true"></svg>' +
        '<div class="h-cap">近期收盤走勢</div></div>' +
      '<div class="h-mini">' + mini + "</div>";
    var anchor = doc.querySelector(".pro-grid") || secs[0];
    if (anchor) anchor.parentNode.insertBefore(hero, anchor);
    var annc = doc.getElementById("annc");
    if (annc && anchor) anchor.parentNode.insertBefore(annc, anchor);
    // 走勢線：market.csv
    fetch("market.csv", { cache: "no-store" }).then(function (r) { return r.ok ? r.text() : ""; }).then(function (t) {
      var pts = t.split(/\r?\n/).slice(1).map(function (l) { return l.split(","); })
        .filter(function (c) { return /^\d{4}-\d\d-\d\d$/.test(c[0]) && !isNaN(parseFloat(c[1])); })
        .map(function (c) { return [c[0], parseFloat(c[1])]; });
      var last = num(val);
      if (pts.length && Math.abs(pts[pts.length - 1][1] - last) > 1 && !isNaN(last)) pts.push(["now", last]);
      pts = pts.slice(-40);
      var s = hero.querySelector(".spark");
      if (pts.length < 2) { hero.querySelector(".h-r").style.display = "none"; return; }
      var ys = pts.map(function (p) { return p[1]; }), mn = Math.min.apply(null, ys), mx = Math.max.apply(null, ys);
      var pad = (mx - mn) * 0.15 || 1; mn -= pad; mx += pad;
      var X = function (i) { return (i / (pts.length - 1)) * 316 + 2; };
      var Y = function (v) { return 104 - ((v - mn) / (mx - mn)) * 96; };
      var d = pts.map(function (p, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(p[1]).toFixed(1); }).join(" ");
      var lx = X(pts.length - 1), ly = Y(pts[pts.length - 1][1]);
      s.innerHTML =
        '<defs><linearGradient id="spg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="rgb(var(--gold-rgb))" stop-opacity=".35"/>' +
        '<stop offset="1" stop-color="rgb(var(--gold-rgb))" stop-opacity="0"/></linearGradient></defs>' +
        '<path class="sp-area" d="' + d + " L" + lx.toFixed(1) + " 110 L2 110 Z" + '" fill="url(#spg)"/>' +
        '<path class="sp-line" d="' + d + '" fill="none"/>' +
        '<circle class="sp-dot" cx="' + lx.toFixed(1) + '" cy="' + ly.toFixed(1) + '" r="3.6"/>';
      var cap = hero.querySelector(".h-cap");
      cap.textContent = "近 " + pts.length + " 個交易日收盤走勢";
      if (!reduce) {
        var line = s.querySelector(".sp-line"), L = line.getTotalLength ? line.getTotalLength() : 0;
        if (L) { line.style.strokeDasharray = L; line.style.strokeDashoffset = L; requestAnimationFrame(function () { line.style.transition = "stroke-dashoffset 1.4s cubic-bezier(.2,.7,.2,1)"; line.style.strokeDashoffset = 0; }); }
      }
    }).catch(function () { hero.querySelector(".h-r").style.display = "none"; });
    // 數字跳動
    var n = hero.querySelector(".h-num"), target = parseFloat(n.getAttribute("data-v"));
    if (!reduce && !isNaN(target)) {
      var t0 = null, from = target * 0.985, dec = (val.split(".")[1] || "").replace(/\D.*$/, "").length;
      var step = function (ts) {
        if (!t0) t0 = ts; var p = Math.min(1, (ts - t0) / 900), e = 1 - Math.pow(1 - p, 3);
        n.textContent = (from + (target - from) * e).toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
        if (p < 1) requestAnimationFrame(step); else n.textContent = val;
      };
      requestAnimationFrame(step);
    }
  }
  buildHero();

  /* ---------- 5. 捲入淡入 ---------- */
  if (!reduce && "IntersectionObserver" in window) {
    var targets = doc.querySelectorAll(".sec, .hero");
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
