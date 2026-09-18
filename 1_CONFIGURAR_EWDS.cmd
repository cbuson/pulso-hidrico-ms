@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Pulso Hidrico MS - Configurar Copernicus EWDS

echo ============================================================
echo  PULSO HIDRICO MS - CONFIGURAR EWDS API
echo ============================================================
echo.
echo GloFAS nao esta no Climate Data Store (CDS).
echo Desde 2024 os dados CEMS/GloFAS estao no Early Warning Data Store (EWDS).
echo.
echo Este assistente cria o arquivo %%USERPROFILE%%\.cdsapirc corretamente.
echo Voce precisa copiar o PERSONAL ACCESS TOKEN mostrado na sua conta EWDS.
echo NAO use o token da pagina CDS.
echo.
echo Vou abrir:
echo  1. EWDS - configuracao da API/token
echo  2. GloFAS Historical no EWDS - aceitar a licenca
echo.
pause
start "" "https://ewds.climate.copernicus.eu/how-to-api"
start "" "https://ewds.climate.copernicus.eu/datasets/cems-glofas-historical?tab=download"

echo.
echo Entre na sua conta EWDS.
echo Na pagina HOW TO API copie SOMENTE o valor depois de "key:".
echo.
set /p EWDS_TOKEN=COLE O TOKEN EWDS AQUI e pressione ENTER: 
if "%EWDS_TOKEN%"=="" goto :sem_token

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Join-Path $env:USERPROFILE '.cdsapirc'; @('url: https://ewds.climate.copernicus.eu/api', ('key: ' + $env:EWDS_TOKEN)) | Set-Content -Path $p -Encoding ascii; Write-Host ('Arquivo criado: ' + $p)"
if errorlevel 1 goto :erro

where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py
) else (
  where python >nul 2>nul
  if errorlevel 1 goto :sem_python
  set PY=python
)

echo.
echo Instalando/atualizando cdsapi...
%PY% -m pip install --upgrade "cdsapi>=0.7.7"
if errorlevel 1 goto :erro

echo.
echo Verificando configuracao EWDS...
%PY% scripts\12_check_cds_setup.py
if errorlevel 1 goto :erro

echo.
echo ============================================================
echo  CONFIGURACAO EWDS CONCLUIDA.
echo.
echo  IMPORTANTE: aceite a licenca do GloFAS Historical no EWDS.
echo  Depois execute: 2_BAIXAR_GLOFAS_TESTE.cmd
echo ============================================================
pause
exit /b 0

:sem_token
echo.
echo Nenhum token foi informado. Nada foi alterado.
pause
exit /b 2

:sem_python
echo.
echo Python nao foi encontrado. Teste no CMD: py --version
pause
exit /b 3

:erro
echo.
echo A configuracao parou com erro. Fotografe esta tela.
pause
exit /b 1
