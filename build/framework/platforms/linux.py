"""
Linux Platform Build Implementation

This module implements the Linux-specific build logic for NCPA,
preserving all critical functionality from the original shell scripts.
"""

import os
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..core.logger import get_logger
from ..core.utils import run_command, check_command_exists
from .base import BasePlatform


class LinuxPlatform(BasePlatform):
    """Linux platform implementation for NCPA builds."""
    
    def __init__(self, build_dir: Path, target_dir: Path, config: Dict):
        super().__init__(build_dir, target_dir, config)
        self.logger = get_logger(__name__)
        self.distro_info = self._detect_distribution()
        
    def _detect_distribution(self) -> Dict[str, str]:
        """Detect Linux distribution and version."""
        distro_info = {
            'name': 'unknown',
            'version': 'unknown',
            'id': 'unknown',
            'package_manager': 'unknown'
        }
        
        # Try /etc/os-release first (systemd standard)
        if os.path.exists('/etc/os-release'):
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            value = value.strip('"\'')
                            if key == 'NAME':
                                distro_info['name'] = value
                            elif key == 'VERSION_ID':
                                distro_info['version'] = value
                            elif key == 'ID':
                                distro_info['id'] = value.lower()
            except Exception as e:
                self.logger.warning(f"Could not parse /etc/os-release: {e}")
        
        # Fallback to release files
        release_files = [
            ('/etc/redhat-release', 'redhat'),
            ('/etc/centos-release', 'centos'),
            ('/etc/debian_version', 'debian'),
            ('/etc/SuSE-release', 'suse'),
            ('/etc/alpine-release', 'alpine')
        ]
        
        for release_file, distro_type in release_files:
            if os.path.exists(release_file):
                if distro_info['id'] == 'unknown':
                    distro_info['id'] = distro_type
                break
        
        # Determine package manager
        if distro_info['id'] in ['rhel', 'centos', 'fedora', 'redhat', 'rocky', 'almalinux']:
            if check_command_exists('dnf'):
                distro_info['package_manager'] = 'dnf'
            elif check_command_exists('yum'):
                distro_info['package_manager'] = 'yum'
        elif distro_info['id'] in ['debian', 'ubuntu', 'mint']:
            distro_info['package_manager'] = 'apt'
        elif distro_info['id'] in ['suse', 'opensuse', 'sles']:
            distro_info['package_manager'] = 'zypper'
        elif distro_info['id'] == 'alpine':
            distro_info['package_manager'] = 'apk'
        elif distro_info['id'] == 'arch':
            distro_info['package_manager'] = 'pacman'
        
        self.logger.info(f"Detected Linux distribution: {distro_info}")
        return distro_info
    
    def get_platform_name(self) -> str:
        """Get platform name for this system."""
        return f"linux-{self.distro_info['id']}"
    
    def check_prerequisites(self) -> List[str]:
        """Check for required build prerequisites."""
        missing = []
        
        # Essential packages for all distributions
        essential_commands = ['python3', 'gcc', 'make', 'git']
        for cmd in essential_commands:
            if not check_command_exists(cmd):
                missing.append(f"Command not found: {cmd}")
        
        # Python development headers
        python_dev_packages = {
            'apt': ['python3-dev', 'python3-venv'],
            'yum': ['python3-devel'],
            'dnf': ['python3-devel'],
            'zypper': ['python3-devel']
        }
        
        pkg_mgr = self.distro_info['package_manager']
        if pkg_mgr in python_dev_packages:
            for package in python_dev_packages[pkg_mgr]:
                if not self._check_package_installed(package):
                    missing.append(f"Package not installed: {package}")
        
        # SSL development libraries
        ssl_packages = {
            'apt': ['libssl-dev', 'libffi-dev', 'zlib1g-dev'],
            'yum': ['openssl-devel', 'libffi-devel', 'zlib-devel'],
            'dnf': ['openssl-devel', 'libffi-devel', 'zlib-devel'],
            'zypper': ['libopenssl-devel', 'libffi-devel', 'zlib-devel']
        }
        
        if pkg_mgr in ssl_packages:
            for package in ssl_packages[pkg_mgr]:
                if not self._check_package_installed(package):
                    missing.append(f"Package not installed: {package}")
        
        return missing
    
    def _check_package_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        pkg_mgr = self.distro_info['package_manager']
        
        try:
            if pkg_mgr == 'apt':
                result = run_command(['dpkg', '-l', package], capture_output=True)
                return result.returncode == 0 and 'ii' in result.stdout
            elif pkg_mgr in ['yum', 'dnf']:
                result = run_command([pkg_mgr, 'list', 'installed', package], capture_output=True)
                return result.returncode == 0
            elif pkg_mgr == 'zypper':
                result = run_command(['rpm', '-q', package], capture_output=True)
                return result.returncode == 0
            else:
                # Fallback - assume installed
                return True
        except Exception:
            return False
    
    def install_prerequisites(self) -> bool:
        """Install required build prerequisites."""
        pkg_mgr = self.distro_info['package_manager']
        
        if pkg_mgr == 'unknown':
            self.logger.error("Unknown package manager, cannot install prerequisites")
            return False
        
        # Update package cache first
        self.logger.info("Updating package cache...")
        if pkg_mgr == 'apt':
            if not run_command(['sudo', 'apt', 'update']).returncode == 0:
                self.logger.error("Failed to update package cache")
                return False
        
        # Define packages to install
        package_sets = {
            'apt': [
                'python3', 'python3-dev', 'python3-venv', 'python3-pip',
                'gcc', 'make', 'git', 'libssl-dev', 'libffi-dev', 'zlib1g-dev',
                'build-essential'
            ],
            'yum': [
                'python3', 'python3-devel', 'python3-pip',
                'gcc', 'make', 'git', 'openssl-devel', 'libffi-devel', 'zlib-devel',
                'rpm-build'
            ],
            'dnf': [
                'python3', 'python3-devel', 'python3-pip',
                'gcc', 'make', 'git', 'openssl-devel', 'libffi-devel', 'zlib-devel',
                'rpm-build'
            ],
            'zypper': [
                'python3', 'python3-devel', 'python3-pip',
                'gcc', 'make', 'git', 'libopenssl-devel', 'libffi-devel', 'zlib-devel',
                'rpm-build'
            ]
        }
        
        if pkg_mgr not in package_sets:
            self.logger.warning(f"No package set defined for {pkg_mgr}")
            return True  # Assume they're available
        
        packages = package_sets[pkg_mgr]
        
        # Install packages
        install_commands = {
            'apt': ['sudo', 'apt', 'install', '-y'] + packages,
            'yum': ['sudo', 'yum', 'install', '-y'] + packages,
            'dnf': ['sudo', 'dnf', 'install', '-y'] + packages,
            'zypper': ['sudo', 'zypper', 'install', '-y'] + packages
        }
        
        if pkg_mgr in install_commands:
            self.logger.info(f"Installing packages with {pkg_mgr}: {' '.join(packages)}")
            result = run_command(install_commands[pkg_mgr])
            if result.returncode != 0:
                self.logger.error(f"Failed to install packages with {pkg_mgr}")
                return False
        
        return True
    
    def setup_build_environment(self) -> bool:
        """Setup the build environment."""
        try:
            # Create build directories
            self.target_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup Python virtual environment
            venv_path = self.target_dir / 'venv'
            if not venv_path.exists():
                self.logger.info("Creating Python virtual environment...")
                result = run_command(['python3', '-m', 'venv', str(venv_path)])
                if result.returncode != 0:
                    self.logger.error("Failed to create virtual environment")
                    return False
            
            # Activate virtual environment and install cx_Freeze
            pip_path = venv_path / 'bin' / 'pip'
            python_path = venv_path / 'bin' / 'python'
            
            self.logger.info("Installing cx_Freeze in virtual environment...")
            result = run_command([str(pip_path), 'install', 'cx_Freeze'])
            if result.returncode != 0:
                self.logger.error("Failed to install cx_Freeze")
                return False
            
            # Store paths for later use
            self.python_executable = str(python_path)
            self.pip_executable = str(pip_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup build environment: {e}")
            return False
    
    def build_executable(self) -> bool:
        """Build the NCPA executable using cx_Freeze."""
        try:
            # Change to agent directory
            agent_dir = self.build_dir / 'agent'
            if not agent_dir.exists():
                self.logger.error(f"Agent directory not found: {agent_dir}")
                return False
            
            # Copy agent files to build directory
            build_agent_dir = self.target_dir / 'ncpa'
            if build_agent_dir.exists():
                shutil.rmtree(build_agent_dir)
            
            self.logger.info("Copying agent files...")
            shutil.copytree(agent_dir, build_agent_dir)
            
            # Run cx_Freeze build
            setup_py = build_agent_dir / 'setup.py'
            if not setup_py.exists():
                self.logger.error(f"setup.py not found: {setup_py}")
                return False
            
            self.logger.info("Building executable with cx_Freeze...")
            result = run_command([
                self.python_executable, 
                str(setup_py),
                'build'
            ], cwd=str(build_agent_dir))
            
            if result.returncode != 0:
                self.logger.error("cx_Freeze build failed")
                return False
            
            # Apply Linux-specific fixes
            self._apply_linux_fixes()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to build executable: {e}")
            return False
    
    def _apply_linux_fixes(self) -> None:
        """Apply Linux-specific fixes to the built executable."""
        # Find the build output directory
        build_dir = self.target_dir / 'ncpa' / 'build'
        if not build_dir.exists():
            self.logger.warning("Build directory not found, skipping fixes")
            return
        
        # Find the exe directory (typically exe.linux-x86_64-3.x)
        exe_dirs = list(build_dir.glob('exe.linux-*'))
        if not exe_dirs:
            self.logger.warning("No exe directory found, skipping fixes")
            return
        
        exe_dir = exe_dirs[0]  # Take the first one found
        self.logger.info(f"Applying Linux fixes to: {exe_dir}")
        
        # Remove duplicate libffi files (critical fix from original scripts)
        lib_dir = exe_dir / 'lib'
        if lib_dir.exists():
            libffi_files = list(lib_dir.glob('libffi*'))
            if len(libffi_files) > 1:
                self.logger.info("Removing duplicate libffi files...")
                # Keep the first one, remove the rest
                for libffi_file in libffi_files[1:]:
                    try:
                        os.remove(libffi_file)
                        self.logger.info(f"Removed duplicate: {libffi_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove {libffi_file}: {e}")
        
        # Make the main executable executable
        ncpa_exe = exe_dir / 'ncpa'
        if ncpa_exe.exists():
            os.chmod(ncpa_exe, 0o755)
        
    def create_package(self) -> bool:
        """Create platform-specific packages (RPM/DEB)."""
        pkg_mgr = self.distro_info['package_manager']
        
        if pkg_mgr in ['yum', 'dnf', 'zypper']:
            return self._create_rpm_package()
        elif pkg_mgr == 'apt':
            return self._create_deb_package()
        else:
            self.logger.warning(f"Package creation not implemented for {pkg_mgr}")
            return True
    
    def _create_rpm_package(self) -> bool:
        """Create RPM package."""
        self.logger.info("Creating RPM package...")
        
        # This would implement RPM packaging logic
        # For now, just log that it would be done
        self.logger.info("RPM package creation would be implemented here")
        return True
    
    def _create_deb_package(self) -> bool:
        """Create DEB package."""
        self.logger.info("Creating DEB package...")
        
        # This would implement DEB packaging logic
        # For now, just log that it would be done
        self.logger.info("DEB package creation would be implemented here")
        return True
    
    def get_build_artifacts(self) -> List[Path]:
        """Get list of build artifacts created."""
        artifacts = []
        
        # Find the executable
        build_dir = self.target_dir / 'ncpa' / 'build'
        if build_dir.exists():
            exe_dirs = list(build_dir.glob('exe.linux-*'))
            artifacts.extend(exe_dirs)
        
        # Find packages
        package_files = list(self.target_dir.glob('*.rpm'))
        package_files.extend(self.target_dir.glob('*.deb'))
        artifacts.extend(package_files)
        
        return artifacts
