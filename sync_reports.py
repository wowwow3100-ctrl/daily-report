# -*- coding: utf-8 -*-
"""同步研究報告資料到網站：
1. processed.csv -> reports.csv（研究報告專區資料）
2. 掃 個股/ 資料夾 -> stocks.json（個股報告圖磚頁資料；只收 .docx，PDF 一律排除）
3. 排一張推送單
"""
import os
import re
import json
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\APP\研究報告\_log\processed.csv"
DST = os.path.join(HERE, "reports.csv")
STOCK_DIR = os.path.join(HERE, "個股")
MANIFEST = os.path.join(HERE, "stocks.json")
REQ = os.path.join(HERE, ".push_request")


def build_manifest():
    stocks = []
    if not os.path.isdir(STOCK_DIR):
        return stocks
    for folder in sorted(os.listdir(STOCK_DIR)):
        full = os.path.join(STOCK_DIR, folder)
        if not os.path.isdir(full):
            continue
        m = re.match(r"^(.*?)(\d{4})$", folder)
        name, code = (m.group(1), m.group(2)) if m else (folder, "")
        files = [f for f in sorted(os.listdir(full))
                 if f.lower().endswith(".docx") and not f.startswith("~$")]
        if files:
            stocks.append({"folder": folder, "name": name, "code": code, "files": files})
    return stocks


def main():
    # 1. reports.csv
    if os.path.exists(SRC):
        shutil.copyfile(SRC, DST)
        print("[完成] reports.csv 已更新（%d KB）" % (os.path.getsize(DST) // 1024))
    else:
        print("[略過] 找不到 %s，reports.csv 未更新" % SRC)

    # 2. stocks.json
    stocks = build_manifest()
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"stocks": stocks}, f, ensure_ascii=False, indent=1)
    total = sum(len(s["files"]) for s in stocks)
    print("[完成] stocks.json：%d 檔個股、%d 份摘要（僅 docx，PDF 不列入）" % (len(stocks), total))

    # 3. 推送單
    with open(REQ, "w", encoding="utf-8") as f:
        f.write("update: 同步研究報告資料與個股清單\n")
    print("[完成] 已排入推送單。推送守護有在跑的話 1-2 分鐘內上線。")


if __name__ == "__main__":
    main()
