#if VERSION == ""
  #undef VERSION
  #define VERSION "0.0.0-dev"
#endif

#define MyAppVersion VERSION


[Setup]
AppName=Zettelprogramm
AppVersion={#MyAppVersion}
OutputBaseFilename=Zettelprogramm_{#MyAppVersion}_Setup
DefaultGroupName=User
SetupIconFile=rsc\icons\app.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={code:GetInstallDir}

[Files]
Source: "dist\launch\*"; \
  DestDir: "{app}"; \
  Excludes: "rsc\*"; \
  Flags: recursesubdirs createallsubdirs
Source: "dist\launch/_internal\rsc\*"; \
  DestDir: "{userappdata}\Zettelprogramm\rsc"; \
  Flags: recursesubdirs createallsubdirs

[Dirs]
Name: "{userappdata}\Zettelprogramm"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Zettelprogramm"; Filename: "{app}\launch.exe"
Name: "{code:GetDesktopDir}\Zettelprogramm"; Filename: "{app}\launch.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Desktop-Verknüpfung erstellen"; Flags: unchecked

[Code]

function GetInstallDir(Param: string): string;
begin
  if IsAdminInstallMode then
    Result := ExpandConstant('{pf}\Zettelprogramm')
  else
    Result := ExpandConstant('{localappdata}\Programs\Zettelprogramm');
end;

function GetDesktopDir(Param: string): string;
begin
  if IsAdminInstallMode then
    Result := ExpandConstant('{commondesktop}')
  else
    Result := ExpandConstant('{userdesktop}');
end;

