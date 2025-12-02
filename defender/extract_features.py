#!/usr/bin/env python3
# extract_features.py
import subprocess
import json
import math
import csv
import sys
import os

def calculate_entropy(text):
    """Calcula la entropía de Shannon de un string"""
    if not text:
        return 0
    entropy = 0
    for x in range(256):
        p_x = float(text.count(chr(x))) / len(text)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

def run_tshark(pcap_file):
    """Ejecuta tshark para extraer campos HTTP y HTTP2"""
    # Extraemos headers y tamaño de frame para ambos protocolos
    cmd = [
        'tshark', '-r', pcap_file,
        '-Y', 'http or http2',
        '-T', 'json',
        '-e', 'frame.time_epoch',
        '-e', 'http.request.line', # Headers HTTP/1.1 raw
        '-e', 'http.content_length',
        '-e', 'http2.header.name',
        '-e', 'http2.header.value',
        '-e', 'http2.length'
    ]
    
    print(f"[*] Ejecutando tshark en {pcap_file}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[!] Error decodificando salida de tshark: {e}")
        # print(f"[!] Primeros 500 caracteres de la salida:\n{result.stdout[:500]}")
        return []

def extract_features(packets):
    features = []
    
    print(f"[*] Procesando {len(packets)} paquetes...")
    
    for packet in packets:
        try:
            layers = packet['_source']['layers']
            
            header_names = []
            header_values = []
            
            # 1. Procesar HTTP/1.1 (http.request.line)
            http1_lines = layers.get('http.request.line', [])
            if not isinstance(http1_lines, list): http1_lines = [http1_lines]
            
            for line in http1_lines:
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    header_names.append(parts[0].strip())
                    header_values.append(parts[1].strip())
            
            # 2. Procesar HTTP/2
            h2_names = layers.get('http2.header.name', [])
            h2_values = layers.get('http2.header.value', [])
            
            if not isinstance(h2_names, list): h2_names = [h2_names]
            if not isinstance(h2_values, list): h2_values = [h2_values]
            
            header_names.extend(h2_names)
            header_values.extend(h2_values)
            
            # Longitud del contenido
            length_val = layers.get('http.content_length', layers.get('http2.length', [0]))
            frame_len = int(length_val[0]) if length_val else 0
            
            # Feature 1: Max Entropy en headers
            max_entropy = 0
            suspicious_headers_count = 0
            total_header_len = 0
            
            for name, value in zip(header_names, header_values):
                if not value: continue
                h_entropy = calculate_entropy(value)
                max_entropy = max(max_entropy, h_entropy)
                total_header_len += len(value)
                
                # Feature 2: Headers sospechosos (X-*)
                if name and (name.startswith('x-') or name.startswith('X-')):
                    suspicious_headers_count += 1
            
            # Feature 3: Ratio Header/Body
            ratio = total_header_len / frame_len if frame_len > 0 else 0
            
            features.append({
                'max_entropy': max_entropy,
                'suspicious_headers': suspicious_headers_count,
                'total_header_len': total_header_len,
                'frame_len': frame_len,
                'ratio': ratio,
                'is_malicious': 1 if suspicious_headers_count > 2 or max_entropy > 4.5 else 0
            })
            
        except Exception as e:
            continue
            
    return features

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 extract_features.py <capture.pcap>")
        sys.exit(1)
        
    pcap_file = sys.argv[1]
    packets = run_tshark(pcap_file)
    
    if not packets:
        print("[!] No se encontraron paquetes HTTP/HTTP2 en la captura.")
        print("[!] Asegúrate de que la captura se realizó correctamente y contiene tráfico.")
        return

    data = extract_features(packets)
    
    if not data:
        print("[!] No se pudieron extraer features de los paquetes.")
        return
    
    output_file = "features.csv"
    keys = data[0].keys()
    
    with open(output_file, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
        
    print(f"[✓] Features extraídas en {output_file} ({len(data)} registros)")

if __name__ == '__main__':
    main()
