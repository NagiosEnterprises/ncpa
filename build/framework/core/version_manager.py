"""
Centralized version management for NCPA builds.

Replaces the scattered version configuration across multiple shell scripts
with a single, comprehensive version management system.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .platform_detector import PlatformInfo
from .logger import Logger

# Try to import yaml, fall back to json if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False


class VersionManager:
    """
    Centralized version management with YAML configuration
    
    Manages all dependency versions across platforms with support for
    environment variable overrides and platform-specific defaults.
    """
    
    def __init__(self, config_file: Optional[Path] = None, logger: Optional[Logger] = None):
        """
        Initialize version manager
        
        Args:
            config_file: Path to version configuration file
            logger: Logger instance
        """
        self.logger = logger or Logger(name="version_manager")
        
        # Default config file location
        if config_file is None:
            config_file = Path(__file__).parent.parent.parent / "config" / "versions.yaml"
        
        self.config_file = config_file
        self.config = self._load_config()
        
        self.logger.debug(f"Loaded version configuration from {self.config_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load version configuration from YAML file"""
        try:
            if not self.config_file.exists():
                self.logger.warning(f"Version config file not found: {self.config_file}")
                self.logger.info("Using default version configuration")
                return self._get_default_config()
            
            with open(self.config_file, 'r') as f:
                if HAS_YAML and self.config_file.suffix in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    # Fallback to JSON or manual parsing for YAML-like format
                    content = f.read()
                    config = self._parse_yaml_like(content)
                
            # Validate configuration structure
            if not isinstance(config, dict):
                raise ValueError("Configuration must be a dictionary")
                
            required_keys = ['default_versions', 'platform_overrides']
            for key in required_keys:
                if key not in config:
                    config[key] = {}
                    
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading version configuration: {e}")
            self.logger.info("Falling back to default configuration")
            return self._get_default_config()
    
    def _parse_yaml_like(self, content: str) -> Dict[str, Any]:
        """Simple YAML-like parser for basic configuration"""
        result = {}
        current_section = None
        current_dict = result
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.endswith(':') and not line.startswith(' '):
                # Top-level section
                section_name = line[:-1]
                current_section = {}
                result[section_name] = current_section
                current_dict = current_section
            elif line.endswith(':') and line.startswith(' '):
                # Subsection
                subsection_name = line.strip()[:-1]
                subsection = {}
                current_section[subsection_name] = subsection
                current_dict = subsection
            elif ':' in line and (line.startswith(' ') or line.startswith('  ')):
                # Key-value pair
                key, value = line.strip().split(':', 1)
                value = value.strip().strip('"\'')
                current_dict[key.strip()] = value
        
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config file is not available"""
        return {
            'default_versions': {
                'python': '3.13.5',
                'openssl': '3.0.17',
                'zlib': '1.3.1'
            },
            'platform_overrides': {
                'aix': {
                    'python': '3.6.15',
                    'openssl': '1.1.1',
                    'zlib': '1.2.11',
                    'openssl_major': '1'
                },
                'sunos': {
                    'python': '3.9.13',
                    'openssl': '1.1.1',
                    'zlib': '1.2.11',
                    'openssl_major': '1'
                },
                'darwin': {
                    'mpdecimal': '4.0.0',
                    'sqlite3': '3.0',
                    'liblzma': '5',
                    'libffi': '8',
                    'openssl_major': '3'
                },
                'windows': {
                    'use_system_python': False,
                    'openssl_major': '3'
                }
            }
        }
    
    def get_python_version(self, platform: PlatformInfo) -> str:
        """
        Get Python version for platform with override support
        
        Args:
            platform: Platform information
            
        Returns:
            Python version string (e.g., '3.13.5')
        """
        return self._get_version('python', platform)
    
    def get_openssl_version(self, platform: PlatformInfo) -> str:
        """
        Get OpenSSL version with platform-specific logic
        
        Args:
            platform: Platform information
            
        Returns:
            OpenSSL version string (e.g., '3.0.17')
        """
        return self._get_version('openssl', platform)
    
    def get_zlib_version(self, platform: PlatformInfo) -> str:
        """
        Get zlib version for platform
        
        Args:
            platform: Platform information
            
        Returns:
            zlib version string (e.g., '1.3.1')
        """
        return self._get_version('zlib', platform)
    
    def get_openssl_major(self, platform: PlatformInfo) -> str:
        """
        Get OpenSSL major version for platform
        
        Args:
            platform: Platform information
            
        Returns:
            OpenSSL major version (e.g., '3' or '1')
        """
        # Default based on OpenSSL version
        openssl_version = self.get_openssl_version(platform)
        default_major = openssl_version.split('.')[0]
        
        return self._get_version('openssl_major', platform, default_major)
    
    def get_all_versions(self, platform: PlatformInfo) -> Dict[str, str]:
        """
        Get all version information for platform
        
        Args:
            platform: Platform information
            
        Returns:
            Dictionary containing all versions for the platform
        """
        versions = {
            'python': self.get_python_version(platform),
            'openssl': self.get_openssl_version(platform),
            'zlib': self.get_zlib_version(platform),
            'openssl_major': self.get_openssl_major(platform)
        }
        
        # Add platform-specific versions
        platform_overrides = self.config.get('platform_overrides', {})
        platform_config = platform_overrides.get(platform.os_family, {})
        
        # Add macOS-specific library versions
        if platform.os_family == 'darwin':
            macos_versions = {
                'mpdecimal': self._get_version('mpdecimal', platform, '4.0.0'),
                'sqlite3': self._get_version('sqlite3', platform, '3.0'),
                'liblzma': self._get_version('liblzma', platform, '5'),
                'libffi': self._get_version('libffi', platform, '8')
            }
            versions.update(macos_versions)
            
            # Derive OpenSSL library versions from major version
            openssl_major = versions['openssl_major']
            if openssl_major == '3':
                versions['libssl'] = '3'
                versions['libcrypto'] = '3'
            else:
                versions['libssl'] = '1.1'
                versions['libcrypto'] = '1.1'
        
        # Add any additional platform-specific versions from config
        for key, value in platform_config.items():
            if key not in versions:
                versions[key] = str(value)
        
        return versions
    
    def _get_version(self, component: str, platform: PlatformInfo, 
                    default: Optional[str] = None) -> str:
        """
        Get version for a component with environment override support
        
        Args:
            component: Component name (e.g., 'python', 'openssl')
            platform: Platform information  
            default: Default value if not found
            
        Returns:
            Version string
        """
        # Check environment variable override first
        env_var = self._get_env_var_name(component, platform)
        env_value = os.environ.get(env_var)
        if env_value:
            self.logger.debug(f"Using environment override {env_var}={env_value}")
            return env_value
        
        # Check platform-specific override
        platform_overrides = self.config.get('platform_overrides', {})
        platform_config = platform_overrides.get(platform.os_family, {})
        if component in platform_config:
            value = str(platform_config[component])
            self.logger.debug(f"Using platform override for {platform.os_family}: {component}={value}")
            return value
        
        # Check default versions
        default_versions = self.config.get('default_versions', {})
        if component in default_versions:
            value = str(default_versions[component])
            self.logger.debug(f"Using default version: {component}={value}")
            return value
        
        # Use provided default
        if default is not None:
            self.logger.debug(f"Using fallback default: {component}={default}")
            return default
        
        # Fallback to hardcoded defaults
        hardcoded_defaults = {
            'python': '3.13.5',
            'openssl': '3.0.17',
            'zlib': '1.3.1',
            'openssl_major': '3'
        }
        
        if component in hardcoded_defaults:
            value = hardcoded_defaults[component]
            self.logger.warning(f"Using hardcoded fallback: {component}={value}")
            return value
        
        raise ValueError(f"No version found for component: {component}")
    
    def _get_env_var_name(self, component: str, platform: PlatformInfo) -> str:
        """
        Generate environment variable name for platform and component
        
        Args:
            component: Component name
            platform: Platform information
            
        Returns:
            Environment variable name (e.g., 'MACOS_PYTHON_VERSION')
        """
        platform_name = platform.os_family.upper()
        if platform_name == 'SUNOS':
            platform_name = 'SOLARIS'
        elif platform_name == 'DARWIN':
            platform_name = 'MACOS'
        
        component_name = component.upper().replace('_', '')
        
        return f"{platform_name}_{component_name}_VERSION"
    
    def validate_versions(self, platform: PlatformInfo) -> Dict[str, Any]:
        """
        Validate version configuration for a platform
        
        Args:
            platform: Platform information
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            versions = self.get_all_versions(platform)
            
            # Validate Python version
            python_version = versions['python']
            if not self._is_valid_python_version(python_version):
                results['errors'].append(f"Invalid Python version: {python_version}")
                results['valid'] = False
            
            # Validate OpenSSL version
            openssl_version = versions['openssl']
            if not self._is_valid_openssl_version(openssl_version):
                results['errors'].append(f"Invalid OpenSSL version: {openssl_version}")
                results['valid'] = False
            
            # Platform-specific validations
            if platform.os_family == 'aix':
                python_major_minor = '.'.join(python_version.split('.')[:2])
                if python_major_minor not in ['3.6', '3.7', '3.8']:
                    results['warnings'].append(f"Python {python_version} may not be compatible with AIX")
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation error: {e}")
        
        return results
    
    def _is_valid_python_version(self, version: str) -> bool:
        """Check if Python version string is valid"""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False
            
            major, minor, patch = map(int, parts)
            return major == 3 and minor >= 6
        except ValueError:
            return False
    
    def _is_valid_openssl_version(self, version: str) -> bool:
        """Check if OpenSSL version string is valid"""
        try:
            parts = version.split('.')
            if len(parts) < 2:
                return False
            
            major, minor = map(int, parts[:2])
            return major >= 1 and (major > 1 or minor >= 1)
        except ValueError:
            return False
    
    def get_config_summary(self, platform: PlatformInfo) -> str:
        """
        Get a human-readable summary of version configuration
        
        Args:
            platform: Platform information
            
        Returns:
            Formatted string with version information
        """
        versions = self.get_all_versions(platform)
        
        lines = [
            f"Version Configuration for {platform}:",
            "=" * 50
        ]
        
        # Group versions by category
        core_versions = ['python', 'openssl', 'zlib']
        
        lines.append("\nCore Dependencies:")
        for component in core_versions:
            if component in versions:
                lines.append(f"  {component:12}: {versions[component]}")
        
        # Platform-specific versions
        platform_specific = {k: v for k, v in versions.items() if k not in core_versions}
        if platform_specific:
            lines.append(f"\n{platform.os_family.title()}-specific:")
            for component, version in sorted(platform_specific.items()):
                lines.append(f"  {component:12}: {version}")
        
        return '\n'.join(lines)
