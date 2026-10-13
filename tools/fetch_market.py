# -*- coding: utf-8 -*-
"""
旺來新聞站 · 盤後信用數據 (tools/fetch_market.py)
================================================
直接向證交所抓「官方」數字，寫到 data 分支 market/latest.json：
  - 融資餘額（上市，億元）與單日增減：MI_MARGN selectType=MS「融資金額(仟元)」
  - 全市場擔保維持率、信用風險戶數：BFIJ4U_TREND
網頁（wl-market.js）讀到後直接覆蓋首頁卡片，並標出資料日期。
證交所融資資料約在交易日 21:30 前後才公布，所以會從今天往前找最近一個有資料的交易日。
用法: python fetch_market.py <輸出資料夾>
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

TW = timezone(timedelta(hours=8))
UA = {"User-Agent": "Mozilla/5.0 (wanglai-news market)", "Accept": "application/json"}


def get(url):
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(3 * (i + 1))
    raise last


def num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None


def margin_on(ds):
    j = get("https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date=%s&selectType=MS&response=json" % ds)
    tables = j.get("tables") or []
    if not tables and j.get("data"):
        tables = [{"fields": j.get("fields"), "data": j.get("data")}]
    for t in tables:
        for r in t.get("data") or []:
            if r and "融資金額" in str(r[0]):
                prev, today = num(r[4]), num(r[5])
                if today:
                    return {"bal": round(today / 100000, 1), "chg": round((today - (prev or today)) / 100000, 1)}
    return None


def keep_trend(ds):
    j = get("https://www.twse.com.tw/rwd/zh/marginTrading/BFIJ4U_TREND?response=json&days=5&date=%s" % ds)
    arr = j if isinstance(j, list) else (j.get("data") or j.get("result") or j.get("list") or [])
    rows = [x for x in arr if isinstance(x, dict) and "keepRate" in x]
    if not rows:
        return None, j
    a, b = rows[-1], (rows[-2] if len(rows) > 1 else None)
    def risk(x):
        return sum(int(num(x.get(k)) or 0) for k in ("belowAccNum", "callAccNum", "exeAccNum"))
    out = {"rate": round(num(a.get("keepRate")) or 0, 2),
           "below": int(num(a.get("belowAccNum")) or 0), "call": int(num(a.get("callAccNum")) or 0),
           "exe": int(num(a.get("exeAccNum")) or 0)}
    out["risk"] = out["below"] + out["call"] + out["exe"]
    if b:
        out["rate_chg"] = round(out["rate"] - (num(b.get("keepRate")) or 0), 2)
        out["risk_chg"] = out["risk"] - risk(b)
    d = a.get("date") or a.get("txDate") or a.get("dataDate")
    out["date"] = str(d) if d else ""
    return out, None


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "market"
    os.makedirs(outdir, exist_ok=True)
    now = datetime.now(TW)
    res = {"updated": now.strftime("%Y-%m-%d %H:%M")}
    day = None
    for k in range(10):
        d = now - timedelta(days=k)
        if d.weekday() >= 5:
            continue
        ds = d.strftime("%Y%m%d")
        try:
            m = margin_on(ds)
        except Exception as e:
            print("margin fail", ds, e)
            m = None
        if m:
            res["margin"] = m
            day = d
            break
        time.sleep(2)
    if not day:
        print("no margin data")
        return 1
    res["date"] = day.strftime("%Y-%m-%d")
    res["label"] = day.strftime("%m/%d")
    try:
        k, raw = keep_trend(day.strftime("%Y%m%d"))
        if k:
            res["keep"] = k
        else:
            print("keep format unknown:", str(raw)[:300])
    except Exception as e:
        print("keep fail", e)
    p = os.path.join(outdir, "latest.json")
    try:
        old = json.load(open(p, encoding="utf-8"))
    except Exception:
        old = None
    if old and {k: v for k, v in old.items() if k != "updated"} == {k: v for k, v in res.items() if k != "updated"}:
        print("no change", res["date"])
        return 0
    with open(p, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
