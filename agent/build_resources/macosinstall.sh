#!/bin/sh

set -e

if ! dscl . read /Groups/nagcmd > /dev/null;
then
    if [ "$1" == "--create-user-and-group" ];
    then
        dscl . create /Groups/nagcmd gid 569
        dscl . create /Groups/nagcmd
        dscl . create /Groups/nagcmd Name "nagcmd"
        dscl . create /Groups/nagcmd RealName “Nagios Command Group”
        dscl . create /Groups/nagcmd passwd “*”
    else
        echo "User nagios is not created. I need the user nagios and the group nagcmd created."
        echo "nagios needs to be in the nagcmd group." 
        echo "Run the script with --create-user-and-group flag if you want me to create them."
        exit 1
    fi
fi

if ! dscl . read /Users/nagios > /dev/null;
then
    if [ "$1" == "--create-user-and-group" ];
    then
        dscl . -create /Users/nagios
        dscl . -create /Users/nagios UserShell /bin/bash 
        dscl . -create /Users/nagios RealName "Nagios Account" 
        dscl . -create /Users/nagios UniqueID 42 
        dscl . -create /Users/nagios PrimaryGroupID 569 
        dscl . -append /Groups/nagcmd GroupMembership nagios 
    else
        echo "User nagios is not created. I need the user nagios and the group nagcmd created."
        echo "nagios needs to be in the nagcmd group." 
        echo "Run the script with --create-user-and-group flag if you want me to create them."
        exit 1
    fi
fi

cp ncpa/build_resources/ncpa_listener.plist /System/Library/LaunchDaemons/org.nagios.ncpa_listener
cp ncpa/build_resources/ncpa_passive.plist /System/Library/LaunchDaemons/org.nagios.ncpa_passive

mkdir -p /usr/local/ncpa
cp -rf ncpa/* /usr/local/ncpa/
chmod -R 775 /usr/local/ncpa
chown -R nagios:nagcmd /usr/local/ncpa
