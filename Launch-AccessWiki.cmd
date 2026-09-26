@echo off
setlocal
if /I "%~1"=="--check" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-AccessWiki.ps1" -Group G6 -ValidateOnly
  exit /b
)
echo AccessWiki - select group
choice /C 123456 /N /M "Group G1-G6: press 1, 2, 3, 4, 5 or 6: "
if errorlevel 7 exit /b 1
if errorlevel 1 (set "awGroup=G%errorlevel%") else (exit /b 1)
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-AccessWiki.ps1" -Group %awGroup%
