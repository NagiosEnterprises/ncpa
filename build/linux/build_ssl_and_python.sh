#!/bin/bash
#
# This script compiles and installs OpenSSL and Python from source on a Linux system.
# It ensures that Python is linked against the newly installed OpenSSL version.
# Note: This script requires sudo privileges to install software and configure the system.
#

# Set versions and installation directories
OPENSSL_VERSION="3.5.5" 
PYTHON_VERSION="3.13.12"
PYTHON_VERSION_SHORT=$(echo $PYTHON_VERSION | cut -d. -f1,2) # Extract major.minor
INSTALL_DIR_OPENSSL="/usr/local/openssl_${OPENSSL_VERSION}"
INSTALL_DIR_PYTHON="/usr/local/python_${PYTHON_VERSION}"

# Determine the package manager and install necessary build dependencies
if command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
# Check if 'apt' command is available
elif command -v apt >/dev/null 2>&1; then
    PKG_MANAGER="apt"
# Check if 'apt-get' command is available (preferred for scripting over 'apt')
elif command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt-get"
# Check for 'yum' as an alternative to 'dnf' for older systems
elif command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
else
    echo "Error: No supported package manager (apt or dnf/yum) found." >&2
    exit 1
fi

echo "Detected package manager: $PKG_MANAGER"

# Update package lists and install build dependencies
if [ "$PKG_MANAGER" = "apt" ] || [ "$PKG_MANAGER" = "apt-get" ]; then
    echo "This is a Debian-based system."
    sudo $PKG_MANAGER update
    sudo $PKG_MANAGER install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl wget tar make perl
elif [ "$PKG_MANAGER" = "dnf" ] || [ "$PKG_MANAGER" = "yum" ]; then
    echo "This is a RedHat-based system."
    sudo $PKG_MANAGER install -y gcc make perl perl-core autoconf automake libtool tar gzip wget zlib-devel libffi-devel sqlite-devel
fi

echo "Build dependencies installed successfully."

# Create source directory
mkdir -p /usr/local/src
cd /usr/local/src

# --- 1. Compile and Install OpenSSL ---

echo "Downloading and installing OpenSSL..."
wget https://github.com/openssl/openssl/releases/download/openssl-${OPENSSL_VERSION}/openssl-${OPENSSL_VERSION}.tar.gz

echo "Extracting OpenSSL source..."
tar -xzvf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}

echo "Configuring OpenSSL with zlib support..."
./config --prefix=$INSTALL_DIR_OPENSSL --openssldir=$INSTALL_DIR_OPENSSL shared zlib
echo "Compiling and installing OpenSSL..."
make -j$(nproc)
# make test # Optional: run tests
sudo make install_sw # Use install_sw to avoid overwriting openssl.cnf

# Configure dynamic linker runtime path for the new OpenSSL version
echo "Configuring dynamic linker for OpenSSL..."
echo "$INSTALL_DIR_OPENSSL/lib64" | sudo tee /etc/ld.so.conf.d/openssl-custom.conf
sudo ldconfig -v

echo "Creating symbolic links for OpenSSL binaries..."
sudo ln -sf $INSTALL_DIR_OPENSSL/lib64 $INSTALL_DIR_OPENSSL/lib

# Return to source directory
echo "OpenSSL installation complete."
cd /usr/local/src

# --- 2. Compile and Install Python with Custom OpenSSL ---

echo "Downloading and installing Python..."
wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz

echo "Extracting Python source..."
tar -xzvf Python-${PYTHON_VERSION}.tgz
cd Python-${PYTHON_VERSION}

# Configure Python to use the newly installed OpenSSL version and enable optimizations
echo "Configuring Python with custom OpenSSL..."
./configure --prefix=$INSTALL_DIR_PYTHON --with-openssl=$INSTALL_DIR_OPENSSL --enable-optimizations --enable-shared

echo "Compiling and installing Python..."
make -j$(nproc)
sudo make altinstall # Use altinstall to avoid overwriting the system python3 binary

echo "Configuring dynamic linker for Python..."
echo "$INSTALL_DIR_PYTHON/lib" | sudo tee /etc/ld.so.conf.d/python-custom.conf
sudo ldconfig -v

echo "Python installation complete."


# --- Verification ---

echo "Installation complete."
echo "New OpenSSL version:"
$INSTALL_DIR_OPENSSL/bin/openssl version
echo "New Python version:"
$INSTALL_DIR_PYTHON/bin/python${PYTHON_VERSION_SHORT} -VV

echo "You may need to add $INSTALL_DIR_PYTHON/bin to your PATH environment variable to use it easily."