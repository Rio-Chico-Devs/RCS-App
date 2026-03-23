; ============================================================
; Script Inno Setup - Gestione Preventivi RCS
; Per compilare: apri con Inno Setup Compiler e premi F9
;                oppure usa il comando da riga di comando:
;                "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; ============================================================

#define AppName      "Gestione Preventivi RCS"
#define AppExeName   "GestionePreventivi.exe"
#define AppPublisher "RCS"
#define AppVersion   FileRead("version.txt")

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}

; Installa in AppData\Local (non richiede diritti amministratore)
DefaultDirName={localappdata}\GestionePreventiviRCS
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Cartella output dell'installer
OutputDir=dist
OutputBaseFilename=GestionePreventivi_Setup_v{#AppVersion}

; Compressione massima
Compression=lzma2/ultra64
SolidCompression=yes

; Icona dell'installer
SetupIconFile=

; Mostra dialogo "Chiudi app in esecuzione" se l'app è aperta
CloseApplications=yes
CloseApplicationsFilter={#AppExeName}
RestartApplications=yes

; Non richiede diritti di amministratore
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=

; Lingua
WizardStyle=modern

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea icona sul {cm:DesktopName}"; GroupDescription: "Icone aggiuntive:"; Flags: checkedonce

[Files]
; Eseguibile principale
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Icona sul desktop
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
; Icona nel menu Start
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"

[Run]
; Avvia l'app al termine dell'installazione
Filename: "{app}\{#AppExeName}"; Description: "Avvia {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Non eliminare la cartella data (contiene il database) durante la disinstallazione
; Type: filesandordirs; Name: "{app}\data"

[Code]
// -------------------------------------------------------
// Controlla se l'app è in esecuzione prima di aggiornare
// -------------------------------------------------------
function IsAppRunning(const FileName: string): Boolean;
var
  FSWbemLocator: Variant;
  FWMIService   : Variant;
  FWbemObjectSet: Variant;
begin
  Result := False;
  try
    FSWbemLocator  := CreateOleObject('WbemScripting.SWbemLocator');
    FWMIService    := FSWbemLocator.ConnectServer('', 'root\CIMV2', '', '');
    FWbemObjectSet := FWMIService.ExecQuery(
      Format('SELECT Name FROM Win32_Process WHERE Name="%s"', [FileName])
    );
    Result := (FWbemObjectSet.Count > 0);
  except
    // Se WMI non è disponibile, ignora il controllo
  end;
end;

function InitializeSetup(): Boolean;
begin
  if IsAppRunning('{#AppExeName}') then
  begin
    MsgBox(
      'L''applicazione "' + '{#AppName}' + '" è attualmente in esecuzione.' + #13#10 +
      'Chiudila prima di procedere con l''aggiornamento.',
      mbError, MB_OK
    );
    Result := False;
  end else
    Result := True;
end;
