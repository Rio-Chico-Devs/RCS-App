@echo off
echo ========================================
echo   Migrazione Database - RCS App
echo ========================================
echo.
echo Questo script converte il vecchio database al nuovo formato.
echo Verra' creato automaticamente un file di backup prima di ogni modifica.
echo.

if "%~1"=="" (
    echo Trascina il file materiali.db su questo batch oppure premi Invio
    echo per usare il database nella cartella data\ corrente.
    echo.
    python migrazione_db.py
) else (
    python migrazione_db.py "%~1"
)

echo.
pause
