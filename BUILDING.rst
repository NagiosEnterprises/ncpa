=============
Building NCPA
=============

This document contains instructions for:

* `Building on Windows <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-windows>`_

* `Building on Linux <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-linux>`_

* `Building on MacOS <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-macos>`_

* `Building on Solaris <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-solaris>`_

*WARNING*: DO THIS ON A DEDICATED VM OR A NON-PRODUCTION SYSTEM!

THE BUILD SCRIPT WILL MAKE CHANGES TO THE SYSTEM THAT MAY BE INCOMPATIBLE WITH OTHER SOFTWARE

Building on Windows
===================

*Note: The current Windows pre-build script is written in batch and
must be executed by cmd.exe. For this reason, any Windows commands
listed in this document will be written with cmd.exe compatibility
in mind.*

*Note: The current Windows build should be run on a Windows machine without Python installed.*

Install the Prerequisites/Build NCPA
------------------------------------

From a command prompt with Administrative priveleges run::

  cd /path/to/ncpa/build/
  build_windows.bat

This will use Chocolatey to install various prerequisites for building NCPA and then build NCPA. If you have not yet built NCPA 3 on your machine, the script will likely tell you that a reboot is required/pending. This means that you need to restart your machine and then rerun the script and it will continue the installation/build processes. This may happen several times during the installation process.

This will create a file called ``ncpa-<version>.exe`` in the ``build`` directory.
This is the installer for NCPA and can be used to install NCPA on a Windows system.


Building on Linux
=================

*Note: Updates that involve a new/updated dependency (i.e. Python or OpenSSL) version will require that you delete the `prereqs.installed` file. If your build fails, try deleting this file and trying again.*

NCPA must be built on the family of distributions which it will ultimately be run on. i.e. a .deb built on Ubuntu 20 will work on Ubuntu 22/24 and should also work on Debian 10/11

To start, clone the repository in your directory::

   cd ~
   git clone https://github.com/NagiosEnterprises/ncpa

Now run the setup scripts as root to install the requirements::

   cd ncpa/build
   ./build.sh

Follow the prompts to setup the system. When running the build.sh script it will setup
the system and build the ncpa binary.


**Install on the target Linux server**
--------------------------------

Copy the resulting ~/ncpa/build/ncpa-3.X.X-latest.x86_64.rpm or ncpa_3.X.X-latest_amd64.deb to the desired server and install using the appropriate package system:

  On CentOS/RHEL/Oracle/Amazon/Rocky::

    yum install ./ncpa-3.X.X-latest.x86_64.rpm

  On Ubuntu 18+/Debian 10+::

    dpkg -i ./ncpa_3.X.X-latest._amd64.deb

  On Ubuntu 14-16/Debian 8-9 (not supported, but may work)::

    dpkg --force-depends -i ./ncpa_3.X.X-latest._amd64.deb

  On OpenSuSE/SLES::

    zypper install ./ncpa-3.X.X-latest.x86_64.rpm


Building on MacOS
=================

*Not updated for v3, yet.*
It's basically the same as Linux, however you may need to
install the libraries and python differently, due to it being macOS. You must have
python3, wget and git installed prior to building NCPA v3.x.:


**Clone the repository into your directory**::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

**Make your user root, and install the xcode command line tools**::

  sudo su -
  xcode-select --install

**Execute the build script**::

  cd ~/ncpa/build
  ./build.sh

Note that there may be some difficulty with installing this on other machines without Apple Developer credentials, and with the enhanced system security in newer versions. Please see `Installing on Nagios NCPA v 2.4 Agent on MacOS <https://nagiosenterprises.my.site.com/support/s/article/Installing-the-Nagios-NCPA-v-2-4-Agent-on-MacOS-7ec3e7de>`_ for more information.


Building on Solaris
===================

NCPA can be built on Solaris 11.4 SRU78 or higher systems. The build process creates a native Solaris package (.pkg) that can be installed using the standard Solaris package management tools.

Prerequisites
------------

Before building NCPA on Solaris, ensure you have the following packages installed::

  pkg install developer/build/gnu-make
  pkg install developer/gcc
  pkg install system/header
  pkg install library/zlib
  pkg install library/security/openssl
  pkg install runtime/python-39
  pkg install library/python/pip-39

**Clone the repository**::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

**Build NCPA**::

  cd ncpa/build
  ./build.sh

The build process will:

1. Set up a Python virtual environment with all required dependencies
2. Build the NCPA binary using cx_Freeze 
3. Create a Solaris package (.pkg file) with install/uninstall scripts
4. Configure automatic startup and service management

**Install on the target Solaris server**

Copy the resulting ``~/ncpa/build/ncpa-3.X.X.sparc.pkg`` or ``~/ncpa/build/ncpa-3.X.X.i386.pkg`` to the desired server and install using::

  pkgadd -d ./ncpa-3.X.X.<arch>.pkg

**Solaris-Specific Features**

The Solaris build includes:

* **SMF Integration**: Attempts to create a proper SMF (Service Management Facility) service
* **Manual Service Management**: Provides backup scripts for systems with SMF issues
* **Automatic Startup**: Configures NCPA to start automatically on boot using init.d scripts
* **Process Cleanup**: Enhanced process management to prevent leftover processes during restarts/upgrades

**Service Management**

Start/stop NCPA using the service script::

  /usr/local/bin/ncpa-service {start|stop|restart|status|killall}

Or use the traditional SMF commands if the service was imported successfully::

  svcadm enable application/ncpa
  svcadm disable application/ncpa
  svcs application/ncpa

**Known Issues**

* Some Solaris systems may experience SMF service visibility issues where the service imports successfully but doesn't appear in ``svcs`` output
* The manual service script provides a reliable workaround for SMF issues
* NCPA may require ``setgroups()`` permission adjustments on some Solaris configurations

**Uninstalling**

Remove NCPA using::

  pkgrm ncpa

This will automatically stop all NCPA processes and clean up service configurations.

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
