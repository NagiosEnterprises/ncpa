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
Administrative privileges are required to install the Nullsoft
Scriptable Install System.

Prerequisite Packages
~~~~~~~~~~~~~~~~~~~~~
* Git for Windows (https://git-scm.com/download/win)
* Python 2.7.10 (32-Bit) (https://www.python.org/downloads/release/python-2710/)
* pip
* OpenSSL for Windows (32-bit) (https://indy.fulgan.com/SSL/)
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
  1. Download the Python installer from::
       https://www.python.org/downloads/release/python-2710/
  2. Once downloaded, python can be installed into the user's home
     directory with the following command::
       msiexec /a python-2.7.10.msi /qb TARGETDIR="%HOME%\Program Files (x86)\python27"*
* pip
  Since Python version 2.7.9, pip can be installed by running::
    %pydir%\python -m ensurepip
* OpenSSL
  1. Download the OpenSSL package from https://indy.fulgan.com/SSL/
  2. Extract the OpenSSL package to your preferred path. A suitable
     location would be::
       %HOME%\Program Files (x86)\Common Files\openssl-x.x.xx-i386-win32
* NSIS
  1. Download NSIS from http://nsis.sourceforge.net/Download 
  2. Run the NSIS installer.

Set Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~
Two variables must be set for the build-setup.bat script to run
properly:
* pydir: The root directory of your Python installation.
  If installed using the command mentioned previously, it will be::
    %HOME%\Program Files (x86)\python27  
  If you installed Python for all users on the system, this will
  probably be::
    C:\python27
* openssldir: The root directory of your OpenSSL installation.

Set these variables by running::
  set pydir=%HOME%\Program Files (x86)\python27  
  set openssldir=%HOME%\Program Files (x86)\Common Files\openssl-x.x.xx-i386-win32

Modify the Directory Structure of the OpenSSL Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The OpenSSL Package from indy.fulgan.com ships with the openssl.exe
executable in the root of the package directory. The NCPA build tools
for Windows require openssl.exe to be located at %openssldir%\bin. To
rectify this, create a directory at %openssldir%\bin and move the
openssl.exe executable to the 'bin' directory::
  cd %openssldir%
  mkdir bin
  move openssl.exe bin\

Patching cx_Freeze
~~~~~~~~~~~~~~~~~~
cx_Freeze interacts poorly with the gevent package used by NCPA due to
a namespace collision. The cx_Freeze package must be patched for the
resulting binary to function properly. Without this patch, the build
will appear to succeed, but the ncpa_listener.exe and ncpa_passive.exe
executables will crash with an error similar to::
  "AttributeError: 'module' object has no attribute 'path'"
when executed. See `cx_Freeze issue #42 <https://bitbucket.org/anthony_tuininga/cx_freeze/issues/42/recent-versions-of-gevent-break#comment-11421289>`
for more details.

1. Navigate to the cx_Freeze directory.
