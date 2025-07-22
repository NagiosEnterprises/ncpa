#!/usr/bin/env python3
"""
Test script for the new NCPA build framework.
This script validates that the framework components are working correctly.
"""

import sys
import os
from pathlib import Path

# Add the framework to the Python path
framework_dir = Path(__file__).parent / 'framework'
sys.path.insert(0, str(framework_dir))

try:
    from core.logger import get_logger, setup_logging
    from core.platform_detector import PlatformDetector
    from core.version_manager import VersionManager
    from core.build_manager import BuildManager
    from platforms.linux import LinuxPlatform
    
    print("✓ All framework imports successful")
    
    # Test logger
    setup_logging('INFO')
    logger = get_logger(__name__)
    logger.info("Logger test successful")
    print("✓ Logger working")
    
    # Test platform detection
    detector = PlatformDetector()
    platform_name = detector.detect_platform()
    print(f"✓ Platform detected: {platform_name}")
    
    # Test version manager
    vm = VersionManager(Path('.'))
    version = vm.get_version()
    print(f"✓ Version detected: {version}")
    
    # Test Linux platform (if on Linux)
    if platform_name.startswith('linux'):
        try:
            linux_platform = LinuxPlatform(Path('.'), Path('./test_build'), {})
            distro = linux_platform.distro_info
            print(f"✓ Linux platform working: {distro['name']} {distro['version']}")
            
            # Test prerequisite checking
            missing = linux_platform.check_prerequisites()
            if missing:
                print(f"Missing prerequisites: {missing}")
            else:
                print("✓ All prerequisites available")
                
        except Exception as e:
            print(f"✗ Linux platform test failed: {e}")
    
    print("\n🎉 Framework validation complete!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)
