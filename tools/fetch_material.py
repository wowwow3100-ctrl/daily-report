# -*- coding: utf-8 -*-
"""
旺來新聞站 · 個股重大訊息 (tools/fetch_material.py)
==================================================
抓證交所／櫃買中心 OpenAPI「上市（櫃）公司每日重大訊息」，累積最近 7 天，
寫到 data 分支 material/latest.json，給首頁「個股重大訊息」區塊（wl-material.js）用。
用法: python fetch_material.py <輸出資料夾>
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

TW = timezone(timedelta(hours=8))
SRC = [("L", "https://openapi.twse.com.tw/v1/opendata/t187ap04_L"),
       ("O", "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O")]
KEEP_DAYS = 7


def get(url):
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (wanglai-news material)", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(4 * (i + 1))
    raise last


def pick(row, *names):
    for k, v in row.items():
        kk = str(k).strip()
        for n in names:
            if kk == n or n in kk:
                return str(v).strip() if v is not None else ""
    return ""


def roc_date(s):
    s = "".join(ch for ch in str(s) if ch.isdigit())
    if len(s) >= 7:
        try:
            return "%04d-%s-%s" % (int(s[:-4]) + 1911, s[-4:-2], s[-2:])
        except Exception:
            return ""
    return ""


def hm(s):
    s = "".join(ch for ch in str(s) if ch.isdigit()).zfill(6)
    return "%s:%s" % (s[:2], s[2:4]) if s.strip("0") or s == "000000" else ""


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "material"
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, "latest.json")
    try:
        old = json.load(open(p, encoding="utf-8"))
    except Exception:
        old = {"items": []}
    items = {(x["d"], x["t"], x["c"], x["title"][:40]): x for x in old.get("items", [])}
    got = 0
    for mkt, url in SRC:
        try:
            data = get(url)
        except Exception as e:
            print("fetch fail", mkt, e)
            continue
        for r in data if isinstance(data, list) else []:
            code = pick(r, "公司代號", "SecuritiesCompanyCode")
            title = " ".join(pick(r, "主旨", "Subject").split())
            if not code or not title:
                continue
            d = roc_date(pick(r, "發言日期", "Date")) or roc_date(pick(r, "出表日期"))
            x = {"d": d, "t": hm(pick(r, "發言時間", "Time")), "c": code, "n": pick(r, "公司名稱", "CompanyName"), "m": mkt,
                 "title": title[:160], "rule": pick(r, "符合條款"), "fact": roc_date(pick(r, "事實發生日")),
                 "body": " ".join(pick(r, "說明", "Description").split())[:600]}
            items[(x["d"], x["t"], x["c"], x["title"][:40])] = x
            got += 1
    cut = (datetime.now(TW) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    arr = [x for x in items.values() if x["d"] >= cut]
    arr.sort(key=lambda x: (x["d"], x["t"], x["c"]), reverse=True)
    res = {"updated": datetime.now(TW).strftime("%Y-%m-%d %H:%M"), "n": len(arr), "items": arr[:2500]}
    if old.get("items") == res["items"]:
        print("no change", len(arr))
        return 0
    with open(p, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", len(arr), "fetched", got)
    return 0


if __name__ == "__main__":
    sys.exit(main())
