"""
Platform-specific implementations for NCPA builds.
"""

from .base_platform import BasePlatform
from ..core.platform_detector import PlatformInfo
from ..core.version_manager import VersionManager
from ..core.logger import Logger


def get_platform_implementation(platform_info: PlatformInfo,
                               version_manager: VersionManager,
                               logger: Logger) -> BasePlatform:
    """
    Get platform-specific implementation
    
    Args:
        platform_info: Detected platform information
        version_manager: Version management instance
        logger: Logger instance
        
    Returns:
        Platform-specific implementation instance
    """
    
    if platform_info.os_family == 'linux':
        from .linux_platform import LinuxPlatform
        return LinuxPlatform(platform_info, version_manager, logger)
    
    elif platform_info.os_family == 'darwin':
        from .macos_platform import MacOSPlatform
        return MacOSPlatform(platform_info, version_manager, logger)
    
    elif platform_info.os_family == 'windows':
        from .windows_platform import WindowsPlatform
        return WindowsPlatform(platform_info, version_manager, logger)
    
    elif platform_info.os_family == 'aix':
        from .aix_platform import AIXPlatform
        return AIXPlatform(platform_info, version_manager, logger)
    
    elif platform_info.os_family == 'sunos':
        from .solaris_platform import SolarisPlatform
        return SolarisPlatform(platform_info, version_manager, logger)
    
    else:
        raise ValueError(f"Unsupported platform: {platform_info.os_family}")
