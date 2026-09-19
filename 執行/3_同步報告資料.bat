@echo off
REM Sync the research-report archive into this site and queue a push.
REM All real work happens in sync_reports.py (Chinese paths live there).
cd /d "%~dp0.."
python sync_reports.py
pause
