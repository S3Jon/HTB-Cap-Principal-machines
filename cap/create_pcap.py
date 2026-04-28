#!/usr/bin/env python3
"""Generate a PCAP file with plaintext FTP credentials for the Cap HTB machine."""
import os
from scapy.all import wrpcap, Raw
from scapy.layers.inet import IP, TCP
from scapy.layers.l2 import Ether

os.makedirs("/pcaps", exist_ok=True)

packets = []
client = "192.168.1.100"
server = "192.168.1.16"
base = Ether(src="aa:bb:cc:dd:ee:01", dst="aa:bb:cc:dd:ee:02")

def pkt(src, dst, sport, dport, payload, seq=1, ack=1):
    return base / IP(src=src, dst=dst) / TCP(sport=sport, dport=dport, flags="PA", seq=seq, ack=ack) / Raw(load=payload.encode())

packets.append(base / IP(src=server, dst=client) / TCP(sport=21, dport=54411, flags="PA", seq=1, ack=1) / Raw(load=b"220 (vsFTPd 3.0.3)\r\n"))
packets.append(pkt(client, server, 54411, 21, "USER nathan\r\n",          seq=1,  ack=20))
packets.append(pkt(server, client, 21, 54411, "331 Please specify the password.\r\n", seq=20, ack=14))
packets.append(pkt(client, server, 54411, 21, "PASS Buck3tH4TF0RM3!\r\n", seq=14, ack=55))
packets.append(pkt(server, client, 21, 54411, "230 Login successful.\r\n", seq=55, ack=36))
packets.append(pkt(client, server, 54411, 21, "SYST\r\n",                 seq=36, ack=78))
packets.append(pkt(server, client, 21, 54411, "215 UNIX Type: L8\r\n",    seq=78, ack=42))

wrpcap("/pcaps/capture_0.pcap", packets)
print("PCAP written to /pcaps/capture_0.pcap")
