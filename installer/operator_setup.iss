; Inno Setup script for Operator Desktop.
; Build first:  powershell -File scripts\build_operator_desktop.ps1
; Then compile this script with Inno Setup 6 (or run scripts\build_operator_installer.ps1).

#define MyAppName "Operator Desktop"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Operator"
#define MyAppExeName "OperatorDesktop.exe"
#define PublishDir "..\dist\operator-desktop"

[Setup]
AppId={{A7B3C4D5-E6F7-4890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Operator Desktop
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=OperatorDesktop-{#MyAppVersion}-win-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#PublishDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup: Boolean;
begin
  if not FileExists(ExpandConstant('{#PublishDir}\{#MyAppExeName}')) then
  begin
    MsgBox('Build output not found. Run scripts\build_operator_desktop.ps1 first.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
