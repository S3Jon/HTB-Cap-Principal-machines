#!/bin/bash
docker build --no-cache -t htb-cap . && docker run -d --privileged --name cap -p 8181:80 -p 2200:22 -p 2100:21 htb-cap
echo ""
echo "✓ La página está lista: http://localhost:8181"
echo ""
