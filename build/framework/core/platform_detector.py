"""
Platform detection and information gathering for NCPA builds.

Consolidates all the scattered platform detection logic from the original
shell scripts into a single, robust Python implementation.
"""

import os
import platform
import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from .logger import Logger


@dataclass
class PlatformInfo:
    """
    Standardized platform information
    
    Consolidates all platform-specific information needed for builds
    into a single, well-defined structure.
    """
    os_family: str          # linux, darwin, windows, aix, sunos
    distribution: str       # ubuntu, centos, rhel, debian, opensuse, etc.
    version: str           # OS/distribution version
    version_major: str     # Major version number
    architecture: str      # x86_64, arm64, aarch64, etc.
    package_manager: str   # apt, yum, dnf, zypper, brew, pkg, etc.
    
    # Additional metadata
    is_64bit: bool
    python_executable: str
    shell_path: str
    
    def __str__(self) -> str:
        return f"{self.distribution} {self.version} ({self.architecture})"
        
    def __repr__(self) -> str:
        return (f"PlatformInfo(os_family={self.os_family}, "
                f"distribution={self.distribution}, version={self.version}, "
                f"architecture={self.architecture})")


class PlatformDetector:
    """
    Robust platform detection for NCPA builds
    
    Consolidates and improves upon the scattered platform detection
    logic from the original shell scripts.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(name="platform_detector")
    
    @classmethod
    def detect(cls, logger: Optional[Logger] = None) -> PlatformInfo:
        """
        Detect current platform with comprehensive information
        
        Returns:
            PlatformInfo object with complete platform details
        """
        detector = cls(logger)
        return detector._detect_platform()
    
    def _detect_platform(self) -> PlatformInfo:
        """Internal platform detection implementation"""
        
        self.logger.debug("Starting platform detection...")
        
        # Get basic system info
        system = platform.system().lower()
        architecture = platform.machine().lower()
        is_64bit = platform.architecture()[0] == '64bit'
        
        self.logger.debug(f"Basic system info: {system}, {architecture}, 64bit={is_64bit}")
        
        # Normalize architecture names
        if architecture in ['x86_64', 'amd64']:
            architecture = 'x86_64'
        elif architecture in ['aarch64', 'arm64']:
            architecture = 'arm64'
        elif architecture in ['i686', 'i386']:
            architecture = 'i386'
        
        # Platform-specific detection
        if system == 'linux':
            return self._detect_linux(architecture, is_64bit)
        elif system == 'darwin':
            return self._detect_macos(architecture, is_64bit)
        elif system == 'windows':
            return self._detect_windows(architecture, is_64bit)
        elif system == 'aix':
            return self._detect_aix(architecture, is_64bit)
        elif system in ['sunos', 'solaris']:
            return self._detect_solaris(architecture, is_64bit)
        else:
            raise ValueError(f"Unsupported operating system: {system}")
    
    def _detect_linux(self, architecture: str, is_64bit: bool) -> PlatformInfo:
        """Detect Linux distribution and version"""
        
        self.logger.debug("Detecting Linux distribution...")
        
        distribution = "unknown"
        version = "unknown"
        version_major = "unknown"
        package_manager = "unknown"
        
        # Try /etc/os-release first (modern standard)
        os_release_file = Path('/etc/os-release')
        if os_release_file.exists():
            os_release = self._parse_os_release(os_release_file)
            if os_release:
                distribution = os_release.get('ID', '').lower()
                version = os_release.get('VERSION_ID', '')
                version_major = version.split('.')[0] if version else ''
                
                self.logger.debug(f"From os-release: {distribution} {version}")
        
        # Fallback to legacy detection methods
        if distribution == "unknown":
            distribution, version, version_major = self._detect_linux_legacy()
        
        # Determine package manager based on distribution
        package_manager = self._get_linux_package_manager(distribution)
        
        # Find Python executable
        python_executable = self._find_python_executable()
        
        return PlatformInfo(
            os_family='linux',
            distribution=distribution,
            version=version,
            version_major=version_major,
            architecture=architecture,
            package_manager=package_manager,
            is_64bit=is_64bit,
            python_executable=python_executable,
            shell_path='/bin/bash'
        )
    
    def _detect_linux_legacy(self) -> tuple[str, str, str]:
        """Legacy Linux detection for systems without os-release"""
        
        # Check for Red Hat-based systems
        if Path('/etc/redhat-release').exists():
            return self._detect_redhat_based()
        
        # Check for SUSE-based systems
        if Path('/etc/SuSE-release').exists() or Path('/etc/os-release').exists():
            return self._detect_suse_based()
        
        # Check for Debian-based systems
        if Path('/etc/debian_version').exists():
            return self._detect_debian_based()
        
        return "unknown", "unknown", "unknown"
    
    def _detect_redhat_based(self) -> tuple[str, str, str]:
        """Detect Red Hat-based distributions"""
        try:
            with open('/etc/redhat-release', 'r') as f:
                release_text = f.read().strip().lower()
            
            if 'centos' in release_text:
                # Extract CentOS version
                match = re.search(r'centos.*?(\d+)', release_text)
                if match:
                    version = match.group(1)
                    return 'centos', version, version
            elif 'red hat' in release_text or 'rhel' in release_text:
                # Extract RHEL version
                match = re.search(r'(\d+)\.(\d+)', release_text)
                if match:
                    version = f"{match.group(1)}.{match.group(2)}"
                    return 'rhel', version, match.group(1)
            elif 'oracle' in release_text:
                # Extract Oracle Linux version
                match = re.search(r'(\d+)\.(\d+)', release_text)
                if match:
                    version = f"{match.group(1)}.{match.group(2)}"
                    return 'oracle', version, match.group(1)
                    
        except Exception as e:
            self.logger.debug(f"Error reading redhat-release: {e}")
        
        return "rhel", "unknown", "unknown"
    
    def _detect_suse_based(self) -> tuple[str, str, str]:
        """Detect SUSE-based distributions"""
        try:
            # Try modern os-release first
            if Path('/etc/os-release').exists():
                os_release = self._parse_os_release(Path('/etc/os-release'))
                if os_release and 'suse' in os_release.get('ID', '').lower():
                    distro_id = os_release.get('ID', '').lower()
                    if 'opensuse' in distro_id:
                        return 'opensuse', os_release.get('VERSION_ID', ''), ''
                    elif 'sles' in distro_id:
                        version = os_release.get('VERSION_ID', '')
                        return 'sles', version, version.split('.')[0]
            
            # Fallback to legacy SuSE-release
            if Path('/etc/SuSE-release').exists():
                with open('/etc/SuSE-release', 'r') as f:
                    release_text = f.read().strip()
                
                if 'opensuse' in release_text.lower():
                    return 'opensuse', 'unknown', 'unknown'
                elif 'sles' in release_text.lower():
                    match = re.search(r'(\d+)', release_text)
                    if match:
                        version = match.group(1)
                        return 'sles', version, version
                        
        except Exception as e:
            self.logger.debug(f"Error reading SUSE release files: {e}")
        
        return "suse", "unknown", "unknown"
    
    def _detect_debian_based(self) -> tuple[str, str, str]:
        """Detect Debian-based distributions"""
        try:
            # Check if it's Ubuntu
            if Path('/etc/lsb-release').exists():
                lsb_release = self._parse_key_value_file(Path('/etc/lsb-release'))
                if lsb_release.get('DISTRIB_ID', '').lower() == 'ubuntu':
                    version = lsb_release.get('DISTRIB_RELEASE', '')
                    version_major = version.split('.')[0] if version else ''
                    return 'ubuntu', version, version_major
            
            # Check Debian version
            if Path('/etc/debian_version').exists():
                with open('/etc/debian_version', 'r') as f:
                    version = f.read().strip()
                
                # Handle Debian testing/unstable
                if '/' in version:
                    return 'debian', 'testing', 'testing'
                
                # Extract major version for numbered releases
                version_major = version.split('.')[0] if version else ''
                return 'debian', version, version_major
                
        except Exception as e:
            self.logger.debug(f"Error reading Debian release files: {e}")
        
        return "debian", "unknown", "unknown"
    
    def _detect_macos(self, architecture: str, is_64bit: bool) -> PlatformInfo:
        """Detect macOS version and details"""
        
        try:
            # Get macOS version
            version = platform.mac_ver()[0]
            version_major = version.split('.')[0] if version else '10'
            
            # Determine package manager (prefer Homebrew)
            package_manager = 'brew' if self._command_exists('brew') else 'port'
            
            python_executable = self._find_python_executable()
            
            return PlatformInfo(
                os_family='darwin',
                distribution='macos',
                version=version,
                version_major=version_major,
                architecture=architecture,
                package_manager=package_manager,
                is_64bit=is_64bit,
                python_executable=python_executable,
                shell_path='/bin/bash'
            )
            
        except Exception as e:
            self.logger.warning(f"Error detecting macOS version: {e}")
            return PlatformInfo(
                os_family='darwin',
                distribution='macos',
                version='unknown',
                version_major='10',
                architecture=architecture,
                package_manager='brew',
                is_64bit=is_64bit,
                python_executable=self._find_python_executable(),
                shell_path='/bin/bash'
            )
    
    def _detect_windows(self, architecture: str, is_64bit: bool) -> PlatformInfo:
        """Detect Windows version and details"""
        
        try:
            version = platform.release()  # e.g., "10", "11"
            python_executable = self._find_python_executable()
            
            return PlatformInfo(
                os_family='windows',
                distribution='windows',
                version=version,
                version_major=version,
                architecture=architecture,
                package_manager='choco',  # Assume Chocolatey
                is_64bit=is_64bit,
                python_executable=python_executable,
                shell_path='powershell'
            )
            
        except Exception as e:
            self.logger.warning(f"Error detecting Windows version: {e}")
            return PlatformInfo(
                os_family='windows',
                distribution='windows',
                version='10',
                version_major='10',
                architecture=architecture,
                package_manager='choco',
                is_64bit=is_64bit,
                python_executable=self._find_python_executable(),
                shell_path='powershell'
            )
    
    def _detect_aix(self, architecture: str, is_64bit: bool) -> PlatformInfo:
        """Detect AIX version and details"""
        
        try:
            # Get AIX version using oslevel command
            result = subprocess.run(['oslevel'], capture_output=True, text=True, timeout=10)
            version = result.stdout.strip() if result.returncode == 0 else 'unknown'
            version_major = version.split('.')[0] if version != 'unknown' else '7'
            
            return PlatformInfo(
                os_family='aix',
                distribution='aix',
                version=version,
                version_major=version_major,
                architecture=architecture,
                package_manager='installp',
                is_64bit=is_64bit,
                python_executable=self._find_python_executable(),
                shell_path='/bin/bash'
            )
            
        except Exception as e:
            self.logger.warning(f"Error detecting AIX version: {e}")
            return PlatformInfo(
                os_family='aix',
                distribution='aix',
                version='7.2',
                version_major='7',
                architecture=architecture,
                package_manager='installp',
                is_64bit=is_64bit,
                python_executable=self._find_python_executable(),
                shell_path='/bin/bash'
            )
    
    def _detect_solaris(self, architecture: str, is_64bit: bool) -> PlatformInfo:
        """Detect Solaris version and details"""
        
        try:
            # Get Solaris version
            version = platform.release()
            version_major = version.split('.')[0] if version else '11'
            
            return PlatformInfo(
                os_family='sunos',
                distribution='solaris',
                version=version,
                version_major=version_major,
                architecture=architecture,
                package_manager='pkg',
                is_64bit=is_64bit,
                python_executable=self._find_python_executable(),
                shell_path='/bin/bash'
            )
            
        except Exception as e:
            self.logger.warning(f"Error detecting Solaris version: {e}")
            return PlatformInfo(
                os_family='sunos',
                distribution='solaris',
                version='11',
                version_major='11',
                architecture=architecture,
                package_manager='pkg',
                is_64bit=is_64bit,
                python_executable=self._find_python_executable(),
                shell_path='/bin/bash'
            )
    
    def _parse_os_release(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Parse /etc/os-release file"""
        try:
            return self._parse_key_value_file(file_path)
        except Exception as e:
            self.logger.debug(f"Error parsing {file_path}: {e}")
            return None
    
    def _parse_key_value_file(self, file_path: Path) -> Dict[str, str]:
        """Parse shell-style key=value file"""
        data = {}
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes
                        value = value.strip('"\'')
                        data[key] = value
        return data
    
    def _get_linux_package_manager(self, distribution: str) -> str:
        """Determine package manager for Linux distribution"""
        package_managers = {
            'ubuntu': 'apt',
            'debian': 'apt',
            'centos': 'yum',
            'rhel': 'yum',
            'fedora': 'dnf',
            'oracle': 'yum',
            'opensuse': 'zypper',
            'sles': 'zypper',
            'arch': 'pacman',
        }
        
        manager = package_managers.get(distribution, 'unknown')
        
        # For CentOS/RHEL 8+, prefer dnf over yum if available
        if manager == 'yum' and self._command_exists('dnf'):
            return 'dnf'
            
        return manager
    
    def _find_python_executable(self) -> str:
        """Find suitable Python executable"""
        python_candidates = [
            'python3', 'python', 'python3.13', 'python3.12', 
            'python3.11', 'python3.10', 'python3.9', 'python3.8'
        ]
        
        for candidate in python_candidates:
            if self._command_exists(candidate):
                try:
                    # Verify it's Python 3.6+
                    result = subprocess.run(
                        [candidate, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        version_str = result.stdout.strip()
                        major, minor = map(int, version_str.split('.'))
                        if major == 3 and minor >= 6:
                            return candidate
                except Exception:
                    continue
        
        # Fallback to system default
        return 'python3'
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            result = subprocess.run(['which', command], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
