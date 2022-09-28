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

# Check if this terminal program has Full Disk Access.
# Since there is no direct method, we try a command that requires FDA
hasFDA=$(cat /Library/Preferences/com.apple.TimeMachine.plist 2>/dev/null)
if [[ ! $hasFDA ]]; then
    echo -e "\nERROR: Full Disk Access is not available!\n"
    echo "    This terminal program must be given 'Full Disk Access' in order to run this installer:"
    echo "        1. Go to System Preferences/Security & Privacy"
    echo "        2. Click the Full Disk Access (FDA) tab"
    echo "        3. Find this terminal program, and check its checkbox"
    echo "        4. Restart this terminal program, and re-run this installer."
    echo "     "
    echo "        Note: For security purposes, turn off FDA privileges for this program by unchecking the checkbox when you are done with this installation."
    exit 1
else
    echo "    Full Disk Access is on for this terminal app."
fi

# Quit if any errors occur
set -e

# Save config and disable NCPA if it's already installed for upgrade
if [ ${upgrade} -eq "1" ]; then
    # Temporarily save etc directory
    echo -n "    Saving configuration... "
    cp -Rf ${homedir}/etc /tmp/ncpa_etc
#     cat /tmp/ncpa_etc/ncpa.cfg | grep "community_string ="
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
# cat ${homedir}/etc/ncpa.cfg | grep "community_string ="
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
#     ls ${homedir}/etc
    cp -Rf "/tmp/ncpa_etc" "${homedir}/etc"
    rm -rf /tmp/ncpa_etc
#     cat ${homedir}/etc/ncpa.cfg | grep "community_string ="
    echo "Done."
#     ls ${homedir}/etc
fi

# Check if required python directory exists, if not make one
pyDir="/usr/local/opt/python@2/Frameworks/Python.framework/Versions/2.7"
if [[ ! -d ${pyDir} ]]; then
    echo "    Installing Python... "
    echo "        Creating Python directory: ${pyDir}... "
    mkdir -p ${pyDir}
#    ls ${pyDir}
fi

# Python doesn't exist in directory, we probably created it,
# so we copy installer provided copy of Python into directory.
if [[ ! -f "${pyDir}/Python" ]]; then
    pyFile="${homedir}/Python"
    echo "        Copying ${pyFile} to ${pyDir}... "
#     echo  "${pyDir}/"
    cp ${pyFile} ${pyDir}

    # Add file so we can identify if we installed this for uninstaller
    touch "${pyDir}/installed_by_ncpa"
#     ls -l ${pyDir}
    echo "    Done."

    echo " "
    echo "    ******** Attention!! ********"
    echo "    An unsigned version of Python, needed for NCPA, has been installed at:.\n        ${pyDir}/Python"
    echo "     "
    echo "    To allow this Python to execute, follow these steps:"
    echo "      1. In the Finder on your Mac, choose from the Go menu: go to folder... "
    echo "      2. enter: '${pyDir}'"
    echo "      3. Control/Right click the Python icon, then choose 'Open' from the shortcut menu. "
    echo "         A terminal window will pop up, and you can ignore it or close it."
    echo "      4. Return to this window and press any key to Continue."
    read -s -k $'?    Press any key to continue.\n'
    echo " "
else
    echo "    Python v2.7 available"
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

    echo "\nCustom Python?:"
    pyDir="/usr/local/opt/python@2/Frameworks/Python.framework/Versions/2.7"
    ls -l ${pyDir} 2>/dev/null
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
