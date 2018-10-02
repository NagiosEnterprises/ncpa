#!/bin/bash -e

# Set global build opts
DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$(realpath "$DIR/..")
BUILD_RPM_DIR="/usr/src/redhat"
VERSION=$(cat $BUILD_DIR/../VERSION)

# Get information about system
. $BUILD_DIR/linux/init.sh

