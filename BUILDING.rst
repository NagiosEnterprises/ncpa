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

From a command prompt with Administrative privileges run::

  cd /path/to/ncpa/build/
  build_windows.bat

This will use Chocolatey to install various prerequisites for building NCPA and then build NCPA. If you have not yet built NCPA 3 on your machine, the script will likely tell you that a reboot is required/pending. This means that you need to restart your machine and then rerun the script and it will continue the installation/build processes. This may happen several times during the installation process.

This will create a file called ``ncpa-<version>.exe`` in the ``build`` directory.
This is the installer for NCPA and can be used to install NCPA on a Windows system.


Building on Linux
=================

*Note: Updates that involve a new/updated dependency (i.e. Python or OpenSSL) version will require that you delete the `prereqs.installed` file. If your build fails, try deleting this file and trying again.*

NCPA must be built on the family of distributions which it will ultimately be run on. i.e. a .deb built on Ubuntu 20 will work on Ubuntu 22/24 and should also work on Debian 10/11

You will need to have python3.11+ (python3.13 is preferred) installed prior to building NCPA v3.x.

If you are on a RHEL/Oracle/CentOS/Amazon/Rocky system you may need to enable additional repositories to get a newer version of python3.13.
You may also need to install the CodeReady Builder repository specific to your distro and version to get all the required development packages.

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

It's basically the same as Linux, however you may need to
install the libraries and python differently, due to it being macOS. You must have
python3.13, homebrew, and git installed prior to building NCPA v3.x.:

**Install the xcode command line tools**::

  xcode-select --install

**Clone the repository into your directory**::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

**Make sure you have homebrew installed**::

  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

**Install python3.13 using homebrew**::

  brew install python@3.13

**Execute the build script with sudo**::

  cd ~/ncpa/build
  sudo ./build.sh

Note that there may be some difficulty with installing this on other machines without Apple Developer credentials, and with the enhanced system security in newer versions. Please see `Installing on Nagios NCPA v 2.4 Agent on MacOS <https://nagiosenterprises.my.site.com/support/s/article/Installing-the-Nagios-NCPA-v-2-4-Agent-on-MacOS-7ec3e7de>`_ for more information.


Building on Solaris
===================

NCPA can be built on Solaris 11.4 SRU78 or higher systems. The build process creates a native Solaris package (.pkg) that can be installed using the standard Solaris package management tools.

Prerequisites
------------

**Clone the repository**::

  cd ~
  git clone https://github.com/NagiosEnterprises/ncpa

**Build NCPA**::

  cd ncpa/build
  sudo ./build.sh

The build process will:

1. Set up a Python virtual environment with all required dependencies
2. Build the NCPA binary using cx_Freeze 
3. Create a Solaris package (.pkg file)

**Install on the target Solaris server**

Copy the resulting ``~/ncpa/build/ncpa-3.X.X.sparc.pkg`` or ``~/ncpa/build/ncpa-3.X.X.i386.pkg`` to the desired server and install using::

  pkgadd -d ./ncpa-3.X.X.<arch>.pkg

**Silent Installation**

For automated installations without interactive prompts, use::

  pkgadd -a ./admin_file -d ./ncpa-3.X.X.<arch>.pkg ncpa

The installation process will:

* Stop any existing NCPA processes
* Create the nagios user and group if they don't exist
* Set up proper file permissions and ownership
* Attempt to create an SMF service for service management
* Start NCPA automatically after installation

**Solaris-Specific Features**

The Solaris build includes:

* **Comprehensive Process Management**: Enhanced cleanup logic prevents leftover processes during upgrades and restarts
* **SMF Integration**: Attempts to create a proper SMF (Service Management Facility) service with full diagnostics
* **Automatic Startup**: Configures NCPA to start automatically on boot using multiple methods
* **SSL Certificate Compatibility**: Generates certificates compatible with both Firefox and Chromium browsers
* **Manual Service Control**: Provides comprehensive service management scripts

**Service Management**

NCPA provides multiple ways to manage the service:

**Primary Method - Service Script**::

  /usr/local/bin/ncpa-service {start|stop|restart|status|killall}

**SMF Method** (if service is visible)::

  svcadm enable application/ncpa
  svcadm disable application/ncpa
  svcs application/ncpa

**Troubleshooting Commands**::

  # Aggressive cleanup of stuck processes
  sudo /usr/local/bin/ncpa-service killall
  
  # Check service status
  sudo /usr/local/bin/ncpa-service status
  
  # View running processes
  ps -ef | grep ncpa
  
  # Check logs
  tail -f /usr/local/ncpa/var/log/ncpa.log

**Auto-Startup Troubleshooting**

If NCPA doesn't start automatically after a reboot:

1. **Check SMF service status**::

     svcs application/ncpa
     svcs -xv application/ncpa

2. **Manually enable SMF service**::

     sudo svcadm enable application/ncpa

3. **Check init script links**::

     ls -la /etc/rc2.d/S99ncpa /etc/rc3.d/S99ncpa

4. **Test init script manually**::

     sudo /etc/init.d/ncpa start
     sudo /etc/init.d/ncpa status

5. **Check init script permissions and syntax**::

     ls -la /etc/init.d/ncpa
     sudo sh -n /etc/init.d/ncpa  # Check for syntax errors

6. **Force startup via service script**::

     sudo /usr/local/bin/ncpa-service start

7. **Check for legacy run control entries**::

     svcs -a | grep ncpa

8. **Debug boot environment issues**::

     # Check if environment variables are available during boot
     sudo /etc/init.d/ncpa start 2>&1 | tee /tmp/ncpa_boot_test.log
     
     # Verify PATH and library paths
     env | grep -E "PATH|LD_LIBRARY_PATH"

**Common Auto-Startup Issues**

* **SMF Include Dependency**: The init script no longer depends on SMF includes that may not be available during early boot
* **Environment Variables**: The init script now explicitly sets PATH and LD_LIBRARY_PATH for boot compatibility  
* **Lock Directory**: The script automatically creates the required lock directory (/var/lock/subsys)
* **Fallback Mechanisms**: If the service script isn't available, the init script can start NCPA directly

If SMF service is not visible, NCPA will use the traditional init script method for auto-startup.

**Known Issues and Solutions**

* **SMF Service Visibility**: Some Solaris systems may experience issues where SMF services import successfully but don't appear in ``svcs`` output due to repository corruption
  
  *Solution*: Use the reliable service script: ``/usr/local/bin/ncpa-service``

* **Process Cleanup**: During upgrades, old NCPA processes are automatically cleaned up before starting new ones

  *Manual cleanup*: ``sudo /usr/local/bin/ncpa-service killall``

* **SSL Certificate Browser Compatibility**: NCPA generates SSL certificates with proper key usage extensions for both Firefox and Chromium-based browsers

* **Permission Issues**: NCPA may require ``setgroups()`` permission adjustments on some Solaris configurations (automatically handled in the code)

* **Multiple Processes**: If you see multiple NCPA processes after an upgrade, use the killall command to clean them up

**Automatic Startup**

NCPA is configured to start automatically on boot using multiple mechanisms:

1. **SMF Service** (if successfully imported): ``application/ncpa``
2. **Service Script**: ``/usr/local/bin/ncpa-service`` called by init scripts

This redundant approach ensures NCPA starts reliably across different Solaris configurations.

**Uninstalling**

Remove NCPA using::

  pkgrm ncpa

The uninstall process will:

* Stop all NCPA processes using multiple methods
* Remove SMF service definitions and startup links  
* Clean up service scripts and configuration files
* Remove PID files and lock files
* Preserve user data and logs (in ``/usr/local/ncpa/var/``)

**Troubleshooting Uninstall Issues**

If ``pkgrm ncpa`` gets stuck or ``pkginfo | grep ncpa`` still shows the package after removal attempts:

1. **Kill hanging pkgrm processes**::

     ps -ef | grep pkgrm
     sudo pkill -f pkgrm

2. **Force package removal from database**::

     # Check package status
     pkginfo | grep ncpa
     
     # Try force removal (skip scripts) - may not work if root operations needed
     sudo pkgrm -a /dev/null ncpa

3. **Manual database cleanup** (if package still shows)::

     # Back up package database
     sudo cp -r /var/sadm/pkg /var/sadm/pkg.backup
     
     # Remove NCPA from package database
     sudo rm -rf /var/sadm/pkg/ncpa
     
     # Refresh package database
     sudo pkgchk -n

4. **Alternative: Edit package scripts to prevent hanging**::

     # If package removal keeps hanging, temporarily modify preremove script
     sudo cp /var/sadm/pkg/ncpa/install/preremove /var/sadm/pkg/ncpa/install/preremove.backup
     sudo sh -c 'echo "#!/bin/bash" > /var/sadm/pkg/ncpa/install/preremove'
     sudo sh -c 'echo "echo NCPA: Skipping preremove operations" >> /var/sadm/pkg/ncpa/install/preremove'
     sudo sh -c 'echo "exit 0" >> /var/sadm/pkg/ncpa/install/preremove'
     sudo chmod +x /var/sadm/pkg/ncpa/install/preremove
     
     # Now try normal removal
     sudo pkgrm ncpa

5. **Complete manual cleanup**::

     # Remove SMF services
     sudo svcadm disable application/ncpa 2>/dev/null || true
     sudo svccfg delete -f application/ncpa 2>/dev/null || true
     
     # Remove startup links
     sudo rm -f /etc/rc2.d/S99ncpa /etc/rc3.d/S99ncpa
     sudo rm -f /etc/rc0.d/K01ncpa /etc/rc1.d/K01ncpa /etc/rc6.d/K01ncpa
     
     # Remove service scripts
     sudo rm -f /usr/local/bin/ncpa-service
     sudo rm -f /usr/local/bin/ncpa-start.sh
     sudo rm -f /etc/init.d/ncpa
     
     # Remove main installation
     sudo rm -rf /usr/local/ncpa
     
     # Remove SMF manifests
     sudo rm -f /var/svc/manifest/application/ncpa.xml

6. **Verify complete removal**::

     pkginfo | grep ncpa          # Should return nothing
     svcs -a | grep ncpa          # Should return nothing
     ps -ef | grep ncpa           # Should return nothing (except grep)

**Upgrade Process**

To upgrade NCPA:

1. **Install new package** (no need to manually stop NCPA)::

     pkgadd -a ./admin_file -d ./ncpa-3.X.X.<arch>.pkg

2. **The upgrade automatically**:
   
   * Stops existing NCPA processes
   * Installs new files
   * Starts fresh NCPA instance
   * Preserves configuration and logs

**Build Requirements**

The Solaris build requires the NCPA source to already be built (frozen) before packaging. The complete build process is::

  cd ncpa/build
  sudo ./build.sh              # Build the frozen NCPA binary and Solaris package

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
