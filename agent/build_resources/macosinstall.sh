#!/bin/sh

set -e

USER=nagios
GROUP=nagcmd

if dscl . list /groups | grep nagcmd > /dev/null;
then
    if [ "$1" -eq "--create-user-and-group" ];
    then
        dscl . create /Groups/nagcmd gid 569
    else
        echo "User nagios is not created. I need the user nagios and the group nagcmd created."
        echo "nagios needs to be in the nagcmd group." 
        echo "Run the script with --create-user-and-group flag if you want me to create them."
        exit 1
    fi
fi

if dscl . list /users | grep nagios > /dev/null;
then
    if [ "$1" -eq "--create-user-and-group" ];
    then
        dscl . create /Users/nagios PrimaryGroupID 569
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
chown -R nagios:nagios /usr/local/ncpa
