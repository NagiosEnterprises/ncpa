#!/usr/bin/env bash

echo -e "***** macos/setup.sh"

# Globals - defined in build.sh
#     PYTHONVER, SSLVER, ZLIBVER

# Make python command, e.g. python3.11
PYTHONCMD="python$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')"
echo -e "***** macos/setup.sh - PYTHONCMD: $PYTHONCMD"

set +e
PYTHONBIN=$(which $PYTHONCMD)
set -e
SKIP_PYTHON=0

# Load some installers and support functions
. $BUILD_DIR/macos/installers.sh

install_prereqs() {
    # ---------------------
    #  INSTALL SYSTEM REQS
    # ---------------------

    # Install proper version of python
    if [ $SKIP_PYTHON -eq 0 ]; then
        echo -e "***** macos/setup.sh - OpenSSL..."
        has_ssl=$(has_openssl $SSLVER)
        if [[ ! -z $($installchk) ]]; then
            echo -e "OpenSSL $SSLVER already installed."

        else
            echo -e "Installing OpenSSL $SSLVER ..."
            cd $BUILD_DIR/resources
            install_devtools && \
            install_openssl $SSLVER
        fi

        echo -e "***** macos/setup.sh - Python..."
        has_python=$(has_python $PYTHONVER)
        if [[ ! -z $($installchk) ]]; then
            echo -e "Python $PYTHONVER already installed."

        else
            echo -e "Installing Python $PYTHONVER ..."
            cd $BUILD_DIR/resources
            install_python $PYTHONVER
            PYTHONBIN=$(which $PYTHONCMD)
            echo -e "***** macos/setup.sh - after Py install PYTHONBIN: $PYTHONBIN"
        fi

        export PATH=$PATH:$BUILD_DIR/bin
    fi

    # --------------------------
    #  INSTALL PYTHON MODULES
    # --------------------------

    update_py_packages

    # --------------------------
    #  MISC ADDITIONS
    # --------------------------

}

# Add users/groups
set +e
sudo sysadminctl -addUser nagios
sudo dseditgroup -o create nagios
sudo dseditgroup -o edit -a nagios -t user nagios
set -e

