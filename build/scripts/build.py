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
framework_path = Path(__file__).parent.parent / "framework"
sys.path.insert(0, str(framework_path))

try:
    from core.build_manager import BuildManager, BuildOptions
    from core.platform_detector import PlatformDetector
    from core.logger import Logger, LogLevel
except ImportError as e:
    print(f"ERROR: Could not import build framework: {e}", file=sys.stderr)
    print("Please ensure you're running this script from the correct location.", file=sys.stderr)
    sys.exit(1)


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

Build Process:
  1. Platform Detection - Automatically detect OS and distribution
  2. Prerequisite Installation - Install required system packages
  3. Python Environment Setup - Ensure proper Python version
  4. Executable Build - Use cx_Freeze to create frozen executable
  5. Platform-Specific Fixes - Apply critical workarounds
  6. Package Creation - Generate distribution packages

For more information, see the documentation in the docs/ directory.
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
        help="Skip prerequisite installation (use if manually configured)"
    )
    parser.add_argument(
        "--no-interaction", "-n",
        action="store_true",
        help="Run without interactive prompts (auto-confirm all actions)"
    )
    
    # Configuration options
    parser.add_argument(
        "--profile",
        choices=["debug", "release", "ci"],
        default="release",
        help="Build profile to use (affects optimization and debug settings)"
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
        help="Set logging verbosity level"
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
        help="Show what would be done without executing commands"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true", 
        help="Validate environment and configuration only, don't build"
    )
    parser.add_argument(
        "--clean-first",
        action="store_true",
        help="Clean build directory before starting build"
    )
    
    return parser


def main() -> int:
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging early
    log_level = LogLevel[args.log_level.upper()]
    log_file = args.log_file or Path("build/build.log")
    logger = Logger(level=log_level, log_file=log_file)
    
    logger.info("NCPA Build System - Next Generation")
    logger.info("=" * 50)
    
    try:
        # Detect platform
        logger.step("Detecting platform")
        platform_info = PlatformDetector.detect(logger)
        logger.success(f"Detected platform: {platform_info}")
        
        # Initialize build manager
        logger.step("Initializing build manager")
        build_manager = BuildManager(
            config_file=args.config,
            platform_info=platform_info,
            logger=logger
        )
        
        # Handle special actions first
        if args.clean:
            logger.step("Cleaning build directory")
            build_manager.clean()
            logger.success("Build directory cleaned successfully")
            return 0
            
        if args.validate_only:
            logger.step("Validating build environment")
            result = build_manager.validate_environment()
            if result.success:
                logger.success("Environment validation passed")
                if result.warnings:
                    logger.info(f"Validation completed with {len(result.warnings)} warnings")
                return 0
            else:
                logger.failure("Environment validation failed")
                if hasattr(result, 'errors'):
                    for error in result.errors:
                        logger.error(f"  • {error}")
                return 1
        
        # Create build options
        build_options = BuildOptions(
            build_only=args.build_only,
            package_only=args.package_only,
            skip_setup=args.skip_setup,
            no_interaction=args.no_interaction,
            profile=args.profile,
            dry_run=args.dry_run,
            clean_first=args.clean_first
        )
        
        # Show configuration summary
        logger.subsection("Build Configuration")
        logger.info(f"Platform: {platform_info}")
        logger.info(f"Profile: {args.profile}")
        logger.info(f"Build Options: {build_options}")
        
        # Execute build
        logger.section("Starting NCPA Build Process")
        result = build_manager.build(build_options)
        
        if result.success:
            elapsed_time = logger.get_elapsed_time()
            logger.section("Build Completed Successfully")
            logger.success(f"Total build time: {elapsed_time:.1f} seconds")
            
            if result.artifacts:
                logger.info("Generated artifacts:")
                for artifact in result.artifacts:
                    logger.info(f"  📦 {artifact}")
                    
            logger.info("\nBuild completed! You can find the built application in:")
            logger.info(f"  {Path('build/ncpa').absolute()}")
            
            return 0
        else:
            logger.section("Build Failed")
            logger.failure(f"Build failed: {result.error}")
            
            if hasattr(result, 'logs') and result.logs:
                logger.info("Recent log entries:")
                for log_entry in result.logs[-10:]:  # Show last 10 log entries
                    logger.info(f"  {log_entry}")
            
            logger.info(f"\nFor detailed logs, check: {log_file}")
            
            return 1
            
    except KeyboardInterrupt:
        logger.warning("\nBuild interrupted by user (Ctrl+C)")
        logger.info("Build process was cancelled")
        return 130
    
    except Exception as e:
        logger.exception(f"Unexpected build system error: {e}")
        
        if log_level == LogLevel.DEBUG:
            import traceback
            logger.debug("Full traceback:")
            logger.debug(traceback.format_exc())
        else:
            logger.info("Run with --log-level debug for detailed error information")
        
        return 1


def show_version():
    """Show version information"""
    try:
        from framework import __version__
        print(f"NCPA Build System v{__version__}")
    except ImportError:
        print("NCPA Build System (development version)")


if __name__ == "__main__":
    sys.exit(main())
