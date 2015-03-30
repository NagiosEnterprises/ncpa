!include "MUI.nsh"
!include "nsDialogs.nsh"
!include "winmessages.nsh"
!include "logiclib.nsh"
!include "InstallOptions.nsh"

!include FileFunc.nsh
!insertmacro GetParameters
!insertmacro GetOptions

!define NAME "NCPA"
!define COMPANY "Nagios Enterprises, LLC"
!define NCPA_VERSION "$%NCPA_BUILD_VER%"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\NCPA"
  
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!include "MultiUser.nsh"

!define CONFIG_INI "$INSTDIR\Config.ini"

BrandingText 'Nagios Enterprises, LLC'

; The name the program
Name "NCPA"

; The file to write
OutFile "ncpa-${NCPA_VERSION}.exe"

; The installer styling
!define MUI_ICON "NCPA\build_resources\ncpa.ico"

; The default installation directory
InstallDir $PROGRAMFILES32\Nagios\NCPA

; Request admin execution
RequestExecutionLevel admin

; Settings
ShowInstDetails hide

LoadLanguageFile "${NSISDIR}\Contrib\Language files\English.nlf"

; Version information
VIProductVersion ${NCPA_VERSION}.0
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${NAME}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "${COMPANY}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" ${NCPA_VERSION}

; Language for pages
LangString PAGE_TITLE ${LANG_ENGLISH} "Nagios Cross-Platform Agent (${NAME})"
LangString PAGE_SUBTITLE ${LANG_ENGLISH} "${NCPA_VERSION} - Windows Version"
LangString LICENSE_TOP ${LANG_ENGLISH} "License Agreement"
LangString LICENSE_BOTTOM ${LANG_ENGLISH} "Nagios Software License 1.3"

; The actual pages displayed (in order)
!define MUI_PAGE_HEADER_TEXT $(PAGE_TITLE)
!define MUI_PAGE_HEADER_SUBTEXT $(PAGE_SUBTITLE)

!define MUI_LICENSEPAGE_TEXT_TOP $(LICENSE_TOP)
!define MUI_LICENSEPAGE_TEXT_BOTTOM $(LICENSE_BOTTOM)
!insertmacro MUI_PAGE_LICENSE "NCPA\build_resources\LicenseAgreement.txt"

Page custom SetAdvancedInstall

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Set language
!define MUI_LANGUAGE "ENGLISH"

Function .onInit

    InitPluginsDir
    !insertmacro INSTALLOPTIONS_EXTRACT_AS "NCPA\build_resources\quickstart.ini" "quickstart.ini"
	
    ${GetParameters} $R0
    ${GetParameters} $R1
    ${GetParameters} $R2
    ${GetParameters} $R3
    ${GetParameters} $R4
	
    ClearErrors
    ${GetOptions} $R0 /TOKEN= $0
    ${GetOptions} $R1 /NRDPURL= $1
    ${GetOptions} $R2 /NRDPTOKEN= $2
    ${GetOptions} $R3 /HOST= $3
    ${GetOptions} $R4 /CONFIG= $4

FunctionEnd

Function SetAdvancedInstall

	IfFileExists $INSTDIR\etc\ncpa.cfg 0 +2
	Abort

    ; Display the InstallOptions dialogue
    !insertmacro INSTALLOPTIONS_DISPLAY "quickstart.ini"
    !insertmacro INSTALLOPTIONS_READ $0 "quickstart.ini" "Field 3" "State"
    !insertmacro INSTALLOPTIONS_READ $1 "quickstart.ini" "Field 4" "State"
    !insertmacro INSTALLOPTIONS_READ $2 "quickstart.ini" "Field 5" "State"
    !insertmacro INSTALLOPTIONS_READ $3 "quickstart.ini" "Field 6" "State"
    !insertmacro INSTALLOPTIONS_READ $4 "quickstart.ini" "Field 7" "State"
    
FunctionEnd

Section # "Create Config.ini"

    ; Disable currently running ncpa listener/passive services
    ReadEnvStr $9 COMSPEC
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --uninstall ncpalistener'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --uninstall ncpapassive'

    SetOutPath $INSTDIR
	
	IfFileExists $INSTDIR\etc\ncpa.cfg SkipUpdateConfig UpdateConfig
	
	; If it's a fresh install, set the config options
	UpdateConfig:
	CreateDirectory $INSTDIR\etc
	File /oname=$INSTDIR\etc\ncpa.cfg .\NCPA\etc\ncpa.cfg
    WriteINIStr $INSTDIR\etc\ncpa.cfg api "community_string" "$0"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "CONFIG_VERSION" "0"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "CONFIG_NAME" "$4"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "URL" "$1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "TOKEN" "$2"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "PLUGIN_DIR" "plugins/"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "UPDATE_CONFIG" "1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrds "UPDATE_PLUGINS" "1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "parent" "$1"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "token" "$2"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "hostname" "$3"
	
	SkipUpdateConfig:
	; Don't overwrite the old config file...
	SetOverwrite off
	File /oname=$INSTDIR\etc\ncpa.cfg .\NCPA\etc\ncpa.cfg
	SetOverwrite on
	
	; Copy over everything we need for NCPA
    File /r .\NCPA\listener
	File /r .\NCPA\passive
	File /r .\NCPA\var
	File .\NCPA\*.*
	CreateDirectory $INSTDIR\plugins

SectionEnd

Section ""

    WriteRegStr SHCTX "${UNINST_KEY}" "DisplayName" "${NAME}"
    WriteRegStr SHCTX "${UNINST_KEY}" "DisplayVersion" "${NCPA_VERSION}"
    WriteRegStr SHCTX "${UNINST_KEY}" "Publisher" "${COMPANY}"

    ; get the size of our install dir, convert it from KB to a DWORD
    ; and write the size regkey
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD SHCTX "${UNINST_KEY}" "EstimatedSize" "$0"

    WriteRegStr SHCTX "${UNINST_KEY}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\" /$MultiUser.InstallMode"
    WriteRegStr HKCU "${UNINST_KEY}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /$MultiUser.InstallMode /S"
 
    WriteUninstaller $INSTDIR\uninstall.exe
  
    ReadEnvStr $9 COMSPEC
    nsExec::Exec '$9 /c diskperf -Y'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --install ncpalistener'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --install ncpapassive'
    nsExec::Exec '$9 /c sc config ncpalistener start= delayed-auto'
    nsExec::Exec '$9 /c sc config ncpapassive start= delayed-auto'

SectionEnd

Section "Uninstall"

    Delete "$INSTDIR\uninstall.exe"
    
    ReadEnvStr $9 COMSPEC
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --uninstall ncpalistener'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --uninstall ncpapassive'
    
    DeleteRegKey HKCU "${UNINST_KEY}"
    
    RMDir /r "$INSTDIR"

SectionEnd
