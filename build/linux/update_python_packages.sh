#!/bin/bash -e

BASEDIR="$(dirname "$BASH_SOURCE")"
PYTHONVER=python2.7
PYTHONBIN=`which python2.7`

# Get OS info
. $BASEDIR/init.sh

# Update with requirements
$PYTHONBIN -m pip install -r $BASEDIR/../resources/require.txt --upgrade

echo "Python pip requirements updated."