!include "MUI.nsh"
!include "nsDialogs.nsh"
!include "winmessages.nsh"
!include "logiclib.nsh"

!include FileFunc.nsh
!insertmacro GetParameters
!insertmacro GetOptions

!define UNINST_KEY \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\NCPA"
; ...
!define MULTIUSER_INSTALLMODE_COMMANDLINE
; ...
!include "MultiUser.nsh"

!define CONFIG_INI "$INSTDIR\Config.ini"

BrandingText 'Nagios Enterprises LLC'

;The name of the installer
Name "NCPA Installer"

;The file to write
OutFile "NCPA_Installer.exe"

;The icon
;~ !define MUI_ICON ".\NCPA\build_resources\ncpa.ico"

;The default installation directory
InstallDir $PROGRAMFILES32\Nagios\NCPA

;request admin execution
RequestExecutionLevel admin

;Settings
ShowInstDetails show

LoadLanguageFile "${NSISDIR}\Contrib\Language files\English.nlf"

; Version information
;VIProductVersion "1.6.0.0"
;VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "NCPA"
;VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "Nagios Enterprises LLC"
;VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "1.6"

;Order of pages
!define MUI_LANGUAGEFILE_DEFAULT "ENGLISH"
LangString MUI_INNERTEXT_LICENSE_BOTTOM "ENGLISH" "Nagios Software License 1.3"
LangString MUI_TEXT_LICENSE_TITLE "ENGLISH" "Nagios Cross-Platform Agent (NCPA)"
LangString MUI_TEXT_LICENSE_SUBTITLE "ENGLISH" "Windows Version"
LangString MUI_INNERTEXT_LICENSE_TOP "ENGLISH" "Software License Agreement"
!insertmacro MUI_PAGE_LICENSE ".\NCPA\build_resources\NagiosSoftwareLicense.txt"
# Page components

Page custom SetAdvancedInstall
Page directory
Page instfiles

Function .onInit

    InitPluginsDir
    !insertmacro MUI_INSTALLOPTIONS_EXTRACT_AS "NCPA\build_resources\quickstart.ini" "quickstart.ini"
	
    ${GetParameters} $R0
    ${GetParameters} $R1
    ${GetParameters} $R2
    ${GetParameters} $R3
	${GetParameters} $R4
	
    ClearErrors
    ${GetOptions} $R0 /TOKEN= $0
    ${GetOptions} $R1 /NRDPURL= $1
	${GetOptions} $R2 /NRDPTOKEN= $2
    ${GetOptions} $R3 /CONFIG= $3
    ${GetOptions} $R4 /HOST= $4

FunctionEnd

Function SetAdvancedInstall
    
    ;Display the InstallOptions dialog
    !insertmacro MUI_INSTALLOPTIONS_DISPLAY "quickstart.ini"
    !insertmacro MUI_INSTALLOPTIONS_READ $0 "quickstart.ini" "Field 3" "State"
    !insertmacro MUI_INSTALLOPTIONS_READ $1 "quickstart.ini" "Field 4" "State"
    !insertmacro MUI_INSTALLOPTIONS_READ $2 "quickstart.ini" "Field 5" "State"
    !insertmacro MUI_INSTALLOPTIONS_READ $3 "quickstart.ini" "Field 6" "State"
	!insertmacro MUI_INSTALLOPTIONS_READ $4 "quickstart.ini" "Field 7" "State"
    
FunctionEnd

Section # "Create Config.ini"
	
    SetOutPath $INSTDIR

    File /r .\NCPA\*.*

    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "CONFIG_VERSION" "0"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "CONFIG_NAME" "$3"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "URL" "$1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "parent" "$1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "TOKEN" "$2"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "token" "$2"
    WriteINIStr $INSTDIR\etc\ncpa.cfg api "community_string" "$0"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "PLUGIN_DIR" "plugins/"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "UPDATE_CONFIG" "1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "UPDATE_PLUGINS" "1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "hostname" "$4"

SectionEnd


Section ""
    ; ...
 
    WriteRegStr SHCTX "${UNINST_KEY}" "DisplayName" "NCPA"
    WriteRegStr SHCTX "${UNINST_KEY}" "UninstallString" \
    "$\"$INSTDIR\uninstall.exe$\" /$MultiUser.InstallMode"
    WriteRegStr SHCTX "${UNINST_KEY}" "QuietUninstallString" \
    "$\"$INSTDIR\uninstall.exe$\" /$MultiUser.InstallMode /S"
 
    WriteUninstaller $INSTDIR\uninstall.exe
  
    ReadEnvStr $9 COMSPEC
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --install ncpalistener'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --install ncpapassive'
 
    ; ...
SectionEnd

Section "Uninstall"

    Delete "$INSTDIR\uninstall.exe"
    
    ReadEnvStr $9 COMSPEC
	
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --uninstall ncpalistener'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --uninstall ncpapassive'
    
    DeleteRegKey SHCTX "${UNINST_KEY}"
    
    RMDir /r "$INSTDIR"
	
SectionEnd
