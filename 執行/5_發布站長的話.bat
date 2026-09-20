@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ============================================================
echo   Publish owner message (announce.txt)
echo ============================================================
echo How to use:
echo   1. Edit announce.txt in this folder with Notepad.
echo      (Empty file = the message bar is hidden on the site.)
echo   2. Double-click this bat to publish.
echo   Requires the push daemon to be running (bat 2).
echo.
echo update: owner message (announce)>.push_request
echo announce.txt>>.push_request
echo Request sent. The new message goes live in about 1 minute
echo (CDN may take up to 10 minutes to show it everywhere).
pause
