=============
Building NCPA
=============

*This document is a work in progress for Python 3 and NCPA 3.*

Building on Windows
===================

*Note: The current Windows pre-build script is written in batch and
must be executed by cmd.exe. For this reason, any Windows commands
listed in this document will be written with cmd.exe compatibility
in mind.*

Prerequisites
-------------

* `Git for Windows <https://git-scm.com/download/win>`_
* \*Python 3.11.x (`Download <https://www.python.org/downloads/>`_)
* \*OpenSSL for Windows (`Download <https://slproweb.com/products/Win32OpenSSL.html>`_) *(Requires admin rights)*
* `Microsoft Visual C++ Compiler Build Tools <https://wiki.python.org/moin/WindowsCompilers>`_ *(Requires admin rights/version used is based on version of python installed)*
* `NSIS 3 <http://nsis.sourceforge.net/Download>`_ *(Requires admin rights)*

\* : Use 32-bit versions if you need to deploy to 32-bit systems

Configure the Build Environment
-------------------------------

Install Prerequisites
~~~~~~~~~~~~~~~~~~~~~

* Python

  1. Download and install Python 3.x. (`see prerequisites <#prerequisites>`_)
  2. Execute the installer as usual.

* OpenSSL

  1. Download and install the OpenSSL package. (`see prerequisites <#prerequisites>`_)
  2. Be sure to make a not of the installation directory while installing.

* Microsoft Visual C++ Compiler` Build Tools

  1. Download and run the installer. The easiest way to do this would be to install Visual 
  Studio Community 2022 and follow the instructions from the link found in the `prerequisites <#prerequisites>`_.
  2. Follow the instructions outlined in the article in prerequisite section to
  ensure you install the proper version for your python version

* NSIS

  1. Download and run the installer. (`see prerequisites <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#prerequisites>`_)

* pip
  
  * Pip is installed by default but should be updated before continuing::

      "%pydir%" -m pip install --upgrade pip

Install the Last Modules
~~~~~~~~~~~~~~~~~~~~~~~~

* Install the full list of python modules
	
  "%pydir%\python" -m pip install --upgrade -r build/resources/require.win.txt

Build NCPA
~~~~~~~~~~

Run the build script::

  "%pydir%\python" build\build_windows.py


Building on Linux
=================

Building from most Linux distros is much less complicated than Windows. We have a
couple helpful scripts that make it much easier. *We will assume you have wget and git installed*

*WARNING: DO THIS ON A VM OR NOT A PRODUCTION SYSTEM*

To start, clone the repository in your directory::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

Now run the setup scripts to install the requirements::

  cd ncpa/build/scripts
  ./build.sh

Follow the prompts to setup the system. When running the build.sh script it will setup
the system and build the ncpa binary.


Building on Mac OS X
====================

Working on this section. It's basically the same as Linux, however you may need to
install the libraries and python differently, due to it being macOS. You must have
python3 installed prior to running it. You'll also have to use the following command
to build the dmg::

  cd ncpa/build/scripts
  ./build.sh
