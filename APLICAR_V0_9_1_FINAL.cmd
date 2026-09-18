@echo off
setlocal
cd /d "%~dp0"
echo ==============================================================
echo PULSO HIDRICO MS - APLICAR V0.9.1 FINAL 2D + 3D
echo ==============================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py scripts\finalize_v091.py
) else (
  python scripts\finalize_v091.py
)
endlocal
