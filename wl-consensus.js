/* =====================================================================
   旺來新聞站 · 券商共識統計 wl-consensus.js
   ---------------------------------------------------------------------
   讀 reports.csv（速查的原始紀錄），在瀏覽器裡即時算：
     - 每檔近 30 天有哪些「具名」券商上修（目標價調高、升等）
     - 每檔近 60 天各券商最新目標價 → 最低～最高區間（排除明顯異常值）
   首頁「券商共識追蹤」「資料交集」與個股頁「目標價區間」共用。
   排程不需要維護這支檔案，資料一更新就自動重算。
   ===================================================================== */
(function () {
  "use strict";

  function parseCSV(t) {
    var rows = [], row = [], f = "", q = false;
    for (var i = 0; i < t.length; i++) {
      var c = t[i];
      if (q) {
        if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else q = false; }
        else f += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(f); f = ""; }
      else if (c === "\n") { row.push(f); rows.push(row); row = []; f = ""; }
      else if (c !== "\r") f += c;
    }
    if (f || row.length) { row.push(f); rows.push(row); }
    return rows;
  }

  var UP = /上修|調升|調高|上調|升等|升評|提高目標/;
  var DN = /下修|調降|下調|降等|降評|調低/;
  // 不算「一家券商」的泛稱
  var GENERIC = { "法人": 1, "外資": 1, "內資": 1, "投信": 1, "投顧": 1, "美系外資": 1, "亞系外資": 1,
                  "歐系外資": 1, "日系外資": 1, "陸系外資": 1, "港系外資": 1, "市場數據": 1, "業界": 1 };

  // 「1、030 元」「1,030 元」都當 1030
  function clean(s) { return String(s || "").replace(/(\d)[、，](\d{3})/g, "$1$2").replace(/,/g, ""); }
  function num(s) { var m = clean(s).match(/(\d+(?:\.\d+)?)\s*元/); return m ? parseFloat(m[1]) : null; }
  function prev(s) { var m = clean(s).match(/前值\s*(\d+(?:\.\d+)?)/); return m ? parseFloat(m[1]) : null; }

  // 「瑞銀 UBS（★具名）」→ 瑞銀；「麥格理證券／摩根大通」→ [麥格理, 摩根大通]；未具名 → []
  function brokers(b) {
    if (/未具名|非券商|市場數據|重述|業界|供應鏈/.test(b)) return [];
    var s = b.split(/[（(]/)[0];
    return s.split(/[／\/＋+、]/).map(function (x) {
      return x.trim().replace(/\s+[A-Za-z].*$/, "").replace(/(證券|投顧|資本|集團)$/, "").trim();
    }).filter(function (x) { return x && !GENERIC[x]; });
  }

  function iso(d) { return d.toISOString().slice(0, 10); }

  function build(text) {
    var rows = parseCSV(text), head = rows.shift() || [], ix = {};
    head.forEach(function (k, i) { ix[k.replace(/^﻿/, "").trim()] = i; });
    var recs = [];
    rows.forEach(function (r) {
      if (r.length < 6) return;
      var o = { date: r[ix.date] || "", broker: r[ix.broker] || "", stock: r[ix.stock] || "",
                rating: r[ix.rating] || "", tp: r[ix.target_price] || "" };
      if (/方法論|收件匣/.test(o.broker + o.stock)) return;
      recs.push(o);
    });
    var maxd = recs.reduce(function (m, r) { return r.date > m ? r.date : m; }, "");
    if (!maxd) return { map: {}, maxd: "", c30: "" };
    var md = new Date(maxd + "T00:00:00Z");
    var c30 = iso(new Date(md - 30 * 864e5)), c60 = iso(new Date(md - 60 * 864e5));
    var S = {};
    recs.forEach(function (r) {
      if (r.date < c60) return;
      var re = /([^\/／()（）、,，;；:：\s]+?)\s*[（(](\d{4}[A-Z]?)[)）]/g, m, st = [];
      while ((m = re.exec(r.stock))) st.push([m[1], m[2]]);
      if (!st.length) return;
      var bs = brokers(r.broker), nw = num(r.tp), pv = prev(r.tp), rt = r.rating + " " + r.tp;
      var up = (nw && pv && nw > pv) || (UP.test(rt) && !DN.test(rt));
      st.forEach(function (p) {
        var d = S[p[1]] || (S[p[1]] = { code: p[1], name: p[0].replace(/\*$/, ""), up: {}, tg: {}, last: "" });
        if (r.date > d.last) d.last = r.date;
        // 一則報告點名超過 3 檔的「名單型」不算個股上修
        if (r.date >= c30 && up && st.length <= 3) {
          bs.forEach(function (b) { if (!d.up[b] || r.date > d.up[b]) d.up[b] = r.date; });
        }
        if (nw && st.length === 1) {
          var k = bs[0] || r.broker.slice(0, 12);
          if (!d.tg[k] || r.date >= d.tg[k][0]) d.tg[k] = [r.date, nw];
        }
        // 最新一筆券商觀點（給「我的自選」顯示用；名單型報告不算）
        if (st.length <= 3 && (!d.lastRec || r.date >= d.lastRec.date)) {
          var tidy = function (s) { return String(s || "").replace(/[（(]★[^）)]*[）)]/g, "").replace(/★/g, "").trim(); };
          d.lastRec = { date: r.date, broker: bs[0] || tidy(r.broker.split(/[（(]/)[0]) || "法人",
                        rating: tidy(r.rating), tp: nw };
        }
      });
    });
    Object.keys(S).forEach(function (c) {
      var d = S[c];
      var t = Object.keys(d.tg).map(function (k) { return d.tg[k][1]; }).sort(function (a, b) { return a - b; });
      if (t.length) {
        var med = t[Math.floor(t.length / 2)];
        t = t.filter(function (x) { return x >= med * 0.4 && x <= med * 2.5; });
      }
      d.range = t.length ? { lo: t[0], hi: t[t.length - 1], n: t.length } : null;
      d.upList = Object.keys(d.up).map(function (b) { return { b: b, d: d.up[b] }; })
        .sort(function (a, b) { return a.d < b.d ? 1 : -1; });
      d.upN = d.upList.length;
    });
    return { map: S, maxd: maxd, c30: c30 };
  }

  var P = null;
  window.WLC = {
    load: function () {
      if (!P) P = fetch("reports.csv", { cache: "no-store" })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(build);
      return P;
    },
    fmt: function (n) { return Number(n).toLocaleString("zh-TW", { maximumFractionDigits: 1 }); },
    md: function (s) { return s ? s.slice(5).replace("-", "/") : ""; }
  };
})();
