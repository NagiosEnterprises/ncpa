#!/bin/sh

set -e

pushd /Volumes/NCPA-*

# These names are baked into the launchd plists, change with caution
username=nagios
groupname=nagios
homedir=/usr/local/ncpa
upgrade=0

# Check if NCPA is installed
if [ -f ${homedir} ]; then
    upgrade=1
fi

# Disable NCPA if it's already installed for upgrade
if [ ${upgrade} -eq 1 ]; then
    launchctl stop com.nagios.ncpa.listener
    launchctl stop com.nagios.ncpa.passive
fi

# Find the highest UID that exists, pick the next one
UniqueID=`dscl . -list /Users UniqueID | awk '{print $2}' | sort -ug | tail -1`
let UniqueID=UniqueID+1

# Select GID the same way
PrimaryGroupID=`dscl . -list /Groups PrimaryGroupID | awk '{print $2}' | sort -ug | tail -1`
let PrimaryGroupID=PrimaryGroupID+1

# Create the user account
if ! dscl . -read /Users/${username} > /dev/null 2>&1;
then
    dscl . -create /Users/${username}
    dscl . -create /Users/${username} UserShell /usr/bin/false
    dscl . -create /Users/${username} UniqueID ${UniqueID}
    dscl . -create /Users/${username} RealName "${username}"
    dscl . -create /Users/${username} PrimaryGroupID ${PrimaryGroupID}
    dscl . -create /Users/${username} Password "*"
    dscl . -create /Users/${username} NFSHomeDirectory ${homedir}
else
    echo 'User already exists, skipping!'
fi

# Create the group account
if ! dscl . -read /Groups/${groupname} > /dev/null 2>&1;
then
    dscl . -create /Groups/${groupname}
    dscl . -create /Groups/${groupname} RecordName "_${groupname} ${username}"
    dscl . -create /Groups/${groupname} PrimaryGroupID ${PrimaryGroupID}
    dscl . -create /Groups/${groupname} RealName "${groupname}"
    dscl . -create /Groups/${groupname} Password "*"
else
    echo 'Group already exists, skipping!'
fi

cp ncpa/build_resources/ncpa_listener.plist /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
cp ncpa/build_resources/ncpa_passive.plist /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

mkdir -p ${homedir}

# Temporarily save etc directory
if [ ${upgrade} -eq 1 ]; then
    cp -rf ${homedir}/etc /tmp/ncpa_etc
fi

# Copy over files
cp -rf ncpa/* ${homedir}
chmod -R 775 ${homedir}
chown -R ${username}:${groupname} ${homedir}

# Replace files
if [ ${upgrade} -eq 1 ]; then
    cp -rf /tmp/ncpa_etc ${homedir}/etc
    rm -rf /tmp/ncpa_etc
fi

launchctl load /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
launchctl load /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

launchctl start com.nagios.ncpa.passive
launchctl start com.nagios.ncpa.listener

popd
