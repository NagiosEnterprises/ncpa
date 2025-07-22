"""
Abstract base class for platform-specific implementations.

All platform implementations must inherit from this class and implement
the abstract methods to ensure consistent behavior across platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Any
from ..core.platform_detector import PlatformInfo
from ..core.version_manager import VersionManager
from ..core.logger import Logger


@dataclass
class InstallResult:
    """Result of prerequisite installation"""
    success: bool
    error: Optional[str] = None
    installed_packages: List[str] = None
    
    def __post_init__(self):
        if self.installed_packages is None:
            self.installed_packages = []
    
    @classmethod
    def success_result(cls, packages: List[str] = None) -> 'InstallResult':
        return cls(success=True, installed_packages=packages or [])
    
    @classmethod
    def error_result(cls, error: str) -> 'InstallResult':
        return cls(success=False, error=error)


@dataclass
class SetupResult:
    """Result of environment setup"""
    success: bool
    error: Optional[str] = None
    python_path: Optional[str] = None
    environment_vars: dict = None
    
    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}
    
    @classmethod
    def success_result(cls, python_path: str = None, env_vars: dict = None) -> 'SetupResult':
        return cls(success=True, python_path=python_path, environment_vars=env_vars or {})
    
    @classmethod
    def error_result(cls, error: str) -> 'SetupResult':
        return cls(success=False, error=error)


@dataclass
class FixResult:
    """Result of post-build fixes"""
    success: bool
    error: Optional[str] = None
    fixes_applied: List[str] = None
    
    def __post_init__(self):
        if self.fixes_applied is None:
            self.fixes_applied = []
    
    @classmethod
    def success_result(cls, fixes: List[str] = None) -> 'FixResult':
        return cls(success=True, fixes_applied=fixes or [])
    
    @classmethod
    def error_result(cls, error: str) -> 'FixResult':
        return cls(success=False, error=error)
    
    @classmethod
    def combine(cls, results: List['FixResult']) -> 'FixResult':
        """Combine multiple fix results"""
        success = all(r.success for r in results)
        errors = [r.error for r in results if r.error]
        fixes = []
        for r in results:
            fixes.extend(r.fixes_applied)
        
        if success:
            return cls.success_result(fixes)
        else:
            return cls.error_result("; ".join(errors))


@dataclass
class PackageResult:
    """Result of package creation"""
    success: bool
    error: Optional[str] = None
    artifacts: List[Path] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
    
    @classmethod
    def success_result(cls, artifacts: List[Path] = None) -> 'PackageResult':
        return cls(success=True, artifacts=artifacts or [])
    
    @classmethod
    def error_result(cls, error: str) -> 'PackageResult':
        return cls(success=False, error=error)


@dataclass
class ValidationResult:
    """Result of environment validation"""
    success: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        
        # Update success based on errors
        self.success = len(self.errors) == 0
    
    @classmethod
    def success_result(cls, warnings: List[str] = None) -> 'ValidationResult':
        return cls(success=True, warnings=warnings or [])
    
    @classmethod
    def error_result(cls, errors: List[str], warnings: List[str] = None) -> 'ValidationResult':
        return cls(success=False, errors=errors, warnings=warnings or [])


class BasePlatform(ABC):
    """
    Abstract base class for platform-specific implementations
    
    All platform implementations must inherit from this class and implement
    the abstract methods. This ensures consistent interfaces while allowing
    platform-specific customization.
    """
    
    def __init__(self, platform_info: PlatformInfo, version_mgr: VersionManager, logger: Logger):
        """
        Initialize platform implementation
        
        Args:
            platform_info: Detected platform information
            version_mgr: Version management instance  
            logger: Logger instance
        """
        self.platform_info = platform_info
        self.version_mgr = version_mgr
        self.logger = logger.create_child(self.__class__.__name__.lower())
        
        # Get all versions for this platform
        self.versions = version_mgr.get_all_versions(platform_info)
        
        self.logger.debug(f"Initialized {self.__class__.__name__} for {platform_info}")
    
    @abstractmethod
    def install_prerequisites(self, options: Any = None) -> InstallResult:
        """
        Install platform-specific prerequisites
        
        This method should install all necessary system packages,
        development tools, and dependencies required for building.
        
        Args:
            options: Build options that may affect installation
            
        Returns:
            InstallResult with installation status
        """
        pass
    
    @abstractmethod
    def setup_python_environment(self) -> SetupResult:
        """
        Set up Python build environment
        
        This method should ensure Python is available and properly
        configured for the build process. May involve compiling
        Python from source on some platforms.
        
        Returns:
            SetupResult with setup status
        """
        pass
    
    @abstractmethod
    def post_build_fixes(self, build_dir: Path) -> FixResult:
        """
        Apply platform-specific post-build fixes
        
        This is where critical platform-specific workarounds are applied,
        such as dynamic library path fixes, permission setting, etc.
        
        Args:
            build_dir: Path to the built application directory
            
        Returns:
            FixResult with fix status
        """
        pass
    
    @abstractmethod
    def create_package(self, build_dir: Path) -> PackageResult:
        """
        Create platform-specific package
        
        This method should create the final distribution package
        for the platform (RPM, DEB, DMG, PKG, etc.).
        
        Args:
            build_dir: Path to the built application directory
            
        Returns:
            PackageResult with package creation status
        """
        pass
    
    def validate_environment(self) -> ValidationResult:
        """
        Standard environment validation with platform hooks
        
        Subclasses can override this method to add platform-specific
        validation while still using the base validation.
        
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        try:
            # Validate Python version
            python_version = self.versions.get('python', '')
            if not python_version:
                errors.append("Python version not configured")
            else:
                # Basic version format validation
                try:
                    parts = python_version.split('.')
                    if len(parts) != 3:
                        errors.append(f"Invalid Python version format: {python_version}")
                    else:
                        major, minor, patch = map(int, parts)
                        if major != 3 or minor < 6:
                            errors.append(f"Python 3.6+ required, configured: {python_version}")
                except ValueError:
                    errors.append(f"Invalid Python version format: {python_version}")
            
            # Validate OpenSSL version
            openssl_version = self.versions.get('openssl', '')
            if not openssl_version:
                warnings.append("OpenSSL version not configured")
            
            # Platform-specific validation hook
            platform_validation = self._validate_platform_specific()
            errors.extend(platform_validation.get('errors', []))
            warnings.extend(platform_validation.get('warnings', []))
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        if errors:
            return ValidationResult.error_result(errors, warnings)
        else:
            return ValidationResult.success_result(warnings)
    
    def _validate_platform_specific(self) -> dict:
        """
        Platform-specific validation hook
        
        Subclasses can override this method to add custom validation.
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        return {'errors': [], 'warnings': []}
    
    def clean_build_directory(self, build_dir: Path) -> None:
        """
        Standard cleanup with platform hooks
        
        Args:
            build_dir: Build directory to clean
        """
        try:
            if build_dir.exists():
                import shutil
                shutil.rmtree(build_dir)
                self.logger.debug(f"Cleaned build directory: {build_dir}")
        except Exception as e:
            self.logger.warning(f"Error cleaning build directory: {e}")
    
    def get_build_environment(self) -> dict:
        """
        Get environment variables for build process
        
        Returns:
            Dictionary of environment variables
        """
        env = {}
        
        # Add version information
        env['NCPA_PYTHON_VERSION'] = self.versions.get('python', '')
        env['NCPA_OPENSSL_VERSION'] = self.versions.get('openssl', '')
        env['NCPA_ZLIB_VERSION'] = self.versions.get('zlib', '')
        
        # Add platform information
        env['NCPA_PLATFORM'] = self.platform_info.os_family
        env['NCPA_DISTRIBUTION'] = self.platform_info.distribution
        env['NCPA_ARCHITECTURE'] = self.platform_info.architecture
        
        return env
    
    def log_platform_info(self):
        """Log platform information for debugging"""
        self.logger.info(f"Platform: {self.platform_info}")
        self.logger.info(f"Package Manager: {self.platform_info.package_manager}")
        self.logger.info(f"Python Executable: {self.platform_info.python_executable}")
        
        self.logger.debug("Version Configuration:")
        for component, version in self.versions.items():
            self.logger.debug(f"  {component}: {version}")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.platform_info})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(platform={self.platform_info.os_family}, "
                f"distribution={self.platform_info.distribution})")
