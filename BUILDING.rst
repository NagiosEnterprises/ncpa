=============
Building NCPA
=============

This document contains instructions for:

* `Building on Windows <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-windows>`_

* `Building on Linux <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-linux>`_

* `Building on MacOS <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-macos>`_

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

This will use Chocolatey to install various prerequisites for building NCPA and then build NCPA. You will likely need to restart your computer if you have not yet built NCPA 3 on your machine. If you need to restart your machine, just rerun the script and it will continue the installation/build processes.

This will create a file called ``ncpa-<version>.exe`` in the ``build`` directory.
This is the installer for NCPA and can be used to install NCPA on a Windows system.


Building on Linux
=================

Building on CentOS 7 is the easiest way to get a working package for all Linux distributions. When you build on CentOS 7, both a .deb as well as an .rpm package are built.

In most cases, building on the distribution that is targeted, e.g. building on Ubuntu 20.04 to deploy on Ubuntu 20.04, will work, but the resulting package will not be as portable.

To start, clone the repository in your directory::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

Now run the setup scripts to install the requirements::

  cd ncpa/build
  ./build.sh

Follow the prompts to setup the system. When running the build.sh script it will setup
the system and build the ncpa binary.


**Install on the target Linux server**
--------------------------------

  Copy the resulting ~/ncpa/build/ncpa-3.x.x-x.x86_64.rpm or ncpa_3.x.x-x_amd64.deb to the desired server and install using the appropriate package system:

  On CentOS/RHEL/Oracle/Amazon/Rocky::

    yum install ./ncpa-3.x.x-1.x86_64.rpm

  On Ubuntu 16+/Debian 9+::

    apt install ./ncpa_3.0.0-1._amd64.deb

  On Ubuntu 14/Debian 8 (not supported, but may work)::

    dpkg --force-depends -i ./ncpa_3.0.0-1._amd64.deb

  On OpenSuSE/SLES::

    zypper install ./ncpa-3.x.x-1.x86_64.rpm


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
