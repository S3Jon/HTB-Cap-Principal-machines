#!/bin/bash
# =============================================================
#  HTB Lab Network Setup
#  Crea una red Docker aislada con IPs fijas para las máquinas
#  de examen, permitiendo usar nmap, ssh, etc. directamente.
#
#  Red:       172.20.0.0/24
#  cap:       172.20.0.10
#  principal: 172.20.0.20
#  Atacante:  172.20.0.99  (contenedor Kali opcional)
# =============================================================

BASEDIR="$(cd "$(dirname "$0")" && pwd)"

NETWORK_NAME="htblab"
SUBNET="172.20.0.0/24"
GATEWAY="172.20.0.1"
CAP_IP="172.20.0.10"
PRINCIPAL_IP="172.20.0.20"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

case "$1" in

  up)
    echo -e "${YELLOW}[*] Creando red Docker '$NETWORK_NAME'...${NC}"
    docker network create \
      --driver bridge \
      --subnet "$SUBNET" \
      --gateway "$GATEWAY" \
      "$NETWORK_NAME" 2>/dev/null \
      && echo -e "${GREEN}[+] Red creada${NC}" \
      || echo -e "${YELLOW}[!] La red ya existe${NC}"

    echo ""
    echo -e "${YELLOW}[*] Construyendo y arrancando cap (${CAP_IP})...${NC}"
    cd "$BASEDIR/cap" || exit 1
    docker build --no-cache -t htb-cap .
    docker run -d \
      --name cap \
      --network "$NETWORK_NAME" \
      --ip "$CAP_IP" \
      --privileged \
      htb-cap
    echo -e "${GREEN}[+] cap arrancado${NC}"

    echo ""
    echo -e "${YELLOW}[*] Construyendo y arrancando principal (${PRINCIPAL_IP})...${NC}"
    cd "$BASEDIR/principal" || exit 1
    docker build -t htb-principal .
    docker run -d \
      --name principal \
      --network "$NETWORK_NAME" \
      --ip "$PRINCIPAL_IP" \
      htb-principal
    echo -e "${GREEN}[+] principal arrancado${NC}"

    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Lab listo. IPs de las maquinas:${NC}"
    echo -e "${GREEN}    cap       -> ${CAP_IP}${NC}"
    echo -e "${GREEN}    principal -> ${PRINCIPAL_IP}${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "  nmap -sV ${CAP_IP}"
    echo "  nmap -sV ${PRINCIPAL_IP}"
    echo ""
    echo "  # Si nmap no llega desde el host directamente:"
    echo "  sh network_setup.sh shell   # abre Kali en la misma red"
    ;;

  down)
    echo -e "${YELLOW}[*] Parando y eliminando contenedores...${NC}"
    docker rm -f cap principal 2>/dev/null
    echo -e "${YELLOW}[*] Eliminando red '$NETWORK_NAME'...${NC}"
    docker network rm "$NETWORK_NAME" 2>/dev/null
    echo -e "${GREEN}[+] Lab eliminado${NC}"
    ;;

  shell)
    # Lanza un contenedor atacante Kali en la misma red htblab.
    # Desde aqui puedes hacer nmap, ssh, ftp, etc. a las IPs del lab.
    echo -e "${YELLOW}[*] Lanzando contenedor atacante Kali en la red ${NETWORK_NAME}...${NC}"
    echo -e "${YELLOW}    IP atacante: 172.20.0.99${NC}"
    echo ""
    docker run -it --rm \
      --name attacker \
      --network "$NETWORK_NAME" \
      --ip "172.20.0.99" \
      kalilinux/kali-rolling \
      bash -c "
        apt-get update -qq 2>/dev/null
        apt-get install -y -qq nmap netcat-openbsd openssh-client python3 python3-pip curl wget ftp wireshark-common 2>/dev/null
        echo ''
        echo '=== Contenedor atacante listo ==='
        echo 'cap:       ${CAP_IP}'
        echo 'principal: ${PRINCIPAL_IP}'
        echo ''
        bash
      "
    ;;

  status)
    echo -e "${YELLOW}[*] Contenedores activos:${NC}"
    docker ps --filter "name=cap" --filter "name=principal" --filter "name=attacker" \
      --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    echo ""
    echo -e "${YELLOW}[*] IPs en la red '$NETWORK_NAME':${NC}"
    docker network inspect "$NETWORK_NAME" \
      --format '{{range .Containers}}  {{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}' 2>/dev/null \
      || echo "  (red no existe, ejecuta: sh network_setup.sh up)"
    ;;

  *)
    echo "Uso: sh network_setup.sh {up|down|shell|status}"
    echo ""
    echo "  up      -> Construye imagenes y arranca el lab con IPs fijas"
    echo "  down    -> Para y elimina los contenedores y la red"
    echo "  shell   -> Abre un contenedor Kali atacante en la misma red"
    echo "  status  -> Muestra contenedores activos e IPs asignadas"
    echo ""
    echo "IPs del lab:"
    echo "  cap:       ${CAP_IP}   (HTTP:80, SSH:22, FTP:21)"
    echo "  principal: ${PRINCIPAL_IP}  (HTTP:8080, SSH:22)"
    ;;
esac
