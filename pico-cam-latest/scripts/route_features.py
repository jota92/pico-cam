#!/usr/bin/env python3
"""
Complete unconnected traces left by add_features.py:

1. Fix LED_PWR_A: delete bad partial trace, route around R12.pad1
2. Fix LED_WIFI_A: delete bad partial trace, route around LED3.pad1
3. Delete VBAT traces that short-circuit U2.3 (now TPS_EN)
4. Route TPS_EN: SW2.pad2 → U2.3 via In2.Cu
5. Route VBAT: SW2.pad3 → C4.1 via In2.Cu
6. Route LED_WIFI: U1.36 → R13.pad1 via B.Cu
7. SW2.pad1 GND connects via F.Cu/B.Cu GND zone fill (no explicit trace needed)
"""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "device_kicad" / "CameraIoT_38x18_routed.kicad_pcb"

# Layer IDs in this 4-layer board
F_CU   = pcbnew.F_Cu    # 0
B_CU   = pcbnew.B_Cu    # 31 (pcbnew constant)
IN1_CU = 4              # In1.Cu (GND plane)
IN2_CU = 6              # In2.Cu (signal layer)


def mm(v):
    return pcbnew.FromMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def get_net(b, net_name):
    net = b.FindNet(net_name)
    try:
        code = net.GetNetCode()
        if code <= 0:
            return None
        return net
    except AttributeError:
        return None


def seg(b, net_name, layer, x1, y1, x2, y2, width=0.15):
    net = get_net(b, net_name)
    if net is None:
        print(f"  WARNING: net '{net_name}' not found")
        return
    t = pcbnew.PCB_TRACK(b)
    t.SetNet(net)
    t.SetLayer(layer)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(mm(width))
    b.Add(t)


def via(b, net_name, x, y, drill=0.3, size=0.6):
    """Add through-hole via on all copper layers."""
    net = get_net(b, net_name)
    if net is None:
        print(f"  WARNING: via net '{net_name}' not found")
        return
    v = pcbnew.PCB_VIA(b)
    v.SetNet(net)
    v.SetPosition(xy(x, y))
    v.SetDrillDefault()
    v.SetWidth(mm(size))
    v.SetDrill(mm(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v)


def collect_bad_tracks(b, specs, tol=0.05):
    """Collect tracks matching (net, layer, x1,y1,x2,y2) specs. Returns list."""
    spec_set = []
    for net_name, layer, x1, y1, x2, y2 in specs:
        spec_set.append((net_name, layer, x1, y1, x2, y2))

    to_del = []
    all_tracks = list(b.GetTracks())  # snapshot before any mutation
    for t in all_tracks:
        try:
            cls = t.GetClass()
        except Exception:
            continue
        if cls != "PCB_TRACK":
            continue
        tnet = t.GetNetname()
        tlay = t.GetLayer()
        s = t.GetStart()
        e = t.GetEnd()
        sx, sy = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        ex, ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        for net_name, layer, x1, y1, x2, y2 in spec_set:
            if tnet != net_name or tlay != layer:
                continue
            match_fwd = (abs(sx-x1)<tol and abs(sy-y1)<tol and
                         abs(ex-x2)<tol and abs(ey-y2)<tol)
            match_rev = (abs(sx-x2)<tol and abs(sy-y2)<tol and
                         abs(ex-x1)<tol and abs(ey-y1)<tol)
            if match_fwd or match_rev:
                to_del.append(t)
                break
    return to_del


def main():
    b = pcbnew.LoadBoard(str(BOARD))

    # ── 1-3. Collect and delete all bad traces at once ─────────────────────
    bad = collect_bad_tracks(b, [
        ("LED_PWR_A", F_CU, 6.25, 14.80, 6.75, 14.80),   # short to R12.pad1
        ("LED_WIFI_A", F_CU, 4.25, 16.30, 4.75, 16.30),  # short to LED3.pad1
        ("VBAT", F_CU, 24.50, 8.30, 24.50, 8.70),        # through U2.3 (now TPS_EN)
        ("VBAT", F_CU, 24.50, 8.70, 24.50, 9.00),        # through U2.3 (now TPS_EN)
    ])
    print(f"Deleting {len(bad)} bad track(s)...")
    for t in bad:
        b.Delete(t)
    print("Bad tracks deleted")

    # ── LED_PWR_A: route around R12.pad1 (detour above, y=14.30) ──────────
    seg(b, "LED_PWR_A", F_CU, 6.25, 14.80, 6.25, 14.30)
    seg(b, "LED_PWR_A", F_CU, 6.25, 14.30, 7.65, 14.30)
    seg(b, "LED_PWR_A", F_CU, 7.65, 14.30, 7.65, 14.80)
    print("LED_PWR_A routed (detour above R12)")

    # ── LED_WIFI_A: route around LED3.pad1 (detour above, y=15.80) ────────
    seg(b, "LED_WIFI_A", F_CU, 4.25, 16.30, 4.25, 15.80)
    seg(b, "LED_WIFI_A", F_CU, 4.25, 15.80, 6.25, 15.80)
    seg(b, "LED_WIFI_A", F_CU, 6.25, 15.80, 6.25, 16.30)
    print("LED_WIFI_A routed (detour above LED3)")

    # ── 4. Route TPS_EN: SW2.pad2 (6.5,17.2) → U2.3 (24.5,8.7) ──────────
    # Use In2.Cu (clear of CAM traces and 3V3 diagonal on B.Cu)
    # Path: F.Cu stub → via → In2.Cu vertical+horizontal → via → F.Cu to U2.3
    seg(b, "TPS_EN", F_CU,   6.5, 17.2,  6.5, 16.9)   # stub to via
    via(b, "TPS_EN",          6.5, 16.9)
    seg(b, "TPS_EN", IN2_CU,  6.5, 16.9,  6.5,  9.0)   # up left side
    seg(b, "TPS_EN", IN2_CU,  6.5,  9.0, 24.0,  9.0)   # right at y=9
    via(b, "TPS_EN",          24.0,  9.0)
    seg(b, "TPS_EN", F_CU,   24.0,  9.0, 24.0,  8.7)   # up to U2.3 level
    seg(b, "TPS_EN", F_CU,   24.0,  8.7, 24.5,  8.7)   # right to U2.3
    print("TPS_EN routed via In2.Cu")

    # ── 5. Route VBAT: SW2.pad3 (8.5,17.2) → C4.1/VBAT at (23.31,7.75) ──
    # Use In2.Cu at y=9.5 (clear of WAKE_BUTTON ending at y=8.96, LNA_IN)
    seg(b, "VBAT", F_CU,   8.5, 17.2,  8.5, 16.7)     # stub to via
    via(b, "VBAT",          8.5, 16.7)
    seg(b, "VBAT", IN2_CU,  8.5, 16.7,  8.5,  9.5)     # up left side
    seg(b, "VBAT", IN2_CU,  8.5,  9.5, 23.31, 9.5)     # right at y=9.5
    via(b, "VBAT",          23.31, 9.5)
    seg(b, "VBAT", F_CU,   23.31, 9.5, 23.31, 7.75)    # up to C4.1 VBAT net
    print("VBAT (SW2.pad3) routed to C4.1 via In2.Cu")

    # ── 6. Route LED_WIFI: U1.36 (21.298,9.189) → R13.pad1 (3.35,16.30) ──
    # Use B.Cu below LED_STATUS (at y=15.65) but above LED3/R13 row (y=16.3)
    # Going via y=16.2 (clear of all B.Cu diagonals at that y)
    seg(b, "LED_WIFI", F_CU,  21.298, 9.189, 19.8,  9.189)   # left from U1.36
    seg(b, "LED_WIFI", F_CU,  19.8,   9.189, 19.8,  13.5)    # down on F.Cu
    via(b, "LED_WIFI",         19.8,  13.5)
    seg(b, "LED_WIFI", B_CU,  19.8,  13.5,  18.5,  13.5)    # step left on B.Cu
    seg(b, "LED_WIFI", B_CU,  18.5,  13.5,  18.5,  16.2)    # down on B.Cu
    seg(b, "LED_WIFI", B_CU,  18.5,  16.2,   3.35, 16.2)    # left to destination
    via(b, "LED_WIFI",          3.35, 16.2)
    seg(b, "LED_WIFI", F_CU,   3.35, 16.2,   3.35, 16.30)   # short stub to R13.pad1
    print("LED_WIFI routed via B.Cu")

    # ── 7. Refill zones ────────────────────────────────────────────────────
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    print("Zone fill done")

    # ── 8. Connectivity check ──────────────────────────────────────────────
    conn = b.GetConnectivity()
    conn.RecalculateRatsnest()
    uc = conn.GetUnconnectedCount(False)
    print(f"\nUnconnected count: {uc}")
    if uc <= 1:
        print("  OK: only known false-positive zone ratsnest remains")
    else:
        print(f"  Still {uc} unconnected (check DRC for details)")

    pcbnew.SaveBoard(str(BOARD), b)
    print(f"\nBoard saved: {BOARD}")


if __name__ == "__main__":
    main()
