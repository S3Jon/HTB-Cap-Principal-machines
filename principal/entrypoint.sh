#!/bin/bash
set -e

# Regenerate SSH host keys if missing
ssh-keygen -A 2>/dev/null || true

# Start SSH daemon
/usr/sbin/sshd

# Start the vulnerable web application
cd /app
echo "[*] Starting Principal web app on :8080 ..."
python3 /app/app.py &

echo ""
echo "=========================================="
echo "  Principal HTB Machine - Ready"
echo "=========================================="
echo "  Web:  http://<IP>:8080"
echo "  SSH:  ssh svc-deploy@<IP>"
echo "  Pass: D3pl0y_\$\$H_Now42!"
echo "=========================================="
echo "  CVE-2026-29000: JWE+PlainJWT bypass"
echo "  PrivEsc: SSH CA cert forgery for root"
echo "=========================================="

tail -f /dev/null
