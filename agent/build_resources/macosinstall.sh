#!/bin/sh

set -e

cd "`dirname '$0'`"
dir="`pwd`"
echo $dir
groupname=nagcmd
homedir=/usr/local/ncpa

# Create the user account
if ! dscl . -read /Groups/${groupname} > /dev/null;
then
    dscl . -create /Users/${username}
    dscl . -create /Users/${username} UserShell /usr/bin/false
    dscl . -create /Users/${username} UniqueID 569      
    dscl . -create /Users/${username} RealName "${username}"
    dscl . -create /Users/${username} PrimaryGroupID 20 
    dscl . -create /Users/${username} Password "*"        
    dscl . -create /Users/${username} NFSHomeDirectory ${homedir}
else
    echo 'User already exists, skipping!'
fi

if ! dscl . -read /Groups/${groupname} > /dev/null;
then
    # Create the group
    dscl . -create /Groups/${groupname}
    dscl . -create /Groups/${groupname} RecordName "_${groupname} ${username}"
    dscl . -create /Groups/${groupname} PrimaryGroupID 20 
    dscl . -create /Groups/${groupname} RealName "${groupname}"
    dscl . -create /Groups/${groupname} Password "*"
else
    echo 'Group already exists, skipping!'
fi

cp ncpa/build_resources/ncpa_listener.plist /System/Library/LaunchDaemons/org.nagios.ncpa_listener
cp ncpa/build_resources/ncpa_passive.plist /System/Library/LaunchDaemons/org.nagios.ncpa_passive

mkdir -p /usr/local/ncpa
cp -rf ncpa/* /usr/local/ncpa/
chmod -R 775 /usr/local/ncpa
chown -R -v nagios:nagcmd /usr/local/ncpa
cd - > /dev/null
