@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - Preparar saida hidrica

echo ============================================================
echo PULSO HIDRICO MS - PREPARAR SAIDA HIDRICA
echo ============================================================
echo.
echo Esta etapa NAO baixa novamente o GloFAS.
echo Usa os blocos existentes em docs\data\pulse-v8.
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERRO: Python nao foi encontrado pelo comando "py".
  pause
  exit /b 1
)

echo [1/3] Verificando dependencias...
py -c "import numpy, shapely" >nul 2>nul
if errorlevel 1 (
  echo Instalando numpy e shapely...
  py -m pip install --upgrade numpy shapely
  if errorlevel 1 goto :fail
)

echo [2/3] Verificando arquivos necessarios...
if not exist "docs\data\pulse-v8\index.json" (
  echo ERRO: docs\data\pulse-v8\index.json nao encontrado.
  echo A serie V8 precisa estar presente antes de gerar a grafica.
  goto :fail
)
if not exist "docs\data\glofas_network.geojson" (
  echo ERRO: docs\data\glofas_network.geojson nao encontrado.
  goto :fail
)
if not exist "docs\data\boundary.geojson" (
  echo ERRO: docs\data\boundary.geojson nao encontrado.
  goto :fail
)

echo [3/3] Calculando serie diaria de saida...
py scripts\21_build_outflow_ms.py
if errorlevel 1 goto :fail

if not exist "docs\data\outflow-ms.json" goto :fail
if not exist "docs\data\outflow-ms.csv" goto :fail
if not exist "docs\data\outflow-ms-outlets.geojson" goto :fail

echo.
echo ============================================================
echo OK - GRAFICA PREPARADA
for %%F in ("docs\data\outflow-ms.json" "docs\data\outflow-ms.csv" "docs\data\outflow-ms-outlets.geojson") do echo   %%~nxF   %%~zF bytes
echo ============================================================
echo.
echo IMPORTANTE PARA GITHUB PAGES:
echo faca COMMIT e PUSH destes tres arquivos em docs\data\
echo Caso contrario a grafica funcionara localmente, mas nao online.
echo.
echo Depois da publicacao, recarregue o celular.
pause
exit /b 0

:fail
echo.
echo ============================================================
echo ERRO - A GRAFICA NAO FOI GERADA

echo Nao apague nenhum dado existente.
echo Envie uma captura desta janela se precisar de ajuda.
echo ============================================================
pause
exit /b 1
