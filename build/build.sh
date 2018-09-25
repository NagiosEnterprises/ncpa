#!/bin/bash -e

UNAME=$(uname)

# Check that pre-reqs have been installed
if [ ! -f prereqs.installed ]; then

    # Try to determine system type
    if [ "$UNAME" == "Linux" ]; then
        linux/setup.sh
    elif [ "$UNAME" == "SunOS" ] || [ "$UNAME" == "Solaris" ]; then
        solaris/setup.sh
    elif [ "$UNAME" == "Darwin" ]; then
        osx/setup.sh
    else
        echo "Could not automatically determine system type."
        echo "Please run the setup.sh script in the folder for the build type below:"
        echo " - linux"
        echo " - osx"
        echo " - aix"
        echo " - solaris"
    fi

fi

# Update the required python modules


# Build the python with cx_Freeze






