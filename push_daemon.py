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
    (例外: commit subject 以 "bulk:" 開頭 → 上限放寬到 2000 檔,
     給排程任務/大批量補檔用; 敏感檔檢查照常)
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
                           text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=(0x08000000 if os.name == "nt" else 0))
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


def safety_check(files, bulk=False):
    limit = 2000 if bulk else MAX_FILES
    if len(files) > limit:
        return "too many files changed (%d > %d)%s" % (
            len(files), limit, "" if bulk else "; prefix subject with 'bulk:' to allow up to 2000")
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
    subject_line = (msg.splitlines()[0] if msg else "").strip()
    bulk = subject_line.lower().startswith("bulk:")
    reason = safety_check(files, bulk=bulk)
    if reason:
        write_result({"status": "rejected", "error": reason, "files": files[:30]})
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


# ---------------------------------------------------------------------------
# 資料幫浦（2026-10-06 加）：GitHub Actions 的排程常常被延後或跳過，
# 營收、資金流向會卡住。改由這台電腦定時自己抓（台灣網路直連證交所／觀測站），
# 寫進 data 分支並推上去；Actions 留著當備援。
#   營收：每月 1~14 日 08:00~23:00 每小時一次；其他日子 08/14/20 點各一次
#   資金流向：週一到週五 14、15、17、20 點（45 分後）各一次
# data 分支放在 repo 外面的資料夾（D:\APP\_wl_data_branch），不會混進 main。
# ---------------------------------------------------------------------------
import sys
NOWIN = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW：pythonw 底下跑 git 不要跳黑窗
DATA_WT = os.path.join(os.path.dirname(HERE), "_wl_data_branch")
PUMP_STATUS = os.path.join(HERE, ".pump_status")
_pump_done = {}


def gitc(args, cwd, timeout=240):
    try:
        p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, creationflags=NOWIN)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except Exception as e:
        return 1, "", "subprocess error: %s" % e


def ensure_data_wt():
    if os.path.exists(os.path.join(DATA_WT, ".git")):
        gitc(["fetch", "origin", "data"], DATA_WT)
        rc, _, err = gitc(["reset", "--hard", "origin/data"], DATA_WT)
        return rc == 0, err
    gitc(["fetch", "origin", "data"], HERE)
    gitc(["worktree", "prune"], HERE)
    rc, _, err = gitc(["worktree", "add", "-f", "-B", "data-local", DATA_WT, "origin/data"], HERE)
    return rc == 0, err


def pump(kind):
    script = {"revenue": "fetch_revenue.py", "sectors": "fetch_sectors.py"}[kind]
    st = {"kind": kind, "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    ok, err = ensure_data_wt()
    if not ok:
        st.update(status="error", error="worktree: " + err[-400:])
    else:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        try:
            p = subprocess.run([sys.executable, os.path.join(HERE, "tools", script), os.path.join(DATA_WT, kind)],
                               cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=900, env=env, creationflags=NOWIN)
            st["fetch"] = (p.stdout or "")[-600:] + (p.stderr or "")[-400:]
        except Exception as e:
            st["fetch"] = "fetch error: %s" % e
        gitc(["add", "-A"], DATA_WT)
        rc, _, _ = gitc(["diff", "--cached", "--quiet"], DATA_WT)
        if rc == 0:
            st["status"] = "nochange"
        else:
            gitc(GIT_AUTHOR + ["commit", "-m", "%s %s (local pump)" % (kind, datetime.datetime.now().strftime("%Y-%m-%d_%H%M"))], DATA_WT)
            rc, _, e1 = gitc(["push", "origin", "HEAD:data"], DATA_WT)
            if rc != 0:
                gitc(["pull", "--rebase", "origin", "data"], DATA_WT)
                rc, _, e1 = gitc(["push", "origin", "HEAD:data"], DATA_WT)
            st["status"] = "pushed" if rc == 0 else "push_error"
            if rc != 0:
                st["error"] = e1[-400:]
    try:
        allst = {}
        if os.path.exists(PUMP_STATUS):
            with open(PUMP_STATUS, encoding="utf-8") as f:
                allst = json.load(f)
        allst[kind] = st
        with open(PUMP_STATUS, "w", encoding="utf-8") as f:
            json.dump(allst, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    log("pump %s -> %s" % (kind, st.get("status")))


def pump_due(now):
    due = []
    h, m, d, wd = now.hour, now.minute, now.day, now.weekday()
    if (1 <= d <= 14 and 8 <= h <= 23 and m >= 5) or (h in (8, 14, 20) and m >= 25):
        key = ("revenue", now.strftime("%Y%m%d%H"))
        if key not in _pump_done:
            due.append(key)
    if wd < 5 and h in (14, 15, 17, 20) and m >= 45:
        key = ("sectors", now.strftime("%Y%m%d%H"))
        if key not in _pump_done:
            due.append(key)
    return due


def run_pumps():
    if os.path.exists(os.path.join(HERE, ".pump_paused")):
        return
    for key in pump_due(datetime.datetime.now()):
        _pump_done[key] = 1
        try:
            pump(key[0])
        except Exception as e:
            log("pump %s crashed: %s" % (key[0], e))
    if os.path.exists(os.path.join(HERE, ".pump_now")):  # 手動立刻跑一次（內容寫 revenue 或 sectors，空白＝兩個都跑）
        try:
            with open(os.path.join(HERE, ".pump_now"), encoding="utf-8") as f:
                want = f.read().strip()
            os.remove(os.path.join(HERE, ".pump_now"))
        except Exception:
            want = ""
        for k in (["revenue", "sectors"] if not want else [want]):
            try:
                pump(k)
            except Exception as e:
                log("pump %s crashed: %s" % (k, e))


_SELF_MTIME = os.path.getmtime(os.path.abspath(__file__))


def maybe_reload():
    """push_daemon.py 被更新了就自己重開（不用再請使用者手動重啟）。"""
    try:
        if os.path.getmtime(os.path.abspath(__file__)) != _SELF_MTIME:
            log("source changed, reloading")
            subprocess.Popen([sys.executable, os.path.abspath(__file__), "--reloaded"], cwd=HERE,
                             creationflags=(NOWIN | 0x00000008) if os.name == "nt" else 0, close_fds=True)
            os._exit(0)
    except Exception as e:
        log("reload failed: %s" % e)


def another_running():
    """已經有一隻守護在跑（心跳 20 秒內有更新）就不要再開第二隻，避免重複推送。"""
    try:
        age = time.time() - os.path.getmtime(HEARTBEAT)
        with open(HEARTBEAT, encoding="utf-8") as f:
            pid = f.read().strip().split("PID=")[-1]
        return age < 20 and pid and int(pid) != os.getpid()
    except Exception:
        return False


def main():
    if "--reloaded" not in sys.argv and another_running():
        return
    log("news push daemon started PID=%d" % os.getpid())
    while True:
        try:
            with open(HEARTBEAT, "w", encoding="utf-8") as f:
                f.write("%s PID=%d\n" % (datetime.datetime.now().isoformat(timespec="seconds"), os.getpid()))
            if os.path.exists(os.path.join(HERE, ".push_restart")):
                os.remove(os.path.join(HERE, ".push_restart"))
                log("restart requested")
                subprocess.Popen([sys.executable, os.path.abspath(__file__), "--reloaded"], cwd=HERE,
                                 creationflags=(NOWIN | 0x00000008) if os.name == "nt" else 0, close_fds=True)
                os._exit(0)
            maybe_reload()
            if os.path.exists(PAUSE):
                time.sleep(POLL_SEC)
                continue
            if os.path.exists(REQ):
                do_push()
            run_pumps()
        except Exception as e:
            log("loop error: %s" % e)
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
