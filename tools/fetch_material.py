# -*- coding: utf-8 -*-
"""
旺來新聞站 · 個股重大訊息 (tools/fetch_material.py)  v2
=====================================================
改抓「公開資訊觀測站 當日重大訊息」(mops.twse.com.tw/mops/api/t05st02)，
上市＋上櫃、即時、最近 8 天都抓得到（原本的 OpenAPI 只給前一天、會漏）。
新出現的公告再呼叫 t05st02_detail 補上說明內文（已抓過的不重抓）。
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
API = "https://mops.twse.com.tw/mops/api/"
KEEP_DAYS = 8
MKT = {"sii": "L", "otc": "O"}          # 只收上市、上櫃（興櫃 rotc、公開發行 pub 不收）
MAX_DETAIL = 250                        # 每次最多補幾則內文，避免一次打太多


def post(name, body):
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(API + name, data=json.dumps(body).encode("utf-8"), headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
                "Content-Type": "application/json", "Accept": "application/json",
                "Origin": "https://mops.twse.com.tw", "Referer": "https://mops.twse.com.tw/mops/"})
            with urllib.request.urlopen(req, timeout=40) as r:
                j = json.loads(r.read().decode("utf-8"))
            if j.get("code") == 200:
                return j.get("result") or {}
            last = Exception("code %s %s" % (j.get("code"), j.get("message")))
        except Exception as e:  # noqa
            last = e
        time.sleep(2 * (i + 1))
    raise last


def roc2iso(s):
    try:
        y, m, d = str(s).split("/")
        return "%04d-%02d-%02d" % (int(y) + 1911, int(m), int(d))
    except Exception:
        return ""


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "material"
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, "latest.json")
    try:
        old = json.load(open(p, encoding="utf-8"))
    except Exception:
        old = {"items": []}
    keep = {}
    for x in old.get("items", []):
        keep[x.get("k") or "%s|%s|%s|%s" % (x["d"], x["t"], x["c"], x["title"][:30])] = x
    now = datetime.now(TW)
    ok_days = 0
    for k in range(KEEP_DAYS):
        day = now - timedelta(days=k)
        try:
            res = post("t05st02", {"year": str(day.year - 1911), "month": str(day.month), "day": str(day.day)})
        except Exception as e:
            print("list fail", day.date(), e)
            continue
        ok_days += 1
        for r in res.get("data") or []:
            try:
                d, t, code, name, title, meta = r[0], r[1], r[2], r[3], r[4], r[5]
                prm = (meta or {}).get("parameters") or {}
            except Exception:
                continue
            mk = MKT.get(prm.get("marketKind"))
            if not mk:
                continue
            key = "%s|%s|%s" % (prm.get("enterDate", ""), code, prm.get("serialNumber", ""))
            x = keep.get(key) or {}
            x.update({"k": key, "d": roc2iso(d), "t": str(t)[:5], "c": str(code).strip(), "n": str(name).strip(), "m": mk,
                      "title": " ".join(str(title).split())[:160], "p": prm})
            keep[key] = x
        time.sleep(0.6)
    if not ok_days:
        print("mops unreachable, keep old")
        return 1
    cut = (now - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    arr = [x for x in keep.values() if x.get("d", "") >= cut and x.get("p")]
    arr.sort(key=lambda x: (x["d"], x["t"], x["c"]), reverse=True)
    # 補內文：只補還沒有 body 的，新的優先
    n = 0
    for x in arr:
        if "body" in x or n >= MAX_DETAIL:
            continue
        n += 1
        try:
            dres = post("t05st02_detail", x["p"])
            row = (dres.get("data") or [[]])[0]
            x["rule"] = ("第%s款" % row[7]) if len(row) > 7 and str(row[7]).strip() else ""
            x["fact"] = roc2iso(row[8]) if len(row) > 8 else ""
            x["body"] = " ".join(str(row[9]).split())[:700] if len(row) > 9 else ""
        except Exception as e:
            x["body"] = ""
            print("detail fail", x["c"], e)
        time.sleep(0.35)
    out = [{k: v for k, v in x.items() if k != "p"} | {"p": x["p"]} for x in arr]
    res = {"updated": now.strftime("%Y-%m-%d %H:%M"), "n": len(out), "src": "mops_t05st02", "items": out}
    if old.get("items") == res["items"]:
        print("no change", len(out))
        return 0
    with open(p, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", len(out), "details", n, "days", ok_days)
    return 0


if __name__ == "__main__":
    sys.exit(main())
