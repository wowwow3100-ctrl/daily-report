# -*- coding: utf-8 -*-
"""
旺來新聞站 · 推送守護看門狗 (watchdog.py)
=========================================
由 Windows 工作排程器每 10 分鐘叫一次（排程名稱 WanglaiPushWatchdog）。
看 .push_heartbeat 有沒有在 2 分鐘內更新；沒有就把 push_daemon.py 重新叫起來。
要停用：工作排程器裡刪掉 WanglaiPushWatchdog，或在本資料夾放一個 .watchdog_off 檔。
"""
import os
import subprocess
import sys
import time
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
HB = os.path.join(HERE, ".push_heartbeat")
LOG = os.path.join(HERE, "logs", "push_daemon.log")


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("[%s] watchdog: %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), msg))
    except Exception:
        pass


def main():
    if os.path.exists(os.path.join(HERE, ".watchdog_off")):
        return
    try:  # 留個足跡：證明工作排程器有在叫看門狗
        with open(os.path.join(HERE, ".watchdog_last"), "w", encoding="utf-8") as f:
            f.write(datetime.datetime.now().isoformat(timespec="seconds"))
    except Exception:
        pass
    try:
        age = time.time() - os.path.getmtime(HB)
    except OSError:
        age = 1e9
    if age < 120:
        return
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        w = exe[:-10] + "pythonw.exe"
        if os.path.exists(w):
            exe = w
    flags = (0x08000000 | 0x00000008) if os.name == "nt" else 0
    subprocess.Popen([exe, os.path.join(HERE, "push_daemon.py"), "--reloaded"], cwd=HERE,
                     creationflags=flags, close_fds=True)
    log("heartbeat %.0fs old, restarted push daemon" % age)


if __name__ == "__main__":
    main()
