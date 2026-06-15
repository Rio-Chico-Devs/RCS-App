@echo off
chcp 65001 >nul
title Creazione eseguibili - Cruscotto Aziendale
cd /d "%~dp0"

echo ========================================
echo   Creazione eseguibili standalone
echo ========================================
echo.
echo [1/3] Installazione strumenti...
pip install pyinstaller anthropic

echo.
echo [2/3] Creazione CruscottoAziendale.exe ...
pyinstaller --onefile --name "CruscottoAziendale" cruscotto.py

echo.
echo [3/3] Creazione Notiziario.exe ...
pyinstaller --onefile --name "Notiziario" notiziario.py

echo.
echo ========================================
echo   Fatto. Gli .exe sono nella cartella  dist\
echo.
echo   IMPORTANTE: copia accanto agli .exe il file
echo   config.json con il percorso del database.
echo   (parti da config.example.json)
echo ========================================
echo.
pause
