"""
Main orchestration class for NCPA builds.

Coordinates the entire build process across all platforms while maintaining
the critical platform-specific nuances from the original shell scripts.
"""

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from .platform_detector import PlatformDetector, PlatformInfo
from .version_manager import VersionManager
from .logger import Logger, LogLevel
from .utils import SystemUtils, FileUtils, ValidationUtils


@dataclass
class BuildOptions:
    """Build configuration options"""
    build_only: bool = False        # Build without packaging
    package_only: bool = False      # Package existing build
    skip_setup: bool = False        # Skip prerequisite installation
    no_interaction: bool = False    # Non-interactive mode
    profile: str = "release"        # Build profile
    dry_run: bool = False          # Show what would be done
    clean_first: bool = False       # Clean before building


@dataclass
class BuildResult:
    """Result of build operation"""
    success: bool
    error: Optional[str] = None
    artifacts: List[Path] = None
    duration: float = 0.0
    logs: List[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.logs is None:
            self.logs = []


class BuildManager:
    """
    Main orchestration class for NCPA builds
    
    Coordinates the complete build process while preserving all the
    platform-specific logic and workarounds from the original scripts.
    """
    
    def __init__(self, 
                 config_file: Optional[Path] = None,
                 platform_info: Optional[PlatformInfo] = None,
                 logger: Optional[Logger] = None):
        """
        Initialize build manager
        
        Args:
            config_file: Optional custom configuration file
            platform_info: Optional pre-detected platform info
            logger: Logger instance
        """
        # Set up logging first
        self.logger = logger or Logger(name="build_manager")
        
        # Detect platform if not provided
        if platform_info is None:
            self.logger.info("Detecting platform...")
            self.platform_info = PlatformDetector.detect(self.logger)
        else:
            self.platform_info = platform_info
        
        # Initialize managers
        self.version_manager = VersionManager(config_file, self.logger)
        self.system_utils = SystemUtils(self.logger)
        self.file_utils = FileUtils(self.logger)
        self.validation_utils = ValidationUtils(self.logger)
        
        # Set up build paths
        self.build_dir = self._get_build_directory()
        self.agent_dir = self.build_dir.parent / "agent"
        
        # Platform-specific implementation will be loaded later
        self.platform_impl = None
        
        self.logger.info(f"Build manager initialized for {self.platform_info}")
        self.logger.debug(f"Build directory: {self.build_dir}")
        self.logger.debug(f"Agent directory: {self.agent_dir}")
    
    def build(self, options: BuildOptions) -> BuildResult:
        """
        Execute complete build process
        
        Args:
            options: Build configuration options
            
        Returns:
            BuildResult with operation details
        """
        start_time = time.time()
        
        try:
            self.logger.section(f"NCPA Build Process - {self.platform_info}")
            self.logger.info(f"Build options: {options}")
            
            # Initialize platform implementation
            self._load_platform_implementation()
            
            if options.dry_run:
                self.logger.info("DRY RUN MODE - No actual changes will be made")
                return self._dry_run_build(options)
            
            # Phase 1: Validation
            self.logger.step("Validating build environment")
            validation_result = self.validate_environment()
            if not validation_result.success:
                return BuildResult(success=False, error=validation_result.error)
            
            # Phase 2: Clean if requested
            if options.clean_first:
                self.logger.step("Cleaning build directory")
                self.clean()
            
            # Phase 3: Prerequisites (unless skipped or package-only)
            if not options.skip_setup and not options.package_only:
                self.logger.step("Installing prerequisites")
                prereq_result = self._install_prerequisites(options)
                if not prereq_result.success:
                    return prereq_result
            
            # Phase 4: Build executable (unless package-only)
            if not options.package_only:
                self.logger.step("Building NCPA executable")
                build_result = self._build_executable(options)
                if not build_result.success:
                    return build_result
            
            # Phase 5: Post-build fixes
            self.logger.step("Applying platform-specific fixes")
            fix_result = self._apply_post_build_fixes(options)
            if not fix_result.success:
                return fix_result
            
            # Phase 6: Packaging (unless build-only)
            artifacts = []
            if not options.build_only:
                self.logger.step("Creating distribution packages")
                package_result = self._create_packages(options)
                if not package_result.success:
                    return package_result
                artifacts.extend(package_result.artifacts)
            
            duration = time.time() - start_time
            self.logger.success(f"Build completed successfully in {duration:.1f}s")
            
            if artifacts:
                self.logger.info("Generated artifacts:")
                for artifact in artifacts:
                    self.logger.info(f"  {artifact}")
            
            return BuildResult(
                success=True,
                artifacts=artifacts,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Build failed after {duration:.1f}s: {e}"
            self.logger.failure(error_msg)
            self.logger.exception("Build exception details")
            
            return BuildResult(
                success=False,
                error=error_msg,
                duration=duration
            )
    
    def clean(self) -> None:
        """Clean build artifacts"""
        self.logger.info("Cleaning build directory...")
        
        patterns_to_clean = [
            "ncpa-*",           # Build directories
            "NCPA-INSTALL-*",   # Install packages
            "*.rpm",            # RPM packages
            "*.deb",            # DEB packages  
            "*.dmg",            # macOS disk images
            "*.pkg",            # Solaris packages
            "*.tar.gz",         # Tarballs
            "ncpa.spec",        # RPM spec file
            "build.log",        # Build logs
        ]
        
        items_cleaned = 0
        
        for pattern in patterns_to_clean:
            for path in self.build_dir.glob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        self.system_utils.remove_path(path, force=True)
                    
                    items_cleaned += 1
                    self.logger.debug(f"Cleaned: {path}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to clean {path}: {e}")
        
        # Clean agent build directory
        agent_build_dir = self.agent_dir / "build"
        if agent_build_dir.exists():
            self.system_utils.remove_path(agent_build_dir, force=True)
            items_cleaned += 1
        
        self.logger.info(f"Cleaned {items_cleaned} items from build directory")
    
    def validate_environment(self) -> BuildResult:
        """
        Validate build environment
        
        Returns:
            BuildResult with validation status
        """
        errors = []
        warnings = []
        
        try:
            # Validate build directories
            if not self.build_dir.exists():
                errors.append(f"Build directory does not exist: {self.build_dir}")
            
            if not self.agent_dir.exists():
                errors.append(f"Agent directory does not exist: {self.agent_dir}")
            
            # Validate Python executable
            python_exe = self.platform_info.python_executable
            if not self.system_utils.command_exists(python_exe):
                errors.append(f"Python executable not found: {python_exe}")
            else:
                # Check Python version
                result = self.system_utils.run_command(
                    [python_exe, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")']
                )
                if result.success:
                    version_str = result.stdout.strip()
                    try:
                        major, minor = map(int, version_str.split('.'))
                        if major != 3 or minor < 6:
                            errors.append(f"Python 3.6+ required, found Python {version_str}")
                    except ValueError:
                        warnings.append(f"Could not parse Python version: {version_str}")
                else:
                    warnings.append(f"Could not check Python version: {result.stderr}")
            
            # Validate version configuration
            version_validation = self.version_manager.validate_versions(self.platform_info)
            if not version_validation['valid']:
                errors.extend(version_validation['errors'])
            warnings.extend(version_validation['warnings'])
            
            # Platform-specific validation
            if self.platform_impl:
                platform_validation = self.platform_impl.validate_environment()
                if hasattr(platform_validation, 'errors'):
                    errors.extend(platform_validation.errors)
                if hasattr(platform_validation, 'warnings'):
                    warnings.extend(platform_validation.warnings)
            
            # Report validation results
            if warnings:
                for warning in warnings:
                    self.logger.warning(f"Validation warning: {warning}")
            
            if errors:
                error_msg = "Environment validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
                return BuildResult(success=False, error=error_msg)
            
            self.logger.success("Environment validation passed")
            return BuildResult(success=True)
            
        except Exception as e:
            error_msg = f"Validation error: {e}"
            self.logger.exception(error_msg)
            return BuildResult(success=False, error=error_msg)
    
    def _load_platform_implementation(self):
        """Load platform-specific implementation"""
        try:
            # Import platform implementations dynamically
            from ..platforms import get_platform_implementation
            
            self.platform_impl = get_platform_implementation(
                self.platform_info, 
                self.version_manager,
                self.logger
            )
            
            self.logger.debug(f"Loaded platform implementation: {type(self.platform_impl).__name__}")
            
        except ImportError as e:
            self.logger.warning(f"Could not load platform implementation: {e}")
            self.logger.info("Some platform-specific features may not be available")
        except Exception as e:
            self.logger.error(f"Error loading platform implementation: {e}")
            raise
    
    def _install_prerequisites(self, options: BuildOptions) -> BuildResult:
        """Install platform prerequisites"""
        try:
            if self.platform_impl:
                return self.platform_impl.install_prerequisites(options)
            else:
                self.logger.warning("No platform implementation available for prerequisite installation")
                return BuildResult(success=True)
                
        except Exception as e:
            error_msg = f"Failed to install prerequisites: {e}"
            self.logger.exception(error_msg)
            return BuildResult(success=False, error=error_msg)
    
    def _build_executable(self, options: BuildOptions) -> BuildResult:
        """Build the NCPA executable using cx_Freeze"""
        try:
            # Change to agent directory
            original_cwd = Path.cwd()
            os.chdir(self.agent_dir)
            
            try:
                # Clean any .pyc files
                self.logger.info("Cleaning Python cache files...")
                pyc_files = list(self.agent_dir.rglob("*.pyc"))
                for pyc_file in pyc_files:
                    pyc_file.unlink()
                self.logger.debug(f"Removed {len(pyc_files)} .pyc files")
                
                # Ensure required directories exist
                required_dirs = [
                    self.agent_dir / "plugins",
                    self.agent_dir / "build", 
                    self.agent_dir / "var" / "log"
                ]
                
                for req_dir in required_dirs:
                    self.system_utils.ensure_directory(req_dir)
                
                # Add Git version information
                git_info = self._get_git_version_info()
                
                # Run cx_Freeze build
                self.logger.info("Running cx_Freeze build (this may take several minutes)...")
                
                python_exe = self.platform_info.python_executable
                build_cmd = [python_exe, "setup.py", "build_exe"]
                
                result = self.system_utils.run_command(
                    build_cmd,
                    cwd=self.agent_dir,
                    timeout=1800  # 30 minutes timeout
                )
                
                if not result.success:
                    return BuildResult(
                        success=False, 
                        error=f"cx_Freeze build failed: {result.stderr}"
                    )
                
                # Find the cx_Freeze build directory
                build_exe_dir = self._find_cxfreeze_build_dir()
                if not build_exe_dir:
                    return BuildResult(
                        success=False,
                        error="Could not find cx_Freeze build directory"
                    )
                
                self.logger.success(f"cx_Freeze build completed: {build_exe_dir}")
                
                # Copy build to standard location
                target_dir = self.build_dir / "ncpa"
                if target_dir.exists():
                    self.system_utils.remove_path(target_dir)
                
                # Platform-specific copy handling
                if self.platform_info.os_family == 'darwin':
                    # macOS: Use -L to follow symlinks
                    copy_result = self.system_utils.run_command([
                        "cp", "-RLf", str(build_exe_dir), str(target_dir)
                    ])
                else:
                    # Other platforms: Standard recursive copy
                    copy_result = self.system_utils.run_command([
                        "cp", "-rf", str(build_exe_dir), str(target_dir) 
                    ])
                
                if not copy_result.success:
                    return BuildResult(
                        success=False,
                        error=f"Failed to copy build directory: {copy_result.stderr}"
                    )
                
                # Write Git version file
                if git_info['hash_file']:
                    git_file = target_dir / git_info['hash_file']
                    self.file_utils.write_text(git_file, git_info['long_hash'])
                
                return BuildResult(success=True)
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            error_msg = f"Build executable failed: {e}"
            self.logger.exception(error_msg)
            return BuildResult(success=False, error=error_msg)
    
    def _apply_post_build_fixes(self, options: BuildOptions) -> BuildResult:
        """Apply platform-specific post-build fixes"""
        try:
            build_dir = self.build_dir / "ncpa"
            
            if not build_dir.exists():
                return BuildResult(
                    success=False,
                    error=f"Build directory not found: {build_dir}"
                )
            
            # Apply platform-specific fixes
            if self.platform_impl:
                platform_result = self.platform_impl.post_build_fixes(build_dir)
                if hasattr(platform_result, 'success') and not platform_result.success:
                    return BuildResult(success=False, error=platform_result.error)
            
            # Apply common fixes
            
            # 1. Remove libffi duplicates (critical workaround)
            self._remove_libffi_duplicates(build_dir)
            
            # 2. Set proper permissions
            self._set_build_permissions(build_dir)
            
            return BuildResult(success=True)
            
        except Exception as e:
            error_msg = f"Post-build fixes failed: {e}"
            self.logger.exception(error_msg)
            return BuildResult(success=False, error=error_msg)
    
    def _create_packages(self, options: BuildOptions) -> BuildResult:
        """Create distribution packages"""
        try:
            artifacts = []
            
            # Create tarball first
            self.logger.info("Creating tarball...")
            tarball = self._create_tarball()
            if tarball:
                artifacts.append(tarball)
            
            # Create platform-specific packages
            if self.platform_impl:
                package_result = self.platform_impl.create_package(self.build_dir / "ncpa")
                if hasattr(package_result, 'artifacts'):
                    artifacts.extend(package_result.artifacts)
            
            return BuildResult(success=True, artifacts=artifacts)
            
        except Exception as e:
            error_msg = f"Package creation failed: {e}"
            self.logger.exception(error_msg)
            return BuildResult(success=False, error=error_msg)
    
    def _dry_run_build(self, options: BuildOptions) -> BuildResult:
        """Show what would be done in a dry run"""
        
        self.logger.info("=== DRY RUN - BUILD PLAN ===")
        
        steps = []
        
        if not options.skip_setup and not options.package_only:
            steps.append("1. Install prerequisites for " + str(self.platform_info))
        
        if not options.package_only:
            steps.append("2. Build NCPA executable with cx_Freeze")
            steps.append("3. Apply platform-specific fixes")
            
        if not options.build_only:
            steps.append("4. Create distribution packages")
        
        for step in steps:
            self.logger.info(f"   {step}")
        
        self.logger.info("=== END DRY RUN ===")
        
        return BuildResult(success=True)
    
    def _get_build_directory(self) -> Path:
        """Get the build directory path"""
        # Try to detect from current location
        current = Path.cwd()
        
        # If we're in the build directory
        if current.name == 'build' and (current.parent / 'agent').exists():
            return current
        
        # If we're in the project root
        if (current / 'build').exists() and (current / 'agent').exists():
            return current / 'build'
        
        # If we're in a subdirectory, try to find the project root
        for parent in current.parents:
            if (parent / 'build').exists() and (parent / 'agent').exists():
                return parent / 'build'
        
        # Fallback: use current directory
        self.logger.warning("Could not auto-detect build directory, using current directory")
        return current
    
    def _find_cxfreeze_build_dir(self) -> Optional[Path]:
        """Find the cx_Freeze build directory"""
        build_dir = self.agent_dir / "build"
        
        if not build_dir.exists():
            return None
        
        # Look for exe.* directories
        for item in build_dir.iterdir():
            if item.is_dir() and item.name.startswith("exe."):
                return item
        
        return None
    
    def _get_git_version_info(self) -> Dict[str, str]:
        """Get Git version information"""
        git_info = {
            'long_hash': 'Not built under GIT',
            'short_hash': 'NoGIT',
            'hash_file': 'NoGIT.githash'
        }
        
        if not self.system_utils.command_exists('git'):
            return git_info
        
        try:
            # Get long hash
            result = self.system_utils.run_command(['git', 'rev-parse', 'HEAD'])
            if result.success:
                long_hash = result.stdout.strip()
                git_info['long_hash'] = long_hash
                
                # Get short hash
                result = self.system_utils.run_command(['git', 'rev-parse', '--short', 'HEAD'])
                if result.success:
                    short_hash = result.stdout.strip()
                    git_info['short_hash'] = short_hash
                    
                    # Check for uncommitted changes
                    result = self.system_utils.run_command([
                        'git', 'status', '--untracked-files=no', '--porcelain'
                    ])
                    if result.success and result.stdout.strip():
                        git_info['long_hash'] += '++  compiled with uncommitted changes'
                        git_info['short_hash'] += '++'
                    
                    git_info['hash_file'] = f"git-{git_info['short_hash']}.githash"
            
        except Exception as e:
            self.logger.debug(f"Could not get Git version info: {e}")
        
        return git_info
    
    def _remove_libffi_duplicates(self, build_dir: Path):
        """
        Remove libffi duplicate copies - critical workaround
        
        This preserves the exact workaround from the original scripts.
        """
        try:
            pattern = "libffi-*.so.*"
            libffi_files = list(build_dir.glob(pattern))
            
            for libffi_file in libffi_files:
                libffi_file.unlink()
                self.logger.info(f"Removed duplicate libffi: {libffi_file.name}")
            
            if libffi_files:
                self.logger.info(f"Removed {len(libffi_files)} libffi duplicate(s)")
                
        except Exception as e:
            self.logger.warning(f"Error removing libffi duplicates: {e}")
    
    def _set_build_permissions(self, build_dir: Path):
        """Set proper permissions on build directory"""
        try:
            # Make readable by all
            self.system_utils.run_command(['chmod', '-R', 'a+r', str(build_dir)])
            self.system_utils.run_command(['chmod', '-R', 'g+r', str(build_dir)])
            
            # Set ownership to nagios if user exists
            if self._user_exists('nagios'):
                var_dir = build_dir / 'var'
                etc_dir = build_dir / 'etc'
                
                for dir_path in [var_dir, etc_dir]:
                    if dir_path.exists():
                        self.system_utils.run_command([
                            'chown', '-R', 'nagios:nagios', str(dir_path)
                        ])
                        self.system_utils.run_command(['chmod', '-R', '755', str(dir_path)])
            
            # Make build directory executable
            self.system_utils.run_command(['chmod', '755', str(build_dir)])
            
        except Exception as e:
            self.logger.warning(f"Error setting permissions: {e}")
    
    def _create_tarball(self) -> Optional[Path]:
        """Create tarball of build"""
        try:
            # Get version
            version_file = self.build_dir.parent / "VERSION"
            if version_file.exists():
                version = version_file.read_text().strip()
            else:
                version = "unknown"
            
            source_dir = self.build_dir / "ncpa" 
            versioned_dir = self.build_dir / f"ncpa-{version}"
            tarball_path = self.build_dir / f"ncpa-{version}.tar.gz"
            
            # Copy to versioned directory
            if versioned_dir.exists():
                self.system_utils.remove_path(versioned_dir)
                
            self.system_utils.copy_path(source_dir, versioned_dir)
            
            # Create tarball
            result = self.system_utils.run_command([
                'tar', '-czvf', str(tarball_path), versioned_dir.name
            ], cwd=self.build_dir)
            
            if result.success:
                self.logger.success(f"Created tarball: {tarball_path}")
                return tarball_path
            else:
                self.logger.error(f"Failed to create tarball: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating tarball: {e}")
            return None
    
    def _user_exists(self, username: str) -> bool:
        """Check if a user exists on the system"""
        try:
            result = self.system_utils.run_command(['id', username])
            return result.success
        except Exception:
            return False
