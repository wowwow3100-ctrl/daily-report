@echo off
REM Install a Windows Task Scheduler job that checks the push daemon every 10 minutes
REM and restarts it if the heartbeat is stale. Remove it later with:
REM   schtasks /delete /tn WanglaiPushWatchdog /f
cd /d "%~dp0.."
set "ROOT=%CD%"
set "PYW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW (
  for /f "delims=" %%i in ('where python 2^>nul') do if not defined PYW set "PYW=%%i"
)
if not defined PYW (
  echo Python was not found. Nothing installed.
  timeout /t 10 >nul
  exit /b 1
)
schtasks /create /tn "WanglaiPushWatchdog" /sc minute /mo 10 /tr "\"%PYW%\" \"%ROOT%\watchdog.py\"" /f
echo.
schtasks /query /tn "WanglaiPushWatchdog"
echo.
echo If you see WanglaiPushWatchdog above, the watchdog is installed.
timeout /t 10 >nul
