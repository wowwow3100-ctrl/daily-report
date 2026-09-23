# -*- coding: utf-8 -*-
"""
旺來新聞站 · 補齊漏掉的個股頁 (backfill_stocks.py)
=====================================================
reports.csv 裡出現過券商觀點、但「個股\」底下沒有資料夾的個股，
在這裡一次補出「觀點彙整頁」(html)，內容直接來自 reports.csv 既有紀錄。

會做的事:
  1. 掃 reports.csv，整理每一檔個股的所有歷史紀錄
  2. 跳過「一則報告涵蓋多檔」那種合併列 (例如「統一／台塑／台化等9檔」)
  3. 沒有資料夾的個股 → 建 個股\<名稱><代號>\ 並寫入 觀點彙整.html (wl-v4 版型)
  4. 重建 stocks.json (★docx 與 html 都算, 不再只認 docx)

用法: python backfill_stocks.py
"""
import csv
import json
import os
import re
import html as html_mod

HERE = os.path.dirname(os.path.abspath(__file__))
STOCK_DIR = os.path.join(HERE, "個股")
DAILY_DIR = os.path.join(HERE, "日報")
REPORTS = os.path.join(HERE, "reports.csv")
STOCKS_JSON = os.path.join(HERE, "stocks.json")

# 檔名不能有這些字元
BAD_CHARS = r'[\\/:*?"<>|]'
# 一則報告涵蓋多檔的合併列, 不建個股頁
MULTI = re.compile(r"[／/]|等\s*\d+\s*檔|三雄|四雄|雙雄|供應鏈|族群|概念股|背景")

SHELL = """<!DOCTYPE html>
<html lang="zh-Hant" data-size="std" data-theme="gold"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s｜旺來新聞整理</title>
<!--wl-v4-->
<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%%3E%%3Ctext y='0.9em' font-size='90'%%3E%%F0%%9F%%8D%%8D%%3C/text%%3E%%3C/svg%%3E">
<script>
(function(){var h=document.documentElement;try{
 h.setAttribute("data-theme",localStorage.getItem("wl_theme")||"gold");
 h.setAttribute("data-size",localStorage.getItem("wl_fs")||"std");
 if((localStorage.getItem("wl_view")||"auto")==="mb")h.classList.add("mob");
}catch(e){}})();
</script>
<style>
 :root{--bg:#0B0B0D;--card:#16161A;--card2:#1D1D23;--line:#2A2A32;--gold:#E8C15A;--gold-dim:#A98B3F;--text:#EDEAE0;--muted:#9C9889;--up:#FF5A5A;--down:#3DD68C;}
 html[data-theme="light"]{--bg:#F6F0E0;--card:#FFFFFF;--card2:#EFE7CF;--line:#DCD2B4;--gold:#7A5E17;--gold-dim:#9C8034;--text:#22381F;--muted:#5A6F58;--up:#C43D3D;--down:#1E7F4F;}
 html[data-theme="navy"]{--bg:#0C1322;--card:#141E33;--card2:#1B2946;--line:#263858;--gold:#9DC0FF;--gold-dim:#5C7FBF;--text:#E8EDF7;--muted:#8FA0BF;--up:#FF6B6B;--down:#43D69A;}
 html{font-size:17px;}
 html[data-size="lg"]{font-size:19px;}
 html[data-size="xl"]{font-size:22px;}
 html[data-size="elder"]{font-size:27px;}
 *{margin:0;padding:0;box-sizing:border-box;}
 body{background:var(--bg);color:var(--text);font-family:"Microsoft JhengHei","Noto Sans TC",sans-serif;line-height:1.8;}
 .wrap{max-width:860px;margin:0 auto;padding:28px 20px 60px;}
 html.mob .wrap{max-width:540px;padding:20px 12px 50px;}
 a.back{color:var(--gold-dim);text-decoration:none;font-size:.85rem;border:1px solid var(--gold-dim);border-radius:18px;padding:3px 14px;}
 a.back:hover{color:var(--gold);border-color:var(--gold);}
 h1{color:var(--gold);font-size:1.25rem;letter-spacing:2px;margin:18px 0 6px;}
 .notice{margin:14px 0 22px;padding:10px 16px;border:1px solid var(--gold-dim);border-radius:8px;color:var(--gold);font-size:.85rem;}
 .notice span{color:var(--muted);display:block;font-size:.78rem;}
 .rec{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--gold-dim);border-radius:10px;padding:12px 16px;margin-bottom:10px;}
 .rec .top{display:flex;gap:10px;flex-wrap:wrap;align-items:baseline;}
 .rec .d{color:var(--gold);font-weight:800;font-size:.9rem;white-space:nowrap;}
 .rec .bk{font-weight:700;}
 .tag{display:inline-block;padding:1px 8px;border-radius:20px;font-size:.72rem;border:1px solid var(--gold-dim);color:var(--gold);white-space:nowrap;}
 .rec .rt{margin-top:4px;font-size:.92rem;}
 .rec .rt b{color:var(--gold);}
 .rec .note{color:var(--muted);font-size:.86rem;margin-top:5px;word-break:break-word;}
 .dl{margin-top:30px;font-size:.82rem;color:var(--muted);line-height:2;}
 .dl a{color:var(--gold-dim);}
</style></head><body><div class="wrap">
<a class="back" href="../../stocks.html">← 回個股報告</a>
<h1>%(title)s</h1>
<div class="notice">⚠ 本頁為新聞整理摘要<span>以下為本站自公開新聞逐日收錄的券商觀點紀錄，非券商原始報告、非投資建議；目標價與評等以各券商原始報告為準。</span></div>
%(body)s
<div class="dl">本頁由歷史紀錄彙整，尚無單獨的 Word 版摘要。完整紀錄可至<a href="../../records.html?q=%(code)s">速查</a>查詢。<br>旺來 @wowwow31001</div>
</div></body></html>
"""


def esc(s):
    return html_mod.escape(str(s or "").strip())


def load_records():
    """回傳 {code: {"name":..., "rows":[...]}}"""
    out = {}
    with open(REPORTS, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            stock = (row.get("stock") or "").strip()
            m = re.search(r"([0-9]{4}[A-Z]?)", stock)
            if not m:
                continue
            code = m.group(1)
            name = re.sub(r"[（(].*?[)）]", "", stock).replace(code, "")
            name = name.strip(" ·、,，()（）-")
            if not name:
                continue
            if MULTI.search(name):        # 多檔合併列, 不建個股頁
                continue
            name = re.sub(BAD_CHARS, "", name)
            d = out.setdefault(code, {"name": name, "rows": []})
            d["rows"].append(row)
    return out


def build_body(rows):
    parts = []
    for row in sorted(rows, key=lambda r: (r.get("date") or ""), reverse=True):
        date = esc(row.get("date"))
        broker = esc(row.get("broker"))
        typ = esc(row.get("type"))
        rating = esc(row.get("rating"))
        tp = esc(row.get("target_price"))
        note = esc(row.get("note"))
        line = '<div class="rec"><div class="top"><span class="d">%s</span>' % date
        if typ:
            line += '<span class="tag">%s</span>' % typ
        if broker:
            line += '<span class="bk">%s</span>' % broker
        line += "</div>"
        bits = []
        if rating:
            bits.append("評等 <b>%s</b>" % rating)
        if tp:
            bits.append("目標價 <b>%s</b>" % tp)
        if bits:
            line += '<div class="rt">%s</div>' % "　".join(bits)
        if note:
            line += '<div class="note">%s</div>' % note
        line += "</div>"
        parts.append(line)
    return "\n".join(parts)


def main():
    os.makedirs(STOCK_DIR, exist_ok=True)
    recs = load_records()
    existing = {}
    for f in os.listdir(STOCK_DIR):
        if os.path.isdir(os.path.join(STOCK_DIR, f)):
            m = re.search(r"([0-9]{4}[A-Z]?)$", f)
            if m:
                existing[m.group(1)] = f

    created = 0
    for code, d in sorted(recs.items()):
        if code in existing:
            continue
        folder = "%s%s" % (d["name"], code)
        fdir = os.path.join(STOCK_DIR, folder)
        os.makedirs(fdir, exist_ok=True)
        title = "%s（%s）券商觀點彙整" % (d["name"], code)
        page = SHELL % {"title": esc(title), "body": build_body(d["rows"]), "code": code}
        with open(os.path.join(fdir, "觀點彙整.html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        existing[code] = folder
        created += 1
        print("  + %s（%d 筆紀錄）" % (folder, len(d["rows"])))

    # ---- 重建 stocks.json：docx 與 html 都算 ----
    stocks = []
    for folder in sorted(os.listdir(STOCK_DIR)):
        fdir = os.path.join(STOCK_DIR, folder)
        if not os.path.isdir(fdir):
            continue
        m = re.search(r"([0-9]{4}[A-Z]?)$", folder)
        if not m:
            continue
        code = m.group(1)
        name = folder[: -len(code)]
        files = sorted(x for x in os.listdir(fdir) if x.lower().endswith((".docx", ".html")))
        # 同名的 docx 與 html 只留 docx（html 是它的網頁版）
        docx_stems = {os.path.splitext(x)[0] for x in files if x.lower().endswith(".docx")}
        keep = [x for x in files
                if x.lower().endswith(".docx") or os.path.splitext(x)[0] not in docx_stems]
        if not keep:
            continue
        stocks.append({"folder": folder, "name": name, "code": code, "files": keep})

    daily = []
    if os.path.isdir(DAILY_DIR):
        daily = sorted(x for x in os.listdir(DAILY_DIR) if x.lower().endswith(".docx"))
        if not daily:
            daily = sorted(x for x in os.listdir(DAILY_DIR) if x.lower().endswith(".html"))

    with open(STOCKS_JSON, "w", encoding="utf-8") as fh:
        json.dump({"stocks": stocks, "daily": daily}, fh, ensure_ascii=False, indent=1)

    print("\n新增個股頁 %d 檔；stocks.json 共 %d 檔個股、%d 份日報" % (created, len(stocks), len(daily)))


if __name__ == "__main__":
    main()
