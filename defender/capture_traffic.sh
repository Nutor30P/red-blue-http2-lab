#!/bin/bash
# capture_traffic.sh
# Captura tráfico y genera dataset para entrenamiento

set -e

INTERFACE="lo"
DURATION=30
PCAP_FILE="capture.pcap"
LOG_DIR="../logs"

mkdir -p $LOG_DIR

echo "[*] Iniciando captura de tráfico en $INTERFACE por $DURATION segundos..."
echo "[*] Archivo de salida: $PCAP_FILE"

# Iniciar tcpdump en background
sudo tcpdump -i $INTERFACE -w $PCAP_FILE -s 0 tcp port 8000 or tcp port 443 > /dev/null 2>&1 &
TCPDUMP_PID=$!

echo "[*] Generando tráfico NORMAL..."
# Generar tráfico normal (peticiones legítimas)
for i in {1..10}; do
    curl -k -s "https://c2.malicious.local/beacon" > /dev/null
    curl -k -s "https://c2.malicious.local/" > /dev/null
    sleep 1
done

echo "[*] Generando tráfico MALICIOSO (Exfiltración)..."
# Ejecutar cliente de exfiltración
cd ..
source venv/bin/activate
python3 exfil_client.py > /dev/null 2>&1
cd defender

echo "[*] Finalizando captura..."
sleep 2
sudo kill $TCPDUMP_PID
echo "[✓] Captura completada: $PCAP_FILE"
