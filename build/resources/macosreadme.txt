Installing NCPA:
    1. Download MacOS archive (https://www.nagios.org/ncpa/#downloads)
    2. Double click open the disk image file to mount it
    3. Find the installer volume name in the terminal:
         ls /Volumes
         Look for NCPA-<version> (e.g. NCPA-3.0.0)

    4. Run the installer, and follow any user prompts:
         sudo zsh /Volumes/NCPA-<version>/install.sh

Note: if you already have NCPA installed, the installer will upgrade the NCPA software, and retain your configuration.

Automatic Startup:
NCPA is configured to start automatically when the system boots. The installer sets up:
    - Main NCPA service (com.nagios.ncpa) - starts on boot and stays running
    - Watchdog service (com.nagios.ncpa.watchdog) - monitors and restarts NCPA if needed
    
You can check if NCPA is running with:
    sudo launchctl list | grep nagios

Restarting NCPA:
After making configuration changes, you will need to restart NCPA for changes to take effect.
This is accomplished by stopping then starting the service.

    1. On the command line, enter:
         sudo launchctl stop com.nagios.ncpa
         sudo launchctl start com.nagios.ncpa

Manual Service Control:
To manually enable/disable automatic startup:
    sudo launchctl enable system/com.nagios.ncpa     # Enable auto-start
    sudo launchctl disable system/com.nagios.ncpa    # Disable auto-start

Uninstalling  NCPA
    1. On the command line, enter:
         sudo zsh /usr/local/ncpa/uninstall.sh
