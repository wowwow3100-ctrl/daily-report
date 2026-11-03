/* =====================================================================
   旺來新聞站 · 盤後信用數據校正 wl-market.js  (v6, 2026-11-02)
   ---------------------------------------------------------------------
   融資餘額、擔保維持率、信用風險戶數改用證交所官方資料（推送守護在
   這台電腦每晚抓好，寫在 data 分支 market/latest.json），網頁打開時
   直接覆蓋首頁卡片與市場脈動列，並標出資料日期，避免排程抓到前一天
   的數字卻標成今天。
   v5：市場脈動多一塊「生命線失守比例」，資料在 market/latest.json 的 breadth。
   v6：改成研究版算法——20 日均量 1,000 張以上的上市櫃普通股、還原收盤價，
   由這台電腦的旺來資料庫每天盤後自動算好（wanglai-db/daily_breadth.py）；
   台股生命線 App 的大盤檢查讀同一份。燈號：40% 以下綠、40～60% 黃、60% 以上紅。
   ===================================================================== */
(function () {
  "use strict";
  var URL = "https://raw.githubusercontent.com/wowwow3100-ctrl/daily-report/data/market/latest.json";
  function fmt(n, d) { return Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }
  function sign(n, d) { return (n > 0 ? "+" : n < 0 ? "-" : "") + fmt(Math.abs(n), d); }

  function setCard(re, val, chgTxt, dir, sub, pulseTxt) {
    document.querySelectorAll(".mkt .m").forEach(function (m) {
      var l = m.querySelector(".lbl"); if (!l || !re.test(l.textContent)) return;
      var v = m.querySelector(".val"), c = m.querySelector(".chg");
      if (v) v.textContent = val;
      if (c) { c.textContent = chgTxt; c.classList.remove("up", "down"); if (dir) c.classList.add(dir); }
      if (sub != null) { var s = m.querySelector(".sub"); if (!s) { s = document.createElement("div"); s.className = "sub"; m.appendChild(s); } s.textContent = sub; }
    });
    document.querySelectorAll(".pulse .pt").forEach(function (t) {
      var k = t.querySelector(".pk"); if (!k || !re.test(k.textContent)) return;
      if (t.classList.contains("pt-br")) return;
      var v = t.querySelector(".pv"), c = t.querySelector(".pc");
      if (v) v.textContent = val;
      if (c) c.textContent = (dir === "up" ? "▲ " : dir === "down" ? "▼ " : "") + (pulseTxt != null ? pulseTxt : chgTxt.replace(/^(單日|較前日)\s*/, "").replace(/^[+\-]\s*/, "").replace(/（.*$/, ""));
      t.classList.remove("up", "down"); if (dir) t.classList.add(dir);
      if (sub != null) t.title = sub;
    });
  }

  function dirOf(n) { return n > 0 ? "up" : n < 0 ? "down" : ""; }

  function applyIndex(d) {
    var ix = d.index, sx = d.sox, notes = [];
    if (ix) {
      setCard(/加權指數/, fmt(Math.round(ix.close), 0), sign(ix.chg, 2) + "（" + sign(ix.pct, 2) + "%）", dirOf(ix.chg), null, sign(ix.pct, 2).replace(/^[+\-]/, "") + "%");
      if (ix.amt) setCard(/成交值/, fmt(ix.amt, 0) + " 億", "較前日 " + (ix.amt_pct != null ? sign(ix.amt_pct, 1) + "%" : "—") + "（" + ix.label + " 證交所" + (ix.amt_prev ? "；前日 " + fmt(ix.amt_prev, 0) + " 億" : "") + "）", dirOf(ix.amt_pct || 0), null);
      notes.push("加權指數、成交值為 " + ix.label + " 收盤");
    }
    if (sx) {
      setCard(/費城半導體|SOX/, fmt(Math.round(sx.close), 0), sign(sx.pct, 2) + "%（" + sx.label + " 美股收盤，前日 " + sign(sx.prev_pct, 2) + "%）", dirOf(sx.pct), null, sign(sx.pct, 2).replace(/^[+\-]/, "") + "%");
      notes.push("SOX 為 " + sx.label + " 美股收盤");
    }
    if (d.label) notes.push("融資、維持率、風險戶為 " + d.label + " 證交所資料");
    if (d.breadth && d.breadth.label) notes.push("生命線失守比例為 " + d.breadth.label + " 收盤、成交量千張以上個股、還原價計算");
    if (!notes.length) return;
    var txt = "（" + notes.join("；") + "）";
    var h = document.getElementById("mkt"), m = h && h.querySelector(".muted");
    if (m) m.textContent = txt;
    var pn = document.querySelector(".pulse .p-note");
    if (pn) pn.textContent = "資料說明：" + txt.replace(/^（|）$/g, "");
  }

  /* ---------- v5：生命線失守比例 ---------- */
  var LIGHT = { g: ["綠燈", "多數個股在線上"], y: ["黃燈", "個股分歧"], r: ["紅燈", "個股在殺"] };
  function lightOf(p) { return p < 40 ? "g" : p < 60 ? "y" : "r"; }   // 研究版的尺，跟台股生命線 App 大盤檢查同一把

  function injectCss() {
    if (document.getElementById("wl-br-css")) return;
    var st = document.createElement("style");
    st.id = "wl-br-css";
    st.textContent = [
      ".pt.pt-br{grid-column:1/-1;display:grid;grid-template-columns:minmax(118px,auto) minmax(0,1fr) auto;grid-template-areas:'l mid sp';align-items:center;column-gap:20px;row-gap:8px;}",
      ".pt-br .br-l{grid-area:l;display:flex;flex-direction:column;gap:2px;min-width:0;}",
      ".pt-br .br-mid{grid-area:mid;min-width:0;display:flex;flex-direction:column;gap:7px;}",
      ".pt-br .br-sp{grid-area:sp;display:flex;flex-direction:column;align-items:flex-end;gap:2px;}",
      ".pt-br .br-sp svg{display:block;width:128px;height:34px;}",
      ".pt-br .br-sp .psl{fill:none;stroke:rgb(var(--gold-rgb));stroke-width:1.6;vector-effect:non-scaling-stroke;stroke-linejoin:round;}",
      ".pt-br .br-sp .psa{fill:rgba(var(--gold-rgb),.12);}",
      ".pt-br .br-sp .dot{fill:rgb(var(--gold-rgb));}",
      ".pt-br .br-cap{font-size:.62rem;color:var(--muted);letter-spacing:1px;white-space:nowrap;}",
      ".pt-br .br-bar{position:relative;height:9px;border-radius:99px;background:rgba(var(--gold-rgb),.13);overflow:visible;}",
      ".pt-br .br-bar i{position:absolute;left:0;top:0;bottom:0;border-radius:99px;background:var(--br-c,var(--gold));transition:width .8s cubic-bezier(.2,.7,.2,1);}",
      ".pt-br .br-bar s{position:absolute;top:-3px;bottom:-3px;width:1px;background:var(--muted);opacity:.55;text-decoration:none;}",
      ".pt-br .br-scale{position:relative;height:12px;font-size:.58rem;color:var(--muted);font-family:var(--num);}",
      ".pt-br .br-scale span{position:absolute;top:0;transform:translateX(-50%);white-space:nowrap;}",
      ".pt-br .br-meta{display:flex;flex-wrap:wrap;align-items:center;gap:4px 12px;font-size:.7rem;color:var(--muted);line-height:1.5;}",
      ".pt-br .br-meta b{color:var(--text);font-family:var(--num);font-weight:700;}",
      ".pt-br .br-lt{display:inline-flex;align-items:center;gap:6px;padding:1px 9px 1px 7px;border-radius:99px;border:1px solid var(--br-c,var(--edge));color:var(--text);font-weight:700;white-space:nowrap;}",
      ".pt-br .br-lt::before{content:'';width:7px;height:7px;border-radius:50%;background:var(--br-c,var(--muted));box-shadow:0 0 0 3px rgba(127,127,127,.12);}",
      ".pt-br .br-link{color:var(--gold);text-decoration:none;white-space:nowrap;}",
      ".pt-br .br-link:hover{text-decoration:underline;}",
      ".pt-br.lt-g{--br-c:var(--down);} .pt-br.lt-y{--br-c:var(--gold);} .pt-br.lt-r{--br-c:var(--up);}",
      "@media (max-width:759px){.pt.pt-br{grid-template-columns:minmax(0,auto) minmax(0,1fr);grid-template-areas:'l sp' 'mid mid';column-gap:12px;}.pt-br .br-sp svg{width:112px;height:30px;}}",
      "html.mob .pt.pt-br{grid-template-columns:minmax(0,auto) minmax(0,1fr);grid-template-areas:'l sp' 'mid mid';column-gap:12px;}",
      "html.mob .pt-br .br-sp svg{width:112px;height:30px;}"
    ].join("\n");
    document.head.appendChild(st);
  }

  function sparkPath(ys) {
    var mn = Math.min.apply(null, ys), mx = Math.max.apply(null, ys), rg = (mx - mn) || 1;
    var pts = ys.map(function (y, i) { return [(i / (ys.length - 1) * 100), (30 - (y - mn) / rg * 24)]; });
    var d = pts.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" ");
    return { line: d, area: d + " L100 34 L0 34 Z", last: pts[pts.length - 1], mn: mn, mx: mx };
  }

  function applyBreadth(d) {
    var b = d.breadth;
    if (!b || b.pct == null || isNaN(Number(b.pct))) return;
    var pct = Number(b.pct), lt = lightOf(pct), L = LIGHT[lt].slice();
    if (pct >= 80) L[1] = "全面跌破";
    var chg = b.chg_pp, dir = chg > 0 ? "up" : chg < 0 ? "down" : "";
    var chgTxt = chg == null ? "—" : (dir === "up" ? "▲ " : dir === "down" ? "▼ " : "持平 ") + (chg ? fmt(Math.abs(chg), 1) + " 個百分點" : "");
    var counts = "成交量千張以上 " + fmt(b.n, 0) + " 檔中 <b>" + fmt(b.below, 0) + "</b> 檔收在生命線下";
    var tip = "近 20 日均量 1,000 張以上的上市櫃普通股，還原收盤價低於生命線的比例（<40% 綠、40～60% 黃、≥60% 紅；80% 以上＝全市場一起跌破）｜" +
      fmt(b.n, 0) + " 檔中 " + fmt(b.below, 0) + " 檔在線下｜" + (b.label || "") + " 收盤" +
      (b.all_pct != null ? "｜全部上市櫃（不分量能）" + fmt(b.all_pct, 1) + "%" : "") + "｜與台股生命線 App 大盤檢查同一份數字";
    var grid = document.querySelector(".pulse .p-grid");
    if (grid) {
      injectCss();
      var t = grid.querySelector(".pt-br");
      if (!t) { t = document.createElement("div"); grid.appendChild(t); }
      t.className = "pt pt-br lt-" + lt + (dir ? " " + dir : "");
      t.setAttribute("data-k", "breadth");
      t.title = tip;
      var hist = (b.hist || []).map(Number).filter(function (x) { return !isNaN(x); });
      var sp = "";
      if (hist.length >= 3) {
        var s = sparkPath(hist);
        sp = '<div class="br-sp"><svg viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true"><path class="psa" d="' + s.area + '"/><path class="psl" d="' + s.line + '"/></svg>' +
          '<span class="br-cap">近 ' + hist.length + " 日 " + fmt(s.mn, 0) + "～" + fmt(s.mx, 0) + "%</span></div>";
      }
      t.innerHTML =
        '<div class="br-l"><span class="pk">生命線失守比例</span><b class="pv">' + fmt(pct, 1) + '%</b><span class="pc">' + chgTxt + "</span></div>" +
        '<div class="br-mid">' +
          '<div class="br-bar" role="img" aria-label="失守比例 ' + fmt(pct, 1) + '%"><i style="width:' + Math.max(0, Math.min(100, pct)) + '%"></i><s style="left:40%"></s><s style="left:60%"></s><s style="left:80%"></s></div>' +
          '<div class="br-scale" aria-hidden="true"><span style="left:0;transform:none">0</span><span style="left:40%">40</span><span style="left:60%">60</span><span style="left:80%">80</span><span style="left:100%;transform:translateX(-100%)">100%</span></div>' +
          '<div class="br-meta"><span class="br-lt">' + L[0] + "・" + L[1] + "</span><span>" + counts + "</span><span>" + (b.label || "") + ' 收盤・還原價・與<a class="br-link" href="https://web-production-e1521.up.railway.app/" target="_blank" rel="noopener">台股生命線 App</a> 同步</span></div>' +
        "</div>" + sp;
      return;
    }
    // 沒有市場脈動列（非首頁版型）→ 退回在大盤速覽補一張卡
    var mk = document.querySelector(".mkt");
    if (!mk) return;
    var m = mk.querySelector(".m-br");
    if (!m) { m = document.createElement("div"); m.className = "m m-br"; mk.appendChild(m); }
    m.title = tip;
    m.innerHTML = '<div class="lbl">生命線失守比例</div><div class="val">' + fmt(pct, 1) + '%</div>' +
      '<div class="chg' + (dir ? " " + dir : "") + '">較前日 ' + (chg == null ? "—" : sign(chg, 1) + " 個百分點") + "（" + (b.label || "") + " 台股生命線）</div>" +
      '<div class="sub">' + L[0] + "・" + L[1] + "｜千張以上 " + fmt(b.n, 0) + " 檔中 " + fmt(b.below, 0) + " 檔在線下</div>";
  }

  function apply(d) {
    applyIndex(d);
    var tag = "（" + d.label + " 證交所）";
    function tagOf(x) { return x && x.label ? "（" + x.label + " " + (x.src || "證交所") + "）" : tag; }
    if (d.margin) {
      var g = d.margin.chg;
      setCard(/融資餘額/, fmt(Math.round(d.margin.bal), 0) + " 億", "單日 " + sign(g, 1) + " 億" + tagOf(d.margin), g > 0 ? "up" : g < 0 ? "down" : "", null);
    }
    if (d.keep) {
      var k = d.keep, tag2 = tagOf(k);
      if (d.fin_keep && d.fin_keep.rate) {
        var f = d.fin_keep;
        document.querySelectorAll(".mkt .m .lbl").forEach(function (l) { if (/擔保維持率|融資維持率/.test(l.textContent)) l.textContent = "大盤融資維持率"; });
        document.querySelectorAll(".pulse .pt .pk").forEach(function (l) { if (/擔保維持率|融資維持率/.test(l.textContent)) l.textContent = "融資維持率"; });
        setCard(/融資維持率/, fmt(f.rate, 2) + "%", "較前日 " + (f.chg != null ? sign(f.chg, 2) : "—") + "（" + d.label + " 證交所資料計算）",
          f.chg > 0 ? "up" : f.chg < 0 ? "down" : "", "130% 為追繳線｜一般落在 130%～180%");
      } else if (k.rate) setCard(/擔保維持率/, fmt(k.rate, 2) + "%", "較前日 " + (k.rate_chg != null ? sign(k.rate_chg, 2) : "—") + tag2,
        k.rate_chg > 0 ? "up" : k.rate_chg < 0 ? "down" : "", null);
      if (k.risk != null) setCard(/信用風險戶/, fmt(k.risk, 0) + " 戶", "較前日 " + (k.risk_chg != null ? sign(k.risk_chg, 0) + " 戶" : "—") + tag2,
        k.risk_chg > 0 ? "up" : k.risk_chg < 0 ? "down" : "", "維持率不足 " + k.below + "｜追繳 " + k.call + "｜處分 " + k.exe);
    }
    try { applyBreadth(d); } catch (e) {}
  }

  function run() {
    fetch(URL + "?t=" + Math.floor(Date.now() / 120000)).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.label) return;
      // 市場脈動列是 wl-pro.js 產生的，稍等它長出來再覆蓋一次
      apply(d); setTimeout(function () { apply(d); }, 800);
    }).catch(function () {});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
