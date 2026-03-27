# api/chat.py
# Required for Vercel: Place this in /api/chat.py
# This handles the streaming chat completion securely.

import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not OPENROUTER_API_KEY:
            self.send_error(500, "API Key not configured")
            return

        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            
            model = post_data.get('model')
            message = post_data.get('message')
            
            if not model or not message:
                self.send_error(400, "Missing model or message")
                return

            # Prepare payload for OpenRouter
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": True
            }
            
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                method="POST"
            )

            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Stream response
            with urllib.request.urlopen(req, timeout=60) as response:
                while True:
                    chunk = response.readline()
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
                    
        except Exception as e:
            error_msg = json.dumps({"error": str(e)}).encode()
            self.wfile.write(f"data: {error_msg}\n\n".encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
