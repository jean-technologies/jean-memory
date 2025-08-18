#!/usr/bin/env python3
"""
Simple HTTP server to test OAuth flow locally
Run this and access http://localhost:8080/test_oauth_flow.html
"""

import http.server
import socketserver
import os

PORT = 8888
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

print(f"Starting OAuth test server...")
print(f"Server running at: http://localhost:{PORT}")
print(f"OAuth test page: http://localhost:{PORT}/test_oauth_flow.html")
print("\nMake sure to add this to Google Console Authorized redirect URIs:")
print(f"  http://localhost:{PORT}/test_oauth_flow.html")
print("\nPress Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")