import subprocess
import time

LAB = "clab-telco-backbone"

def run_cmd(node, *args):
    res = subprocess.run(
        ["docker", "exec", f"{LAB}-{node}", *args],
        capture_output=True, text=True, timeout=30,
    )
    return res.returncode, res.stdout + res.stderr

def vtysh(node, cmd):
    return run_cmd(node, "vtysh", "-c", cmd)

def wait_until(check, timeout=60, interval=2):
    end = time.time() + timeout
    while time.time() < end:
        if check():
            return True
        time.sleep(interval)
    return False

def test_isis_adjacencies():
    def ok():
        _, out = vtysh("p1", "show isis neighbor")
        return all(n in out for n in ("p2", "p3", "pe1")) and out.count("Up") >= 3
    assert wait_until(ok), vtysh("p1", "show isis neighbor")[1]

def test_ldp_labels_populated():
    def ok():
        _, out = vtysh("pe1", "show mpls table")
        return "LDP" in out
    assert wait_until(ok), vtysh("pe1", "show mpls table")[1]

def test_vpn_labels_populated():
    # label VPN allocata da bgpd per le VRF locali
    _, out = vtysh("pe1", "show mpls table")
    assert "BGP" in out, out

def test_rr_vpnv4_routes():
    def ok():
        _, out = vtysh("rr1", "show bgp ipv4 vpn")
        return "65000:100" in out and "65000:200" in out
    assert wait_until(ok), vtysh("rr1", "show bgp ipv4 vpn")[1]

def test_customer_a_connectivity():
    rc, out = run_cmd("ce-a1", "ping", "-c", "3", "-W", "1", "-I", "192.168.1.1", "192.168.1.2")
    assert rc == 0 and "0% packet loss" in out, out

def test_customer_b_connectivity():
    rc, out = run_cmd("ce-b1", "ping", "-c", "3", "-W", "1", "-I", "192.168.1.1", "192.168.1.2")
    assert rc == 0 and "0% packet loss" in out, out