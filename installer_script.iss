; This is an example Inno Setup script (.iss file)
; You would typically combine this with other sections for [Setup], [Files], etc.
; This snippet focuses on the [Registry] section for context menu integration.

[Setup]
AppName=MagPy
AppVersion=1.0
DefaultDirName={autopf}\MagPy
UninstallDisplayIcon={app}\magnifier.exe

[Files]
; Assuming your PyInstaller output is in a 'dist' folder relative to this script
; You would copy your magnifier.exe and any other necessary files here.
Source: "dist\magnifier\*"; DestDir: "{app}\magnifier"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\magpy_settings\*"; DestDir: "{app}\magpy_settings"; Flags: ignoreversion recursesubdirs createallsubdirs
; Add other files from your dist folder if you used the single-folder PyInstaller output
; Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
Root: HKCR; Subkey: "Directory\Background\shell\MagPy"; ValueType: string; ValueName: ""; ValueData: "Launch MagPy"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Directory\Background\shell\MagPy"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\magnifier\magnifier.exe"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "Directory\Background\shell\MagPy\command"; ValueType: string; ValueName: ""; ValueData: """{app}\magnifier\magnifier.exe"""; Flags: uninsdeletekey

[Icons]
Name: "{group}\MagPy"; Filename: "{app}\magnifier\magnifier.exe"
Name: "{group}\MagPy Settings"; Filename: "{app}\magpy_settings\magpy_settings.exe"

; You might also want to add entries for specific file types if your magnifier
; could be used to inspect images, for example.