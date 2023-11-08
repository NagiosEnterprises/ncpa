#!/usr/bin/env bash

echo -e "***** macos/setup.sh"

# Globals - defined in build.sh
#     PYTHONVER, SSLVER, ZLIBVER

# Make python command, e.g. python3.11
PYTHONSHORTVER=$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')
PYTHONCMD="python$PYTHONSHORTVER"
echo -e "    - PYTHONCMD: $PYTHONCMD"

set +e
PYTHONBIN=$(which $PYTHONCMD)
set -e
SKIP_PYTHON=0

# Load some installers and support functions
. $BUILD_DIR/macos/installers.sh

install_prereqs() {
    echo -e "***** macos/setup.sh - install_prereqs()..."
    # ---------------------
    #  INSTALL SYSTEM REQS
    # ---------------------

    # Install proper version of python
    if [ $SKIP_PYTHON -eq 0 ]; then
        echo -e "    - Install dev tools..."
        # if [[ -z $( which brew 2>/dev/null ) ]]; then
            cd $BUILD_DIR/resources
            install_devtools

        # else
        #     echo -e "Homebrew and dev tools already installed.\n"
        # fi

        echo -e "    - Install Python..."
        has_python=$(has_python $PYTHONSHORTVER)
        if [[ ! -z $has_python ]]; then
            echo -e "      Python $PYTHONSHORTVER already installed.\n"

        else
            echo -e "    - Installing Python $PYTHONVER with OpenSSL 3 ..."
            cd $BUILD_DIR/resources
            install_python $PYTHONVER
            PYTHONBIN=$(which $PYTHONCMD)
        fi

        export PATH=$PATH:$BUILD_DIR/bin
    fi

    # --------------------------
    #  INSTALL PYTHON MODULES
    # --------------------------

    update_py_packages | sudo tee -a $BUILD_DIR/build.log

    # --------------------------
    #  MISC ADDITIONS
    # --------------------------

}

# Add users/groups
if ! dscl . -read /Users/nagios > /dev/null 2>&1; then
    set +e
    sudo sysadminctl -addUser nagios
    sudo dseditgroup -o create nagios
    sudo dseditgroup -o edit -a nagios -t user nagios
    set -e
fi
