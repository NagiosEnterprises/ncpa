"""
Common utilities for NCPA build framework.

Provides shared functionality across all build components.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from .logger import Logger


class CommandResult:
    """Result of a command execution"""
    
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "", 
                 command: str = "", duration: float = 0.0):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command
        self.duration = duration
        
    @property
    def success(self) -> bool:
        """True if command executed successfully"""
        return self.returncode == 0
    
    @property
    def failed(self) -> bool:
        """True if command failed"""
        return self.returncode != 0
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else f"FAILED({self.returncode})"
        return f"CommandResult[{status}]: {self.command}"


class SystemUtils:
    """System-level utilities for build operations"""
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(name="system_utils")
    
    def run_command(self, 
                   command: Union[str, List[str]], 
                   cwd: Optional[Path] = None,
                   env: Optional[Dict[str, str]] = None,
                   timeout: Optional[float] = None,
                   capture_output: bool = True,
                   shell: bool = False) -> CommandResult:
        """
        Run a command with proper logging and error handling
        
        Args:
            command: Command to run (string or list)
            cwd: Working directory  
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            shell: Whether to use shell
            
        Returns:
            CommandResult with execution details
        """
        import time
        
        start_time = time.time()
        
        # Convert command to string for logging
        if isinstance(command, list):
            command_str = ' '.join(command)
        else:
            command_str = command
            
        self.logger.debug(f"Executing: {command_str}")
        if cwd:
            self.logger.debug(f"Working directory: {cwd}")
            
        try:
            # Set up environment
            cmd_env = os.environ.copy()
            if env:
                cmd_env.update(env)
            
            # Run command
            process = subprocess.run(
                command,
                cwd=cwd,
                env=cmd_env,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                shell=shell
            )
            
            duration = time.time() - start_time
            
            result = CommandResult(
                returncode=process.returncode,
                stdout=process.stdout if capture_output else "",
                stderr=process.stderr if capture_output else "",
                command=command_str,
                duration=duration
            )
            
            if result.success:
                self.logger.debug(f"Command completed successfully in {duration:.2f}s")
            else:
                self.logger.warning(f"Command failed with code {result.returncode} in {duration:.2f}s")
                if result.stderr:
                    self.logger.debug(f"Error output: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            self.logger.error(f"Command timed out after {duration:.2f}s")
            return CommandResult(
                returncode=-1,
                stderr=f"Command timed out after {timeout}s",
                command=command_str,
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Command execution failed: {e}")
            return CommandResult(
                returncode=-1,
                stderr=str(e),
                command=command_str,
                duration=duration
            )
    
    def which(self, command: str) -> Optional[str]:
        """Find the full path of a command"""
        return shutil.which(command)
    
    def command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        return shutil.which(command) is not None
    
    def create_temp_dir(self, prefix: str = "ncpa_build_") -> Path:
        """Create a temporary directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir
    
    def remove_path(self, path: Path, force: bool = False) -> bool:
        """
        Safely remove a file or directory
        
        Args:
            path: Path to remove
            force: Whether to ignore errors
            
        Returns:
            True if successful
        """
        try:
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            
            self.logger.debug(f"Removed: {path}")
            return True
            
        except Exception as e:
            if force:
                self.logger.debug(f"Failed to remove {path}: {e}")
                return False
            else:
                self.logger.error(f"Failed to remove {path}: {e}")
                raise
    
    def copy_path(self, src: Path, dst: Path, 
                 follow_symlinks: bool = False,
                 preserve_permissions: bool = True) -> bool:
        """
        Copy file or directory with proper handling
        
        Args:
            src: Source path
            dst: Destination path  
            follow_symlinks: Whether to follow symlinks
            preserve_permissions: Whether to preserve file permissions
            
        Returns:
            True if successful
        """
        try:
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                if follow_symlinks:
                    shutil.copy2(src, dst)
                else:
                    shutil.copy(src, dst)
            elif src.is_dir():
                if follow_symlinks:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
            
            self.logger.debug(f"Copied: {src} -> {dst}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy {src} to {dst}: {e}")
            raise
    
    def ensure_directory(self, path: Path, mode: int = 0o755) -> bool:
        """
        Ensure directory exists with proper permissions
        
        Args:
            path: Directory path
            mode: Directory permissions
            
        Returns:
            True if successful
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(mode)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    def set_permissions(self, path: Path, mode: int) -> bool:
        """
        Set file or directory permissions
        
        Args:
            path: Path to modify
            mode: Permission mode (octal)
            
        Returns:
            True if successful
        """
        try:
            path.chmod(mode)
            self.logger.debug(f"Set permissions {oct(mode)} on {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set permissions on {path}: {e}")
            return False
    
    def get_file_hash(self, path: Path, algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate file hash
        
        Args:
            path: File path
            algorithm: Hash algorithm (sha256, md5, etc.)
            
        Returns:
            Hex digest of file hash
        """
        import hashlib
        
        try:
            hasher = hashlib.new(algorithm)
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate {algorithm} hash of {path}: {e}")
            return None


class FileUtils:
    """File manipulation utilities"""
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(name="file_utils")
    
    def read_text(self, path: Path, encoding: str = 'utf-8') -> str:
        """Read text file content"""
        try:
            return path.read_text(encoding=encoding)
        except Exception as e:
            self.logger.error(f"Failed to read {path}: {e}")
            raise
    
    def write_text(self, path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """Write text to file"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write {path}: {e}")
            return False
    
    def append_text(self, path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """Append text to file"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to append to {path}: {e}")
            return False
    
    def find_files(self, directory: Path, pattern: str = "*", 
                  recursive: bool = True) -> List[Path]:
        """Find files matching pattern"""
        try:
            if recursive:
                return list(directory.rglob(pattern))
            else:
                return list(directory.glob(pattern))
        except Exception as e:
            self.logger.error(f"Failed to find files in {directory}: {e}")
            return []
    
    def replace_in_file(self, path: Path, old: str, new: str) -> bool:
        """Replace text in file"""
        try:
            content = self.read_text(path)
            new_content = content.replace(old, new)
            return self.write_text(path, new_content)
        except Exception as e:
            self.logger.error(f"Failed to replace text in {path}: {e}")
            return False


class ValidationUtils:
    """Validation utilities"""
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(name="validation_utils")
    
    def validate_python_version(self, version: str) -> Tuple[bool, str]:
        """
        Validate Python version string
        
        Args:
            version: Version string (e.g., '3.13.5')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False, "Version must have three parts (major.minor.patch)"
            
            major, minor, patch = map(int, parts)
            
            if major != 3:
                return False, "Only Python 3.x is supported"
            
            if minor < 6:
                return False, "Python 3.6 or higher is required"
            
            return True, ""
            
        except ValueError:
            return False, "Version must contain only numbers and dots"
    
    def validate_path_exists(self, path: Path, path_type: str = "path") -> Tuple[bool, str]:
        """
        Validate that a path exists
        
        Args:
            path: Path to validate
            path_type: Type description for error message
            
        Returns:
            Tuple of (exists, error_message)  
        """
        if not path.exists():
            return False, f"{path_type.title()} does not exist: {path}"
        
        return True, ""
    
    def validate_executable(self, path: Path) -> Tuple[bool, str]:
        """
        Validate that a file is executable
        
        Args:
            path: Path to executable
            
        Returns:
            Tuple of (is_executable, error_message)
        """
        exists, error = self.validate_path_exists(path, "executable")
        if not exists:
            return False, error
        
        if not os.access(path, os.X_OK):
            return False, f"File is not executable: {path}"
        
        return True, ""
    
    def validate_directory_writable(self, path: Path) -> Tuple[bool, str]:
        """
        Validate that a directory is writable
        
        Args:
            path: Directory path
            
        Returns:
            Tuple of (is_writable, error_message)
        """
        try:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            
            if not path.is_dir():
                return False, f"Path is not a directory: {path}"
            
            # Test write access
            test_file = path / f".write_test_{os.getpid()}"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                return False, f"Directory is not writable: {path}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Cannot access directory {path}: {e}"
