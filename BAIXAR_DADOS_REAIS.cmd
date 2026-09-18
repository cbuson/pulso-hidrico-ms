@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py scripts\08_download_pin_hydrology.py) || (python scripts\08_download_pin_hydrology.py)
pause
