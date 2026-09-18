@echo off
setlocal
cd /d "%~dp0"
title Pulso Hidrico MS - Preparar saida hidrica

echo ============================================================
echo PULSO HIDRICO MS - SAIDA HIDRICA DE MS
echo ============================================================
echo.
echo Calcula a serie diaria agregada nos cruzamentos GloFAS/LISFLOOD
echo que saem de Mato Grosso do Sul. Nao baixa novamente os 25 anos.
echo Usa os blocos V8 que ja estao em docs\data\pulse-v8.
echo.

py scripts\21_build_outflow_ms.py
if errorlevel 1 (
  echo.
  echo ERRO: a serie de saida nao foi criada.
  echo Nao apague os dados existentes. Envie a mensagem de erro se precisar.
  pause
  exit /b 1
)

echo.
echo OK. Recarregue a PWA com Ctrl+Shift+R ou atualize o GitHub Pages.
pause
endlocal
