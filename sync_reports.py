# -*- coding: utf-8 -*-
"""同步研究報告資料到網站：
1. processed.csv -> reports.csv（研究報告專區資料）
2. 掃 個股/、日報/ 的 .docx -> 各生成同名 .html（黑金網頁版，可直接點開看）
3. 掃 個股/ -> stocks.json（個股圖磚頁資料；只收 .docx，PDF 一律排除）
4. 排一張推送單
只用標準庫，不需 pip 安裝任何東西。
"""
import os
import re
import json
import shutil
import sys
import zipfile
import html as html_mod
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\APP\研究報告\_log\processed.csv"
LEGACY_DAILY = r"D:\APP\研究報告\日報"
DST = os.path.join(HERE, "reports.csv")
STOCK_DIR = os.path.join(HERE, "個股")
DAILY_DIR = os.path.join(HERE, "日報")
MANIFEST = os.path.join(HERE, "stocks.json")
REQ = os.path.join(HERE, ".push_request")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

SHELL = """<!DOCTYPE html>
<html lang="zh-Hant" data-size="std" data-theme="gold"><head><meta charset="UTF-8"><script>(function(){var N="https://daily-tw.up.railway.app";try{var L=location;if(L.hostname.slice(-9)==="github.io"){var m={};for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k&&k.indexOf("wl_")===0)m[k]=localStorage.getItem(k);}var p=L.pathname.replace("/daily-report","")||"/";var h=(L.hash&&L.hash.length>1)?L.hash:"#wlm="+encodeURIComponent(JSON.stringify(m));L.replace(N+p+L.search+h);}else if(L.hash.indexOf("#wlm=")===0){var o=JSON.parse(decodeURIComponent(L.hash.slice(5)));for(var k2 in o){if(localStorage.getItem(k2)===null)localStorage.setItem(k2,o[k2]);}sessionStorage.setItem("wl_nav","1");history.replaceState(null,"",L.pathname+L.search);}}catch(e){}})();</script><!--wl-move-->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s｜旺來新聞整理</title>
<!--wl-v4-->
<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%%3E%%3Ctext y='0.9em' font-size='90'%%3E%%F0%%9F%%8D%%8D%%3C/text%%3E%%3C/svg%%3E">
<script>
(function(){var h=document.documentElement;try{
 h.setAttribute("data-theme",(localStorage.getItem("wl_theme")||"gold").replace("navy","gold"));
 h.setAttribute("data-size",localStorage.getItem("wl_fs")||"std");
 if((localStorage.getItem("wl_view")||"auto")==="mb")h.classList.add("mob");
}catch(e){}})();
</script>
<style>
 :root{--bg:#0B0B0D;--card:#16161A;--card2:#1D1D23;--line:#2A2A32;--gold:#E8C15A;--gold-dim:#A98B3F;--text:#EDEAE0;--muted:#9C9889;}
 html[data-theme="light"]{--bg:#F6F0E0;--card:#FFFFFF;--card2:#EFE7CF;--line:#DCD2B4;--gold:#7A5E17;--gold-dim:#9C8034;--text:#22381F;--muted:#5A6F58;}
 html[data-theme="white"]{--bg:#F4F5F7;--card:#FFFFFF;--card2:#EEF0F3;--line:#DDE1E6;--gold:#222326;--gold-dim:#9A8255;--text:#1B1C1E;--muted:#6A6F76;--up:#D2302C;--down:#16804A;--bgt:rgba(244,245,247,.94);}
 html[data-theme="red"]{--bg:#1C0709;--card:#2A0D10;--card2:#361216;--line:#4E1D21;--gold:#F2C75C;--gold-dim:#B8903E;--text:#F6ECE4;--muted:#C4A69E;--up:#FF7B6B;--down:#4FD99A;--bgt:rgba(28,7,9,.94);}
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
 p{margin:10px 0;font-size:.95rem;}
 b{color:var(--gold);}
 table{width:100%%;border-collapse:separate;border-spacing:0;background:var(--card);
   border:1px solid var(--gold-dim);border-radius:12px;overflow:hidden;margin:16px 0;font-size:.9rem;}
 td,th{padding:10px 12px;border-top:1px solid var(--line);border-right:1px solid var(--line);}
 td:last-child,th:last-child{border-right:none;}
 tr:first-child td{background:var(--card2);color:var(--gold);font-weight:700;border-top:none;border-bottom:2px solid var(--gold-dim);}
 tr:nth-child(even) td{background:rgba(255,255,255,.022);}
 html[data-theme="light"] tr:nth-child(even) td{background:rgba(0,0,0,.02);}
 .dl{margin-top:30px;font-size:.82rem;color:var(--muted);}
 .dl a{color:var(--gold-dim);}
 @media (max-width:720px){
   .wrap{padding:20px 12px 50px;}
   table{display:block;overflow-x:auto;}
 }
</style></head><body><div class="wrap">
<a class="back" href="%(back)s" onclick="if(/(stocks|reports|wish)\.html/.test(document.referrer)&&history.length>1){history.back();return false;}">%(backlabel)s</a>
<h1>%(title)s</h1>
<div class="notice">⚠ 本頁為新聞整理摘要<span>依公開新聞整理（來源見文末），非券商原始報告、非投資建議。</span></div>
%(body)s
<div class="dl">Word 版下載：<a href="%(docx)s" download>%(docx)s</a>｜旺來 @wowwow31001</div>
</div></body></html>
"""


def para_html(p):
    parts = []
    for r in p.iter(W + "r"):
        t = "".join(n.text or "" for n in r.iter(W + "t"))
        if not t:
            continue
        rpr = r.find(W + "rPr")
        bold = rpr is not None and rpr.find(W + "b") is not None
        t = html_mod.escape(t)
        parts.append("<b>%s</b>" % t if bold else t)
    return "".join(parts)


def docx_to_html(path):
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
    except Exception as e:
        return None, "unzip failed: %s" % e
    try:
        root = ET.fromstring(xml)
    except Exception as e:
        return None, "xml parse failed: %s" % e
    body = root.find(W + "body")
    if body is None:
        return None, "no body"
    out = []
    for child in list(body):
        tag = child.tag
        if tag == W + "p":
            h = para_html(child)
            if h.strip():
                out.append("<p>%s</p>" % h)
        elif tag == W + "tbl":
            rows = []
            for tr in child.iter(W + "tr"):
                cells = []
                for tc in tr.findall(W + "tc"):
                    txt = "<br>".join(filter(None, (para_html(p) for p in tc.iter(W + "p"))))
                    cells.append("<td>%s</td>" % txt)
                rows.append("<tr>%s</tr>" % "".join(cells))
            out.append("<table>%s</table>" % "".join(rows))
    return "\n".join(out), None


def convert_tree(folder, back, backlabel):
    made = skipped = failed = 0
    if not os.path.isdir(folder):
        return made, skipped, failed
    for dirpath, _dirs, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith(".docx") or f.startswith("~$") or ".tmp." in f.lower():
                continue
            src = os.path.join(dirpath, f)
            dst = os.path.splitext(src)[0] + ".html"
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                try:
                    with open(dst, encoding="utf-8") as fh:
                        head = fh.read(2048)
                except Exception:
                    head = ""
                if "wl-v4" in head:  # 已是最新版型才略過
                    skipped += 1
                    continue
            body, err = docx_to_html(src)
            if body is None:
                print("  [轉檔失敗] %s：%s" % (f, err))
                failed += 1
                continue
            title = os.path.splitext(f)[0].replace("_", "｜")
            page = SHELL % {"title": html_mod.escape(title), "body": body,
                            "docx": html_mod.escape(f),
                            "back": back, "backlabel": backlabel}
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(page)
            made += 1
    return made, skipped, failed


def build_manifest():
    stocks = []
    if not os.path.isdir(STOCK_DIR):
        return stocks
    for folder in sorted(os.listdir(STOCK_DIR)):
        full = os.path.join(STOCK_DIR, folder)
        if not os.path.isdir(full):
            continue
        m = re.match(r"^(.*?)(\d{4})$", folder)
        if not m:
            continue  # 非個股資料夾（如 _策略清單）不列
        name, code = m.group(1), m.group(2)
        files = [f for f in sorted(os.listdir(full))
                 if f.lower().endswith(".docx") and not f.startswith("~$")
                 and ".tmp." not in f.lower()]
        if files:
            stocks.append({"folder": folder, "name": name, "code": code, "files": files})
    return stocks


def copy_legacy_daily():
    """把歷史日報 docx（研究報告\\日報）補進網站的 日報\\，已存在的不動。"""
    n = 0
    if not os.path.isdir(LEGACY_DAILY):
        return n
    os.makedirs(DAILY_DIR, exist_ok=True)
    for f in os.listdir(LEGACY_DAILY):
        if not f.lower().endswith(".docx") or f.startswith("~$"):
            continue
        dst = os.path.join(DAILY_DIR, f)
        if not os.path.exists(dst):
            shutil.copyfile(os.path.join(LEGACY_DAILY, f), dst)
            n += 1
    return n


def main():
    n = copy_legacy_daily()
    print("[完成] 歷史日報補入 %d 份" % n)
    if os.path.exists(SRC):
        # 公開站的 reports.csv 只放「真正的券商觀點列」；
        # processed.csv 內的方法論／內部工作筆記列不得外流到公開站。
        import csv as _csv
        with open(SRC, encoding="utf-8-sig", newline="") as _f:
            _rows = list(_csv.reader(_f))
        _kept, _dropped = [], 0
        for _i, _r in enumerate(_rows):
            if _i > 0 and len(_r) >= 5 and (
                "方法論" in _r[3] or "收件匣" in _r[3] or "大盤與方法論" in _r[4]
            ):
                _dropped += 1
                continue
            _kept.append(_r)
        with open(DST, "w", encoding="utf-8", newline="") as _f:
            _csv.writer(_f, lineterminator="\n").writerows(_kept)
        print("[完成] reports.csv 已更新（%d KB，濾除內部工作筆記 %d 列）"
              % (os.path.getsize(DST) // 1024, _dropped))
    else:
        print("[略過] 找不到 %s" % SRC)

    jobs = (("個股", STOCK_DIR, "../../stocks.html", "← 回個股報告"),
            ("日報", DAILY_DIR, "../reports.html", "← 回研究報告專區"))
    for label, folder, back, backlabel in jobs:
        made, skipped, failed = convert_tree(folder, back, backlabel)
        print("[完成] %s docx→html：新轉 %d、已是最新 %d、失敗 %d" % (label, made, skipped, failed))

    stocks = build_manifest()
    daily = []
    if os.path.isdir(DAILY_DIR):
        daily = [f for f in sorted(os.listdir(DAILY_DIR))
                 if f.lower().endswith(".docx") and not f.startswith("~$")
                 and ".tmp." not in f.lower()]
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"stocks": stocks, "daily": daily}, f, ensure_ascii=False, indent=1)
    total = sum(len(s["files"]) for s in stocks)
    print("[完成] stocks.json：%d 檔個股、%d 份摘要、%d 份日報" % (len(stocks), total, len(daily)))

    with open(REQ, "w", encoding="utf-8") as f:
        f.write("update: 同步研究報告資料（網頁版摘要＋個股清單）\n")
    print("[完成] 已排入推送單。")


if __name__ == "__main__":
    main()
