@echo off
echo ========================================
echo Creazione eseguibile Gestione Preventivi
echo ========================================
echo.

echo [1/4] Installazione dipendenze Python...
pip install pyinstaller
pip install PyQt5
pip install PyQt5-sip
pip install odfpy
pip install reportlab

echo.
echo [2/4] Verifica dipendenze...
python -c "import PyQt5; print('PyQt5 OK')"
python -c "import sqlite3; print('sqlite3 OK')"

echo.
echo [3/5] Creazione eseguibile...
rem I moduli sotto sono elencati uno per uno di proposito. PyInstaller di
rem solito li trova da solo, ma diversi vengono importati DENTRO le funzioni
rem e non in cima al file: se ne mancasse uno, l'eseguibile si creerebbe
rem senza errori e si pianterebbe solo al momento di usare quella funzione,
rem magari mesi dopo. Elencarli non costa nulla e toglie il dubbio.
pyinstaller --onefile --windowed --name="GestionePreventivi" ^
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
    --hidden-import=ui.preventivo_business_logic ^
    --hidden-import=ui.preventivo_ui_components ^
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
echo IMPORTANTE: prima di distribuirlo, avvialo una volta e apri
echo "Impostazioni di archiviazione": se quella schermata si apre e
echo mostra lo stato dei dati, vuol dire che tutti i moduli sono
echo stati inclusi correttamente.
echo.
pause