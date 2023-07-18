#!/bin/bash -e

echo -e "***** macos/setup.sh"

# Globals
PYTHONVER="3.11.3"
PYTHONTAR="Python-$PYTHONVER"

# Make python command, e.g. python3.11
PYTHONCMD="python$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')"
echo -e "***** macos/setup.sh - PYTHONCMD: $PYTHONCMD"

set +e
PYTHONBIN=$(which $PYTHONCMD)
set -e

SKIP_PYTHON=0

update_py_packages() {
    $PYTHONBIN -m pip install --upgrade pip
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}

install_prereqs() {

    cd $BUILD_DIR/resources

    # Install bundled Python version from source
    if [ $SKIP_PYTHON -eq 0 ]; then
        tar xf $PYTHONTAR.tgz
        cd $PYTHONTAR
        ./configure && make && make altinstall
        cd ..
        rm -rf $PYTHONTAR
        PYTHONBIN=$(which $PYTHONCMD)
    fi

    # Install modules
#     update_py_packages

}

# Add users/groups
set +e
sudo sysadminctl -addUser nagios
sudo dseditgroup -o create nagios
sudo dseditgroup -o edit -a nagios -t user nagios
set -e

