#!/bin/sh

set -e

# These values are set in the ncpa.cfg for the user to drop permissions to
username="nagios"
groupname="nagios"
homedir="/usr/local/ncpa"

# Check if NCPA is installed
if [ -d ${homedir} ]; then

	echo "Starting uninstall..."
else
	echo "NCPA is not installed or installed in an alternate location."
	exit 0
fi

echo -n "Stopping NCPA services..."
launchctl stop com.nagios.ncpa.listener
launchctl stop com.nagios.ncpa.passive

# Give launchctl time to stop services before continuing
sleep 5
echo "done"

echo "Unloading NCPA services..."
launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

echo "Removing NCPA services..."
rm -f /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
rm -f /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

echo -n "Removing NCPA..."
rm -rf $homedir
echo "done"

echo -n "Removing nagios user and group..."
dscl . -delete /Groups/{$groupname}
dscl . -delete /Users/${username}
echo "done"

echo "\n\n"
echo "----------------------"
echo " Un-install Completed "
echo "----------------------"
