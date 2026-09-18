@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - GloFAS teste

echo ============================================================
echo  PULSO HIDRICO MS - TESTE GLOFAS
echo  08/02/2001  08/02/2010  08/02/2020  08/02/2025
echo ============================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py
) else (
  set PY=python
)

%PY% -c "import cdsapi, xarray, netCDF4, numpy" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias minimas...
  %PY% -m pip install --upgrade "cdsapi>=0.7.7" xarray netCDF4 numpy
  if errorlevel 1 goto :erro
)

echo.
echo ETAPA 1/2 - Baixar quatro datas GloFAS
%PY% scripts\10_download_glofas_test_dates.py
if errorlevel 1 goto :erro

echo.
echo ETAPA 2/2 - Cruzar GloFAS com a rede PIN MS
%PY% scripts\11_build_pulse_from_pin.py
if errorlevel 1 goto :erro

echo.
echo ============================================================
echo  PRONTO.
echo  Recarregue http://localhost:9564 com Ctrl+Shift+R.
echo  Escolha 08/02/2001, 2010, 2020 ou 2025 e clique em REAL.
echo ============================================================
pause
exit /b 0

:erro
echo.
echo O processo parou com erro.
echo Consulte CONFIGURAR_GLOFAS.txt e copie a mensagem se precisar de ajuda.
pause
exit /b 1
