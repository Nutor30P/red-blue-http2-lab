<div align="center">

# 🛡️ HTTP/2 Stealth Exfiltration & ML Detection Lab
### Red Team vs. Blue Team Simulation

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<p align="center">
  Un laboratorio de ciberseguridad que simula la exfiltración de datos mediante headers HTTP/2 personalizados y detecta anomalías utilizando Machine Learning (Isolation Forest).
</p>

</div>

---

## 📖 Descripción

Este proyecto implementa un escenario completo de ataque y defensa:
1.  **🔴 Red Team (Ataque):** Exfiltra archivos sensibles ocultando fragmentos en Base64 dentro de headers HTTP/2 (`X-File-Part`) a través de un proxy Nginx.
2.  **🔵 Blue Team (Defensa):** Captura el tráfico de red, extrae características estadísticas (entropía, longitud de headers) y entrena un modelo **Isolation Forest** para detectar la intrusión.

## 🏗️ Arquitectura

El flujo de ataque y defensa se visualiza de la siguiente manera:

```mermaid
graph LR
    A[🔴 Infected Client] -->|HTTP/2 Encrypted| B[Nginx Proxy]
    B -->|HTTP/1.1 Plain| C[🔴 C2 Server]
    D[🔵 Defender/Sniffer] -.->|PCAP Capture| A
    D -.->|PCAP Capture| B
    subgraph "Detección ML"
    E[Extract Features] --> F[Isolation Forest]
    end
