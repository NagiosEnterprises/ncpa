=============
Building NCPA
=============

Building on Windows
===================

*Note: The current Windows pre-build script is written in batch and
must be executed by cmd.exe. For this reason, any Windows commands
listed in this document will be written with cmd.exe compatibility
in mind.*

Prerequisites
-------------

* `Git for Windows <https://git-scm.com/download/win>`_
* Python 2.7.16 (32-Bit) (`Download <https://www.python.org/downloads/release/python-2716/>`_)
* OpenSSL for Windows (32-bit) (`Download <https://slproweb.com/download/Win32OpenSSL-1_1_1d.exe>`_) *Requires admin rights*
* `Microsoft Visual C++ Compiler for Python 2.7 <http://aka.ms/vcpython27>`_
* `Microsoft Visual C++ 2010 runtime (32-bit) <http://www.microsoft.com/en-us/download/details.aspx?id=8328>`_ *Requires admin rights*
* `NSIS 3 <http://nsis.sourceforge.net/Download>`_ *Requires admin rights*

**Python Packages**

* pip (installed by default in Python 2.7 for Windows)
* cx_Freeze (patched)
* cx_Logging (http://cx-logging.sourceforge.net/)

There are more Python packages that need to be installed too but they are installed later on with a setup script that you can run. A full list of required packages is available in `ncpa/build/resources/requires.txt`.

Configure the Build Environment
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

* pip
  
  * Pip is installed by default in Python 2.7.16 but should be updated before continuing::

      "%pydir%" -m pip install --upgrade pip
	  
Set Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~
Two variables must be set for the win_build_setup.bat script to run properly:

* **pydir**: The root directory of your Python installation.

  This should be::
  
    C:\Python27

* **openssldir**: The root directory of your OpenSSL installation.
  
  This should be::
  
    C:\Program Files (x86)\OpenSSL-Win32

Set these variables by running::

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

Building from most Linux distros is much less complicated than Windows. We have a
couple helpful scripts that make it much easier. *We will assume you have wget and git installed*

To start, clone the repository in your directory::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

*Note: Running the following scripts on CentOS 7 will make yum not work due to the
Python version that yum uses. You can build the CentOS 7 version with the Python version
that comes with it, but you will have to install things manually.*

Now run the setup scripts to install the requirements::

  cd ncpa/build/scripts
  ./linux_build_prereqs.sh
  ./linux_build_setup.sh

Once these have completed you can do an actual build. You can run make differently depending
on which type of Linux you have.

*Warning: Be careful when making changes to NCPA while building, you should commit your
changes since `make all` will do a `git reset --hard` before building.*

On RPM-based systems::

  cd build
  make build_rpm

On DEB-based systems::

  cd build
  make build_deb


Building on Mac OS X
====================

Working on this section. Using the new build system, these four lines should be enough
to create a working NCPA DMG.

    sudo su -
    xcode-select --install
    cd build
    ./build.sh

Note that there may be some difficulty with installing this on other machines without
Apple Developer credentials. As of MacOS Catalina, this means going to 
System Preferences -> Security & Privacy and explicitly allowing the programs each time
they run.

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

Making NCPA is pretty easy once the requirements are done, just run make:

*Warning: Be careful when making changes to NCPA while building, you should commit your
changes since `make all` will do a `git reset --hard` before building.*

On RPM-based systems::

  cd build
  make build_rpm

On DEB-based systems::

  cd build
  make build_deb
