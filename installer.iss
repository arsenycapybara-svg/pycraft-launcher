[Setup]
AppName=PyCraft Launcher
AppVersion=0.1.0
AppPublisher=PyCraft
DefaultDirName={autopf}\PyCraft Launcher
DefaultGroupName=PyCraft Launcher
OutputBaseFilename=PyCraft-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\PyCraft.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; Flags: unchecked

[Files]
Source: "dist\PyCraft\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\PyCraft Launcher"; Filename: "{app}\PyCraft.exe"
Name: "{autodesktop}\PyCraft Launcher"; Filename: "{app}\PyCraft.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PyCraft.exe"; Description: "Запустить PyCraft Launcher"; Flags: nowait postinstall skipifsilent