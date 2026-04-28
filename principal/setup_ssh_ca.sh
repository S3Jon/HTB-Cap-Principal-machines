#!/bin/bash
# Setup SSH CA for Principal machine
# This runs at container build time

set -e

SSH_DIR="/opt/principal/ssh"
mkdir -p "$SSH_DIR"

# Generate the SSH CA key pair
ssh-keygen -t rsa -b 4096 -f "$SSH_DIR/ca" -N "" -C "principal-deploy-ca" > /dev/null 2>&1

# Create the README
cat > "$SSH_DIR/README.txt" << 'EOF'
CA keypair for SSH certificate automation.
This CA is trusted by sshd for certificate-based authentication.
Use deploy.sh to issue short-lived certificates for service accounts.

Key details:
  Algorithm: RSA 4096-bit
  Created: 2025-11-15
  Purpose: Automated deployment authentication
EOF

# Create the sshd config (VULNERABLE: TrustedUserCAKeys without AuthorizedPrincipalsFile)
cat > /etc/ssh/sshd_config.d/60-principal.conf << 'EOF'
# Principal machine SSH configuration
PubkeyAuthentication yes
PasswordAuthentication yes
PermitRootLogin prohibit-password
TrustedUserCAKeys /opt/principal/ssh/ca.pub
EOF

# Set permissions - deployers group can read CA private key (that's the vulnerability)
groupadd -f deployers
usermod -aG deployers svc-deploy

chown -R root:deployers "$SSH_DIR"
chmod 750 "$SSH_DIR"
chmod 640 "$SSH_DIR/ca"          # Group readable = deployers can read private key!
chmod 644 "$SSH_DIR/ca.pub"
chmod 640 "$SSH_DIR/README.txt"

echo "[+] SSH CA configured at $SSH_DIR"
echo "[+] Vulnerable sshd config written to /etc/ssh/sshd_config.d/60-principal.conf"
