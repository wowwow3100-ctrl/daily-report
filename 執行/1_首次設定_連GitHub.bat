@echo off
REM First-time setup: link this folder to GitHub and push.
REM Requires: git installed, and the GitHub repo "daily-report" already created.
cd /d "%~dp0.."
if not exist ".git" (
  git init
  git branch -M main
  git remote add origin https://github.com/wowwow3100-ctrl/daily-report.git
)
git add -A
git -c user.email=wowwow3100@gmail.com -c user.name=wowwow3100-ctrl commit -m "init: wanglai news site"
git push -u origin main
echo.
echo ==========================================
echo Done. If you see errors above, screenshot and tell Claude.
echo ==========================================
pause
