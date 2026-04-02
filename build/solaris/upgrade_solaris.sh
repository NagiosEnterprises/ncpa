#!/bin/bash

# Solaris NCPA Upgrade Script
# Preserves /usr/local/ncpa/etc during upgrade

set -e

NCPA_ETC="/usr/local/ncpa/etc"
NCPA_ETC_BACKUP="/tmp/ncpa_etc_backup_$(date +%s)"
NEW_PKG_FILE="${1:?Error: Please provide the new NCPA pkg file as argument}"

if [ ! -f "$NEW_PKG_FILE" ]; then
    echo "Error: Package file not found: $NEW_PKG_FILE"
    exit 1
fi

if [ ! -d "$NCPA_ETC" ]; then
    echo "Error: NCPA config directory not found: $NCPA_ETC"
    exit 1
fi

echo "Backing up $NCPA_ETC to $NCPA_ETC_BACKUP..."
cp -r "$NCPA_ETC" "$NCPA_ETC_BACKUP"

echo "Removing current NCPA package..."
pkgrm -n -a admin_file ncpa

echo "Verifying NCPA package removal..."
if pkginfo -l ncpa > /dev/null 2>&1; then
    echo "Error: NCPA package removal failed."
    exit 1
fi

echo "Installing new NCPA package..."
pkgadd -a admin_file -d "$NEW_PKG_FILE" ncpa

echo "Restoring configuration files..."
cp -r "$NCPA_ETC_BACKUP"/* "$NCPA_ETC/"

echo "Cleaning up backup..."
rm -rf "$NCPA_ETC_BACKUP"

echo "Restarting NCPA service..."
svcadm restart ncpa

echo "NCPA upgrade completed successfully!"