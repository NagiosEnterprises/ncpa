#!/bin/sh

cp ncpa/build_resources/ncpa_listener.plist /System/Library/LaunchDaemons/org.nagios.ncpa_listener
cp ncpa/build_resources/ncpa_passive.plist /System/Library/LaunchDaemons/org.nagios.ncpa_passive

mkdir -p /usr/local/ncpa
cp -rf ncpa/* /usr/local/ncpa/
chmod -R 775 /usr/local/ncpa
chown -R nagios:nagios /usr/local/ncpa
