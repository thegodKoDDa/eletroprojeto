@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\start_local.py --setup %*
) else (
  python scripts\start_local.py --setup %*
)
if errorlevel 1 pause
endlocal
