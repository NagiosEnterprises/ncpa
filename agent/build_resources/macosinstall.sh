#!/bin/sh

set -e

# This script was derived from
# https://wwwx.cs.unc.edu/~hays/archives/2010/11/entry_31.php

username=nagios
groupname=nagcmd
new_gid=569
homedir=/usr/local/ncpa

# Create the user account
if ! dscl . -read /Users/${username} > /dev/null;
then
    dscl . -create /Users/${username}
    dscl . -create /Users/${username} UserShell /usr/bin/false
    dscl . -create /Users/${username} UniqueID ${new_uid}      
    dscl . -create /Users/${username} RealName "${username}"
    dscl . -create /Users/${username} PrimaryGroupID "${new_gid}"
    dscl . -create /Users/${username} Password "*"        
    dscl . -create /Users/${username} NFSHomeDirectory ${homedir}
else
    echo 'User already exists, skipping!'
fi

if ! dscl . -read /Groups/${groupname} > /dev/null;
then
    # Create the group
    dscl . -create /Groups/${groupname}
    dscl . -create /Groups/${username} RecordName "_${groupname} ${username}"
    dscl . -create /Groups/${username} PrimaryGroupID "${new_gid}"
    dscl . -create /Groups/${username} RealName "${groupname}"
    dscl . -create /Groups/${username} Password "*"
else
    echo 'Group already exists, skipping!'
fi

cp ncpa/build_resources/ncpa_listener.plist /System/Library/LaunchDaemons/org.nagios.ncpa_listener
cp ncpa/build_resources/ncpa_passive.plist /System/Library/LaunchDaemons/org.nagios.ncpa_passive

mkdir -p /usr/local/ncpa
cp -rf ncpa/* /usr/local/ncpa/
chmod -R 775 /usr/local/ncpa
chown -R nagios:nagcmd /usr/local/ncpa
