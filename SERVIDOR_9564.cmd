@echo off
cd /d "%~dp0docs"
where py >nul 2>nul && (py -m http.server 9564) || (python -m http.server 9564)
