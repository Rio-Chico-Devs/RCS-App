@echo off
echo ========================================
echo   Build - Gestione Preventivi RCS
echo ========================================
echo.

REM Leggi la versione corrente
set /p VERSION=<version.txt
echo Versione: %VERSION%
echo.

echo [1/4] Installazione dipendenze...
pip install pyinstaller PyQt5 python-docx odfpy
echo.

echo [2/4] Creazione eseguibile...
pyinstaller --onefile --windowed --name="GestionePreventivi" ^
    --hidden-import=PyQt5.sip ^
    --hidden-import=odf ^
    --hidden-import=odf.opendocument ^
    --hidden-import=docx ^
    --hidden-import=docx.oxml.ns ^
    main.py

if errorlevel 1 (
    echo ERRORE: Build dell'eseguibile fallita.
    pause
    exit /b 1
)
echo.

echo [3/4] Creazione installer...
REM Cerca Inno Setup in posizioni standard
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

if %ISCC%=="" (
    echo ATTENZIONE: Inno Setup non trovato. Salto la creazione dell'installer.
    echo.
    echo Per creare l'installer, scarica e installa Inno Setup da:
    echo   https://jrsoftware.org/isdl.php
    echo Poi esegui: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo.
) else (
    %ISCC% installer.iss
    if errorlevel 1 (
        echo ERRORE: Build dell'installer fallita.
    ) else (
        echo Installer creato: dist\GestionePreventivi_Setup_v%VERSION%.exe
    )
)

echo [4/4] Completato!
echo.
echo ========================================
echo  File pronti in: dist\
echo ========================================
echo.
echo  - GestionePreventivi.exe         (eseguibile diretto)
echo  - GestionePreventivi_Setup_v%VERSION%.exe   (installer per distribuzione)
echo.
echo IMPORTANTE:
echo   Per aggiornare su un altro PC, copia sulla chiavetta:
echo     GestionePreventivi_Setup_v%VERSION%.exe
echo   Eseguilo sul PC di destinazione: Avanti ^> Installa ^> Fine
echo.
echo   Il database (cartella "data") NON viene toccato dall'aggiornamento.
echo.
pause
