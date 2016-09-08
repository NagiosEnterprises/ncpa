=============
Building NCPA
=============

Building on Windows
===================

*Note: The current Windows pre-build script is written in batch and
must be executed by cmd.exe. For this reason, any Windows commands
listed in this document will be written with cmd.exe compatibility
in mind.*

Build Requirements
------------------

User Rights
~~~~~~~~~~~
Administrative privileges are required to install:

* The Nullsoft Scriptable Install System.
* OpenSSL for Windows
* Microsoft Visual C++ 2010 runtime

Prerequisite Packages
~~~~~~~~~~~~~~~~~~~~~
* Git for Windows (https://git-scm.com/download/win)
* Python 2.7.10 (32-Bit) (https://www.python.org/downloads/release/python-2710/)
* pip
* OpenSSL for Windows (32-bit) (http://slproweb.com/download/Win32OpenSSL-1_0_2d.exe)
* Microsoft Visual C++ Compiler for Python 2.7 (http://aka.ms/vcpython27)
* Microsoft Visual C++ 2010 runtime (32-bit) (http://www.microsoft.com/en-us/download/details.aspx?id=8328)
* Nullsoft Scriptable Install System (NSIS) 2.4.6 (http://nsis.sourceforge.net/Download)
* cx_Freeze (patched)
* gevent-websocket (patched)


Assumptions
-----------
This document assumes that the packages in the prerequisites section are
installed from the URLs specified. While other packages may function,
they have not been tested with the build procedure listed below. 

Configure the Build Environment
-------------------------------

Install Prerequisites
~~~~~~~~~~~~~~~~~~~~~
* Python

  1. Download the Python installer from
     https://www.python.org/downloads/release/python-2710/
  2. Execute the installer as usual. It's important that the
     installation path is not changed from the default of
     C:\python27 as cx_Freeze can have difficulty finding
     Python resources if it's installed at a custom path.

* pip
  
  1. Since Python version 2.7.9, pip can be installed by running::
    
      "%pydir%\python" -m ensurepip

  2. Pip should then be updated::

      "%pydir%\Scripts\pip" install --upgrade pip

* OpenSSL

  1. Download the OpenSSL package from http://slproweb.com/download/Win32OpenSSL-1_0_2d.exe
  2. Run the installer. Be sure to make a not of the installation directory.

* Microsoft Visual C++ Compiler for Python 2.7

  1. Download the installer from http://aka.ms/vcpython27.
  2. Run the installer.

  Running the installer without administrator privileges will
  cause the files to be installed to::
  
  %LOCALAPPDATA%\Programs\Common\Microsoft\Visual C++ for Python\9.0

* Microsoft Visual C++ 2010 runtime (32-bit)
  
  1. Download the installer from http://www.microsoft.com/en-us/download/details.aspx?id=8328
  2. Run the installer. 

* NSIS

  1. Download NSIS from http://nsis.sourceforge.net/Download 
  2. Run the NSIS installer.

* cx_Freeze (patched)

  * Install cx_Freeze via the included patched version::
    ncpa\build\resources\cx_Freeze-4.3.4-patched.tar.gz
    "%pydir%\python" cx_Freeze-4.3.4\setup.py install

* gevent-websocket (patched)

  * Install gevent-websocket via the included patched version::
    ncpa\build\resources\gevent-websocket-0.9.5-patched.tar.gz
    "%pydir%\python" gevent-websocket-0.9.5\setup.py install


Set Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~
Two variables must be set for the win_build_setup.bat script to run properly:

* **pydir**: The root directory of your Python installation.

  This should be::
  
    C:\Python27

* **openssldir**: The root directory of your OpenSSL installation.
  
  This should be::
  
    C:\OpenSSL-Win32

Set these variables by running::

  set pydir=C:\Python27
  set openssldir=C:\OpenSSL-Win32


Run the Pre-Build Script
~~~~~~~~~~~~~~~~~~~~~~~~

Run win_build_setup.bat located in build/scripts. You should see some packages installed by pip then
a message saying "to build ncpa: python build\build_windows.py".


Build NCPA
~~~~~~~~~~

Run the build script::

  "%pydir%\python" build\build_windows.py
