@echo off
chcp 65001 >nul
title RCS - Cruscotto Aziendale
cd /d "%~dp0"

echo ========================================
echo   RCS - Cruscotto Aziendale
echo   (sola lettura - non modifica i dati)
echo ========================================
echo.

REM Prova prima 'python', poi 'py' (launcher Windows)
python genera_report.py
if %errorlevel% neq 0 (
    py genera_report.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Python non trovato o errore di esecuzione.
    echo Assicurati che Python 3 sia installato.
    echo.
    pause
)
