# NCPA Build Version Configuration

This document explains how to use the centralized version configuration system for NCPA builds.

## Overview

The version configuration system allows different versions of dependencies (Python, OpenSSL, ZLIB) for different platforms while maintaining centralized management. This is necessary because:

- Different operating systems may have different package availability
- System compatibility requirements may dictate specific versions
- Build environments may have constraints that require older versions

## Configuration Files

### `build/version_config.sh`
Bash configuration file used by Linux, macOS, AIX, and Solaris build scripts.

### `build/version_config.py`
Python configuration file used by setup.py and other Python-based build tools.

## Default Versions

- **Python**: 3.13.5 (default for modern platforms)
- **OpenSSL**: 3.0.17 (default for modern platforms) 
- **ZLIB**: 1.3.1

## Platform-Specific Overrides

### macOS (Darwin)
```bash
export MACOS_PYTHONVER="3.13.5"    # Override macOS Python version
export MACOS_SSLVER="3.0.17"       # Override macOS OpenSSL version
export MACOS_ZLIBVER="1.3.1"       # Override macOS ZLIB version
```

### Linux
```bash
export LINUX_PYTHONVER="3.13.5"    # Override Linux Python version
export LINUX_SSLVER="3.0.17"       # Override Linux OpenSSL version
export LINUX_ZLIBVER="1.3.1"       # Override Linux ZLIB version
```

### AIX
```bash
export AIX_PYTHONVER="3.6.15"      # Override AIX Python version (defaults to older version)
export AIX_SSLVER="1.1.1"          # Override AIX OpenSSL version (defaults to 1.x)
export AIX_ZLIBVER="1.2.11"        # Override AIX ZLIB version
```

### Solaris
```bash
export SOLARIS_PYTHONVER="3.9.13"  # Override Solaris Python version (defaults to older version)
export SOLARIS_SSLVER="1.1.1"      # Override Solaris OpenSSL version (defaults to 1.x)
export SOLARIS_ZLIBVER="1.2.11"    # Override Solaris ZLIB version
```

### Windows
```powershell
$env:WINDOWS_PYTHONVER = "3.13.5"  # Override Windows Python version
```

## Usage Examples

### To build with a specific Python version on macOS:
```bash
export MACOS_PYTHONVER="3.12.7"
./build/build.sh
```

### To build with older OpenSSL on Linux for compatibility:
```bash
export LINUX_SSLVER="1.1.1"
./build/build.sh
```

### To use different versions across platforms in CI:
```bash
# In CI script
if [[ "$RUNNER_OS" == "macOS" ]]; then
    export MACOS_PYTHONVER="3.13.5"
    export MACOS_SSLVER="3.0.17"
elif [[ "$RUNNER_OS" == "Linux" ]]; then
    export LINUX_PYTHONVER="3.11.9"  # Use older Python on Linux for broader compatibility
    export LINUX_SSLVER="3.0.17"
fi
./build/build.sh
```

## How It Works

1. **Platform Detection**: The system automatically detects the current platform using `uname` (bash) or `platform.system()` (Python)

2. **Version Resolution**: For each platform, versions are resolved in this order:
   - Environment variable override (e.g., `MACOS_PYTHONVER`)
   - Platform-specific default (e.g., AIX uses older versions)
   - Global default

3. **Library Path Generation**: Platform-specific library paths are automatically generated using the resolved versions

## Files Updated

The following files now use the centralized version configuration:

- `build/build.sh` - Main build script
- `agent/setup.py` - cx_Freeze configuration
- `build/macos/installers.sh` - macOS installer script
- `build/macos/package.sh` - macOS packaging script
- `build/macos/linkdynlibs.sh` - macOS library linking
- `build/solaris/setup.sh` - Solaris setup script
- `build/windows/choco_prereqs.ps1` - Windows prerequisites

## Testing

Run the test script to verify configuration:
```bash
./build/test_versions.sh
```

This will show the resolved versions for your current platform and verify both bash and Python configurations are working correctly.
