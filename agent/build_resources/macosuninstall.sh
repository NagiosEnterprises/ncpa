#!/bin/sh

scriptUser=$(whoami)
if ! id -Gn "${scriptUser}" | grep -q -w admin; then
    echo -e "\n\n        ERROR!!!: You must have admin privileges to run this script!\n\n"
    exit 1
fi

# These values are set in the ncpa.cfg for the user to drop permissions to
username="nagios"
groupname="nagios"
homedir="/usr/local/ncpa"

# Check if NCPA is installed
if [ -d ${homedir} ]; then
	echo "Starting uninstall... "
else
	echo "NCPA may not be fully installed, clean up other NCPA artifacts."
fi

# Get MacOS version
macOSVer=""
if [[ $OSTYPE == 'darwin'* ]]; then
    macOSVer=`sw_vers | grep ProductVersion | awk '{print $2}'`
    echo "    MacOS version: $macOSVer."
fi

removeNCPAdaemons() {
    echo -n "    Stopping NCPA services... "
    stopped=''
    hasListener=$(launchctl list | grep ncpa_listener)
    if [[ $hasListener ]]; then
        launchctl stop com.nagios.ncpa.listener
        echo -n "listener stopped... "
        stopped=1
    fi
    hasPassive=$(launchctl list | grep ncpa_passive)
    if [[ $hasPassive ]]; then
        launchctl stop com.nagios.ncpa.passive
        echo -n "passive stopped... "
        stopped=1
    fi

    # Give launchctl time to stop services before continuing
    if [[ $stopped ]]; then
        sleep 5
    fi
    echo "Done."

    echo -n "    Unloading NCPA services... "
    if [[ -f "/Library/LaunchDaemons/com.nagios.ncpa.listener.plist" ]] ; then
        launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
    fi

    if [[ -f "/Library/LaunchDaemons/com.nagios.ncpa.listener.plist" ]] ; then
        launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.passive.plist
    fi

    launchctl remove com.nagios.ncpa.listener
    launchctl remove com.nagios.ncpa.passive
    echo "Done."
}

removeNCPAplists() {
    echo -n "    Removing NCPA plists... "
    rm -f /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
    rm -f /Library/LaunchDaemons/com.nagios.ncpa.passive.plist
    echo "Done."
}

killNCPAprocesses() {
    echo -n "    Kill NCPA processes... "
    pid=`ps aux | grep -v grep | grep ncpa_listener  | awk '{print $2}'`
    if [[ $pid ]]; then
        kill $pid
        echo -n "Killed $pid ncpa_listener, "
    fi

    pid=`ps aux | grep -v grep | grep ncpa_passive  | awk '{print $2}'`
    if [[ $pid ]]; then
        kill $pid
        echo -n "Killed $pid ncpa_passive, "
    fi
    echo "Done."
}

removeNCPAuser() {
    if dscl . -read "/Groups/${groupname}" > /dev/null 2>&1; then
        echo -n "    Removing nagios user and group... "
        echo -n "/Users/${username}... "
        sudo dscl . -delete "/Users/${username}"
        echo -n "/Groups/${groupname}... "
        sudo dscl . -delete "/Groups/${groupname}"
        echo -n "/Groups/_${groupname} ${groupname}... "
        sudo dscl . -delete "/Groups/_${groupname} ${groupname}"
        echo "Done."
    else
        echo "No group/user to remove."
    fi
}

removeNCPAcode() {
    if [[ -d "${homedir}" ]]; then
        echo -n "    Removing $homedir... "
        rm -rf $homedir
        echo "Done."
    else
        echo "No ${homedir} to remove"
    fi
}

listNCPAcomponents() {
    echo "\n---------------------------------------"
    echo "Listing NCPA components... "
    echo "\nProcesses?:"
    ps aux | grep -v grep | grep ncpa_

    echo "\nLaunchDaemons?:"
    launchctl list | grep nagios

    echo "\nLaunchDaemon plists?:"
    ls -al /Library/LaunchDaemons/ | grep nagios

    echo "\ndscl group?:"
    sudo dscl . -ls /Groups | grep nagios

    echo "\ndscl user?:"
    sudo dscl . -ls /Users | grep nagios

    echo "\nHome dir?:"
    ls -al /usr/local | grep ncpa
}

removeNCPAdaemons
removeNCPAplists
killNCPAprocesses
removeNCPAuser
removeNCPAcode
listNCPAcomponents

echo "\n--------------------------"
echo " Uninstall NCPA Completed "
echo "--------------------------"

exit
