@echo off
chcp 65001 >nul
title RCS - Notiziario di settore
cd /d "%~dp0"

echo Raccolta notizie di settore dal web...
echo.

python notiziario.py
if %errorlevel% neq 0 (
    py notiziario.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Python non trovato, oppure chiave API mancante.
    echo Vedi README.md per la configurazione.
)
echo.
pause
