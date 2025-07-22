#!/usr/bin/env python3
"""
Test script to verify HTTP redirect functionality
"""
import sys
import os

# Add the agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

try:
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
    app = create_redirect_app(5693)
    
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
        response = client.get('/api/system/cpu', headers={'Host': 'example.com:5692'})
        print(f"Custom host redirect: {response.status_code} -> {response.headers.get('Location', 'No redirect')}")
    
    print("HTTP redirect app test completed successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires Flask to be installed")
except Exception as e:
    print(f"Test error: {e}")
