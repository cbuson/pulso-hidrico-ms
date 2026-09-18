@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - Preparar rede GloFAS V7

echo ================================================================
echo PULSO HIDRICO MS - V7 - REDE NATIVA GLOFAS / LISFLOOD
echo ================================================================
echo.
echo Esta etapa NAO baixa novamente os quatro dias GloFAS.
echo Reutiliza os NetCDF que voce ja baixou e acrescenta a rede estatica v4.
echo Download adicional aproximado: 108 MB uma unica vez.
echo.

py -m pip install -q requests xarray netCDF4 numpy shapely
if errorlevel 1 goto :erro

py scripts\13_download_glofas_static_v4.py
if errorlevel 1 goto :erro

py scripts\14_build_glofas_network_v4.py
if errorlevel 1 goto :erro

py scripts\15_build_pulse_glofas_native.py
if errorlevel 1 goto :erro

py scripts\16_audit_glofas_v7.py
if errorlevel 1 goto :erro

echo.
echo ================================================================
echo V7 CONCLUIDA
echo Recarregue http://localhost:9564 com Ctrl+Shift+R
echo Os quatro dias devem aparecer em modo REAL com rede GloFAS nativa.
echo ================================================================
pause
exit /b 0

:erro
echo.
echo O processo parou com erro. Tire uma captura desta janela.
pause
exit /b 1
