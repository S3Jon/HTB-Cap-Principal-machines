#!/usr/bin/env python3
"""
Principal HTB Machine - Vulnerable web application
CVE-2026-29000: JWE wrapping a PlainJWT bypasses signature verification
"""
import json
import time
import base64
import os
from flask import Flask, request, jsonify, redirect, send_from_directory
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from jwcrypto import jwk, jwe, jwt as jwcrypto_jwt
import jwt as pyjwt

app = Flask(__name__, static_folder="/app/static")

# ─── Generate RSA key pair on startup ───
RSA_KEY = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)
RSA_PUB = RSA_KEY.public_key()

# Convert to JWK for jwcrypto
_priv_pem = RSA_KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption()
)
_pub_pem = RSA_PUB.public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo
)
JWK_PRIVATE = jwk.JWK.from_pem(_priv_pem)
JWK_PUBLIC  = jwk.JWK.from_pem(_pub_pem)
JWK_PUBLIC["kid"] = "enc-key-1"
JWK_PRIVATE["kid"] = "enc-key-1"

# RS256 signing key (separate - not exposed via JWKS)
RS256_SECRET = "super-secret-signing-key-not-exposed"

USERS = {
    "admin":      {"password": "AdminP@ss2025!", "role": "ROLE_ADMIN",    "name": "Sarah Chen",       "dept": "IT Security",  "status": "Active"},
    "svc-deploy": {"password": "D3pl0y_$$H_Now42!", "role": "deployer",   "name": "Deploy Service",   "dept": "DevOps",       "status": "Active"},
    "jthompson":  {"password": "jthompson2025",  "role": "ROLE_USER",    "name": "James Thompson",   "dept": "Engineering",  "status": "Active"},
    "amorales":   {"password": "amorales2025",   "role": "ROLE_USER",    "name": "Ana Morales",      "dept": "Engineering",  "status": "Active"},
    "bwright":    {"password": "bwright2025",    "role": "ROLE_MANAGER", "name": "Benjamin Wright",  "dept": "Operations",   "status": "Active"},
    "kkumar":     {"password": "kkumar2025",     "role": "ROLE_ADMIN",   "name": "Kavitha Kumar",    "dept": "IT Security",  "status": "Disabled"},
    "mwilson":    {"password": "mwilson2025",    "role": "ROLE_USER",    "name": "Marcus Wilson",    "dept": "QA",           "status": "Active"},
    "lzhang":     {"password": "lzhang2025",     "role": "ROLE_MANAGER", "name": "Lisa Zhang",       "dept": "Engineering",  "status": "Active"},
}

def b64url_decode(s):
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def verify_token(token):
    """
    CVE-2026-29000 vulnerable implementation:
    1. Decrypt JWE envelope
    2. Extract inner payload
    3. If inner payload has alg:none (PlainJWT), toSignedJWT() returns null
    4. Signature check is skipped when signedJWT is null
    """
    try:
        # Step 1: Try JWE decryption
        jwe_token = jwe.JWE()
        jwe_token.deserialize(token, key=JWK_PRIVATE)
        inner = jwe_token.payload.decode()

        # Step 2: Parse the inner token
        parts = inner.split(".")
        if len(parts) != 3:
            return None, "Invalid token format"

        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        signature = parts[2]

        # Step 3: VULNERABLE CHECK - CVE-2026-29000
        # If alg is "none", this is a PlainJWT -> signedJWT would be null
        # Signature verification is skipped entirely
        alg = header.get("alg", "").lower()
        if alg == "none":
            # BUG: should reject, but instead skips signature verification
            signed_jwt = None  # toSignedJWT() returns null for PlainJWT
        else:
            signed_jwt = inner  # normal signed JWT

        # Step 4: Vulnerable gate - only verifies if signedJWT != null
        if signed_jwt is not None:
            # Verify RS256 signature (only reached for properly signed tokens)
            try:
                payload = pyjwt.decode(inner, RS256_SECRET, algorithms=["RS256"])
            except Exception:
                return None, "Invalid signature"

        # Verify expiration (this check still happens)
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None, "Token expired"

        return payload, None

    except Exception as e:
        return None, str(e)

def get_auth_payload(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "No token"
    token = auth[7:]
    return verify_token(token)

# ─── Routes ───

@app.route("/")
def root():
    return redirect("/login")

@app.route("/login")
def login_page():
    return send_from_directory("/app/static", "index.html")

@app.route("/dashboard")
def dashboard_page():
    return send_from_directory("/app/static", "dashboard.html")

@app.route("/users")
def users_page():
    return send_from_directory("/app/static", "dashboard.html")

@app.route("/settings")
def settings_page():
    return send_from_directory("/app/static", "dashboard.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("/app/static", filename)

@app.route("/api/auth/jwks")
def jwks():
    """Expose RSA public key for JWE encryption (NOT the signing key)."""
    pub_dict = json.loads(JWK_PUBLIC.export_public())
    pub_dict["kid"] = "enc-key-1"
    return jsonify({"keys": [pub_dict]})

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    now = int(time.time())
    claims = {
        "sub": username,
        "role": user["role"],
        "iss": "principal-platform",
        "iat": now,
        "exp": now + 3600,
    }
    # Sign with RS256 (legitimate token)
    inner_signed = pyjwt.encode(claims, RS256_SECRET, algorithm="RS256")
    # Wrap in JWE
    jwe_tok = jwe.JWE(
        inner_signed.encode() if isinstance(inner_signed, str) else inner_signed,
        recipient=JWK_PUBLIC,
        protected=json.dumps({
            "alg": "RSA-OAEP-256",
            "enc": "A128GCM",
            "kid": "enc-key-1",
            "cty": "JWT"
        })
    )
    return jsonify({"token": jwe_tok.serialize(compact=True)})

@app.route("/api/dashboard")
def dashboard():
    payload, err = get_auth_payload(request)
    if err:
        return jsonify({"error": err}), 401
    return jsonify({
        "user": {"username": payload.get("sub"), "role": payload.get("role")},
        "stats": {"totalUsers": 8, "activeDeployments": 3, "systemHealth": "operational", "uptime": "99.7%"},
        "announcements": [
            {"title": "Maintenance Window", "body": "Scheduled maintenance on Jan 15 02:00-04:00 UTC.", "date": "2025-12-30"},
            {"title": "New SSH CA Rotation", "body": "SSH CA keys have been rotated. All deploy certificates issued before Dec 1 are revoked.", "date": "2025-12-15"},
        ]
    })

@app.route("/api/users")
def users():
    payload, err = get_auth_payload(request)
    if err:
        return jsonify({"error": err}), 401
    if payload.get("role") not in ("ROLE_ADMIN", "ROLE_MANAGER"):
        return jsonify({"error": "Forbidden"}), 403
    user_list = []
    for uname, udata in USERS.items():
        user_list.append({
            "username": uname,
            "name": udata["name"],
            "role": udata["role"],
            "department": udata["dept"],
            "status": udata["status"],
            "notes": {
                "svc-deploy": "Service account for automated deployments via SSH certificate auth.",
                "jthompson": "Team lead - backend services",
                "amorales": "Frontend developer",
                "bwright": "Operations manager",
                "kkumar": "Security analyst - on leave until Jan 6",
                "mwilson": "QA engineer",
                "lzhang": "Engineering director",
            }.get(uname, "")
        })
    return jsonify({"users": user_list})

@app.route("/api/settings")
def settings():
    payload, err = get_auth_payload(request)
    if err:
        return jsonify({"error": err}), 401
    if payload.get("role") != "ROLE_ADMIN":
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({
        "system": {
            "applicationName": "Principal Internal Platform",
            "version": "1.2.0",
            "environment": "production",
            "serverType": "Jetty 12.x (Embedded)",
            "javaVersion": "21.0.10"
        },
        "security": {
            "authFramework": "pac4j-jwt",
            "authFrameworkVersion": "6.0.3",
            "jwAlgorithm": "RS256",
            "jweAlgorithm": "RSA-OAEP-256",
            "jweEncryption": "A128GCM",
            "encryptionKey": "D3pl0y_$$H_Now42!",
            "tokenExpiry": "3600s",
            "sessionManagement": "stateless"
        },
        "infrastructure": {
            "sshCaPath": "/opt/principal/ssh/",
            "sshCertAuth": "enabled",
            "database": "H2 (embedded)",
            "notes": "SSH certificate auth configured for automation - see /opt/principal/ssh/ for CA config."
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
