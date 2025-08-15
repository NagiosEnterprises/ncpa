#!/bin/bash

# NCPA Build Version Configuration
# This file contains version information for all dependencies used in the build process
# Update this file when upgrading Python, OpenSSL, ZLIB, or other core dependencies
# 
# Different platforms may require different versions due to:
# - Available packages in repositories
# - System compatibility requirements  
# - Build environment constraints

# Detect current platform
UNAME=$(uname)

# Default versions (can be overridden per platform)
DEFAULT_PYTHONVER="3.13.5"
DEFAULT_SSLVER="3.0.17"
DEFAULT_ZLIBVER="1.3.1"

# Platform-specific version overrides
case "$UNAME" in
    "Darwin")
        # macOS versions
        PYTHONVER="${MACOS_PYTHONVER:-$DEFAULT_PYTHONVER}"
        SSLVER="${MACOS_SSLVER:-$DEFAULT_SSLVER}"
        ZLIBVER="${MACOS_ZLIBVER:-$DEFAULT_ZLIBVER}"
        OPENSSL_MAJOR="3"
        # Library versions for macOS builds
        MPDECIMAL_VERSION="4.0.0"
        SQLITE3_VERSION="3.0"
        LIBLZMA_VERSION="5"
        LIBFFI_VERSION="8"
        ;;
    "Linux")
        # Linux versions
        PYTHONVER="${LINUX_PYTHONVER:-$DEFAULT_PYTHONVER}"
        SSLVER="${LINUX_SSLVER:-$DEFAULT_SSLVER}"
        ZLIBVER="${LINUX_ZLIBVER:-$DEFAULT_ZLIBVER}"
        OPENSSL_MAJOR="3"
        ;;
    "AIX")
        # AIX versions (may need older versions for compatibility)
        PYTHONVER="${AIX_PYTHONVER:-3.6.15}"
        SSLVER="${AIX_SSLVER:-1.1.1}"
        ZLIBVER="${AIX_ZLIBVER:-1.2.11}"
        OPENSSL_MAJOR="1"
        ;;
    "SunOS")
        # Solaris versions - updated to prefer Python 3.13
        PYTHONVER="${SOLARIS_PYTHONVER:-3.13.5}"
        SSLVER="${SOLARIS_SSLVER:-3.0.17}"
        ZLIBVER="${SOLARIS_ZLIBVER:-1.3.1}"
        OPENSSL_MAJOR="3"
        ;;
    *)
        # Default fallback
        PYTHONVER="$DEFAULT_PYTHONVER"
        SSLVER="$DEFAULT_SSLVER"
        ZLIBVER="$DEFAULT_ZLIBVER"
        OPENSSL_MAJOR="3"
        ;;
esac

# OpenSSL library versions (derived from OPENSSL_MAJOR)
if [[ "$OPENSSL_MAJOR" == "3" ]]; then
    LIBSSL_VERSION="3"
    LIBCRYPTO_VERSION="3"
else
    LIBSSL_VERSION="1.1"
    LIBCRYPTO_VERSION="1.1"
fi

# Derived variables (computed from above)
PYTHON_MAJOR_MINOR=$(echo $PYTHONVER | cut -d. -f1-2)
PYTHON_MAJOR=$(echo $PYTHONVER | cut -d. -f1)
