@echo off
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

python verifica_installazione.py

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
