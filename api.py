from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'message': 'ColorBot API is running!',
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'path': self.path
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'message': 'POST request received',
            'timestamp': datetime.now().isoformat(),
            'path': self.path
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
