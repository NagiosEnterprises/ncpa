#!/usr/bin/env python3
"""
Test script to verify that disable_gui configuration option works properly.
This script tests both API access (should work) and GUI access (should be blocked).
"""

import sys
import os
import requests
import json
import time
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def test_api_access(host, port, token):
    """Test that API access still works when GUI is disabled."""
    print(f"\n=== Testing API Access ===")
    
    # Test basic API endpoint
    api_url = f"https://{host}:{port}/api/"
    try:
        response = requests.get(api_url, params={'token': token}, verify=False, timeout=10)
        if response.status_code == 200:
            print("✓ API root endpoint accessible")
            data = response.json()
            print(f"  Available endpoints: {', '.join(data.keys())}")
        else:
            print(f"✗ API root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API root endpoint error: {e}")
        return False
    
    # Test specific API endpoint
    cpu_url = f"https://{host}:{port}/api/cpu/percent"
    try:
        response = requests.get(cpu_url, params={'token': token}, verify=False, timeout=10)
        if response.status_code == 200:
            print("✓ CPU API endpoint accessible")
            data = response.json()
            print(f"  CPU usage: {data.get('cpu', {}).get('percent', 'N/A')}%")
        else:
            print(f"✗ CPU API endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ CPU API endpoint error: {e}")
        return False
    
    return True

def test_gui_blocked(host, port, token):
    """Test that GUI access is blocked when disable_gui is enabled."""
    print(f"\n=== Testing GUI Access (Should be blocked) ===")
    
    gui_endpoints = [
        "/",
        "/gui/",
        "/gui/dashboard",
        "/gui/api",
        "/gui/stats",
        "/gui/admin",
        "/login",
        "/logout",
        "/top",
        "/tail",
        "/graph/cpu/percent"
    ]
    
    blocked_count = 0
    for endpoint in gui_endpoints:
        url = f"https://{host}:{port}{endpoint}"
        try:
            response = requests.get(url, params={'token': token}, verify=False, timeout=10)
            if "Web GUI is disabled" in response.text:
                print(f"✓ {endpoint} properly blocked")
                blocked_count += 1
            elif response.status_code == 403:
                print(f"✓ {endpoint} properly blocked (403)")
                blocked_count += 1
            else:
                print(f"✗ {endpoint} not blocked (status: {response.status_code})")
        except Exception as e:
            print(f"? {endpoint} error: {e}")
    
    print(f"\nBlocked {blocked_count}/{len(gui_endpoints)} GUI endpoints")
    return blocked_count == len(gui_endpoints)

def main():
    """Main test function."""
    if len(sys.argv) != 4:
        print("Usage: python test_disable_gui.py <host> <port> <token>")
        print("Example: python test_disable_gui.py localhost 5693 mytoken")
        sys.exit(1)
    
    host = sys.argv[1]
    port = sys.argv[2]
    token = sys.argv[3]
    
    print(f"Testing NCPA disable_gui functionality")
    print(f"Host: {host}:{port}")
    print(f"Token: {token}")
    
    # Test API access
    api_works = test_api_access(host, port, token)
    
    # Test GUI blocking
    gui_blocked = test_gui_blocked(host, port, token)
    
    print(f"\n=== Test Results ===")
    print(f"API Access: {'✓ PASS' if api_works else '✗ FAIL'}")
    print(f"GUI Blocked: {'✓ PASS' if gui_blocked else '✗ FAIL'}")
    
    if api_works and gui_blocked:
        print("\n✓ ALL TESTS PASSED - disable_gui is working correctly!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED - disable_gui may not be working correctly!")
        sys.exit(1)

if __name__ == "__main__":
    main()
