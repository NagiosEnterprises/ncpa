#!/bin/sh

set -e

pushd /Volumes/NCPA-*

# These values are set in the ncpa.cfg for the user to drop permissions to
username="nagios"
groupname="nagios"
homedir="/usr/local/ncpa"
upgrade="0"
added="0"

# Check if NCPA is installed
if [ -d ${homedir} ]; then
    upgrade="1"
	echo "Starting upgrade..."
else
	echo "Starting install..."
fi

# Disable NCPA if it's already installed for upgrade
if [ ${upgrade} -eq "1" ]; then
	echo -n "Stopping old NCPA services..."
    launchctl stop com.nagios.ncpa.listener
    launchctl stop com.nagios.ncpa.passive

    # Give launchctl time to stop services before continuing
    sleep 5
	echo "done"
fi

# Create the group account
if ! dscl . -read /Groups/${groupname} > /dev/null 2>&1;
then
	# Select GID the same way
	PrimaryGroupID=`dscl . -list /Groups PrimaryGroupID | awk '{print $2}' | sort -ug | tail -1`
	let PrimaryGroupID=PrimaryGroupID+1

	# Create the group if we need to
    dscl . -create /Groups/${groupname}
    dscl . -create /Groups/${groupname} RecordName "_${groupname} ${username}"
    dscl . -create /Groups/${groupname} PrimaryGroupID ${PrimaryGroupID}
    dscl . -create /Groups/${groupname} RealName "${groupname}"
    dscl . -create /Groups/${groupname} Password "*"

	added="1"
fi

# Create the user account
if ! dscl . -read /Users/${username} > /dev/null 2>&1;
then
	# Find the highest UID that exists, pick the next one
	UniqueID=`dscl . -list /Users UniqueID | awk '{print $2}' | sort -ug | tail -1`
	let UniqueID=UniqueID+1

	# Create the actual user if we need to
    dscl . -create /Users/${username}
    dscl . -create /Users/${username} UserShell /usr/bin/false
    dscl . -create /Users/${username} UniqueID ${UniqueID}
    dscl . -create /Users/${username} RealName "${username}"
    dscl . -create /Users/${username} PrimaryGroupID ${PrimaryGroupID}
    dscl . -create /Users/${username} Password "*"
    dscl . -create /Users/${username} NFSHomeDirectory ${homedir}

	added="1"
fi

if [ ${added} -eq "1" ]; then
	echo "Users and group set"
fi

# Unload the daemons so they can be re-loaded after
if [ ${upgrade} -eq "1" ]; then
	echo -n "Re-loading services..."
    launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
    launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.passive.plist
else
	echo -n "Loading services..."
fi

cp ncpa/build_resources/ncpa_listener.plist /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
cp ncpa/build_resources/ncpa_passive.plist /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

echo "done"
echo -n "Setting permissions..."

mkdir -p ${homedir}

# Temporarily save etc directory
if [ ${upgrade} -eq "1" ]; then
    cp -Rf ${homedir}/etc /tmp/ncpa_etc
fi

# Copy over files
cp -Rf ncpa/* ${homedir}
chmod -R 775 ${homedir}
chown -R ${username}:${groupname} ${homedir}
chmod +x "${homedir}/uninstall.sh"

# Replace files
if [ ${upgrade} -eq "1" ]; then
    cp -Rf /tmp/ncpa_etc ${homedir}
    rm -rf /tmp/ncpa_etc
fi

echo "done"
echo -n "Starting NCPA..."

launchctl load /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
launchctl load /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

launchctl start com.nagios.ncpa.passive
launchctl start com.nagios.ncpa.listener

echo "done"

# Installation completed
echo "\n\n"
if [ ${upgrade} -eq "1" ]; then
	echo "-------------------"
	echo " Upgrade Completed "
	echo "-------------------"
else
	echo "-------------------"
	echo " Install Completed "
	echo "-------------------"
fi

popd
