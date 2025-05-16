#!/usr/bin/env python3
"""
Browser Preview Utility for Computer Use Agent

This module provides functionality to display a browser window showing the 
live screenshots captured during Computer Use Agent execution. This provides
visual feedback during test execution.
"""

import os
import time
import json
import base64
import threading
import http.server
import socketserver
from pathlib import Path
from typing import Optional, List, Dict, Any

# Global variables
DEFAULT_PORT = 8080
running_servers = {}

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for browser preview"""
    
    def __init__(self, *args, screenshot_dir=None, **kwargs):
        self.screenshot_dir = screenshot_dir
        self.latest_screenshot = None
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Send preview HTML
            html = self._generate_preview_html()
            self.wfile.write(html.encode())
            
        elif self.path == '/latest':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Get the latest screenshot info
            latest = self._get_latest_screenshot()
            self.wfile.write(json.dumps(latest).encode())
            
        elif self.path.startswith('/screenshots/'):
            screenshot_name = os.path.basename(self.path)
            screenshot_path = os.path.join(self.screenshot_dir, screenshot_name)
            
            if os.path.exists(screenshot_path):
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                
                with open(screenshot_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Screenshot not found')
        else:
            super().do_GET()
    
    def _generate_preview_html(self):
        """Generate HTML for preview page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Computer Use Agent Preview</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                }
                #screenshot {
                    max-width: 100%;
                    border: 1px solid #ddd;
                    margin-top: 10px;
                }
                .info {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                }
                .controls {
                    margin-top: 20px;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Computer Use Agent Preview</h1>
                <p>Directory: <code id="dir-path">{}</code></p>
                <div class="controls">
                    <button id="refresh-btn">Refresh</button>
                    <button id="auto-refresh-btn">Auto Refresh</button>
                    <span id="auto-refresh-status">Auto-refresh: Off</span>
                </div>
                <img id="screenshot" src="" alt="Loading screenshot...">
                <div class="info">
                    <p>Timestamp: <span id="timestamp">Loading...</span></p>
                    <p>Filename: <span id="filename">Loading...</span></p>
                </div>
            </div>
            
            <script>
                const dirPath = document.getElementById('dir-path');
                const refreshBtn = document.getElementById('refresh-btn');
                const autoRefreshBtn = document.getElementById('auto-refresh-btn');
                const autoRefreshStatus = document.getElementById('auto-refresh-status');
                const screenshotImg = document.getElementById('screenshot');
                const timestampEl = document.getElementById('timestamp');
                const filenameEl = document.getElementById('filename');
                
                let autoRefreshInterval = null;
                let isAutoRefreshOn = false;
                
                // Set directory path
                dirPath.textContent = '{screenshot_dir}';
                
                // Function to fetch and display latest screenshot
                async function refreshScreenshot() {{
                    try {{
                        const response = await fetch('/latest');
                        const data = await response.json();
                        
                        if (data.filename) {{
                            screenshotImg.src = `/screenshots/${{data.filename}}?t=${{Date.now()}}`;
                            screenshotImg.alt = data.filename;
                            timestampEl.textContent = new Date(data.timestamp * 1000).toLocaleString();
                            filenameEl.textContent = data.filename;
                        }} else {{
                            screenshotImg.alt = 'No screenshots available';
                            timestampEl.textContent = 'N/A';
                            filenameEl.textContent = 'N/A';
                        }}
                    }} catch (error) {{
                        console.error('Error fetching latest screenshot:', error);
                    }}
                }}
                
                // Initial refresh
                refreshScreenshot();
                
                // Set up manual refresh
                refreshBtn.addEventListener('click', refreshScreenshot);
                
                // Set up auto-refresh
                autoRefreshBtn.addEventListener('click', () => {{
                    if (isAutoRefreshOn) {{
                        // Turn off auto-refresh
                        clearInterval(autoRefreshInterval);
                        autoRefreshStatus.textContent = 'Auto-refresh: Off';
                        isAutoRefreshOn = false;
                    }} else {{
                        // Turn on auto-refresh
                        autoRefreshInterval = setInterval(refreshScreenshot, 1000);
                        autoRefreshStatus.textContent = 'Auto-refresh: On (1s)';
                        isAutoRefreshOn = true;
                    }}
                }});
            </script>
        </body>
        </html>
        """.format(self.screenshot_dir)
        
        return html
    
    def _get_latest_screenshot(self):
        """Get the latest screenshot information"""
        if not self.screenshot_dir or not os.path.exists(self.screenshot_dir):
            return {"error": "Screenshot directory not found"}
        
        # Find all PNG files in the screenshot directory
        try:
            screenshot_files = [f for f in os.listdir(self.screenshot_dir) 
                                if f.endswith('.png') and os.path.isfile(os.path.join(self.screenshot_dir, f))]
        except Exception as e:
            return {"error": f"Error listing directory: {str(e)}"}
        
        if not screenshot_files:
            return {"error": "No screenshots found"}
        
        # Sort by modification time (newest first)
        screenshot_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshot_dir, x)), reverse=True)
        
        latest_file = screenshot_files[0]
        latest_path = os.path.join(self.screenshot_dir, latest_file)
        mtime = os.path.getmtime(latest_path)
        
        return {
            "filename": latest_file,
            "path": latest_path,
            "timestamp": mtime
        }


class PreviewServer:
    """Server for preview page"""
    
    def __init__(self, screenshot_dir: str, port: int = DEFAULT_PORT):
        self.screenshot_dir = screenshot_dir
        self.port = port
        self.httpd = None
        self.server_thread = None
    
    def start(self):
        """Start the preview server in a background thread"""
        # Create handler class with screenshot_dir
        handler = lambda *args, **kwargs: PreviewHandler(*args, screenshot_dir=self.screenshot_dir, **kwargs)
        
        try:
            # Try to start server
            self.httpd = socketserver.TCPServer(("", self.port), handler)
            self.server_thread = threading.Thread(target=self._run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"Preview server started on http://localhost:{self.port}")
            return self.port
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"Port {self.port} is already in use. Trying another port...")
                
                # Port is in use, try another port
                for port_attempt in range(self.port + 1, self.port + 10):
                    try:
                        self.port = port_attempt
                        self.httpd = socketserver.TCPServer(("", self.port), handler)
                        self.server_thread = threading.Thread(target=self._run_server)
                        self.server_thread.daemon = True
                        self.server_thread.start()
                        print(f"Preview server started on http://localhost:{self.port}")
                        return self.port
                    except OSError:
                        continue
                
                # Could not find an open port
                print("Could not start preview server: all ports in range are in use")
                return None
            else:
                print(f"Error starting preview server: {e}")
                return None
    
    def _run_server(self):
        """Run the server in the background thread"""
        try:
            self.httpd.serve_forever()
        except Exception as e:
            print(f"Preview server error: {e}")
    
    def stop(self):
        """Stop the preview server"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print(f"Preview server stopped on port {self.port}")


def start_preview(screenshot_dir: str, port: int = DEFAULT_PORT) -> Optional[int]:
    """Start a preview server for the given screenshot directory
    
    Args:
        screenshot_dir: Directory containing screenshots
        port: Port number to use for the server
    
    Returns:
        The port number of the started server, or None if failed
    """
    global running_servers
    
    # Create absolute path for screenshot directory
    screenshot_dir_path = Path(screenshot_dir).absolute()
    if not screenshot_dir_path.exists():
        os.makedirs(screenshot_dir_path, exist_ok=True)
    
    # Check if we already have a server for this directory
    server_key = str(screenshot_dir_path)
    if server_key in running_servers:
        existing_server = running_servers[server_key]
        if existing_server.server_thread and existing_server.server_thread.is_alive():
            return existing_server.port
    
    # Start a new server
    server = PreviewServer(str(screenshot_dir_path), port)
    port = server.start()
    
    if port:
        running_servers[server_key] = server
        return port
    
    return None


def stop_preview(screenshot_dir: str) -> bool:
    """Stop the preview server for the given directory
    
    Args:
        screenshot_dir: Directory that the server is serving screenshots from
    
    Returns:
        True if server was stopped, False otherwise
    """
    global running_servers
    
    screenshot_dir_path = Path(screenshot_dir).absolute()
    server_key = str(screenshot_dir_path)
    
    if server_key in running_servers:
        server = running_servers[server_key]
        server.stop()
        del running_servers[server_key]
        return True
    
    return False


def stop_all_previews():
    """Stop all running preview servers"""
    global running_servers
    
    for server_key, server in list(running_servers.items()):
        server.stop()
    
    running_servers = {}


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        # Use the provided directory
        screenshot_dir = sys.argv[1]
    else:
        # Use a default directory
        screenshot_dir = "data/screenshots"
    
    print(f"Starting preview server for {screenshot_dir}")
    port = start_preview(screenshot_dir)
    
    if port:
        print(f"Preview available at http://localhost:{port}")
        print("Press Ctrl+C to stop server")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping server...")
            stop_all_previews()
    else:
        print("Failed to start preview server")
