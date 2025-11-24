"""
NCPA Build Version Configuration
This file contains version information for all dependencies used in the build process
Update this file when upgrading Python, OpenSSL, ZLIB, or other core dependencies

Different platforms may require different versions due to:
- Available packages in repositories
- System compatibility requirements  
- Build environment constraints
"""

import platform
import os
import sys
import glob

# Detect current platform
system = platform.system()

# Default versions (can be overridden per platform)
DEFAULT_PYTHON_VERSION = "3.13.5"
DEFAULT_OPENSSL_VERSION = "3.0.17"
DEFAULT_ZLIB_VERSION = "1.3.1"

# Platform-specific version configurations
PLATFORM_VERSIONS = {
    "Darwin": {  # macOS
        "python": os.environ.get("MACOS_PYTHONVER", DEFAULT_PYTHON_VERSION),
        "openssl": os.environ.get("MACOS_SSLVER", DEFAULT_OPENSSL_VERSION),
        "zlib": os.environ.get("MACOS_ZLIBVER", DEFAULT_ZLIB_VERSION),
        "openssl_major": "3",
        "mpdecimal": "4.0.0",
        "sqlite3": "3.0",
        "liblzma": "5",
        "libffi": "8"
    },
    "Linux": {
        "python": os.environ.get("LINUX_PYTHONVER", DEFAULT_PYTHON_VERSION),
        "openssl": os.environ.get("LINUX_SSLVER", DEFAULT_OPENSSL_VERSION),
        "zlib": os.environ.get("LINUX_ZLIBVER", DEFAULT_ZLIB_VERSION),
        "openssl_major": "3"
    },
    "AIX": {
        "python": os.environ.get("AIX_PYTHONVER", "3.6.15"),
        "openssl": os.environ.get("AIX_SSLVER", "1.1.1"),
        "zlib": os.environ.get("AIX_ZLIBVER", "1.2.11"),
        "openssl_major": "1"
    },
    "SunOS": {  # Solaris
        "python": os.environ.get("SOLARIS_PYTHONVER", "3.12.8"),
        "openssl": os.environ.get("SOLARIS_SSLVER", "3.0.17"),
        "zlib": os.environ.get("SOLARIS_ZLIBVER", "1.3.1"),
        "openssl_major": "3"
    }
}

# Get platform-specific versions
platform_config = PLATFORM_VERSIONS.get(system, {
    "python": DEFAULT_PYTHON_VERSION,
    "openssl": DEFAULT_OPENSSL_VERSION,
    "zlib": DEFAULT_ZLIB_VERSION,
    "openssl_major": "3"
})

# Export version variables
PYTHON_VERSION = platform_config["python"]
OPENSSL_VERSION = platform_config["openssl"]
ZLIB_VERSION = platform_config["zlib"]
OPENSSL_MAJOR = platform_config["openssl_major"]

# Platform-specific library versions (macOS only)
MPDECIMAL_VERSION = platform_config.get("mpdecimal", "4.0.0")
SQLITE3_VERSION = platform_config.get("sqlite3", "3.0")  
LIBLZMA_VERSION = platform_config.get("liblzma", "5")
LIBFFI_VERSION = platform_config.get("libffi", "8")

# OpenSSL library versions (derived from OPENSSL_MAJOR)
if OPENSSL_MAJOR == "3":
    LIBSSL_VERSION = "3"
    LIBCRYPTO_VERSION = "3"
else:
    LIBSSL_VERSION = "1.1"
    LIBCRYPTO_VERSION = "1.1"

# Derived variables (computed from above)
PYTHON_MAJOR_MINOR = '.'.join(PYTHON_VERSION.split('.')[:2])
PYTHON_MAJOR = PYTHON_VERSION.split('.')[0]

# macOS library paths with versions
def get_macos_lib_paths():
    """Return macOS library paths with proper versioning"""
    if system != "Darwin":
        return []
    
    return [
        (f'/usr/local/opt/mpdecimal/lib/libmpdec.{MPDECIMAL_VERSION}.dylib', f'lib/libmpdec.{MPDECIMAL_VERSION}.dylib'),
        (f'/usr/local/opt/openssl@{OPENSSL_MAJOR}/lib/libcrypto.{LIBCRYPTO_VERSION}.dylib', f'lib/libcrypto.{LIBCRYPTO_VERSION}.dylib'),
        (f'/usr/local/opt/openssl@{OPENSSL_MAJOR}/lib/libssl.{LIBSSL_VERSION}.dylib', f'lib/libssl.{LIBSSL_VERSION}.dylib'),
        (f'/usr/local/opt/sqlite/lib/libsqlite{SQLITE3_VERSION}.dylib', f'lib/libsqlite{SQLITE3_VERSION}.dylib'),
        (f'/usr/local/opt/xz/lib/liblzma.{LIBLZMA_VERSION}.dylib', f'lib/liblzma.{LIBLZMA_VERSION}.dylib')
    ]

def get_macos_libffi_path(os_major_version):
    """Return libffi path based on macOS version"""
    if system != "Darwin" or os_major_version != '10':
        return []
    return [(f'/usr/local/opt/libffi/lib/libffi.{LIBFFI_VERSION}.dylib', f'lib/libffi.{LIBFFI_VERSION}.dylib')]

def get_linux_lib_includes():
    """Return Linux library includes with proper versioning"""
    return [f'libffi.so', f'libssl.so.{LIBSSL_VERSION}', f'libcrypto.so.{LIBCRYPTO_VERSION}']

def get_solaris_lib_paths():
    """Return Solaris library paths with proper versioning"""
    if system != "SunOS":
        return []
    
    import sys
    import glob
    
    # Detect the actual Python version being used
    actual_python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    paths = []
    
    # Try to find the Python library in IPS locations first (preferred)
    python_lib_found = False
    for python_lib_path in [
        f'/usr/lib/python{actual_python_version}/config-{actual_python_version}*/libpython{actual_python_version}.so*',
        f'/usr/lib/libpython{actual_python_version}.so*',
        f'/usr/local/lib/libpython{actual_python_version}.so*'
    ]:
        matches = glob.glob(python_lib_path)
        if matches:
            # Use the first match found
            paths.append((matches[0], f'libpython{actual_python_version}.so'))
            python_lib_found = True
            break
    
    # Fall back to OpenCSW Python if IPS version not found
    if not python_lib_found:
        csw_python_lib = f'/opt/csw/lib/libpython{actual_python_version}.so'
        if os.path.exists(csw_python_lib):
            paths.append((csw_python_lib, f'libpython{actual_python_version}.so'))
    
    # Add other libraries, preferring IPS locations over OpenCSW
    lib_mappings = [
        # (IPS_path, CSW_path, target_name)
        ('/usr/lib/libsqlite3.so', '/opt/csw/lib/libsqlite3.so', 'libsqlite3.so'),
        ('/usr/lib/libssl.so', '/opt/csw/lib/libssl.so', 'libssl.so'),
        ('/usr/lib/libcrypto.so', '/opt/csw/lib/libcrypto.so', 'libcrypto.so'),
        ('/usr/lib/libffi.so', '/opt/csw/lib/libffi.so', 'libffi.so'),
        ('/usr/lib/libz.so', '/opt/csw/lib/libz.so', 'libz.so')
    ]
    
    for ips_path, csw_path, target_name in lib_mappings:
        # Check for versioned libraries in IPS locations
        ips_matches = glob.glob(f'{ips_path}*')
        if ips_matches:
            paths.append((ips_matches[0], target_name))
        elif os.path.exists(csw_path):
            # Fall back to OpenCSW
            paths.append((csw_path, target_name))
        else:
            # Try to find the library anywhere on the system
            system_matches = []
            for search_path in ['/lib', '/usr/lib', '/usr/local/lib', '/opt/csw/lib']:
                system_matches.extend(glob.glob(f'{search_path}/{target_name}*'))
            if system_matches:
                paths.append((system_matches[0], target_name))
    
    return paths
