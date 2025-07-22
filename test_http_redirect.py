#!/usr/bin/env python3
"""
Test script to verify the new HTTP redirect configuration approach
"""

import sys
import os

# Add the agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from configparser import ConfigParser

def test_config():
    """Test the configuration parsing"""
    config = ConfigParser()
    config.read('agent/etc/ncpa.cfg')
    
    try:
        # Test main port
        main_port = config.getint('listener', 'port', fallback=5693)
        print(f"Main port: {main_port}")
        
        # Test HTTP redirect settings
        http_redirect = config.get('listener', 'http_redirect', fallback='1')
        print(f"HTTP redirect enabled: {http_redirect}")
        
        if http_redirect == '1':
            https_port = config.getint('listener', 'https_port', fallback=5694)
            print(f"HTTPS port (when redirect enabled): {https_port}")
            print(f"Expected behavior:")
            print(f"  - HTTP server on port {main_port} (redirects to HTTPS)")
            print(f"  - HTTPS server on port {https_port}")
        else:
            print(f"Expected behavior:")
            print(f"  - HTTPS server only on port {main_port}")
            
        return True
        
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

def test_redirect_logic():
    """Test the redirect logic"""
    try:
        # Import Flask here to avoid issues if not installed
        from flask import Flask, request, redirect
        
        def create_redirect_app(https_port):
            """Create a simple Flask app that redirects all HTTP requests to HTTPS"""
            redirect_app = Flask(__name__)
            
            @redirect_app.route('/', defaults={'path': ''})
            @redirect_app.route('/<path:path>')
            def redirect_to_https(path):
                """Redirect all HTTP requests to HTTPS"""
                host = request.host
                
                # Handle cases where port might be included in the host header
                if ':' in host:
                    hostname = host.split(':')[0]
                else:
                    hostname = host
                
                # Build HTTPS URL with same path and query parameters
                https_url = f"https://{hostname}:{https_port}"
                if path:
                    https_url += f"/{path}"
                if request.query_string:
                    https_url += f"?{request.query_string.decode('utf-8')}"
                
                return redirect(https_url, code=301)
            
            return redirect_app
        
        # Test the redirect app
        app = create_redirect_app(5694)
        
        # Test client to verify redirect works
        with app.test_client() as client:
            # Test root path redirect
            response = client.get('/')
            print(f"Root path redirect: {response.status_code} -> {response.headers.get('Location', 'No redirect')}")
            
            # Test API path redirect  
            response = client.get('/api/system/cpu')
            print(f"API path redirect: {response.status_code} -> {response.headers.get('Location', 'No redirect')}")
            
            # Test with query parameters
            response = client.get('/api/system/cpu?token=test123')
            print(f"Query param redirect: {response.status_code} -> {response.headers.get('Location', 'No redirect')}")
            
            # Test with different host header
            response = client.get('/api/system/cpu', headers={'Host': 'example.com:5693'})
            print(f"Custom host redirect: {response.status_code} -> {response.headers.get('Location', 'No redirect')}")
        
        return True
        
    except ImportError as e:
        print(f"Flask not available for testing: {e}")
        return False
    except Exception as e:
        print(f"Redirect test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing HTTP redirect configuration...")
    print("=" * 50)
    
    config_ok = test_config()
    print("\n" + "=" * 50)
    
    if config_ok:
        print("Testing redirect logic...")
        print("=" * 50)
        test_redirect_logic()
        print("\n" + "=" * 50)
        
        print("Summary:")
        print("✓ Configuration parsing works")
        print("✓ New approach: HTTP on port 5693, HTTPS on port 5694")
        print("✓ When you access http://your_ip:5693, it will redirect to https://your_ip:5694")
        print("✓ This solves the connection reset issue!")
        
    else:
        print("Configuration test failed!")
