#!/bin/bash
#
# check_os.sh
#
# Nagios Plugin to display the Operating System type

# Fetch the OS name using uname
OS_TYPE=$(uname -s)
OS_RELEASE=$(uname -r)

# Verify we got a response
if [ -z "$OS_TYPE" ]; then
    echo "UNKNOWN - Unable to determine operating system type."
    exit 3
fi

# Print the Nagios-formatted string 
echo "OK - Operating System: $OS_TYPE ($OS_RELEASE)"

# Exit with status 0 (OK)
exit 0