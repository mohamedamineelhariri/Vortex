from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - MOCK BRAIN - %(message)s')
logger = logging.getLogger()

class MockBrainHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            logger.info(f"Received request: {json.dumps(data, indent=2)}")
            
            # Simulate a decision
            filename = data.get("filename", "unknown")
            
            response = {
                "category": "Documents",
                "confidence": 0.95,
                "suggested_name": f"organized_{filename}",
                "folder": "Documents/Organized",
                "tags": ["mock", "test"]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            logger.info(f"Sent response: {json.dumps(response)}")
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.send_response(500)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=MockBrainHandler, port=5678):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting Mock Brain on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
