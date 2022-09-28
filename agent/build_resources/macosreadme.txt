Installing NCPA with the Installer

    1. Download MacOS archive (https://www.nagios.org/ncpa/#downloads)
    2. Double click open the disk image file to mount it
    3. Find the installer volume name in the terminal:
         ls /Volumes
         Look for NCPA-<version> (e.g. NCPA-2.4.0)

    4. Run the installer, and follow any user prompts:
         sudo zsh /Volumes/NCPA-<version>/install.sh

Note: if you already have NCPA installed, the installer will upgrade the NCPA software, and retain your configuration.

About Python
Python 2 is no longer available on newer versions of MacOS, e.g. Monterey. MacPorts installs it in an incorrect location. Homebrew no longer supports it, so if you do not already have python2.7 installed in the correct location, the installer will copy the installer's Python executable into the appropriate path.

The Python executable from the installer is unsigned, and MacOS won't run it without admin approval, this process is handled by the installer.

Uninstalling  NCPA
    1. On the command line, enter: sudo zsh /usr/local/ncpa/uninstall.sh
