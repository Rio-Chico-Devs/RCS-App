@echo off
echo ========================================
echo   Unione Database - RCS App
echo ========================================
echo.
echo Questo script importa i preventivi dal vecchio database
echo nel nuovo database (che contiene i materiali aggiornati).
echo.
echo Verranno chiesti i percorsi dei due file .db
echo Un backup automatico viene creato prima di qualsiasi modifica.
echo.
python unisci_db.py
echo.
pause
