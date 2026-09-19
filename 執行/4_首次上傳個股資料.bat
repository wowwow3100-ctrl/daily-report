@echo off
REM One-time bulk upload: rebuild data files, then commit and push EVERYTHING
REM (bypasses the daemon's 30-file safety limit on purpose).
REM .gitignore already blocks *.pdf so full broker reports never go public.
cd /d "%~dp0.."
python sync_reports.py
git add -A
git -c user.email=wowwow3100@gmail.com -c user.name=wowwow3100-ctrl commit -m "feat: bulk upload stock report summaries + manifest"
git push origin main
echo.
echo ==========================================
echo Done. If you see errors above, screenshot and tell Claude.
echo ==========================================
pause
