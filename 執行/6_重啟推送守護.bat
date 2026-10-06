@echo off
REM Restart the news-site push daemon (stop old push_daemon.py, start a new one).
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*push_daemon.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
timeout /t 2 >nul
del /q .push_heartbeat 2>nul
where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "" pythonw push_daemon.py
) else (
  start "" /min python push_daemon.py
)
timeout /t 5 >nul
echo Heartbeat file content:
type .push_heartbeat 2>nul
echo.
echo If you see a fresh timestamp above, the daemon has been restarted.
timeout /t 8 >nul
