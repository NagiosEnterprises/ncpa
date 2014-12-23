set PATH=%PATH%;c:\Python27;c:\Python27\scripts;c:\OpenSSL-Win64\bin;

if not exist "%PROGRAMFILES%\NSIS" (
  echo Install NSIS 2.46 from http://sourceforge.net/projects/nsis/files/NSIS%202/2.46/
   exit /B 1
)

where python > nul:
if ERRORLEVEL 1 (
  echo python isn't in your path, fix your path or install python 
  exit /B 1
)

for /f "delims=" %%F in ('where python') do set pydir=%%~dpF
if not exist %PYDIR%\Lib\site-packages\cx_Freeze (
  echo cx_Freeze isn't in your python install, install cx_Freeze 4.3.2
  exit /B 1
)

where pip > nul:
if ERRORLEVEL 1 (
  echo pip isn't in your path, fix your path or install pip from https://bootstrap.pypa.io/get-pip.py
  exit /B 1
)

pip install pywin32
pip install cx_Logging --allow-external cx-Logging --allow-unverified cx-Logging
pip install cx_PyGenLib --allow-external cx-PyGenLib --allow-unverified cx-PyGenLib
pip install nose

