#!/usr/bin/env python3
import subprocess
import time
import re

print("1. Avvio flusso ping ad alta frequenza (1 pacchetto ogni 20ms per 6 secondi)...")
ping_proc = subprocess.Popen(
    ["sudo", "docker", "exec", "clab-telco-backbone-ce-a1", "ping", "-i", "0.02", "-c", "250", "-I", "192.168.1.1", "192.168.1.2"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)

time.sleep(1.5)
print("2. [FAULT INJECTION] Abbattimento link primario Roma-Milano (p1:eth2)...")
t_down = time.time()
subprocess.run(["sudo", "docker", "exec", "clab-telco-backbone-p1", "ip", "link", "set", "eth2", "down"], check=True)

stdout, _ = ping_proc.communicate()

tx_match = re.search(r"(\d+) packets transmitted, (\d+) (?:packets )?received", stdout)
if tx_match:
    tx, rx = int(tx_match.group(1)), int(tx_match.group(2))
    lost = tx - rx
    convergence_ms = lost * 20
    print(f"\n--- RISULTATO FAILOVER IS-IS + BFD ---")
    print(f"Pacchetti inviati: {tx} | Ricevuti: {rx} | Persi durante il guasto: {lost}")
    print(f"Tempo di convergenza stimato (Reroute via P3 Napoli): ~{convergence_ms} ms")

print("\n3. Verifica nuovo percorso (Traceroute via P3 - 10.0.13.2):")
tr = subprocess.run(["sudo", "docker", "exec", "clab-telco-backbone-ce-a1", "traceroute", "-n", "-s", "192.168.1.1", "192.168.1.2"], capture_output=True, text=True)
print(tr.stdout)

print("4. Ripristino link primario p1:eth2...")
subprocess.run(["sudo", "docker", "exec", "clab-telco-backbone-p1", "ip", "link", "set", "eth2", "up"], check=True)
