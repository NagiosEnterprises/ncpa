=============
Building NCPA
=============

This document contains instructions for:

* `Building on Windows <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-windows>`_

* `Building on Linux <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-linux>`_

* `Building on MacOS <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-macos>`_


Building on Windows
===================

*Note: The current Windows pre-build script is written in batch and
must be executed by cmd.exe. For this reason, any Windows commands
listed in this document will be written with cmd.exe compatibility
in mind.*

**Prerequisites for Windows** (Installing some of these prerequisites requires admin rights)
-------------------------

* `Git for Windows <https://git-scm.com/download/win>`_
* Python 2.7.16 (32-Bit) (`Download <https://www.python.org/downloads/release/python-2716/>`_)
* `OpenSSL for Windows (32-bit) <https://slproweb.com/download/Win32OpenSSL-1_1_1d.exe>`_
* `Microsoft Visual C++ Compiler for Python 2.7 <https://web.archive.org/web/20160309215513/https://www.microsoft.com/en-us/download/details.aspx?id=44266>`_
* `Microsoft Visual C++ 2010 runtime (32-bit) <https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe>`_
* `NSIS 3 <http://nsis.sourceforge.net/Download>`_

**Python Packages**

* pip (installed by default in Python 2.7 for Windows)
* cx_Freeze (patched)
* cx_Logging (http://cx-logging.sourceforge.net/)
* pywin32 (https://github.com/mhammond/pywin32/releases/download/b228/pywin32-228.win32-py2.7.exe)

  (pywin32 provides a bunch OS checking stuff that is not available via pip.)
  
There are more Python packages that need to be installed too but they are installed when you run the build.sh script for the first time. A full list of required packages is available in *ncpa/build/resources/requires.txt*.

Configure the Windows Build Environment
-------------------------------

Install Prerequisites
~~~~~~~~~~~~~~~~~~~~~

* Python

  1. Download and install Python 2.7.16. (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)
  2. Execute the installer as usual. It's important that the
     installation path is not changed from the default of
     C:\\python27 as cx_Freeze can have difficulty finding
     Python resources if it's installed at a custom path.

* OpenSSL

  1. Download and install the OpenSSL package. (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)
  2. Be sure to make a not of the installation directory while installing.

* Microsoft Visual C++ Compiler for Python 2.7

  1. Download and run the installer. (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)

  Running the installer without administrator privileges will
  cause the files to be installed to::

  %LOCALAPPDATA%\Programs\Common\Microsoft\Visual C++ for Python\9.0

* Microsoft Visual C++ 2010 runtime (32-bit)

  1. Download and run the installer. (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)

* NSIS

  1. Download and run the installer. (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)

* pywin32

  1. Download and run the installer (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)
  
  If the installer says python isn't in the registry, then the installer doesn't match your python (which should be 2.7.16 32-bit).

* pip

  * Pip is installed by default in Python 2.7.16 but should be updated before continuing::

      "%pydir%" -m pip install --upgrade pip

Set Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~
Two variables must be set for the win_build_setup.bat script to run properly:

* **pydir**: The root directory of your Python installation.

  This should be:

    C:\Python27

* **openssldir**: The root directory of your OpenSSL installation.

  This should be:

    C:\Program Files (x86)\OpenSSL-Win32

Set these variables by entering::

  set pydir=C:\Python27
  set openssldir=C:\Program Files (x86)\OpenSSL-Win32

Install the Last Modules
~~~~~~~~~~~~~~~~~~~~~~~~

* Install the full list of python modules

  "%pydir%\python" -m pip install --upgrade -r build/resources/require.txt

* cx_Logging (http://cx-logging.sourceforge.net/)

  * Install the python 2.7 version of cx_Logging for Windows via the .msi

* cx_Freeze (patched)

  * Install cx_Freeze via pip:

    pip install cx_Freeze==4.3.4

  * Then, copy our patch into the package:

      ncpa\build\resources\cx_Freeze-4.3.4.tar.gz
      copy "ncpa\build\resources\cx_Freeze-4.3.4.tar\cx_Freeze-4.3.4\cx_Freeze\freezer.py" C:\Python27\Lib\site-packages\cx_Freeze\freezer.py

Build NCPA
~~~~~~~~~~

Run the build script::

  "%pydir%\python" build\build_windows.py


Building on Linux
=================

Building on CentOS 7 is the easiest way to get a working package for all Linux distributions except the SuSE variants which seem to build most easily on openSuSE 15 Leap, and SLES 15. For Ubuntu/Debian, you will need copy the generated .rpm to an Ubuntu system (20.04 recommended) with alien installed and run alien to create a .deb file that will work on all of the supported distributions.

That said, in most cases (CentOS 9 being a notable exception), building on the distribution that is targeted, e.g. building on Ubuntu 20.04 to deploy on Ubuntu 20.04, will work, but the resulting package will not be as portable.

The CentOS 7 build flow (for all non-SuSE linux)
-------------------------------------------------
  **Clone the git repo on a CentOS 7 machine** (*It must have wget and git installed*)::

    cd ~
    git clone https://github.com/NagiosEnterprises/ncpa

  **Select the correct .spec file**::

    cd ~/ncpa/build/linux

  For a package targeting CentOS 9::

    cp ncpa.spec el7-ncpa.spec
    cp el9-ncpa.spec  ncpa.spec

  For other non-SuSE distributions, use the existing ncpa.spec file

  **Run build script to install the requirements and build an rpm**::

    cd ~/ncpa/build
    ./build.sh

  **Creating a package for Ubuntu or Debian**
  (*Note: this step not necessary if building on Ubuntu*)

  Copy the resulting ~/ncpa/build/ncpa-2.x.x-1.elx.x86_64.rpm to an Ubuntu 20.04 server** with alien installed (`apt install alien`) and generate a .deb file::

    `alien -c -k -v ./ncpa-2.x.x-1.elx.x86_64.rpm > build.log`

  ** *Ubuntu 20.04 generates a .deb that will run on the most targets, but other distributions may work for your specific case.*

The SuSE build flows (OpenSuSE and SLES):
------------------------------------------------

  **OpenSuSE**

  Building on OpenSuSE is the same process as build on CentOS 7, except you do it on an OpenSuSE machine, and you use a different .spec file.

  **Clone the git repo on an OpenSuSE Leap 15 machine** (*It must have wget and git installed*)::

    cd ~
    git clone https://github.com/NagiosEnterprises/ncpa

  **Select the correct .spec file**::

    cd ~/ncpa/build/linux
    cp ncpa.spec el7-ncpa.spec
    cp suse-ncpa.spec  ncpa.spec

  Note: this will name your rpm with "sle15" in the release segment. If you want it to be "os15", edit line 3 in ncpa.spec accordingly.

  **Run build script to install the requirements and build an rpm**::

    cd ~/ncpa/build
    ./build.sh


  **SLES**

  On SLES 15, the build script fails because rpm-build is no longer available in the zypper repositories. Hence, this process is not really recommended, but it is provided for those useers for whom building on older versions of SLES is necessary.
  
  **Clone the repo as for OpenSuSE above.**

  **Edit linux/setup.sh and remove "rpm-build" from line 49**

  **Run build script to install the requirements and build an archive**
  
  The script will die when it tries to invoke rpm-build leaving a compressed tarball in the build directory, e.g., ncpa-2.4.1.tar.gz.
  
  **Copy this .gz into the build dir of the ncpa repo on another distrbution that that has rpm-build available, .e.g, a CentOS 7 VM.**
  
  **Select the proper .spec file, as for OpenSuSE above.**
  
  **From the build directory, run linux/package.sh**
  
  An rpm, e.g., ncpa-2.4.1-sle15.x86_64.rpm, will be generated.


**Install on the target Linux server**
--------------------------------

  Copy the resulting ~/ncpa/build/ncpa-2.x.x-1.elx.x86_64.rpm or ncpa_2.4.1-1.el7_amd64.deb to the desired server and install using the appropriate package system:

  On CentOs/RHEL::

    yum install ./ncpa-2.x.x-1.elx.x86_64.rpm

  On Ubuntu/Debian::

    apt install ./ncpa_2.4.1-1.el7_amd64.deb

  On OpenSuSE/SLES::

    zypper install ./ncpa_2.4.1-1.el7_amd64.deb


Building on MacOS
=================

Working on this section. Using the new build system, these four lines should be enough
to create a working NCPA DMG.

**Clone the git repo on an MacOS machine** (*It must have wget and git installed*)::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

**Make your user root, and install the xcode command line tools**::

  sudo su -
  xcode-select --install

**Execute the build script**::

  cd ~/ncpa/build
  ./build.sh

Note that there may be some difficulty with installing this on other machines without Apple Developer credentials, and with the enhanced system security in newer versions. Please see `Installing on Nagios NCPA v 2.4 Agent on MacOS <https://nagiosenterprises.my.site.com/support/s/article/Installing-the-Nagios-NCPA-v-2-4-Agent-on-MacOS-7ec3e7de>`_ for more information.

Building Tips
=============

There are plenty of derivative operating systems that will not work by following just
the instructions given in this document. NCPA is capable of being built on any system
that supports Python, so not to worry - it is possible!

The common problem is going to be getting the libraries for all the python modules
to be compiled and behave correctly with Python. We recommend compiling them from
source if you must, and compiling Python from source too - with any changes you need
to give the Python build process for library locations. Once that's done, you can
continue by installing the required `pip` modules and trying the build process.
