#!/bin/bash

# Test script to verify version configuration is working correctly

echo "Testing version configuration..."
echo "Platform: $(uname)"

# Test bash version config
echo "=== Testing bash version config ==="
BUILD_DIR=$(dirname "$0")
source "$BUILD_DIR/version_config.sh"

echo "PYTHONVER: $PYTHONVER"
echo "SSLVER: $SSLVER" 
echo "ZLIBVER: $ZLIBVER"
echo "OPENSSL_MAJOR: $OPENSSL_MAJOR"
echo "LIBSSL_VERSION: $LIBSSL_VERSION"
echo "LIBCRYPTO_VERSION: $LIBCRYPTO_VERSION"

if [[ "$(uname)" == "Darwin" ]]; then
    echo "MPDECIMAL_VERSION: $MPDECIMAL_VERSION"
    echo "SQLITE3_VERSION: $SQLITE3_VERSION"
    echo "LIBLZMA_VERSION: $LIBLZMA_VERSION"
    echo "LIBFFI_VERSION: $LIBFFI_VERSION"
fi

# Test Python version config
echo -e "\n=== Testing Python version config ==="
python3 << EOF
import sys
sys.path.insert(0, '$BUILD_DIR')
from version_config import *

print(f"Platform: {system}")
print(f"PYTHON_VERSION: {PYTHON_VERSION}")
print(f"OPENSSL_VERSION: {OPENSSL_VERSION}")
print(f"ZLIB_VERSION: {ZLIB_VERSION}")
print(f"OPENSSL_MAJOR: {OPENSSL_MAJOR}")
print(f"LIBSSL_VERSION: {LIBSSL_VERSION}")
print(f"LIBCRYPTO_VERSION: {LIBCRYPTO_VERSION}")

if system == "Darwin":
    print(f"MPDECIMAL_VERSION: {MPDECIMAL_VERSION}")
    print(f"SQLITE3_VERSION: {SQLITE3_VERSION}")
    print(f"LIBLZMA_VERSION: {LIBLZMA_VERSION}")
    print(f"LIBFFI_VERSION: {LIBFFI_VERSION}")
    
    print("\nMacOS library paths:")
    for src, dst in get_macos_lib_paths():
        print(f"  {src} -> {dst}")

print("\nLinux lib includes:")
for lib in get_linux_lib_includes():
    print(f"  {lib}")
EOF

# Test environment variable overrides
echo -e "\n=== Testing environment variable overrides ==="
echo "Testing with LINUX_PYTHONVER=3.11.9..."

LINUX_PYTHONVER=3.11.9 bash << 'EOFBASH'
BUILD_DIR=$(dirname "$0")
source "$BUILD_DIR/version_config.sh"
echo "PYTHONVER with override: $PYTHONVER"
EOFBASH

echo -e "\n=== Version config test complete ==="
