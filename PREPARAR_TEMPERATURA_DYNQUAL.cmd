@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - Temperatura DynQual

echo ==============================================================
echo PULSO HIDRICO MS - PREPARAR TEMPERATURA DA AGUA
echo DynQual 1980-2019 - climatologia mensal 0,5 grau
echo ==============================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

echo [1/2] Verificando dependencias Python...
%PY% -m pip install --user --upgrade requests numpy netCDF4
if errorlevel 1 goto :erro

echo.
echo [2/2] Baixando/processando DynQual...
%PY% scripts\v85_prepare_temperature.py
if errorlevel 1 goto :erro

echo.
echo ==============================================================
echo TEMPERATURA PREPARADA COM SUCESSO.
echo Recarregue http://localhost:9564 com Ctrl+Shift+R.
echo ==============================================================
pause
exit /b 0

:erro
echo.
echo ==============================================================
echo O PROCESSO PAROU COM ERRO.
echo Nao apague os dados ja baixados. Envie uma captura do erro.
echo ==============================================================
pause
exit /b 1
