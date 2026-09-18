@echo off
setlocal
cd /d "%~dp0"
echo ==============================================================
echo PULSO HIDRICO MS - PRECHECK V0.9.1
echo ==============================================================
echo.
set ERR=0
if exist docs\index.html (echo OK  docs\index.html) else (echo FALTA docs\index.html & set ERR=1)
if exist docs\data\pulse-v8\index.json (echo OK  serie GloFAS V8) else (echo AVISO  falta docs\data\pulse-v8\index.json)
if exist docs\data\temperature-climatology.json (echo OK  DynQual) else (echo AVISO  falta temperatura)
if exist docs\data\outflow-ms.json (echo OK  saida hidrica) else (echo AVISO  falta docs\data\outflow-ms.json)
if exist docs\3d\index.html (echo OK  modo 3D) else (echo FALTA docs\3d\index.html & set ERR=1)
if exist docs\assets\final-v090.css (echo OK  estilo botao 3D) else (echo FALTA estilo final & set ERR=1)
echo.
if "%ERR%"=="0" (
  echo PRECHECK ESTRUTURAL OK.
) else (
  echo HA ARQUIVOS ESTRUTURAIS AUSENTES.
)
echo.
echo URLs locais:
echo   http://localhost:9564/
echo   http://localhost:9564/3d/
echo.
pause
endlocal
