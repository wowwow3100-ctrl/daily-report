# -*- coding: utf-8 -*-
"""同步研究報告紀錄到網站：processed.csv -> reports.csv，並排一張推送單。"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\APP\研究報告\_log\processed.csv"
DST = os.path.join(HERE, "reports.csv")
REQ = os.path.join(HERE, ".push_request")

def main():
    if not os.path.exists(SRC):
        print("[錯誤] 找不到來源檔：%s" % SRC)
        sys.exit(1)
    shutil.copyfile(SRC, DST)
    size_kb = os.path.getsize(DST) // 1024
    with open(REQ, "w", encoding="utf-8") as f:
        f.write("update: 同步研究報告紀錄到專區 (reports.csv)\n")
    print("[完成] 已複製 reports.csv（%d KB）並排入推送單。" % size_kb)
    print("推送守護有在跑的話，1-2 分鐘內就會上線。")

if __name__ == "__main__":
    main()
