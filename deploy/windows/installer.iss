#define MyAppName "CCNA EVE Lab Builder"
#define MyAppPublisher "NPX25"
#define MyAppExeName "CCNA EVE Lab Builder.exe"
#ifndef AppVersion
  #define AppVersion "4.1.0"
#endif

[Setup]
AppId={{1EA7F810-88D9-4F66-9AD9-CCEA20030141}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\CCNA EVE Lab Builder
DefaultGroupName=CCNA EVE Lab Builder
DisableProgramGroupPage=yes
OutputDir=..\..\release
OutputBaseFilename=CCNA-EVE-Lab-Builder-Windows-x64-{#AppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
LicenseFile=..\..\LICENSE
InfoBeforeFile=windows-install-notice.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\CCNA EVE Lab Builder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\CCNA EVE Lab Builder"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\CCNA EVE Lab Builder"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,CCNA EVE Lab Builder}"; Flags: nowait postinstall skipifsilent
