@echo off
setlocal EnableDelayedExpansion
echo ========================================
echo Creazione eseguibile Gestione Preventivi
echo ========================================
echo.

rem ----------------------------------------------------------------
rem  Su questo computer ci sono piu' versioni di Python, e i pacchetti
rem  installati in una NON si vedono dalle altre. Scrivendo solo
rem  "python" si prende la prima che capita: e' gia' successo con
rem  VERIFICA.bat, partito con la 3.11 mentre il programma gira con la
rem  3.13. Qui sarebbe peggio: si compilerebbe l'eseguibile con
rem  l'interprete sbagliato, o l'installazione dei pacchetti finirebbe
rem  in un Python diverso da quello che poi compila.
rem
rem  Si cerca quindi il Python che ha DAVVERO PyQt5 e si usa quello per
rem  tutto, con "-m pip" e "-m PyInstaller": cosi' non c'e' modo che
rem  qualche pezzo finisca altrove.
rem ----------------------------------------------------------------
set "PYEXE="
for %%C in ("py -3.13" "py -3.12" "py -3.11" "py -3" "py" "python") do (
    if not defined PYEXE (
        %%~C -c "import PyQt5" >nul 2>&1
        if !errorlevel! equ 0 set "PYEXE=%%~C"
    )
)
if not defined PYEXE (
    echo Nessun Python con PyQt5 gia' installato: uso quello predefinito
    echo e lo installo io.
    set "PYEXE=python"
)
echo Interprete usato per la compilazione: %PYEXE%
%PYEXE% -c "import sys; print('   versione:', sys.version.split()[0]); print('   percorso:', sys.executable)"
echo.

echo [1/5] Installazione dipendenze Python...
%PYEXE% -m pip install pyinstaller
%PYEXE% -m pip install PyQt5
%PYEXE% -m pip install PyQt5-sip
%PYEXE% -m pip install odfpy
%PYEXE% -m pip install reportlab

echo.
echo [2/5] Verifica dipendenze...
%PYEXE% -c "import PyQt5; print('PyQt5 OK')"
%PYEXE% -c "import sqlite3; print('sqlite3 OK')"
%PYEXE% -c "import PyInstaller; print('PyInstaller OK')"

echo.
echo [3/5] Creazione eseguibile...
rem I moduli sotto sono elencati uno per uno di proposito. PyInstaller di
rem solito li trova da solo, ma diversi vengono importati DENTRO le funzioni
rem e non in cima al file: se ne mancasse uno, l'eseguibile si creerebbe
rem senza errori e si pianterebbe solo al momento di usare quella funzione,
rem magari mesi dopo. Elencarli non costa nulla e toglie il dubbio.
%PYEXE% -m PyInstaller --onefile --windowed --name="GestionePreventivi" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtPrintSupport ^
    --hidden-import=sqlite3 ^
    --hidden-import=database ^
    --hidden-import=database.db_manager ^
    --hidden-import=database.backup_manager ^
    --hidden-import=database.archivio ^
    --hidden-import=database.esportazione ^
    --hidden-import=utils ^
    --hidden-import=utils.logger ^
    --hidden-import=utils.percorsi ^
    --hidden-import=utils.diagnostica ^
    --hidden-import=utils.bozze ^
    --hidden-import=utils.segnalazione ^
    --hidden-import=ui ^
    --hidden-import=ui.main_window ^
    --hidden-import=ui.main_window_business_logic ^
    --hidden-import=ui.main_window_ui_components ^
    --hidden-import=ui.preventivo_window ^
    --hidden-import=ui.visualizza_preventivi_window ^
    --hidden-import=ui.impostazioni_archiviazione_window ^
    --hidden-import=ui.finestre_preventivo ^
    --hidden-import=ui.responsive ^
    --hidden-import=ui.misure ^
    --hidden-import=ui.magazzino_window ^
    --hidden-import=ui.gestione_materiali_window ^
    --hidden-import=ui.anagrafica_clienti_window ^
    --hidden-import=ui.confronto_preventivi_window ^
    --hidden-import=ui.materiale_window ^
    --hidden-import=ui.materiale_business_logic ^
    --hidden-import=ui.materiale_ui_components ^
    --hidden-import=ui.tela_preview_widget ^
    --hidden-import=ui.visualizza_modifiche_dialog ^
    --hidden-import=ui.document_utils ^
    --hidden-import=models ^
    --hidden-import=models.preventivo ^
    --hidden-import=models.materiale ^
    main.py

echo.
echo [4/5] Verifica che l'eseguibile sia stato creato...
if not exist "dist\GestionePreventivi.exe" (
    echo.
    echo ATTENZIONE: l'eseguibile NON e' stato creato.
    echo Controlla i messaggi di errore qui sopra.
    echo.
    pause
    exit /b 1
)

echo.
echo [5/5] Completato!
echo.
echo L'eseguibile si trova in: dist\GestionePreventivi.exe
echo.
echo ATTENZIONE, l'errore piu' facile da fare adesso:
echo.
echo   NON avviare l'eseguibile da dentro la cartella "dist".
echo   Da li' non trova la configurazione e ti chiede dove sta il
echo   database, come fosse una installazione nuova.
echo.
echo   Copialo PRIMA nella cartella dell'applicazione, accanto a
echo   config.json e alla cartella data, e avvialo da li'.
echo.
echo Poi apri "Impostazioni di archiviazione": se mostra il percorso
echo giusto del database e il numero di preventivi che ti aspetti,
echo l'eseguibile e' a posto.
echo.
pause