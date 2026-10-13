/* =====================================================================
   旺來新聞站 · 券商摘要重點強化 wl-sum.js
   ---------------------------------------------------------------------
   排程每天會重寫「券商報告摘要」的文字（ul.sum-list），這支程式在前端
   把每一條整理成「股名大標＋代號＋動作標籤」，內文的目標價、評等、
   調升／下修、金額數字自動加粗上色。排程不用改格式，也不會被洗掉。
   ===================================================================== */
(function () {
  "use strict";
  var UPW = /(調升|升評|上修|升等|上調|調高)/, DNW = /(調降|降評|下修|降等|下調|調低)/, KEEPW = /(重申|維持|續抱)/;
  var RT_UP = /(買進|加碼|增持|優於大盤|強力買進|outperform|buy|overweight)/i, RT_DN = /(賣出|減碼|劣於大盤|underperform|sell|underweight)/i;

  function hlText(node) {
    // 只動純文字節點，連結、粗體標籤原樣保留
    var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, null), list = [], n;
    while ((n = walker.nextNode())) {
      if (n.parentNode && /^(A|SCRIPT)$/.test(n.parentNode.nodeName)) continue;
      list.push(n);
    }
    list.forEach(function (t) {
      var s = t.nodeValue, h = s
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/「([^」]{1,10})」/g, function (_, r) {
          var c = RT_UP.test(r) ? "up" : (RT_DN.test(r) ? "dn" : "");
          return '<span class="sl-rt ' + c + '">' + r + "</span>";
        })
        .replace(/(目標價\s*)([\d,]+(?:\.\d+)?\s*元)/g, '$1<b class="sl-tp">$2</b>')
        .replace(/([\d,]+(?:\.\d+)?\s*(?:兆|億)元?|[\d.]+\s*%)/g, '<b class="sl-n">$1</b>')
        .replace(new RegExp(UPW.source, "g"), '<span class="sl-up">▲$1</span>')
        .replace(new RegExp(DNW.source, "g"), '<span class="sl-dn">▼$1</span>');
      if (h !== s.replace(/&/g, "&amp;").replace(/</g, "&lt;")) {
        var span = document.createElement("span");
        span.innerHTML = h;
        t.parentNode.replaceChild(span, t);
      }
    });
  }


  // ---- 今日焦點：前 15 則直接顯示，第 16 則以後才摺疊 ----
  var SHOW = 15;
  function focusFold() {
    var det = document.querySelector("details.more");
    if (!det || det.getAttribute("data-ff")) return;
    det.setAttribute("data-ff", "1");
    var par = det.parentNode;
    // 摺疊裡的卡片先全部搬出來，排在摺疊前面
    [].slice.call(det.querySelectorAll(":scope > .card")).forEach(function (c) { par.insertBefore(c, det); });
    // 往前數同一層、在摺疊之前的新聞卡
    var cards = [], el = det.previousElementSibling;
    while (el && el.classList.contains("card") && el.querySelector(".news-title")) { cards.unshift(el); el = el.previousElementSibling; }
    var extra = cards.slice(SHOW);
    if (!extra.length) { det.remove(); return; }
    extra.forEach(function (c) { det.appendChild(c); });
    var sm = det.querySelector("summary");
    if (sm) sm.textContent = "▾ 更多焦點（再看 " + extra.length + " 則）";
  }
  function enhance() {
    document.querySelectorAll("ul.sum-list li").forEach(function (li) {
      if (li.getAttribute("data-sl")) return;
      li.setAttribute("data-sl", "1");
      var html = li.innerHTML;
      var m = html.match(/^\s*([^<（(：:，,\s]{1,12}?)\s*[（(](\d{4}[A-Z]?)[）)]\s*[：:]?\s*/);
      if (!m) { hlText(li); return; }
      var name = m[1], code = m[2], rest = html.slice(m[0].length);
      var plain = li.textContent;
      var badge = UPW.test(plain) ? '<span class="sl-badge up">調升</span>'
        : KEEPW.test(plain) ? '<span class="sl-badge">維持</span>'
        : DNW.test(plain) ? '<span class="sl-badge dn">下修</span>' : "";
      li.innerHTML =
        '<div class="sl-h"><a class="sl-nm" href="stocks.html?code=' + code + '">' + name + '</a>' +
        '<span class="sl-cd">' + code + "</span>" + badge + "</div>" +
        '<div class="sl-b">' + rest + "</div>";
      li.classList.add("sl-card");
      hlText(li.querySelector(".sl-b"));
    });
  }
  function run() { try { focusFold(); } catch (e) {} enhance(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
