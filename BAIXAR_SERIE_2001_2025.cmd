@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - V8.2 serie 2001-2025

echo ====================================================================
echo PULSO HIDRICO MS - V8.2 - GloFAS v4 2001-2025
echo ====================================================================
echo.
echo Correcao V8.2:
echo - preserva respostas anuais EWDS incompletas;
echo - detecta exatamente os dias ausentes;
echo - baixa apenas o(s) dia(s) faltante(s);
echo - combina tudo no processamento mensal.
echo.
echo A serie continua REANUDAVEL. Nao apague os arquivos ja baixados.
echo.
pause

py -m pip install -r requirements.txt
if errorlevel 1 goto :erro

py scripts\v8_run_series.py --start-year 2001 --end-year 2025
if errorlevel 1 goto :erro

py scripts\v8_audit_archive.py
if errorlevel 1 goto :erro

echo.
echo ====================================================================
echo V8.2 CONCLUIDA. Recarregue localhost:9564 com Ctrl+Shift+R.
echo ====================================================================
pause
exit /b 0

:erro
echo.
echo ====================================================================
echo O processo parou com erro.
echo NAO APAGUE NADA: a serie e reanudavel.
echo A V8.2 preserva o arquivo anual e tenta reparar apenas dias ausentes.
echo ====================================================================
pause
exit /b 1
