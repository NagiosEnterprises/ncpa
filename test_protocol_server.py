#!/usr/bin/env python3

"""
Test script for the ProtocolDetectingServer
"""

import sys
import os
import ssl
import time
import logging
import requests
from threading import Thread

# Add the agent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

# Configure basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test')

def test_protocol_detection():
    """Test the protocol detection functionality"""
    
    try:
        # Import after path setup
        from ncpa import ProtocolDetectingServer
        from flask import Flask
        from gevent.pool import Pool
        import listener.certificate as certificate
        
        print("=== Testing Protocol Detection Server ===")
        
        # Create a simple Flask app for testing
        test_app = Flask(__name__)
        
        @test_app.route('/')
        def hello():
            return "Hello from HTTPS!"
        
        @test_app.route('/<path:path>')
        def catch_all(path):
            return f"HTTPS path: {path}"
        
        # Create self-signed certificates for testing
        cert_file, key_file = certificate.create_self_signed_cert('/tmp', 'test_ncpa.crt', 'test_ncpa.key')
        
        # SSL context
        ssl_context = {
            'certfile': cert_file,
            'keyfile': key_file,
            'ssl_version': ssl.PROTOCOL_TLS_SERVER
        }
        
        # Create the protocol detecting server
        server = ProtocolDetectingServer(
            listener_address=('127.0.0.1', 5693),
            https_app=test_app,
            ssl_context=ssl_context,
            logger=logger,
            spawn=Pool(10)
        )
        
        print("Created ProtocolDetectingServer successfully")
        
        # Start server in background thread
        server_thread = Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        print("Server started, waiting for it to be ready...")
        time.sleep(2)
        
        # Test HTTP request (should redirect)
        print("\n=== Testing HTTP Request (should redirect) ===")
        try:
            response = requests.get('http://127.0.0.1:5693/', allow_redirects=False, timeout=5)
            print(f"HTTP response status: {response.status_code}")
            print(f"HTTP response headers: {dict(response.headers)}")
            if 'Location' in response.headers:
                print(f"Redirect location: {response.headers['Location']}")
        except Exception as e:
            print(f"HTTP test error: {e}")
        
        # Test HTTPS request (should work)
        print("\n=== Testing HTTPS Request (should work) ===")
        try:
            # Disable SSL verification for self-signed cert
            response = requests.get('https://127.0.0.1:5693/', verify=False, timeout=5)
            print(f"HTTPS response status: {response.status_code}")
            print(f"HTTPS response content: {response.text}")
        except Exception as e:
            print(f"HTTPS test error: {e}")
        
        print("\n=== Test completed ===")
        
        # Stop server
        server.stop()
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_protocol_detection()
