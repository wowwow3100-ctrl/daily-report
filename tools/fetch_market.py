# -*- coding: utf-8 -*-
"""
旺來新聞站 · 盤後信用數據 (tools/fetch_market.py)
================================================
直接向證交所抓「官方」數字，寫到 data 分支 market/latest.json：
  - 融資餘額（上市，億元）與單日增減：MI_MARGN selectType=MS「融資金額(仟元)」
  - 全市場擔保維持率、信用風險戶數：BFIJ4U_TREND
  - 加權指數收盤／漲跌、上市成交值：FMTQIK（約 14:30 收盤後就有）
  - 費城半導體 SOX：Yahoo Finance 日線（美股收盤）
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


def roc(s):
    y, m, d = str(s).strip().split("/")
    return datetime(int(y) + 1911, int(m), int(d))


def fmtqik(d):
    j = get("https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=%s&response=json" % d.strftime("%Y%m01"))
    out = []
    for r in j.get("data") or []:
        try:
            out.append({"d": roc(r[0]), "amt": num(r[2]), "close": num(r[4]), "chg": num(r[5])})
        except Exception:
            pass
    return out


def index_info(now):
    rows = fmtqik(now)
    if len(rows) < 2:
        time.sleep(1.5)
        rows = fmtqik(now.replace(day=1) - timedelta(days=1)) + rows
    rows = [r for r in rows if r["close"]]
    if not rows:
        return None
    a = rows[-1]
    b = rows[-2] if len(rows) > 1 else None
    prev_close = a["close"] - (a["chg"] or 0)
    out = {"close": round(a["close"], 2), "chg": round(a["chg"] or 0, 2),
           "pct": round((a["chg"] or 0) / prev_close * 100, 2) if prev_close else 0,
           "amt": round(a["amt"] / 1e8), "date": a["d"].strftime("%Y-%m-%d"), "label": a["d"].strftime("%m/%d")}
    if b and b["amt"]:
        out["amt_prev"] = round(b["amt"] / 1e8)
        out["amt_pct"] = round((a["amt"] / b["amt"] - 1) * 100, 1)
    return out


def sox_info():
    req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/%5ESOX?range=10d&interval=1d",
                                 headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode("utf-8"))
    res = j["chart"]["result"][0]
    ts, cl = res["timestamp"], res["indicators"]["quote"][0]["close"]
    pts = [(t, c) for t, c in zip(ts, cl) if c]
    if len(pts) < 3:
        return None
    ny = timezone(timedelta(hours=-4))
    nyn = datetime.now(ny)
    last = datetime.fromtimestamp(pts[-1][0], ny)
    if last.date() == nyn.date() and nyn.hour * 60 + nyn.minute < 16 * 60 + 10:
        pts = pts[:-1]  # 美股還沒收盤的那一根不要
    if len(pts) < 3:
        return None
    (t0, c0), (t1, c1), (t2, c2) = pts[-3], pts[-2], pts[-1]
    return {"close": round(c2, 2), "pct": round((c2 / c1 - 1) * 100, 2), "prev_pct": round((c1 / c0 - 1) * 100, 2),
            "label": datetime.fromtimestamp(t2, ny).strftime("%m/%d")}


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
    try:
        ix = index_info(now)
        if ix:
            res["index"] = ix
    except Exception as e:
        print("index fail", e)
    try:
        sx = sox_info()
        if sx:
            res["sox"] = sx
    except Exception as e:
        print("sox fail", e)
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
