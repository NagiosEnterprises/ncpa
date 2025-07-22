# NCPA Build System Improvement Plan

## Vision Statement

Transform the NCPA build system from a collection of platform-specific shell scripts into a modern, maintainable, and robust build framework while preserving all critical platform-specific nuances and workarounds that ensure successful builds across all supported platforms.

## Design Principles

1. **Preserve Functionality**: Maintain all existing platform support and workarounds
2. **Improve Maintainability**: Standardize code structure and reduce duplication
3. **Enhance Readability**: Clear naming conventions and comprehensive documentation
4. **Increase Reliability**: Better error handling and validation
5. **Enable Extensibility**: Modular design for easy platform additions

## Proposed Architecture

### Core Framework Structure

```
build/
├── framework/                    # New build framework
│   ├── core/
│   │   ├── build_manager.py     # Main orchestration
│   │   ├── platform_detector.py # Platform detection and validation
│   │   ├── version_manager.py   # Centralized version management
│   │   ├── logger.py            # Unified logging system
│   │   └── utils.py             # Common utilities
│   ├── platforms/               # Platform-specific modules
│   │   ├── base_platform.py    # Abstract base class
│   │   ├── linux_platform.py   # Linux implementation
│   │   ├── macos_platform.py   # macOS implementation
│   │   ├── windows_platform.py # Windows implementation
│   │   ├── aix_platform.py     # AIX implementation
│   │   └── solaris_platform.py # Solaris implementation
│   ├── installers/              # Dependency installers
│   │   ├── base_installer.py   # Base installer class
│   │   ├── python_installer.py # Python source builds
│   │   ├── ssl_installer.py    # OpenSSL builds
│   │   └── system_packages.py  # System package managers
│   └── packagers/               # Package generators
│       ├── base_packager.py    # Base packaging class
│       ├── rpm_packager.py     # RPM packaging
│       ├── deb_packager.py     # DEB packaging
│       ├── dmg_packager.py     # macOS DMG packaging
│       └── pkg_packager.py     # Solaris PKG packaging
├── config/                      # Configuration files
│   ├── versions.yaml           # Version definitions
│   ├── platform_configs/       # Platform-specific configs
│   └── build_profiles/         # Build profile definitions
├── scripts/                     # Wrapper scripts
│   ├── build.py                # New main build script
│   └── legacy/                 # Legacy script compatibility
└── docs/                       # Comprehensive documentation
```

## Implementation Strategy

### Phase 1: Framework Foundation

#### 1.1 Core Infrastructure

**Build Manager (`framework/core/build_manager.py`)**
```python
class BuildManager:
    """Main orchestration class for NCPA builds"""
    
    def __init__(self, config_path: str = None):
        self.platform = PlatformDetector.detect()
        self.version_mgr = VersionManager()
        self.logger = Logger()
        
    def build(self, options: BuildOptions) -> BuildResult:
        """Execute complete build process"""
        # 1. Validate environment
        # 2. Install prerequisites 
        # 3. Build executable
        # 4. Package distribution
        # 5. Generate artifacts
        
    def clean(self) -> None:
        """Clean build artifacts"""
        
    def validate_environment(self) -> ValidationResult:
        """Validate build environment"""
```

**Platform Detector (`framework/core/platform_detector.py`)**
```python
class PlatformInfo:
    """Standardized platform information"""
    
    def __init__(self):
        self.os_family: str      # linux, darwin, windows, aix, sunos
        self.distribution: str   # ubuntu, centos, rhel, etc.
        self.version: str        # version number
        self.architecture: str   # x86_64, arm64, etc.
        self.package_manager: str # apt, yum, zypper, brew, etc.

class PlatformDetector:
    @staticmethod
    def detect() -> PlatformInfo:
        """Detect current platform with comprehensive information"""
        # Robust detection logic consolidating current scattered code
```

**Version Manager (`framework/core/version_manager.py`)**
```python
class VersionManager:
    """Centralized version management with YAML configuration"""
    
    def __init__(self, config_file: str = "config/versions.yaml"):
        self.config = self._load_config(config_file)
        
    def get_python_version(self, platform: PlatformInfo) -> str:
        """Get Python version for platform with override support"""
        
    def get_openssl_version(self, platform: PlatformInfo) -> str:
        """Get OpenSSL version with platform-specific logic"""
        
    def get_all_versions(self, platform: PlatformInfo) -> dict:
        """Get all version information for platform"""
```

#### 1.2 Configuration System

**Version Configuration (`config/versions.yaml`)**
```yaml
# NCPA Build Version Configuration
# Centralized version management with platform overrides

default_versions:
  python: "3.13.5"
  openssl: "3.0.17"
  zlib: "1.3.1"

platform_overrides:
  aix:
    python: "3.6.15"    # Legacy compatibility
    openssl: "1.1.1"    # System limitations
    zlib: "1.2.11"
    
  solaris:
    python: "3.9.13"    # System limitations
    openssl: "1.1.1"    # System limitations
    zlib: "1.2.11"
    
  darwin:
    # macOS-specific library versions
    mpdecimal: "4.0.0"
    sqlite3: "3.0"
    liblzma: "5"
    libffi: "8"
    
  windows:
    # Windows-specific configurations
    use_system_python: false

# Environment variable overrides
# MACOS_PYTHON_VERSION, LINUX_OPENSSL_VERSION, etc.
```

#### 1.3 Abstract Platform Class

**Base Platform (`framework/platforms/base_platform.py`)**
```python
from abc import ABC, abstractmethod

class BasePlatform(ABC):
    """Abstract base class for platform-specific implementations"""
    
    def __init__(self, platform_info: PlatformInfo, version_mgr: VersionManager):
        self.platform_info = platform_info
        self.version_mgr = version_mgr
        self.logger = Logger()
        
    @abstractmethod
    def install_prerequisites(self) -> InstallResult:
        """Install platform-specific prerequisites"""
        pass
        
    @abstractmethod
    def setup_python_environment(self) -> SetupResult:
        """Set up Python build environment"""
        pass
        
    @abstractmethod
    def post_build_fixes(self, build_dir: Path) -> FixResult:
        """Apply platform-specific post-build fixes"""
        pass
        
    @abstractmethod
    def create_package(self, build_dir: Path) -> PackageResult:
        """Create platform-specific package"""
        pass
        
    def validate_environment(self) -> ValidationResult:
        """Standard environment validation"""
        # Common validation logic
        
    def clean_build_directory(self, build_dir: Path) -> None:
        """Standard cleanup with platform hooks"""
```

### Phase 2: Platform-Specific Implementations

#### 2.1 Linux Platform Implementation

**Linux Platform (`framework/platforms/linux_platform.py`)**
```python
class LinuxPlatform(BasePlatform):
    """Linux platform implementation with distribution support"""
    
    def __init__(self, platform_info: PlatformInfo, version_mgr: VersionManager):
        super().__init__(platform_info, version_mgr)
        self.package_installer = self._get_package_installer()
        
    def install_prerequisites(self) -> InstallResult:
        """Install Linux prerequisites based on distribution"""
        try:
            # Distribution-specific package installation
            if self.platform_info.distribution in ['ubuntu', 'debian']:
                return self._install_debian_packages()
            elif self.platform_info.distribution in ['centos', 'rhel', 'fedora']:
                return self._install_rpm_packages()
            elif self.platform_info.distribution in ['opensuse', 'sles']:
                return self._install_suse_packages()
        except Exception as e:
            return InstallResult.error(str(e))
            
    def _install_debian_packages(self) -> InstallResult:
        """Install packages on Debian/Ubuntu systems"""
        packages = [
            'gcc', 'g++', 'make', 'libffi-dev', 
            'sqlite3', 'libsqlite3-dev', 'wget', 'rpm'
        ]
        
        # Handle SSL conditionally
        ssl_version = self._get_system_ssl_version()
        if ssl_version.major < 3:
            # Will build from source
            self.logger.info("System OpenSSL < 3.0, will build from source")
        else:
            packages.extend(['zlib1g-dev', 'openssl', 'libssl-dev'])
            
        return self.package_installer.install(packages)
        
    def setup_python_environment(self) -> SetupResult:
        """Set up Python environment with source compilation if needed"""
        python_version = self.version_mgr.get_python_version(self.platform_info)
        
        # Check if system Python is adequate
        system_python = self._check_system_python(python_version)
        if system_python.adequate:
            return self._setup_system_python(system_python)
        else:
            return self._compile_python_from_source(python_version)
            
    def post_build_fixes(self, build_dir: Path) -> FixResult:
        """Apply Linux-specific post-build fixes"""
        fixes = []
        
        # Remove libffi duplicates (preserve existing workaround)
        libffi_fix = self._remove_libffi_duplicates(build_dir)
        fixes.append(libffi_fix)
        
        # Set permissions
        permission_fix = self._set_linux_permissions(build_dir)
        fixes.append(permission_fix)
        
        return FixResult.combine(fixes)
        
    def _remove_libffi_duplicates(self, build_dir: Path) -> FixResult:
        """
        Remove libffi duplicate copies - critical workaround
        
        This is a known issue with cx_Freeze where duplicate libffi
        libraries cause linking problems. The exact version varies.
        """
        try:
            libffi_pattern = build_dir / "ncpa" / "libffi-*.so.*"
            removed_files = list(libffi_pattern.parent.glob(libffi_pattern.name))
            
            for libffi_file in removed_files:
                libffi_file.unlink()
                self.logger.info(f"Removed duplicate libffi: {libffi_file}")
                
            return FixResult.success(f"Removed {len(removed_files)} libffi duplicates")
        except Exception as e:
            return FixResult.error(f"Failed to remove libffi duplicates: {e}")
```

#### 2.2 macOS Platform Implementation

**macOS Platform (`framework/platforms/macos_platform.py`)**
```python
class MacOSPlatform(BasePlatform):
    """macOS platform implementation with Homebrew integration"""
    
    def __init__(self, platform_info: PlatformInfo, version_mgr: VersionManager):
        super().__init__(platform_info, version_mgr)
        self.homebrew = HomebrewManager()
        self.dylib_fixer = DylibPathFixer()
        
    def install_prerequisites(self) -> InstallResult:
        """Install macOS prerequisites via Homebrew"""
        results = []
        
        # Install Xcode command line tools
        xcode_result = self._install_xcode_tools()
        results.append(xcode_result)
        
        # Install Homebrew if needed
        brew_result = self.homebrew.ensure_installed()
        results.append(brew_result)
        
        # Install required packages
        packages = ['pkg-config', 'xz', 'gdbm', 'mpdecimal']
        if self._is_macos_10():
            packages.append('libffi')  # Only needed on macOS 10.x
            
        package_result = self.homebrew.install_packages(packages)
        results.append(package_result)
        
        return InstallResult.combine(results)
        
    def post_build_fixes(self, build_dir: Path) -> FixResult:
        """Apply macOS-specific post-build fixes"""
        fixes = []
        
        # Critical: Fix dylib paths for relocatable libraries
        dylib_fix = self._fix_dylib_paths(build_dir)
        fixes.append(dylib_fix)
        
        # Remove libffi duplicates 
        libffi_fix = self._remove_libffi_duplicates(build_dir)
        fixes.append(libffi_fix)
        
        # Set macOS permissions
        permission_fix = self._set_macos_permissions(build_dir)
        fixes.append(permission_fix)
        
        return FixResult.combine(fixes)
        
    def _fix_dylib_paths(self, build_dir: Path) -> FixResult:
        """
        Fix dynamic library paths for macOS relocatable packaging
        
        This is critical for macOS distribution - converts absolute
        Homebrew paths to @loader_path relative paths so the app
        can run on systems without Homebrew.
        """
        try:
            python_version = self.version_mgr.get_python_version(self.platform_info)
            py_suffix = python_version.replace(".", "")[:3]  # e.g., "313" for 3.13
            
            # Define library path mappings (preserve existing logic)
            lib_mappings = self._generate_lib_mappings(py_suffix)
            
            fixes_applied = 0
            for old_path, new_path, target_file in lib_mappings:
                target_path = build_dir / target_file
                if target_path.exists():
                    result = self.dylib_fixer.change_install_name(
                        target_path, old_path, new_path
                    )
                    if result.success:
                        fixes_applied += 1
                        self.logger.info(f"Fixed dylib path in {target_file}")
                    else:
                        self.logger.warning(f"Failed to fix {target_file}: {result.error}")
                        
            return FixResult.success(f"Applied {fixes_applied} dylib path fixes")
            
        except Exception as e:
            return FixResult.error(f"Dylib path fixing failed: {e}")
            
    def _generate_lib_mappings(self, py_suffix: str) -> List[Tuple[str, str, str]]:
        """Generate library path mappings based on current versions"""
        versions = self.version_mgr.get_all_versions(self.platform_info)
        
        mappings = [
            # OpenSSL libraries
            (f"/usr/local/Cellar/openssl@{versions['openssl_major']}/{versions['openssl']}/lib/libcrypto.{versions['libcrypto']}.dylib",
             f"@loader_path/libcrypto.{versions['libcrypto']}.dylib",
             f"ncpa/lib/libssl.{versions['libssl']}.dylib"),
             
            # SSL library for Python SSL module
            (f"/usr/local/opt/openssl@{versions['openssl_major']}/lib/libssl.{versions['libssl']}.dylib",
             f"@loader_path/libssl.{versions['libssl']}.dylib",
             f"ncpa/lib/_ssl.cpython-{py_suffix}-darwin.so"),
             
            # Add more mappings based on existing logic...
        ]
        
        # Conditional mappings for macOS 10.x
        if self._is_macos_10():
            mappings.append(
                (f"/usr/local/opt/libffi/lib/libffi.{versions['libffi']}.dylib",
                 f"@loader_path/libffi.{versions['libffi']}.dylib",
                 f"ncpa/lib/_ctypes.cpython-{py_suffix}-darwin.so")
            )
            
        return mappings
```

### Phase 3: Unified Build Script

#### 3.1 New Main Build Script

**Main Build Script (`scripts/build.py`)**
```python
#!/usr/bin/env python3
"""
NCPA Build System - Next Generation

Modern Python-based build system for NCPA that preserves all
platform-specific nuances while providing better maintainability.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent / "framework"))

from core.build_manager import BuildManager
from core.platform_detector import PlatformDetector
from core.logger import Logger, LogLevel

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Build NCPA for multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full build for current platform
  %(prog)s --clean                  # Clean build directory
  %(prog)s --build-only             # Build without packaging
  %(prog)s --package-only           # Package existing build
  %(prog)s --skip-setup             # Skip prerequisite installation
  %(prog)s --profile release        # Use release build profile
  %(prog)s --log-level debug        # Verbose debugging output

Supported Platforms:
  Linux:   CentOS, RHEL, Ubuntu, Debian, OpenSUSE, SLES
  macOS:   10.15+ (Homebrew required)
  Windows: Windows 10+ (PowerShell/batch compatibility)
  AIX:     AIX 7.x
  Solaris: Solaris 11
        """
    )
    
    # Build actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--build-only", "-b",
        action="store_true",
        help="Build executables only, skip packaging"
    )
    action_group.add_argument(
        "--package-only", "-p", 
        action="store_true",
        help="Package existing build only (requires existing ncpa directory)"
    )
    action_group.add_argument(
        "--clean", "-c",
        action="store_true", 
        help="Clean build directory and exit"
    )
    
    # Setup options
    parser.add_argument(
        "--skip-setup", "-S",
        action="store_true",
        help="Skip prerequisite installation"
    )
    parser.add_argument(
        "--no-interaction", "-n",
        action="store_true",
        help="Run without interactive prompts (auto-confirm)"
    )
    
    # Configuration options
    parser.add_argument(
        "--profile",
        choices=["debug", "release", "ci"],
        default="release",
        help="Build profile to use"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to custom configuration file"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging verbosity"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file (default: build/build.log)"
    )
    
    # Development options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true", 
        help="Validate environment and configuration only"
    )
    
    return parser

def main() -> int:
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging
    log_level = LogLevel[args.log_level.upper()]
    log_file = args.log_file or Path("build/build.log")
    logger = Logger(level=log_level, log_file=log_file)
    
    try:
        # Detect platform
        platform_info = PlatformDetector.detect()
        logger.info(f"Detected platform: {platform_info}")
        
        # Initialize build manager
        build_manager = BuildManager(
            config_file=args.config,
            platform_info=platform_info,
            logger=logger
        )
        
        # Handle actions
        if args.clean:
            logger.info("Cleaning build directory...")
            build_manager.clean()
            logger.info("Build directory cleaned successfully")
            return 0
            
        if args.validate_only:
            logger.info("Validating build environment...")
            result = build_manager.validate_environment()
            if result.success:
                logger.info("Environment validation passed")
                return 0
            else:
                logger.error(f"Environment validation failed: {result.error}")
                return 1
        
        # Create build options
        build_options = BuildOptions(
            build_only=args.build_only,
            package_only=args.package_only,
            skip_setup=args.skip_setup,
            no_interaction=args.no_interaction,
            profile=args.profile,
            dry_run=args.dry_run
        )
        
        # Execute build
        logger.info("Starting NCPA build process...")
        result = build_manager.build(build_options)
        
        if result.success:
            logger.info("Build completed successfully")
            if result.artifacts:
                logger.info("Generated artifacts:")
                for artifact in result.artifacts:
                    logger.info(f"  {artifact}")
            return 0
        else:
            logger.error(f"Build failed: {result.error}")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("Build interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if log_level == LogLevel.DEBUG:
            import traceback
            logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Phase 4: Advanced Features

#### 4.1 Build Profiles

**Build Profiles (`config/build_profiles/release.yaml`)**
```yaml
# Release build profile
name: "release"
description: "Production release build"

build_options:
  optimize: true
  debug_symbols: false
  strip_binaries: true
  
validation:
  strict_dependencies: true
  require_git_clean: false
  check_code_signing: false  # Future feature

packaging:
  include_debug_info: false
  compress_packages: true
  generate_checksums: true
  
platform_overrides:
  darwin:
    code_signing:
      enabled: false  # Future: true for distribution
      identity: "Developer ID Application"
      
  windows:
    authenticode:
      enabled: false  # Future: true for distribution
```

#### 4.2 Enhanced Error Handling

**Error Handling System**
```python
class BuildError(Exception):
    """Base exception for build errors"""
    
class PlatformNotSupportedError(BuildError):
    """Raised when platform is not supported"""
    
class DependencyError(BuildError):
    """Raised when dependencies are missing or incompatible"""
    
class BuildResult:
    """Standardized build result"""
    
    def __init__(self, success: bool, error: Optional[str] = None, 
                 artifacts: Optional[List[Path]] = None):
        self.success = success
        self.error = error
        self.artifacts = artifacts or []
        self.duration: Optional[float] = None
        self.logs: List[str] = []
```

#### 4.3 Testing Framework

**Build Testing (`framework/testing/build_test.py`)**
```python
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

class TestLinuxPlatform(unittest.TestCase):
    """Test Linux platform implementation"""
    
    def setUp(self):
        self.platform_info = Mock()
        self.platform_info.os_family = "linux"
        self.platform_info.distribution = "ubuntu"
        self.version_mgr = Mock()
        
    def test_ubuntu_package_installation(self):
        """Test Ubuntu package installation"""
        # Test implementation
        
    def test_libffi_duplicate_removal(self):
        """Test libffi duplicate removal"""
        # Test implementation
```

## Migration Strategy

### Phase 1: Foundation (Weeks 1-2)
1. Implement core framework classes
2. Create configuration system
3. Implement platform detection
4. Set up logging system

### Phase 2: Platform Implementation (Weeks 3-6)
1. Implement Linux platform (highest priority)
2. Implement macOS platform 
3. Implement Windows platform
4. Implement AIX and Solaris platforms

### Phase 3: Integration and Testing (Weeks 7-8)
1. Create new build script
2. Implement legacy compatibility
3. Comprehensive testing across platforms
4. Documentation and examples

### Phase 4: Advanced Features (Weeks 9-10)
1. Build profiles and advanced configuration
2. Enhanced error handling and recovery
3. Performance optimizations
4. CI/CD integration improvements

## Backward Compatibility Strategy

### Legacy Script Wrapper
```bash
#!/bin/bash
# build/legacy/build.sh - Legacy wrapper for new build system

echo "WARNING: Using legacy build.sh wrapper"
echo "Consider migrating to: python scripts/build.py"
echo ""

# Convert legacy arguments to new format
PYTHON_ARGS=""

for arg in "$@"; do
    case "$arg" in
        -h|--help)          PYTHON_ARGS="$PYTHON_ARGS --help" ;;
        -c|--clean)         PYTHON_ARGS="$PYTHON_ARGS --clean" ;;
        -S|--skip-setup)    PYTHON_ARGS="$PYTHON_ARGS --skip-setup" ;;
        -p|--package-only)  PYTHON_ARGS="$PYTHON_ARGS --package-only" ;;
        -b|--build-only)    PYTHON_ARGS="$PYTHON_ARGS --build-only" ;;
        -n|--no-interaction) PYTHON_ARGS="$PYTHON_ARGS --no-interaction" ;;
        *) echo "Warning: Unknown legacy argument: $arg" ;;
    esac
done

# Execute new build system
exec python3 "$(dirname "$0")/../scripts/build.py" $PYTHON_ARGS
```

## Benefits of the New System

### For Developers
1. **Unified Interface**: Single entry point for all platforms
2. **Better Debugging**: Comprehensive logging and error reporting
3. **Faster Development**: Modular design enables focused testing
4. **Documentation**: Self-documenting code with type hints

### For Maintainers  
1. **Reduced Duplication**: Shared code for common operations
2. **Easier Updates**: Centralized version and configuration management
3. **Better Testing**: Unit tests for platform-specific logic
4. **Clearer Separation**: Platform-specific code isolated

### for Operations
1. **Consistent Behavior**: Standardized error handling and reporting
2. **Better Logging**: Structured logs for troubleshooting
3. **Configuration Management**: YAML-based configuration
4. **Build Profiles**: Environment-specific optimizations

### For Security
1. **Input Validation**: Proper argument and configuration validation
2. **Error Boundaries**: Contained failure modes
3. **Audit Trail**: Comprehensive build logging
4. **Dependency Tracking**: Clear dependency documentation

## Implementation Considerations

### Preserving Critical Workarounds
1. **libffi Duplicate Removal**: Maintain exact logic with better documentation
2. **macOS Dylib Fixing**: Preserve install_name_tool operations
3. **SSL Version Detection**: Keep conditional compilation logic
4. **Platform-Specific Paths**: Maintain all hardcoded paths that work

### Performance Optimization
1. **Parallel Operations**: Where safe, parallelize independent operations
2. **Caching**: Cache platform detection and validation results
3. **Incremental Builds**: Skip unchanged components when possible
4. **Resource Management**: Better cleanup of temporary files

### Documentation Strategy
1. **API Documentation**: Comprehensive docstrings for all classes
2. **Platform Guides**: Specific guides for each platform's quirks
3. **Migration Guide**: Step-by-step migration from old system
4. **Troubleshooting**: Common issues and solutions

This improved build system will maintain all the critical functionality of the current system while providing a much more maintainable and extensible foundation for future development.
