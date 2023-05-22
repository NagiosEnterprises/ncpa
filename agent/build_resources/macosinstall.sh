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
upgrade="0"
added="0"

# Check if NCPA is installed
if [ -d ${homedir} ]; then
    upgrade="1"
    echo "Starting upgrade... "
else
    echo "Starting install... "
fi

# Get MacOS version
macOSVer=""
if [[ $OSTYPE == 'darwin'* ]]; then
    macOSVer=`sw_vers | grep ProductVersion | awk '{print $2}'`
    echo "    MacOS version: $macOSVer."
fi

# Go to install script directory
pushd $( dirname -- "${0}" )

# Quit if any errors occur
set -e

# Save config and disable NCPA if it's already installed for upgrade
if [ ${upgrade} -eq "1" ]; then
    # Temporarily save etc directory
    echo -n "    Saving configuration... "
    cp -Rf ${homedir}/etc /tmp/ncpa_etc
    echo "Done."

    echo -n "    Stopping old NCPA services... "
    launchctl stop com.nagios.ncpa.listener
    launchctl stop com.nagios.ncpa.passive

    # Give launchctl time to stop services before continuing
    sleep 5
    echo "Done."
fi

# Create the group account
if ! dscl . -read /Groups/${groupname} > /dev/null 2>&1; then
    echo -n "    Adding nagios user and group... "
    echo -n "Creating the group account... "
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
if ! dscl . -read /Users/${username} > /dev/null 2>&1; then
    echo -n "Creating the user account... "
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
    echo "Done."
else
    echo "    Nagios user and group already exist."
fi

# Unload the daemons so they can be re-loaded after
if [ ${upgrade} -eq "1" ]; then
    echo -n "    Unloading old NCPA services... "
    launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
    launchctl unload /Library/LaunchDaemons/com.nagios.ncpa.passive.plist
    echo "Done."
fi

cp ncpa/build_resources/ncpa_listener.plist /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
cp ncpa/build_resources/ncpa_passive.plist /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

# Remove MacOS x attributes
echo -n "    Removing MacOS xattributes from LaunchDaemon plists... "
if [[ $(xattr -l /Library/LaunchDaemons/com.nagios.ncpa.listener.plist) ]]; then
    xattr -d com.apple.quarantine /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
fi

if [[ $(xattr -l /Library/LaunchDaemons/com.nagios.ncpa.passive.plist) ]]; then
    xattr -d com.apple.quarantine /Library/LaunchDaemons/com.nagios.ncpa.passive.plist
fi

echo "Done."

echo -n "    Copying new NCPA files... "
mkdir -p ${homedir}
cp -Rf ncpa/* ${homedir}
echo "Done."

echo -n "    Setting permissions... "
chmod -R 775 ${homedir}
chown -R ${username}:${groupname} ${homedir}
chmod +x "${homedir}/uninstall.sh"
echo "Done."

echo -n "    Removing MacOS xattributes from ${homedir}... "
xattr -d -r com.apple.quarantine ${homedir}
echo "Done."

# Restore config files
if [ ${upgrade} -eq "1" ]; then
    echo -n "    Restoring configuration to ${homedir}/etc... "
    rm -rf ${homedir}/etc
    cp -Rf "/tmp/ncpa_etc" "${homedir}/etc"
    rm -rf /tmp/ncpa_etc
    echo "Done."
fi

echo -n "    Starting NCPA... "
launchctl load /Library/LaunchDaemons/com.nagios.ncpa.listener.plist
launchctl load /Library/LaunchDaemons/com.nagios.ncpa.passive.plist

launchctl start com.nagios.ncpa.passive
launchctl start com.nagios.ncpa.listener
echo "Done."

listNCPAcomponents() {
    echo "---------------------------------------"
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

listNCPAcomponents

# Installation completed
echo " "
tokenPhrase="'mytoken'"
if [ ${upgrade} -eq "1" ]; then
    echo "-------------------"
    echo " Upgrade Completed "
    echo "-------------------"
    tokenPhrase="your token"
else
    echo "-------------------"
    echo " Install Completed "
    echo "-------------------"
fi

echo "\nConfirm your installation:"
echo "    1. In a web browser, navigate to https://localhost:5693 "
echo "       (acknowledge the uncertified certificate warning, if necessary)"
echo "    2. Enter ${tokenPhrase} when it asks for a token or a password"
echo "    3. Click the 'See Live Stats' button\n"
echo "    After several seconds the graphs should start populating with data."
echo "    NCPA is now capturing data from your Mac!"

popd
exit 0
