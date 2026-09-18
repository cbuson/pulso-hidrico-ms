@echo off
setlocal
cd /d "%~dp0"
echo ==============================================================
echo PULSO HIDRICO MS - APLICAR V0.9.2
echo ==============================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py scripts\finalize_v092.py
) else (
  python scripts\finalize_v092.py
)
endlocal
