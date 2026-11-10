; FishBot kurulum dosyasi (Inno Setup 6). exe_yap.bat bunu kendisi derler.
#ifndef AppDir
  #define AppDir "..\cikti\FishBot"
#endif
#ifndef OutDir
  #define OutDir "..\cikti"
#endif
#ifndef IconFile
  #define IconFile "..\assets\app.ico"
#endif

[Setup]
AppId={{6B1F2A4E-6E0B-4C7E-9D7A-2F3C9A51F0B1}
AppName=FishBot
AppVersion=2.0
AppPublisher=FishBot
; Kullanici klasorune kurulur: program kendi klasorune (ayarlar, ogrendigi resimler) yazabilsin
DefaultDirName={localappdata}\Programs\FishBot
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir={#OutDir}
OutputBaseFilename=FishBot_Kurulum
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\FishBot.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "tr"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#AppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\*"
; mevcut uyeler/ayarlar sadece ilk kurulumda konur, guncellemede uzerine yazilmaz
Source: "{#AppDir}\data\*"; DestDir: "{app}\data"; Flags: onlyifdoesntexist skipifsourcedoesntexist recursesubdirs

[Dirs]
Name: "{app}\data"

[Icons]
Name: "{autoprograms}\FishBot"; Filename: "{app}\FishBot.exe"
Name: "{autoprograms}\FishBot Uye Yonetimi"; Filename: "{app}\UyeYonetimi.exe"
Name: "{autodesktop}\FishBot"; Filename: "{app}\FishBot.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FishBot.exe"; Description: "{cm:LaunchProgram,FishBot}"; Flags: nowait postinstall skipifsilent
