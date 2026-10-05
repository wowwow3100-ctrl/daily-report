# -*- coding: utf-8 -*-
"""
旺來新聞站 · 資金流向資料 (tools/fetch_sectors.py)
==================================================
由 GitHub Actions（.github/workflows/sectors.yml）在交易日收盤後自動跑，
抓證交所「每日收盤行情」的類股指數漲跌，取漲幅前 5 名族群，
再抓每個族群裡漲幅最大的 5 檔，寫到 data 分支：

  sectors/latest.json  {"date":"2026-10-05","label":"10/05","top":[{"name":..,"pct":..,"stocks":[{"n":..,"c":..,"p":..}]}]}

網頁（wl-sectors.js）讀到比頁面上更新的日期，就直接換掉「資金流向 TOP 5」。
只用 Python 標準庫。
用法: python fetch_sectors.py <輸出資料夾>
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

TW = timezone(timedelta(hours=8))
BASE = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=%s&type=%s&response=json"
# 證交所類股代碼（只放「單一產業」類股，不放水泥窯製、電子工業這種合併指數）
CODES = {
    "水泥": "01", "食品": "02", "塑膠": "03", "紡織纖維": "04", "電機機械": "05", "電器電纜": "06",
    "玻璃陶瓷": "08", "造紙": "09", "鋼鐵": "10", "橡膠": "11", "汽車": "12", "建材營造": "14",
    "航運": "15", "觀光餐旅": "16", "金融保險": "17", "貿易百貨": "18", "其他": "20", "化學": "21",
    "生技醫療": "22", "油電燃氣": "23", "半導體": "24", "電腦及週邊設備": "25", "光電": "26",
    "通信網路": "27", "電子零組件": "28", "電子通路": "29", "資訊服務": "30", "其他電子": "31",
    "綠能環保": "35", "數位雲端": "36", "運動休閒": "37", "居家生活": "38",
}


def get(url):
    last = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (wanglai-news sectors)", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(4 * (i + 1))
    raise last


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return None


def sector_table(d):
    for t in d.get("tables") or []:
        f = t.get("fields") or []
        if "指數" in f and any("百分比" in x for x in f) and t.get("data"):
            return f, t["data"]
    return None, None


def stock_table(d):
    for t in d.get("tables") or []:
        f = t.get("fields") or []
        if "證券代號" in f and "收盤價" in f and t.get("data"):
            return f, t["data"]
    return None, None


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "sectors"
    os.makedirs(out, exist_ok=True)
    now = datetime.now(TW)
    day, rows, fields = None, None, None
    for k in range(10):
        d = now - timedelta(days=k)
        if d.weekday() >= 5:
            continue
        ds = d.strftime("%Y%m%d")
        try:
            fields, rows = sector_table(get(BASE % (ds, "IND")))
        except Exception as e:
            print("IND fail", ds, e)
            rows = None
        if rows:
            day = d
            break
        time.sleep(3)
    if not rows:
        print("no sector data")
        return 1
    ds = day.strftime("%Y%m%d")
    i_name, i_pct = fields.index("指數"), [i for i, x in enumerate(fields) if "百分比" in x][0]
    secs = []
    for r in rows:
        nm = re.sub(r"類指數$", "", str(r[i_name]).strip())
        if "報酬" in str(r[i_name]) or nm not in CODES:
            continue
        p = num(r[i_pct])
        if p is None:
            continue
        secs.append((nm, p))
    secs.sort(key=lambda x: -x[1])
    top = []
    for nm, p in secs[:5]:
        time.sleep(3)
        stocks = []
        try:
            f, data = stock_table(get(BASE % (ds, CODES[nm])))
        except Exception as e:
            print("stock fail", nm, e)
            f, data = None, None
        if data:
            ic, inm, icl, isg, idf = f.index("證券代號"), f.index("證券名稱"), f.index("收盤價"), f.index("漲跌(+/-)"), f.index("漲跌價差")
            for r in data:
                code = str(r[ic]).strip()
                if not re.fullmatch(r"\d{4}[A-Z]?", code):
                    continue
                close, diff = num(r[icl]), num(r[idf])
                if close is None or diff is None:
                    continue
                sg = str(r[isg])
                sign = -1 if "-" in re.sub(r"<[^>]+>", "", sg) else (1 if "+" in sg else 0)
                prev = close - sign * diff
                if prev <= 0:
                    continue
                stocks.append({"n": str(r[inm]).strip(), "c": code, "p": round(sign * diff / prev * 100, 2)})
            stocks.sort(key=lambda x: -x["p"])
        top.append({"name": nm, "pct": round(p, 2), "stocks": stocks[:5]})
    res = {"date": day.strftime("%Y-%m-%d"), "label": day.strftime("%m/%d"), "top": top,
           "src": BASE % (ds, "IND"), "updated": now.strftime("%Y-%m-%d %H:%M")}
    p = os.path.join(out, "latest.json")
    old = None
    try:
        old = json.load(open(p, encoding="utf-8"))
    except Exception:
        pass
    if old and old.get("date") == res["date"] and old.get("top") == res["top"]:
        print("no change", res["date"])
        return 0
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, separators=(",", ":"))
    print("wrote", res["date"], [t["name"] for t in top])
    return 0


if __name__ == "__main__":
    sys.exit(main())
