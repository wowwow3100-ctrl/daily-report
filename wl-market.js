/* =====================================================================
   旺來新聞站 · 盤後信用數據校正 wl-market.js
   ---------------------------------------------------------------------
   融資餘額、擔保維持率、信用風險戶數改用證交所官方資料（推送守護在
   這台電腦每晚抓好，寫在 data 分支 market/latest.json），網頁打開時
   直接覆蓋首頁卡片與市場脈動列，並標出資料日期，避免排程抓到前一天
   的數字卻標成今天。
   ===================================================================== */
(function () {
  "use strict";
  var URL = "https://raw.githubusercontent.com/wowwow3100-ctrl/daily-report/data/market/latest.json";
  function fmt(n, d) { return Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }
  function sign(n, d) { return (n > 0 ? "+" : n < 0 ? "-" : "") + fmt(Math.abs(n), d); }

  function setCard(re, val, chgTxt, dir, sub) {
    document.querySelectorAll(".mkt .m").forEach(function (m) {
      var l = m.querySelector(".lbl"); if (!l || !re.test(l.textContent)) return;
      var v = m.querySelector(".val"), c = m.querySelector(".chg");
      if (v) v.textContent = val;
      if (c) { c.textContent = chgTxt; c.classList.remove("up", "down"); if (dir) c.classList.add(dir); }
      if (sub != null) { var s = m.querySelector(".sub"); if (!s) { s = document.createElement("div"); s.className = "sub"; m.appendChild(s); } s.textContent = sub; }
    });
    document.querySelectorAll(".pulse .pt").forEach(function (t) {
      var k = t.querySelector(".pk"); if (!k || !re.test(k.textContent)) return;
      var v = t.querySelector(".pv"), c = t.querySelector(".pc");
      if (v) v.textContent = val;
      if (c) c.textContent = (dir === "up" ? "▲ " : dir === "down" ? "▼ " : "") + chgTxt.replace(/^(單日|較前日)\s*/, "").replace(/^[+\-]\s*/, "").replace(/（.*$/, "");
      t.classList.remove("up", "down"); if (dir) t.classList.add(dir);
      if (sub != null) t.title = sub;
    });
  }

  function apply(d) {
    var tag = "（" + d.label + " 證交所）";
    function tagOf(x) { return x && x.label ? "（" + x.label + " " + (x.src || "證交所") + "）" : tag; }
    if (d.margin) {
      var g = d.margin.chg;
      setCard(/融資餘額/, fmt(Math.round(d.margin.bal), 0) + " 億", "單日 " + sign(g, 1) + " 億" + tagOf(d.margin), g > 0 ? "up" : g < 0 ? "down" : "", null);
    }
    if (d.keep) {
      var k = d.keep, tag2 = tagOf(k);
      if (k.rate) setCard(/擔保維持率/, fmt(k.rate, 2) + "%", "較前日 " + (k.rate_chg != null ? sign(k.rate_chg, 2) : "—") + tag2,
        k.rate_chg > 0 ? "up" : k.rate_chg < 0 ? "down" : "", null);
      if (k.risk != null) setCard(/信用風險戶/, fmt(k.risk, 0) + " 戶", "較前日 " + (k.risk_chg != null ? sign(k.risk_chg, 0) + " 戶" : "—") + tag2,
        k.risk_chg > 0 ? "up" : k.risk_chg < 0 ? "down" : "", "維持率不足 " + k.below + "｜追繳 " + k.call + "｜處分 " + k.exe);
    }
  }

  function run() {
    fetch(URL + "?t=" + Math.floor(Date.now() / 600000)).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.label) return;
      // 市場脈動列是 wl-pro.js 產生的，稍等它長出來再覆蓋一次
      apply(d); setTimeout(function () { apply(d); }, 800);
    }).catch(function () {});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
