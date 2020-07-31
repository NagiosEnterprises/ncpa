!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "winmessages.nsh"
!include "LogicLib.nsh"
!include "InstallOptions.nsh"
!include "FileFunc.nsh"
!include "StrFunc.nsh"
!insertmacro GetParameters
!insertmacro GetOptions
${StrRep}

; --
; NCPA Installer Code
; --

!define NAME "NCPA"
!define COMPANY "Nagios Enterprises, LLC"
!define NCPA_VERSION "$%NCPA_BUILD_VER%"
!define NCPA_VERSION_CLEAN "$%NCPA_BUILD_VER_CLEAN%"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\NCPA"

!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!include "MultiUser.nsh"

!define CONFIG_INI "$INSTDIR\Config.ini"

BrandingText 'Nagios Enterprises, LLC'

; The name the program
Name "NCPA"

; Define variables for storing config info we get during install
Var token
Var bind_ip
Var bind_port
Var ssl_version
Var log_level_active
Var nrdp
Var nrdp_url
Var nrdp_token
Var nrdp_hostname
Var check_interval
Var log_level_passive
Var passive_checks
Var installed

; Define status variables
; 0 - stopped
; 1 - running
Var status_listener
Var status_passive

; The file to write
OutFile "ncpa-${NCPA_VERSION}.exe"

; The installer styling
!define MUI_ICON "NCPA\build_resources\ncpa.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "NCPA\build_resources\nagios_installer.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "NCPA\build_resources\nagios_installer.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "NCPA\build_resources\nagios_installer_logo.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "NCPA\build_resources\nagios_installer_logo.bmp"

; The default installation directory
InstallDir $PROGRAMFILES32\Nagios\NCPA

; Request admin execution
RequestExecutionLevel admin

; Settings
ShowInstDetails hide

; Version information
VIProductVersion ${NCPA_VERSION_CLEAN}.0
VIAddVersionKey "ProductName" "${NAME}"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "FileVersion" ${NCPA_VERSION}
VIAddVersionKey "LegalCopyright" "2014-2017 ${COMPANY}"
VIAddVersionKey "FileDescription" "NCPA Setup"

; Language values for pages
LangString PAGE_TITLE ${LANG_ENGLISH} "Nagios Cross-Platform Agent (${NAME})"
LangString PAGE_SUBTITLE ${LANG_ENGLISH} "Windows Version - ${NCPA_VERSION}"
LangString LICENSE_TOP ${LANG_ENGLISH} "License Agreement"
LangString LICENSE_BOTTOM ${LANG_ENGLISH} "Nagios Software License 1.3"
LangString FINISH_LINK ${LANG_ENGLISH} "View NCPA website and documentation"

;--------------------------------
; Pages (actual pages in order)

; Defines for pre-configured MUI pages
!define MUI_PAGE_HEADER_TEXT $(PAGE_TITLE)
!define MUI_PAGE_HEADER_SUBTEXT $(PAGE_SUBTITLE)
!define MUI_LICENSEPAGE_TEXT_TOP $(LICENSE_TOP)
!define MUI_LICENSEPAGE_TEXT_BOTTOM $(LICENSE_BOTTOM)
!define MUI_FINISHPAGE_LINK $(FINISH_LINK)
!define MUI_FINISHPAGE_LINK_LOCATION "https://nagios.org/ncpa/"
!define MUI_FINISHPAGE_LINK_COLOR 4d89f9

; Installer
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "NCPA\build_resources\LicenseAgreement.txt"

; Custom pages for NCPA configuration
Page custom ConfigListener
Page custom ConfigPassive
Page custom ConfigPassiveChecks

!insertmacro MULTIUSER_PAGE_INSTALLMODE

; Define function that causes changes to UI for upgrades
!define MUI_PAGE_CUSTOMFUNCTION_SHOW UpgradeOnly
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Language
!insertmacro MUI_LANGUAGE "English"

Function .onInit

    !insertmacro MULTIUSER_INIT

    InitPluginsDir
    !insertmacro INSTALLOPTIONS_EXTRACT_AS "NCPA\build_resources\nsis_listener_options.ini" "nsis_listener_options.ini"
    !insertmacro INSTALLOPTIONS_EXTRACT_AS "NCPA\build_resources\nsis_passive_options.ini" "nsis_passive_options.ini"
    !insertmacro INSTALLOPTIONS_EXTRACT_AS "NCPA\build_resources\nsis_passive_checks.ini" "nsis_passive_checks.ini"

    ; Define defaults for silent installs
    StrCpy $ssl_version "TLSv1_2"
    StrCpy $check_interval "300"
    StrCpy $log_level_active "warning"
    StrCpy $log_level_passive "warning"

    ${GetParameters} $R0

    ClearErrors
    ${GetOptions} $R0 "/TOKEN=" $token
    ${GetOptions} $R0 "/NRDPURL=" $nrdp_url
    ${GetOptions} $R0 "/NRDPTOKEN=" $nrdp_token
    ${GetOptions} $R0 "/NRDPHOSTNAME=" $nrdp_hostname
    ${GetOptions} $R0 "/IP=" $bind_ip
    ${GetOptions} $R0 "/PORT=" $bind_port

    ${If} $nrdp_url != ''
        StrCpy $nrdp 1
    ${EndIf}

    ; Default port if not given
    ${If} $bind_port == ''
        StrCpy $bind_port "5693"
    ${EndIf}

    ; Default ip if not given
    ${If} $bind_ip == ''
        StrCpy $bind_ip "0.0.0.0"
    ${EndIf}

FunctionEnd

Function un.onInit
    
    !insertmacro MULTIUSER_UNINIT

FunctionEnd

Function CheckInstall

    ; Status doesn't matter, since we are installing
    StrCpy $status_listener "0"
    StrCpy $status_passive "0"

    ; Set installed to 0
    StrCpy $installed "0"

    ; Check if previously installed (non-silent installs)
    IfFileExists "$INSTDIR\uninstall.exe" 0 +2
    StrCpy $installed "1"

    ${If} $installed == "1"

        ExpandEnvStrings $0 COMSPEC

        ; Get status of the listener service
        nsExec::ExecToStack '"$SYSDIR\cmd.exe" /c "sc QUERY ncpalistener | FIND /C "RUNNING""'
        Pop $0  # contains return code
        Pop $1  # contains output
        StrCpy $1 $1 1
        ${If} $1 == "1"
            ; Not running, so give status 1
            StrCpy $status_listener "1"
        ${EndIf}

        ; Get status of the passive service
        nsExec::ExecToStack '"$SYSDIR\cmd.exe" /c "sc QUERY ncpapassive | FIND /C "RUNNING""'
        Pop $0  # contains return code
        Pop $1  # contains output
        StrCpy $1 $1 1
        ${If} $1 == "1"
            ; Not running, so give status 1
            StrCpy $status_passive "1"
        ${EndIf}

    ${EndIf}

FunctionEnd

Function ConfigListener

    !insertmacro MUI_HEADER_TEXT $(PAGE_TITLE) $(PAGE_SUBTITLE)

    IfFileExists $INSTDIR\etc\ncpa.cfg 0 +2
    Abort

    ; Display the listener setup options
    !insertmacro INSTALLOPTIONS_DISPLAY "nsis_listener_options.ini"

    ; Grab listener options
    !insertmacro INSTALLOPTIONS_READ $token "nsis_listener_options.ini" "Field 4" "State"
    !insertmacro INSTALLOPTIONS_READ $bind_ip "nsis_listener_options.ini" "Field 12" "State"
    !insertmacro INSTALLOPTIONS_READ $bind_port "nsis_listener_options.ini" "Field 13" "State"
    !insertmacro INSTALLOPTIONS_READ $ssl_version "nsis_listener_options.ini" "Field 7" "State"
    !insertmacro INSTALLOPTIONS_READ $log_level_active "nsis_listener_options.ini" "Field 10" "State"

FunctionEnd

Function ConfigPassive

    !insertmacro MUI_HEADER_TEXT $(PAGE_TITLE) $(PAGE_SUBTITLE)

    IfFileExists $INSTDIR\etc\ncpa.cfg 0 +2
    Abort
    
    ; Display the passive setup options
    !insertmacro INSTALLOPTIONS_DISPLAY "nsis_passive_options.ini"

    ; Grab passive options
    !insertmacro INSTALLOPTIONS_READ $nrdp "nsis_passive_options.ini" "Field 14" "State"
    !insertmacro INSTALLOPTIONS_READ $nrdp_url "nsis_passive_options.ini" "Field 3" "State"
    !insertmacro INSTALLOPTIONS_READ $nrdp_token "nsis_passive_options.ini" "Field 4" "State"
    !insertmacro INSTALLOPTIONS_READ $nrdp_hostname "nsis_passive_options.ini" "Field 5" "State"
    !insertmacro INSTALLOPTIONS_READ $check_interval "nsis_passive_options.ini" "Field 6" "State"
    !insertmacro INSTALLOPTIONS_READ $log_level_passive "nsis_passive_options.ini" "Field 12" "State"

FunctionEnd

Function ConfigPassiveChecks

    !insertmacro MUI_HEADER_TEXT $(PAGE_TITLE) $(PAGE_SUBTITLE)

    IfFileExists $INSTDIR\etc\ncpa.cfg 0 +2
    Abort
    
    ; Skip this step unless 'send passive checks over NRDP' is checked
    ${If} $nrdp == 0
        Abort
    ${EndIf} 

    ; Display the passive setup options
    !insertmacro INSTALLOPTIONS_DISPLAY "nsis_passive_checks.ini"

    ; Get passive checks
    !insertmacro INSTALLOPTIONS_READ $passive_checks "nsis_passive_checks.ini" "Field 1" "State"

FunctionEnd

Function UpgradeOnly

    IfFileExists $INSTDIR\etc\ncpa.cfg 0 +6
    FindWindow $R5 "#32770" "" $HWNDPARENT
    GetDlgItem $R6 $R5 1019
    EnableWindow $R6 0
    FindWindow $R5 "#32770" "" $HWNDPARENT
    GetDlgItem $R6 $R5 1001
    EnableWindow $R6 0

FunctionEnd

Section # "Create Config.ini"

    Call CheckInstall

    ; Disable currently running ncpa listener/passive services
    ReadEnvStr $9 COMSPEC
    nsExec::Exec '$9 /c sc stop ncpalistener'
    nsExec::Exec '$9 /c sc stop ncpapassive'

    ; Remove old log files for services and old passive section
    Delete "$INSTDIR\ncpa_listener.log"
    Delete "$INSTDIR\ncpa_passive.log"
    RMDir /r "$INSTDIR\passive"

    SetOutPath $INSTDIR

    ; --------------
    ; ncpa.cfg Setup
    ; --------------
    
    CreateDirectory $INSTDIR\etc
    CreateDirectory $INSTDIR\etc\ncpa.cfg.d

    IfFileExists $INSTDIR\etc\ncpa.cfg SkipUpdateConfig UpdateConfig
    
    ; If it's a fresh install, set the config options
    UpdateConfig:
    File /oname=$INSTDIR\etc\ncpa.cfg .\NCPA\etc\ncpa.cfg
    
    WriteINIStr $INSTDIR\etc\ncpa.cfg api "community_string" "$token"

    ; Listener settings
    WriteINIStr $INSTDIR\etc\ncpa.cfg listener "ip" "$bind_ip"
    WriteINIStr $INSTDIR\etc\ncpa.cfg listener "port" "$bind_port"
    WriteINIStr $INSTDIR\etc\ncpa.cfg listener "ssl_version" "$ssl_version"
    WriteINIStr $INSTDIR\etc\ncpa.cfg listener "loglevel" "$log_level_active"

    ; If send via NRDP was selected, set nrdp handler
    ${If} $nrdp == 1
        WriteINIStr $INSTDIR\etc\ncpa.cfg passive "handlers" "nrdp"

        ; Set the passive checks into a new config file
        ${StrRep} $7 "$passive_checks" "\n\n" "$\r$\n"
        FileOpen $8 $INSTDIR\etc\ncpa.cfg.d\nrdp.cfg w
        FileWrite $8 "#$\r$\n"
        FileWrite $8 "# AUTO GENERATED NRDP CONFIG FROM WINDOWS INSTALLER$\r$\n"
        FileWrite $8 "#$\r$\n$\r$\n"
        FileWrite $8 "[passive checks]$\r$\n$\r$\n"
        FileWrite $8 "$7"
        FileClose $8
    ${Else}
        WriteINIStr $INSTDIR\etc\ncpa.cfg passive "handlers" "None"
    ${EndIf}

    ; Passive settings
    WriteINIStr $INSTDIR\etc\ncpa.cfg passive "sleep" "$check_interval"
    WriteINIStr $INSTDIR\etc\ncpa.cfg passive "loglevel" "$log_level_passive"

    ; NRDP settings
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "parent" "$nrdp_url"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "token" "$nrdp_token"
    WriteINIStr $INSTDIR\etc\ncpa.cfg nrdp "hostname" "$nrdp_hostname"

    ; Set log locations for Windows
    WriteINIStr $INSTDIR\etc\ncpa.cfg listener "logfile" " var/log/ncpa_listener.log"
    WriteINIStr $INSTDIR\etc\ncpa.cfg passive "logfile" " var/log/ncpa_passive.log"
    
    SkipUpdateConfig:
    ; Don't overwrite the old config file...
    SetOverwrite off
    File /oname=$INSTDIR\etc\ncpa.cfg .\NCPA\etc\ncpa.cfg
    SetOverwrite on

    ; ---------
    ; Directory
    ; ---------
    
    ; Copy over everything we need for NCPA
    File /r .\NCPA\listener
    File /r .\NCPA\var
    File .\NCPA\*.*
    CreateDirectory $INSTDIR\plugins

    ; Copy over example configs
    File /oname=$INSTDIR\etc\ncpa.cfg.sample .\NCPA\etc\ncpa.cfg.sample
    File /oname=$INSTDIR\etc\ncpa.cfg.d\example.cfg .\NCPA\etc\ncpa.cfg.d\example.cfg
    File /oname=$INSTDIR\etc\ncpa.cfg.d\README.txt .\NCPA\etc\ncpa.cfg.d\README.txt

    ; --------------
    ; INI File Setup
    ; --------------

    IfFileExists $INSTDIR\ncpa_listener.ini SkipListenerIniFile CreateListenerIniFile

    ; Set up the listener service ini file for log name setup
    CreateListenerIniFile:

    FileOpen $8 $INSTDIR\ncpa_listener.ini w
    FileWrite $8 "[Logging]$\r$\n"
    FileWrite $8 "FileName=$INSTDIR\var\log\win32service_ncpalistener.log"
    FileClose $8

    SkipListenerIniFile:

    IfFileExists $INSTDIR\ncpa_passive.ini SkipPassiveIniFile CreatePassiveIniFile

    ; Set up the passive service ini file for log name setup
    CreatePassiveIniFile:

    FileOpen $8 $INSTDIR\ncpa_passive.ini w
    FileWrite $8 "[Logging]$\r$\n"
    FileWrite $8 "FileName=$INSTDIR\var\log\win32service_ncpapassive.log"
    FileClose $8

    SkipPassiveIniFile:

SectionEnd

Section ""

    ; Remove old user key to fix double uninstall oafter SHCTX fix
    DeleteRegKey HKCU "${UNINST_KEY}"

    WriteRegStr SHCTX "${UNINST_KEY}" "DisplayName" "${NAME}"
    WriteRegStr SHCTX "${UNINST_KEY}" "ProductID" "732ae10d-f3f1-4946-85c3-0a2aee05e716"
    WriteRegStr SHCTX "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\ncpa_listener.exe"
    WriteRegStr SHCTX "${UNINST_KEY}" "DisplayVersion" "${NCPA_VERSION}"
    WriteRegStr SHCTX "${UNINST_KEY}" "Publisher" "${COMPANY}"

    ; Get the size of our install dir, convert it from KB to a DWORD and write the size regkey
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD SHCTX "${UNINST_KEY}" "EstimatedSize" "$0"

    WriteRegStr SHCTX "${UNINST_KEY}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\" /$MultiUser.InstallMode"
    WriteRegStr SHCTX "${UNINST_KEY}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /$MultiUser.InstallMode /S"
 
    WriteUninstaller $INSTDIR\uninstall.exe
	
    !define PORT $bind_port
  
    ; Install the service on new install
    ReadEnvStr $9 COMSPEC
    ${If} $installed == "0"
        nsExec::Exec '$9 /c diskperf -Y'
        nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --install ncpalistener'
        nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --install ncpapassive'
        nsExec::Exec '$9 /c sc config ncpalistener start= delayed-auto'
        nsExec::Exec '$9 /c sc config ncpapassive start= delayed-auto'
        nsExec::Exec '$9 /c netsh advfirewall firewall add rule name="NCPA" dir=in action=allow protocol=TCP localport=${PORT}'
        nsExec::Exec '$9 /c sc start ncpalistener'
        nsExec::Exec '$9 /c sc start ncpapassive'
    ${EndIf}

    ; Start the listener and passive services
    ; if they were running before upgrade (or if this is a new install)

    ${If} $status_listener == "1"
        nsExec::Exec '$9 /c sc start ncpalistener'
    ${EndIf}

    ${If} $status_passive == "1"
        nsExec::Exec '$9 /c sc start ncpapassive'
    ${EndIf}

SectionEnd

Section "Uninstall"

    Delete "$INSTDIR\uninstall.exe"
    
    ReadEnvStr $9 COMSPEC
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_listener.exe" --uninstall ncpalistener'
    nsExec::Exec '$9 /c "$INSTDIR\ncpa_passive.exe" --uninstall ncpapassive'
    
    DeleteRegKey SHCTX "${UNINST_KEY}"
    
    RMDir /r "$INSTDIR"

SectionEnd
