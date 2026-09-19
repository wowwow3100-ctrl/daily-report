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
DST = os.path.join(HERE, "reports.csv")
STOCK_DIR = os.path.join(HERE, "個股")
DAILY_DIR = os.path.join(HERE, "日報")
MANIFEST = os.path.join(HERE, "stocks.json")
REQ = os.path.join(HERE, ".push_request")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

SHELL = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s｜旺來新聞整理</title>
<style>
 :root{--bg:#0B0B0D;--card:#16161A;--line:#2A2A32;--gold:#E8C15A;--gold-dim:#A98B3F;--text:#EDEAE0;--muted:#9C9889;}
 *{margin:0;padding:0;box-sizing:border-box;}
 body{background:var(--bg);color:var(--text);font-family:"Microsoft JhengHei","Noto Sans TC",sans-serif;line-height:1.8;}
 .wrap{max-width:860px;margin:0 auto;padding:28px 20px 60px;}
 a.back{color:var(--gold-dim);text-decoration:none;font-size:.85rem;border:1px solid var(--gold-dim);border-radius:18px;padding:3px 14px;}
 h1{color:var(--gold);font-size:1.25rem;letter-spacing:2px;margin:18px 0 6px;}
 .notice{margin:14px 0 22px;padding:10px 16px;border:1px solid var(--gold-dim);border-radius:8px;color:var(--gold);font-size:.85rem;}
 .notice span{color:var(--muted);display:block;font-size:.78rem;}
 p{margin:10px 0;font-size:.95rem;}
 b{color:var(--gold);}
 table{width:100%%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);margin:14px 0;font-size:.9rem;}
 td,th{padding:8px 12px;border:1px solid var(--line);}
 tr:first-child td{background:#1D1D23;color:var(--gold);font-weight:700;}
 .dl{margin-top:30px;font-size:.82rem;color:var(--muted);}
 .dl a{color:var(--gold-dim);}
</style></head><body><div class="wrap">
<a class="back" href="../../stocks.html">← 回個股報告</a>
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


def convert_tree(folder):
    made = skipped = failed = 0
    if not os.path.isdir(folder):
        return made, skipped, failed
    for dirpath, _dirs, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith(".docx") or f.startswith("~$"):
                continue
            src = os.path.join(dirpath, f)
            dst = os.path.splitext(src)[0] + ".html"
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                skipped += 1
                continue
            body, err = docx_to_html(src)
            if body is None:
                print("  [轉檔失敗] %s：%s" % (f, err))
                failed += 1
                continue
            title = os.path.splitext(f)[0].replace("_", "｜")
            page = SHELL % {"title": html_mod.escape(title), "body": body,
                            "docx": html_mod.escape(f)}
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
                 if f.lower().endswith(".docx") and not f.startswith("~$")]
        if files:
            stocks.append({"folder": folder, "name": name, "code": code, "files": files})
    return stocks


def main():
    if os.path.exists(SRC):
        shutil.copyfile(SRC, DST)
        print("[完成] reports.csv 已更新（%d KB）" % (os.path.getsize(DST) // 1024))
    else:
        print("[略過] 找不到 %s" % SRC)

    for label, folder in (("個股", STOCK_DIR), ("日報", DAILY_DIR)):
        made, skipped, failed = convert_tree(folder)
        print("[完成] %s docx→html：新轉 %d、已是最新 %d、失敗 %d" % (label, made, skipped, failed))

    stocks = build_manifest()
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"stocks": stocks}, f, ensure_ascii=False, indent=1)
    total = sum(len(s["files"]) for s in stocks)
    print("[完成] stocks.json：%d 檔個股、%d 份摘要" % (len(stocks), total))

    with open(REQ, "w", encoding="utf-8") as f:
        f.write("update: 同步研究報告資料（網頁版摘要＋個股清單）\n")
    print("[完成] 已排入推送單。")


if __name__ == "__main__":
    main()
