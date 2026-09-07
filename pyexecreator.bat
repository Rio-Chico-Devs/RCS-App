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
echo [3/4] Creazione eseguibile...
pyinstaller --onefile --windowed --name="GestionePreventivi" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtPrintSupport ^
    --hidden-import=sqlite3 ^
    main.py

echo.
echo [4/4] Completato!
echo.
echo L'eseguibile si trova in: dist\GestionePreventivi.exe
echo.
echo Puoi copiare GestionePreventivi.exe dove vuoi e cliccarci sopra!
echo.
pause