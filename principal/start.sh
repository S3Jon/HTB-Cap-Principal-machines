#!/bin/bash
docker build -t htb-principal . && docker run -d --name principal -p 8182:8080 -p 2222:22 htb-principal
echo ""
echo "✓ La página está lista: http://localhost:8182"
echo ""
