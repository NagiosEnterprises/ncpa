@echo off
REM Windows setup for NCPA build with virtual environment support

REM Check if we should use virtual environment (set NCPA_USE_VENV=1 to enable)
if "%NCPA_USE_VENV%"=="1" (
    echo Using virtual environment approach...
    
    REM Create venv if it doesn't exist
    if not exist "venv\" (
        echo Creating virtual environment...
        python -m venv venv
    )
    
    REM Activate virtual environment
    call venv\Scripts\activate.bat
    
    REM Update pip in virtual environment
    python -m pip install --upgrade pip
    
    REM Install packages in virtual environment
    pip install pypiwin32 cx_Freeze psutil requests flask pyOpenSSL gevent gevent-websocket
    
    echo Virtual environment setup complete. To build NCPA:
    echo call venv\Scripts\activate.bat
    echo python build\build_windows.py
) else (
    echo Using system Python approach...
    
    if not exist "%pydir%" (
      echo Set %%pydir%% to point to the desired python install
      exit /B 1
    )
    set PATH=%pydir%;%pydir%\scripts;%PATH%

    if not exist "%openssldir%" (
      echo Set %%openssldir%% to point to the desired OpenSSL install
      exit /B 1
    )
    set PATH=%openssldir%\bin;%PATH%

    if not exist "%PROGRAMFILES%\NSIS" (
        if not exist "%PROGRAMFILES(x86)%\NSIS" (
            echo Install NSIS 3.03 from http://nsis.sourceforge.net/Download
       exit /B 1
        )
    )

    where python > nul:
    if ERRORLEVEL 1 (
      echo python isn't in your path, fix your path or install python 
      exit /B 1
    )

    where pip > nul:
    if ERRORLEVEL 1 (
      echo pip isn't in your path, fix your path or install pip from https://bootstrap.pypa.io/get-pip.py
      exit /B 1
    )

    pip install pypiwin32 cx_Freeze psutil requests flask pyOpenSSL gevent gevent-websocket

    echo to build ncpa:
    echo python build\build_windows.py
)
