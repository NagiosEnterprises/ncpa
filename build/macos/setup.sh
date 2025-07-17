#!/usr/bin/env bash

echo -e "***** macos/setup.sh"

# Globals - defined in build.sh
#     PYTHONVER, SSLVER, ZLIBVER

# Load some installers and support functions
. $BUILD_DIR/macos/installers.sh

# Find system Python - will be set by verify_python function
PYTHONCMD=""
PYTHONBIN=""

set +e
SKIP_PYTHON=0

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

        echo -e "    - Verify or install Python..."
        if verify_or_install_python; then
            echo -e "      Python setup successful.\n"
        else
            echo -e "      Python setup failed. Exiting.\n"
            exit 1
        fi

        export PATH=$PATH:$BUILD_DIR/bin
    fi

    # --------------------------
    #  INSTALL PYTHON MODULES
    # --------------------------

    echo -e "    - Debug: Before update_py_packages - PYTHONCMD='$PYTHONCMD', PYTHONBIN='$PYTHONBIN'"
    update_py_packages
    echo $? > /tmp/update_py_packages_exit_code
    
    # Append the log separately to avoid pipe issues
    if [ -f $BUILD_DIR/build.log ]; then
        echo "update_py_packages completed with exit code: $(cat /tmp/update_py_packages_exit_code)" | sudo tee -a $BUILD_DIR/build.log
    fi

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
