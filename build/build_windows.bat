@echo off
goto endFileDoc
:: TODO: update this for the new version that just uses Chocolatey-downloaded python instead of building Python and OpenSSL
::          and remove comments that are no longer used
::
:: Controller script for building NCPA on Windows.
::     THIS SCRIPT MUST BE RUN AS ADMINISTRATOR
::
:: Table of Contents:
:: 1. Configuration
:: 2. Set execution policy to allow running powershell scripts
:: 3. Build OpenSSL/Python (ncpa\build\windows\build_ossl_python\build_python.ps1)
::   3.1 Chocolatey: (ncpa\build\windows\choco_prereqs.ps1)
::     3.1.1 Install Chocolatey
::     3.1.2 Install Git, Perl, VS Build Tools, etc. w/ Chocolatey
::   3.2 Install 7-Zip
::   3.3 Download/Build OpenSSL (ncpa\build\windows\build_ossl_python\build_openssl.ps1)
::   3.4 Download/Build Python (ncpa\build\windows\build_ossl_python\build_python.ps1)
:: 4. Build NCPA (ncpa\build\windows\build_ncpa.py)
:: 5. Restore original execution policy
::
::
:: TODO: Add better support for building NCPA with a pre-built Python - Allow building with official Python releases (will have OSSL 3 soon)
:endFileDoc

setlocal

:::: Take options from command line to pass to build_config.ps1
:: TODO: add -only-[p/prereqs/d/download/b/build_openssl_python/n/build_ncpa] options to run just one part of the script
:: TODO: add -skip-tests option
:: TODO: add stuff from configuration so this actually does something again
@REM :options_loop
@REM set "build_options="
@REM if "%~1"=="" goto :end_options_loop
@REM if "%~1"=="-np"          goto :no_prereqs
@REM if "%~1"=="-no_prereqs"  goto :no_prereqs
@REM if "%~1"=="-nn"          goto :no_ncpa
@REM if "%~1"=="-no_ncpa"     goto :no_ncpa

@REM if "%~1"=="-h" (
@REM     set "build_options=-h"
@REM     shift
@REM     goto :end_options_loop
@REM )
@REM :no_prereqs
@REM     set "build_options=%build_options% -no_prereqs"
@REM     shift
@REM     goto :options_loop
@REM :no_ncpa
@REM     set "build_options=%build_options% -no_ncpa"
@REM     shift
@REM     goto :options_loop
@REM echo Invalid option: %~1, use -h for help
@REM shift
@REM goto :options_loop
@REM :end_options_loop

@REM :::::::::::::::::::::::
@REM :::: 1. Configuration
@REM :::::::::::::::::::::::
@REM echo Configuring build
@REM call %~dp0\windows\build_config.bat %build_options%
@REM if ERRORLEVEL 1 exit /B %ERRORLEVEL%

:::::::::::::::::::::::
:::: 2. Set execution policy to allow running powershell scripts
:::::::::::::::::::::::
for /f "tokens=*" %%a in ('powershell.exe -Command "if((Get-ExecutionPolicy -Scope CurrentUser) -ne $null) { Get-ExecutionPolicy -Scope CurrentUser } else { echo 'Undefined' }"') do set ORIGINAL_POLICY=%%a
echo Current policy: %ORIGINAL_POLICY%
powershell.exe -Command "Set-ExecutionPolicy Unrestricted -Scope CurrentUser -Force"
echo Setting execution policy to Unrestricted
if ERRORLEVEL 1 goto :restore_policy

@REM :::::::::::::::::::::::
@REM :::: 3. Build OpenSSL/Python
@REM :::::::::::::::::::::::
@REM echo Building OpenSSL/Python
@REM :: build_all.ps1 will:
@REM :: 1. Install Prerequisites
@REM :: 2. Download/Build OpenSSL
@REM :: 3. Download/Build Python
@REM powershell -File %~dp0\windows\build_ossl_python\build_all.ps1 ^
@REM     -ncpa_build_dir %~dp0 ^
@REM     -base_dir %base_dir% ^
@REM     -7z_ver %ver_7z% ^
@REM     -python_ver %python_ver% ^
@REM     -openssl_ver %openssl_ver% ^
@REM     -cpu_arch %cpu_arch% ^
@REM     -install_prereqs %install_prereqs% ^
@REM     -download_openssl_and_python %download_openssl_and_python% ^
@REM     -build_openssl_python %build_openssl_python% ^
@REM     -build_ncpa %build_ncpa%
@REM if ERRORLEVEL 1 goto :restore_policy

:::::::::::::::::::::::
:::: 3. Install Prereqs
:::::::::::::::::::::::
powershell -File %~dp0\windows\choco_prereqs.ps1
if ERRORLEVEL 1 goto :restore_policy

@REM :::::::::::::::::::::::
@REM :::: 4. Build NCPA with Built Python:
@REM :::::::::::::::::::::::
@REM :: i.e. C:\Users\Administrator\NCPA_PYTHON\Python-3.11.3\Python-3.11.3\PCbuild\amd64\py.exe - Built Python Launcher
@REM :: if build_ncpa is true, print python version and build NCPA
@REM if "%build_ncpa%"=="" set build_ncpa=true
@REM IF "%build_ncpa%"=="true" (
@REM     echo Building NCPA with Built Python
@REM     set pydir=%PYEXEPATH%
@REM     set python=%PYEXEPATH%
@REM     echo Building NCPA with python version:
@REM     Call %PYEXEPATH% -c "import sys; print(sys.version); import ssl; print('OpenSSL version:'); print(ssl.OPENSSL_VERSION)"
@REM     echo.

@REM     :: Copy built Python SSL DLLs to installed Python DLLs directory
@REM     echo Copying OpenSSL DLLs to Python DLLs directory
@REM     set ssl_dlls=%PYSSLPATH%\libcrypto-3-x64.dll %PYSSLPATH%\libssl-3-x64.dll %PYSSLPATH%\_ssl.pyd
@REM     for %%i in (%ssl_dlls%) do (
@REM         echo Copying %%~nxi to %PYDLLPATH%
@REM         copy %%i %PYDLLPATH%
@REM     )
@REM     if ERRORLEVEL 1 goto :restore_policy

@REM     echo Calling %PYEXEPATH% %~dp0\windows\build_ncpa.py %PYTHONPATH%
@REM     echo NOTE: This will take a while... You can check ncpa\build\build_ncpa.log for progress
@REM     echo.
@REM     @REM Call %PYEXEPATH% %~dp0\windows\build_ncpa.py %PYEXEPATH% > build_ncpa.log
@REM     Call %PYEXEPATH% %~dp0\windows\build_ncpa.py %PYEXEPATH%
@REM     if ERRORLEVEL 1 goto :restore_policy
@REM )

:::::::::::::::::::::::
:::: 4. Build NCPA
:::::::::::::::::::::::
echo Building NCPA
@REM FOR /F "tokens=* USEBACKQ" %%F IN (`where python`) DO (
@REM     echo Pydir: %%F
@REM   set pydir=%%F
@REM )
:: Set manually because of Windows 10 Pro
:: It already has a python.exe (that links to the windows store for installing Python 3.7) that breaks the dynamic linking
set pydir="C:\Python312\python.exe"
Call "%pydir%" %~dp0\windows\build_ncpa.py %pydir%

:::::::::::::::::::::::
:::: 5. Restore original execution policy
:::::::::::::::::::::::
:restore_policy
powershell.exe -Command "Set-ExecutionPolicy %ORIGINAL_POLICY% -Scope CurrentUser -Force"
echo Execution policy restored to %ORIGINAL_POLICY%
if ERRORLEVEL 1 exit /B %ERRORLEVEL%

endlocal