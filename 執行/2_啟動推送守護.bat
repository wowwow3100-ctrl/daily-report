@echo off
REM Start the news-site push daemon in the background.
cd /d "%~dp0.."
where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "" pythonw push_daemon.py
) else (
  start "" /min python push_daemon.py
)
timeout /t 4 >nul
echo Heartbeat file content:
type .push_heartbeat 2>nul
echo.
echo If you see a fresh timestamp above, the daemon is running.
pause
