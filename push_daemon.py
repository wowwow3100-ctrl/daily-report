# -*- coding: utf-8 -*-
"""
旺來新聞站 · 推送守護精靈 (push_daemon.py)
=============================================
跑在使用者 PC 背景, 監聽 D:\\APP\\旺來新聞站\\.push_request, 看到就自動 git push。
複製自生命線 App 的推送精靈模式 (2026-09-19), 守同樣的護欄。

互動檔 (都在本資料夾):
  .push_request   ← 觸發檔 (內容第一行=commit subject, 其餘=body)
  .push_result    → 結果 JSON {status, commit_hash, output, error, files, ts}
  .push_heartbeat → 每輪寫一次 (timestamp + PID), 證明還活著
  .push_paused    ← 放著就暫停 (自己建/刪)
  logs/push_daemon.log → 完整 log

安全護欄:
  - 改動 > 30 檔 → 拒推
  - *.xlsx / *.xls / *.bak / .env / secrets/ 改動 → 拒推
  - branch 不是 main → 拒推
  - 30 秒內只准推 1 次
  - 推前自動清 .git lock
"""
import os
import time
import json
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REQ       = os.path.join(HERE, ".push_request")
RESULT    = os.path.join(HERE, ".push_result")
HEARTBEAT = os.path.join(HERE, ".push_heartbeat")
PAUSE     = os.path.join(HERE, ".push_paused")
LOGDIR    = os.path.join(HERE, "logs")
LOG       = os.path.join(LOGDIR, "push_daemon.log")

POLL_SEC       = 5
RATE_LIMIT_SEC = 30
MAX_FILES      = 30
BAD_SUFFIX     = (".xlsx", ".xls", ".bak", ".env")
GIT_AUTHOR     = ["-c", "user.email=wowwow3100@gmail.com", "-c", "user.name=wowwow3100-ctrl"]

_last_push_ts = 0.0


def log(msg):
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), msg))
    except Exception:
        pass


def git(args, timeout=180):
    try:
        p = subprocess.run(["git"] + args, cwd=HERE, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except Exception as e:
        return 1, "", "subprocess error: %s" % e


def write_result(d):
    try:
        d["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
        with open(RESULT, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log("write_result failed: %s" % e)


def clear_locks():
    for lk in (".git/index.lock", ".git/HEAD.lock"):
        try:
            os.remove(os.path.join(HERE, lk))
            log("cleared stale %s" % lk)
        except OSError:
            pass


def changed_files():
    rc, out, err = git(["status", "--porcelain"])
    if rc != 0:
        return None, err
    files = [ln[3:].strip().strip('"') for ln in out.splitlines() if ln.strip()]
    return files, ""


def safety_check(files):
    if len(files) > MAX_FILES:
        return "too many files changed (%d > %d)" % (len(files), MAX_FILES)
    for f in files:
        low = f.lower()
        if low.endswith(BAD_SUFFIX) or low.startswith("secrets/") or "/.env" in low or low == ".env":
            return "blocked file in change set: %s" % f
    rc, out, _ = git(["rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0 or out.strip() != "main":
        return "branch is not main (%s)" % out.strip()
    return None


def do_push():
    global _last_push_ts
    if time.time() - _last_push_ts < RATE_LIMIT_SEC:
        write_result({"status": "rejected", "error": "rate limited, wait 30s"})
        return
    try:
        with open(REQ, encoding="utf-8") as f:
            msg = f.read().strip() or "update news site"
    except Exception:
        msg = "update news site"
    try:
        os.remove(REQ)
    except OSError:
        pass

    clear_locks()
    files, err = changed_files()
    if files is None:
        write_result({"status": "error", "error": "git status failed: %s" % err})
        return
    if not files:
        write_result({"status": "noop", "output": "nothing to commit"})
        return
    reason = safety_check(files)
    if reason:
        write_result({"status": "rejected", "error": reason, "files": files})
        log("REJECTED: %s" % reason)
        return

    subject = msg.splitlines()[0][:120]
    body = "\n".join(msg.splitlines()[1:]).strip()
    rc1, o1, e1 = git(["add", "-A"])
    cargs = GIT_AUTHOR + ["commit", "-m", subject] + (["-m", body] if body else [])
    rc2, o2, e2 = git(cargs)
    rc3, o3, e3 = git(["push", "origin", "main"])
    rc4, sha, _ = git(["rev-parse", "--short", "HEAD"])

    ok = (rc1 == 0 and rc2 == 0 and rc3 == 0)
    _last_push_ts = time.time()
    write_result({
        "status": "ok" if ok else "error",
        "commit_hash": sha.strip(),
        "files": files,
        "output": (o1 + o2 + o3)[-1500:],
        "error": "" if ok else (e1 + e2 + e3)[-1500:],
    })
    log("push %s (%d files) -> %s" % ("OK" if ok else "FAILED", len(files), sha.strip()))


def main():
    log("news push daemon started PID=%d" % os.getpid())
    while True:
        try:
            with open(HEARTBEAT, "w", encoding="utf-8") as f:
                f.write("%s PID=%d\n" % (datetime.datetime.now().isoformat(timespec="seconds"), os.getpid()))
            if os.path.exists(PAUSE):
                time.sleep(POLL_SEC)
                continue
            if os.path.exists(REQ):
                do_push()
        except Exception as e:
            log("loop error: %s" % e)
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
