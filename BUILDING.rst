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
* pywin32 (http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win32-py2.7.exe/download)
* cx_Freeze
* Nullsoft Scriptable Install System (NSIS) 2.4.6 (http://nsis.sourceforge.net/Download)

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

* pywin32

  * Install via easy_install::

    "%pydir%\Scripts\easy_install" http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20219/pywin32-219.win32-py2.7.exe

* cx_Freeze

  * Install cx_Freeze via pip::

    "%pydir%\Scripts\pip" install cx_Freeze

* NSIS

  1. Download NSIS from http://nsis.sourceforge.net/Download 
  2. Run the NSIS installer.

Set Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~
Two variables must be set for the build-setup.bat script to run
properly:

* **pydir**: The root directory of your Python installation.

  This should be::
  
    C:\Python27

* **openssldir**: The root directory of your OpenSSL installation.
  
  This should be::
  
    C:\OpenSSL-Win32

Set these variables by running::

  set pydir=C:\Python27
  set openssldir=C:\OpenSSL-Win32
  
Patch cx_Freeze
~~~~~~~~~~~~~~~
cx_Freeze interacts poorly with the gevent package used by NCPA due to
a namespace collision. The cx_Freeze package must be patched for the
resulting binary to function properly. Without this patch, the build
will appear to succeed, but the ncpa_listener.exe and ncpa_passive.exe
executables will crash with an error similar to
:code:`"AttributeError: 'module' object has no attribute 'path'"` when
executed. See `cx_Freeze issue #42 <https://bitbucket.org/anthony_tuininga/cx_freeze/issues/42/recent-versions-of-gevent-break#comment-11421289>`_.
for more details.

1. Navigate to the cx_Freeze directory::

     cd "%pydir%\Lib\site-packages\cx_Freeze"

2. Open freezer.py in your favorite editor::

     vim freezer.py

3. Find the line which reads::

     import imp, os, sys

4. Replace the previous line with the following::

     import imp, sys
     os = sys.modules['os']

Run the Pre-Build Script
~~~~~~~~~~~~~~~~~~~~~~~~

Run build-setup.bat. You should see some packages installed by pip then
a message saying "to build ncpa: python build\build_windows.py".


Build NCPA
~~~~~~~~~~

Run the build script::

  "%pydir%\python" build\build_windows.py
