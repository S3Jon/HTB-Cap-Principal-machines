#!/usr/bin/env python3
"""Cap HTB - Vulnerable web application. Vulnerabilities: IDOR on /data/<id> + cap_setuid on python3."""
import os
import subprocess
import glob
from flask import Flask, send_file, jsonify, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

PCAP_DIR = "/pcaps"
os.makedirs(PCAP_DIR, exist_ok=True)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>Dashboard</title>
<style>
body{font-family:Arial,sans-serif;margin:0;display:flex;}
.sidebar{width:220px;background:#1a1a2e;color:white;min-height:100vh;padding:20px;}
.sidebar a{display:block;color:#ccc;text-decoration:none;padding:8px 0;font-size:14px;}
.sidebar a:hover{color:white;}
.content{padding:30px;flex:1;background:#f5f5f5;}
.card{background:white;padding:20px;margin:10px;border-radius:8px;display:inline-block;min-width:150px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.1);}
.card h2{margin:0;font-size:2em;color:#333;}
.card p{color:#888;margin:5px 0 0;}
h3{color:#333;}
pre{background:#1a1a2e;color:#00ff00;padding:15px;border-radius:5px;overflow-x:auto;}
table{width:100%;border-collapse:collapse;background:white;}
th,td{padding:10px;border:1px solid #ddd;text-align:left;}
th{background:#eee;}
.btn{background:#17a2b8;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;text-decoration:none;}
</style>
</head>
<body>
<div class="sidebar">
  <h3 style="color:white;">&#8962; Dashboard</h3>
  <a href="/dashboard">Dashboard</a>
  <a href="/capture">Security Snapshot (5 Second PCAP + Analysis)</a>
  <a href="/ip">IP Config</a>
  <a href="/netstat">Network Status</a>
</div>
<div class="content">
  {% block content %}{% endblock %}
</div>
</body>
</html>
"""

INDEX_HTML = DASHBOARD_HTML.replace("{% block content %}{% endblock %}", """
<h2>Dashboard</h2>
<div>
  <div class="card"><h2>1</h2><p>Security Events</p></div>
  <div class="card"><h2>0</h2><p>Failed Login Attempts</p></div>
  <div class="card"><h2>1</h2><p>Active Sessions</p></div>
</div>
<p>Logged in as: <b>nathan</b></p>
""")

IP_HTML = DASHBOARD_HTML.replace("{% block content %}{% endblock %}", """
<h2>IP Config</h2>
<pre>{{ ifconfig }}</pre>
""")

NETSTAT_HTML = DASHBOARD_HTML.replace("{% block content %}{% endblock %}", """
<h2>Network Status</h2>
<pre>{{ netstat }}</pre>
""")

DATA_HTML = DASHBOARD_HTML.replace("{% block content %}{% endblock %}", """
<h2>Security Snapshot - ID: {{ capture_id }}</h2>
<table>
  <tr><th>Data Type</th><th>Value</th></tr>
  <tr><td>Number of Packets</td><td>{{ stats.total }}</td></tr>
  <tr><td>Number of IP Packets</td><td>{{ stats.ip }}</td></tr>
  <tr><td>Number of TCP Packets</td><td>{{ stats.tcp }}</td></tr>
  <tr><td>Number of UDP Packets</td><td>{{ stats.udp }}</td></tr>
</table>
<br>
<a class="btn" href="/download/{{ capture_id }}">Download</a>
""")

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template_string(INDEX_HTML)

@app.route("/ip")
def ip_config():
    try:
        out = subprocess.check_output("ifconfig", shell=True, stderr=subprocess.STDOUT).decode()
    except Exception as e:
        out = str(e)
    return render_template_string(IP_HTML, ifconfig=out)

@app.route("/netstat")
def netstat():
    try:
        out = subprocess.check_output("netstat -an 2>/dev/null || ss -an", shell=True, stderr=subprocess.STDOUT).decode()
    except Exception as e:
        out = str(e)
    return render_template_string(NETSTAT_HTML, netstat=out)

@app.route("/capture")
def capture():
    """Create a new PCAP (live capture of 5 seconds) and redirect to /data/<id>."""
    # Count existing captures to get next ID (starts at 1 since 0 is pre-seeded)
    existing = glob.glob(f"{PCAP_DIR}/capture_*.pcap")
    next_id = len(existing)  # 0 is pre-seeded, so next will be 1, 2...
    outfile = f"{PCAP_DIR}/capture_{next_id}.pcap"
    try:
        # Short capture; in Docker we may not have traffic - that's fine
        subprocess.run(
            ["tcpdump", "-w", outfile, "-G", "5", "-W", "1", "-i", "any"],
            timeout=6, capture_output=True
        )
    except Exception:
        # Create empty pcap if tcpdump fails
        open(outfile, "wb").close()
    return redirect(f"/data/{next_id}")

@app.route("/data/<int:capture_id>")
def data(capture_id):
    """IDOR vulnerability: no ownership check on capture_id."""
    pcap_file = f"{PCAP_DIR}/capture_{capture_id}.pcap"
    stats = {"total": 0, "ip": 0, "tcp": 0, "udp": 0}
    if os.path.exists(pcap_file):
        try:
            from scapy.all import rdpcap, IP, TCP, UDP
            pkts = rdpcap(pcap_file)
            stats["total"] = len(pkts)
            stats["ip"] = sum(1 for p in pkts if IP in p)
            stats["tcp"] = sum(1 for p in pkts if TCP in p)
            stats["udp"] = sum(1 for p in pkts if UDP in p)
        except Exception:
            pass
    return render_template_string(DATA_HTML, capture_id=capture_id, stats=stats)

@app.route("/download/<int:capture_id>")
def download(capture_id):
    """IDOR vulnerability: no ownership check."""
    pcap_file = f"{PCAP_DIR}/capture_{capture_id}.pcap"
    if os.path.exists(pcap_file):
        return send_file(pcap_file, as_attachment=True, download_name=f"capture_{capture_id}.pcap")
    return "Not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
