@echo off
echo ========================================
echo Creazione eseguibile Gestione Preventivi
echo ========================================
echo.

echo [1/3] Installazione PyInstaller...
pip install pyinstaller

echo.
echo [2/3] Creazione eseguibile...
pyinstaller --onefile --windowed --name="GestionePreventivi" main.py

echo.
echo [3/3] Completato!
echo.
echo L'eseguibile si trova in: dist\GestionePreventivi.exe
echo.
echo Puoi copiare GestionePreventivi.exe dove vuoi e cliccarci sopra!
echo.
pause