@echo off
echo ========================================
echo Creazione eseguibile Gestione Preventivi
echo ========================================
echo.

echo [1/3] Installazione dipendenze...
pip install pyinstaller PyQt5 python-docx odfpy

echo.
echo [2/3] Creazione eseguibile...
pyinstaller --onefile --windowed --name="GestionePreventivi" ^
    --hidden-import=PyQt5.sip ^
    --hidden-import=odf ^
    --hidden-import=odf.opendocument ^
    --hidden-import=docx ^
    --hidden-import=docx.oxml.ns ^
    main.py

echo.
echo [3/3] Completato!
echo.
echo L'eseguibile si trova in: dist\GestionePreventivi.exe
echo.
echo IMPORTANTE: Al primo avvio verra' creata automaticamente la cartella
echo             "data" con il database nella stessa directory dell'exe.
echo             Non spostare solo il file .exe: mantieni insieme exe e cartella data.
echo.
pause