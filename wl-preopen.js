/* =====================================================================
   旺來新聞站 · 盤前快訊（雲端版）wl-preopen.js
   ---------------------------------------------------------------------
   盤前快訊改由雲端排程每天 06:40 抓好，寫在 data 分支
   preopen/latest.json，不再經過這台電腦。網頁打開時讀這份 JSON，
   比頁面上寫死的清單新就換上去；讀不到就保留原本的清單。
   ===================================================================== */
(function () {
  "use strict";
  var URL = "https://raw.githubusercontent.com/wowwow3100-ctrl/daily-report/data/preopen/latest.json";

  // 頁面上原本清單的時間（h2 裡的「（MM/DD HH:MM 更新…）」），換成 YYYY-MM-DD HH:MM 才能跟 JSON 比
  function staticStamp(h2, jsonStamp) {
    var m = h2 && /(\d{1,2})\/(\d{1,2})\s+(\d{1,2}):(\d{2})/.exec(h2.textContent || "");
    if (!m) return "";
    var y = parseInt(jsonStamp.slice(0, 4), 10);
    function p(n) { return ("0" + n).slice(-2); }
    var s = y + "-" + p(m[1]) + "-" + p(m[2]) + " " + p(m[3]) + ":" + m[4];
    if (s.slice(0, 7) > jsonStamp.slice(0, 7) && parseInt(m[1], 10) - parseInt(jsonStamp.slice(5, 7), 10) > 6) {
      s = (y - 1) + s.slice(4); // 跨年：頁面是 12 月、JSON 是 1 月
    }
    return s;
  }

  function apply(d) {
    var ul = document.querySelector("ul.prelist");
    if (!ul || !d || !d.updated || !d.label || !d.items || d.items.length < 3) return;
    var items = d.items.filter(function (it) {
      return it && it.title && /^https?:\/\//i.test(it.url || "");
    });
    if (items.length < 3) return;
    var h2 = document.getElementById("preopen");
    var old = staticStamp(h2, d.updated);
    if (old && old >= d.updated) return; // 頁面上的比較新（例如手動更新過），不要蓋掉

    var frag = document.createDocumentFragment();
    items.forEach(function (it) {
      var li = document.createElement("li");
      if (it.cat) { var c = document.createElement("span"); c.className = "cat"; c.textContent = it.cat; li.appendChild(c); }
      var a = document.createElement("a");
      a.href = it.url; a.target = "_blank"; a.rel = "noopener"; a.textContent = it.title;
      li.appendChild(a);
      if (it.src) { var s = document.createElement("span"); s.className = "psrc"; s.textContent = it.src; li.appendChild(s); }
      frag.appendChild(li);
    });
    ul.innerHTML = "";
    ul.appendChild(frag);

    var muted = h2 && h2.querySelector(".muted");
    if (muted) muted.textContent = "（" + d.label + " 更新．點標題看原文）";
    // 自選股區塊會掃盤前快訊找股票，換完清單通知它重算
    try { document.dispatchEvent(new CustomEvent("wl:preopen", { detail: d })); } catch (e) {}
  }

  function run() {
    fetch(URL + "?t=" + Math.floor(Date.now() / 300000))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(apply)
      .catch(function () {});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
