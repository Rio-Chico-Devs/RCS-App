@echo off
setlocal EnableDelayedExpansion
echo ========================================================
echo  VERIFICA DELL'INSTALLAZIONE - RCS Gestione Preventivi
echo ========================================================
echo.
echo  Questo controllo NON MODIFICA NULLA.
echo  Non tocca il database, non crea copie, non cambia
echo  impostazioni: legge soltanto e dice come sta l'installazione.
echo.
echo  Alla fine crea un file VERIFICA_....txt da inviare
echo  all'assistenza se qualcosa non va.
echo.
echo --------------------------------------------------------
echo.

REM ----------------------------------------------------------------
REM  Su Windows e' normale avere piu' versioni di Python installate,
REM  e i pacchetti installati in una NON si vedono dalle altre.
REM  Scrivendo solo "python" si prende la prima che capita: e' successo
REM  davvero, il controllo e' partito con la 3.11 mentre il programma
REM  gira con la 3.13, e ha dichiarato PyQt5 mancante e otto file del
REM  programma assenti. Tutti falsi allarmi, ed era saltato proprio il
REM  controllo delle linguette.
REM
REM  Quindi si cerca il Python che ha DAVVERO PyQt5, provandoli in
REM  ordine. Se nessuno ce l'ha si usa comunque "python": il controllo
REM  parte lo stesso e spiega la situazione, invece di non partire.
REM ----------------------------------------------------------------
set "PYEXE="
for %%C in ("py -3.13" "py -3.12" "py -3.11" "py -3" "py" "python") do (
    if not defined PYEXE (
        %%~C -c "import PyQt5" >nul 2>&1
        if !errorlevel! equ 0 set "PYEXE=%%~C"
    )
)

if not defined PYEXE (
    echo  ATTENZIONE: non ho trovato un Python con PyQt5 installato.
    echo  Il controllo parte lo stesso e ti spiega cosa significa.
    echo.
    set "PYEXE=python"
)

echo  Controllo eseguito con: %PYEXE%
echo.
%PYEXE% verifica_installazione.py

if errorlevel 9009 (
    echo.
    echo ERRORE: Python non risulta installato su questo computer,
    echo oppure non e' raggiungibile dal Prompt dei comandi.
    echo.
    echo Se il programma viene usato come eseguibile ^(.exe^) questo
    echo controllo non serve: eseguilo sul computer dove si sviluppa.
    echo.
    pause
)
