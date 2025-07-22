#!/usr/bin/env python3
"""
Test script to verify configuration parsing for HTTP redirect
"""
from configparser import ConfigParser

# Test the configuration parsing
config = ConfigParser()

# Read the configuration file
config.read('/home/bbahner/ncpa/agent/etc/ncpa.cfg')

# Test the new configuration options
try:
    http_redirect = config.get('listener', 'http_redirect', fallback='1')
    http_redirect_port = config.getint('listener', 'http_redirect_port', fallback=5692)
    
    print(f"HTTP Redirect enabled: {http_redirect}")
    print(f"HTTP Redirect port: {http_redirect_port}")
    
    # Test the main HTTPS port
    https_port = config.getint('listener', 'port', fallback=5693)
    print(f"HTTPS port: {https_port}")
    
    # Test if redirect is enabled
    if http_redirect == '1':
        print(f"✓ HTTP redirect is enabled")
        print(f"✓ HTTP server will run on port {http_redirect_port}")
        print(f"✓ Redirects will point to HTTPS port {https_port}")
    else:
        print("✗ HTTP redirect is disabled")
        
except Exception as e:
    print(f"Configuration parsing error: {e}")

print("\nConfiguration test completed!")
