# -*- coding: utf-8 -*-
"""
旺來新聞站 · 營收佈告欄資料 (tools/fetch_revenue.py)
====================================================
由 GitHub Actions（.github/workflows/revenue.yml）每天自動跑，
抓證交所／櫃買中心公開的「每月營業收入彙總表」，寫到 data 分支：

  revenue/meta.json      {"ym":"2026-08","n":1978,"updated":"...","months":[...]}
  revenue/latest.json    最新月份完整資料
  revenue/YYYY-MM.json   各月份存檔（累積起來就有歷史，可看「近 12 個月新高」）

只用 Python 標準庫。資料沒變就不改檔（Actions 就不會多一筆 commit）。
用法: python fetch_revenue.py <輸出資料夾>
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

SRC = [
    ("L", "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"),
    ("O", "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O"),
]
TW = timezone(timedelta(hours=8))


def get(url):
    last = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (wanglai-news revenue board)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(5 * (i + 1))
    raise last


def num(v):
    try:
        return int(float(str(v).replace(",", "")))
    except Exception:
        return 0


def roc_ym(s):
    s = str(s).strip()
    y, m = int(s[:-2]) + 1911, int(s[-2:])
    return "%d-%02d" % (y, m)


def load(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def dump(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "revenue"
    os.makedirs(out, exist_ok=True)
    by_ym = {}
    issued = {}
    for mkt, url in SRC:
        try:
            data = get(url)
        except Exception as e:
            print("fetch failed", mkt, e)
            continue
        for x in data:
            code = str(x.get("公司代號", "")).strip()
            if not code:
                continue
            ym = roc_ym(x.get("資料年月", "0"))
            issued[mkt] = str(x.get("出表日期", ""))
            by_ym.setdefault(ym, []).append([
                code, str(x.get("公司名稱", "")).strip(), str(x.get("產業別", "")).strip(), mkt,
                num(x.get("營業收入-當月營收")), num(x.get("營業收入-上月營收")),
                num(x.get("營業收入-去年當月營收")),
                num(x.get("累計營業收入-當月累計營收")), num(x.get("累計營業收入-去年累計營收")),
                (str(x.get("備註", "")).strip() if str(x.get("備註", "")).strip() not in ("-", "") else ""),
            ])
    if not by_ym:
        print("no data")
        return 1

    changed = False
    for ym, rows in by_ym.items():
        rows.sort(key=lambda r: r[0])
        p = os.path.join(out, ym + ".json")
        old = load(p)
        if old and old.get("rows") == rows:
            continue
        if old and len(old.get("rows", [])) > len(rows):
            continue  # 不要用比較少的資料蓋掉
        dump(p, {"ym": ym, "issued": issued,
                 "cols": ["code", "name", "ind", "mkt", "rev", "prev", "ly", "cum", "cumly", "memo"],
                 "unit": "千元", "rows": rows})
        changed = True
        print("wrote", ym, len(rows))

    months = sorted(f[:-5] for f in os.listdir(out) if len(f) == 12 and f[4] == "-" and f.endswith(".json"))
    latest = months[-1]
    cur = load(os.path.join(out, latest + ".json"))

    # 近 12 個月新高：用累積的月份存檔算（有 6 個月以上歷史才標）
    hist = {}
    prev_months = [m for m in months if m < latest][-11:]
    for m in prev_months:
        d = load(os.path.join(out, m + ".json")) or {}
        for r in d.get("rows", []):
            hist.setdefault(r[0], []).append(r[4])
    high = []
    if len(prev_months) >= 5:
        for r in cur["rows"]:
            h = hist.get(r[0]) or []
            if len(h) >= 5 and r[4] > 0 and r[4] > max(h + [r[5], r[6]]):
                high.append(r[0])
    if cur.get("high12") != high:
        cur["high12"] = high
        dump(os.path.join(out, latest + ".json"), cur)
        changed = True

    latest_p = os.path.join(out, "latest.json")
    if changed or load(latest_p) != cur:
        dump(latest_p, cur)
        changed = True
    meta_p = os.path.join(out, "meta.json")
    meta_old = load(meta_p) or {}
    meta = {"ym": latest, "n": len(cur["rows"]), "months": months, "issued": cur.get("issued", {}),
            "updated": meta_old.get("updated", "")}
    if changed or {k: v for k, v in meta.items() if k != "updated"} != {k: v for k, v in meta_old.items() if k != "updated"}:
        meta["updated"] = datetime.now(TW).strftime("%Y-%m-%d %H:%M")
        dump(meta_p, meta)
    print("latest", latest, "rows", len(cur["rows"]), "high12", len(high), "changed", changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
