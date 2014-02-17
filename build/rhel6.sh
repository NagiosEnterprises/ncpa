set -e

. ./libinstall.sh

valid_python_version
binary_installed pip cxfreeze rpmbuild
