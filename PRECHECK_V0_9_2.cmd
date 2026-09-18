@echo off
setlocal
cd /d "%~dp0"
echo ==============================================================
echo PULSO HIDRICO MS - PRECHECK V0.9.2
echo ==============================================================
echo.
set ERR=0
if exist docs\index.html (echo OK  interface 2D) else (echo FALTA docs\index.html & set ERR=1)
if exist docs\3d\index.html (echo OK  interface 3D) else (echo FALTA docs\3d\index.html & set ERR=1)
if exist docs\assets\final-v090.css (echo OK  estilo integrado) else (echo FALTA estilo integrado & set ERR=1)
if exist docs\data\pulse-v8\index.json (echo OK  GloFAS V8) else (echo AVISO  falta serie GloFAS V8)
if exist docs\data\temperature-climatology.json (echo OK  DynQual) else (echo AVISO  falta DynQual)
if exist docs\data\outflow-ms.json (echo OK  saida hidrica) else (echo AVISO  falta saida hidrica)
echo.
echo VERIFICACAO MANUAL:
echo   1. Na raiz, deve existir botao 3D.
echo   2. No /3d/, deve existir botao 2D mesmo no celular.
echo   3. Em Informacao, ITA ARANDU MS e PIH-MS devem ser clicaveis.
echo.
if "%ERR%"=="0" (echo PRECHECK ESTRUTURAL OK.) else (echo HA ARQUIVOS AUSENTES.)
echo.
pause
endlocal
