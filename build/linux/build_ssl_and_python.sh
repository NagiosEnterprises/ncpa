#!/bin/bash

OPENSSL_VERSION="3.5.5" 
PYTHON_VERSION="3.13.12"
PYTHON_VERSION_SHORT=$(echo $PYTHON_VERSION | cut -d. -f1,2) # Extract major.minor for symlink  

INSTALL_DIR_OPENSSL="/usr/local/openssl"
INSTALL_DIR_PYTHON="/usr/local/python_${PYTHON_VERSION}"

# Update package lists and install build dependencies
echo "Installing build dependencies..."
sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl wget tar make perl

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
#./configure --enable-shared --enable-optimizations --prefix=/usr/local LDFLAGS="-Wl,-rpath /usr/local/lib"

echo "Compiling and installing Python..."
make -j$(nproc)
sudo make altinstall # Use altinstall to avoid overwriting the system python3 binary

echo "Configuring dynamic linker for Python..."
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$INSTALL_DIR_PYTHON/lib
echo "$INSTALL_DIR_PYTHON/lib" | sudo tee /etc/ld.so.conf.d/python-custom.conf
sudo ldconfig -v

echo "Python installation complete."


# --- Verification ---

echo "Installation complete."
echo "New OpenSSL version:"
$INSTALL_DIR_OPENSSL/bin/openssl version
echo "New Python version:"
$INSTALL_DIR_PYTHON/bin/python${PYTHON_VERSION_SHORT} --version

echo "You may need to add $INSTALL_DIR_PYTHON/bin to your PATH environment variable to use it easily."