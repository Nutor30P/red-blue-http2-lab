#!/bin/bash
# run_analysis.sh
# Wrapper para ejecutar el análisis usando el entorno virtual correcto

# Obtener el directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PYTHON="$DIR/../venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[!] Error: No se encuentra el entorno virtual en $VENV_PYTHON"
    echo "[!] Ejecuta 'bash run_http2_lab.sh' en el directorio principal primero."
    exit 1
fi

echo "[*] Usando Python del entorno virtual: $VENV_PYTHON"

echo -e "\n=== 1. Extrayendo Features ==="
"$VENV_PYTHON" extract_features.py capture.pcap

if [ $? -eq 0 ]; then
    echo -e "\n=== 2. Entrenando Modelo ==="
    "$VENV_PYTHON" train_model.py
else
    echo "[!] Falló la extracción de features."
fi
