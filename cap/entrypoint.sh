#!/bin/bash

# Start SSH
service ssh start

# Start FTP
service vsftpd start || true

# Start web app
cd /app
python3.8 app.py &

echo "[*] Cap machine ready!"
echo "[*] Web on :80  |  SSH on :22  |  FTP on :21"
echo "[*] User: nathan / Buck3tH4TF0RM3!"
echo "[*] PCAP disponible en /data/0"

tail -f /dev/null
