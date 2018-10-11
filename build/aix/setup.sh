#!/bin/bash -e

PYTHONBIN=$(which python2.7)

update_py_packages() {
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}
