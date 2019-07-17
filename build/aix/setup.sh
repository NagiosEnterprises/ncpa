#!/bin/bash -e

PYTHONBIN=$(which python2.7)

update_py_packages() {
    echo "Skipping update packages, manually update them with:"
    echo "$PYTHONBIN -m pip install -r $BUILD_DIR/aix/require.aix.txt --upgrade"
}
