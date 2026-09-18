@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - Validar grafica

echo ============================================================
echo VALIDACAO DA GRAFICA DE SAIDA HIDRICA

echo.
set ERR=0
for %%F in ("docs\data\outflow-ms.json" "docs\data\outflow-ms.csv" "docs\data\outflow-ms-outlets.geojson") do (
  if exist %%F (
    echo OK  %%~nxF  %%~zF bytes
  ) else (
    echo FALTA  %%~nxF
    set ERR=1
  )
)
if "%ERR%"=="1" (
  echo.
  echo Execute PREPARAR_SAIDA_HIDRICA_MS.cmd antes de publicar.
  pause
  exit /b 1
)

echo.
echo OK: os tres arquivos estao prontos para commit/push.
pause
exit /b 0
