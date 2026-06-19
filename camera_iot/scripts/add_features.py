#!/usr/bin/env python3
"""
Add missing features to CameraIoT_38x18_routed.kicad_pcb:

1. SW2 (SPDT slide switch) on TPS63031 EN pin for main power off
   - SW2.1 = GND  (slide OFF: EN→GND → TPS disabled → device OFF)
   - SW2.2 = TPS_EN (COM, connected to U2.3 which was VBAT=always-on)
   - SW2.3 = VBAT  (slide ON: EN→VBAT → TPS enabled → device ON)

2. LED2 (red 0603): power indicator, always on via 3V3→R12→LED2→GND
   R12 (1k 0402): current limiter for LED2

3. LED3 (green 0603): WiFi/success status, GPIO-driven via U1.36→R13→LED3→GND
   R13 (1k 0402): current limiter for LED3

4. Silkscreen cleanup: uniform text size, move refs off pads

5. Update U2.3 net: VBAT → TPS_EN (new net)
   Update U1.36: unassigned → LED_WIFI (new net)
"""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "device_kicad" / "CameraIoT_38x18_routed.kicad_pcb"


def mm(v):
    return pcbnew.FromMM(v)


def add_net(b, name):
    existing = b.FindNet(name)
    if existing and existing.GetNetCode() > 0:
        return existing
    ni = pcbnew.NETINFO_ITEM(b, name)
    b.Add(ni)
    return b.FindNet(name)


def clone_fp(b, src_ref, new_ref, new_val, x, y, pad_nets, orientation=0):
    """Clone existing footprint, relocate, rename, reassign nets."""
    src = next(f for f in b.GetFootprints() if f.GetReference() == src_ref)
    clone = pcbnew.Cast_to_FOOTPRINT(src.Duplicate(False))
    clone.SetReference(new_ref)
    clone.SetValue(new_val)
    clone.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    clone.SetOrientationDegrees(orientation)
    for pad in clone.Pads():
        pn = pad.GetNumber()
        if pn in pad_nets:
            net = b.FindNet(pad_nets[pn])
            if net and net.GetNetCode() > 0:
                pad.SetNet(net)
    b.Add(clone)
    return clone


def create_switch_fp(b, ref, val, cx, cy, net_gnd, net_com, net_vbat):
    """
    Create 3-pad SMD slide switch footprint (MSK-12C02 / SS-12D00 compatible).
    Pads in a row with 2.0mm pitch:
      pad1 = net_gnd  (left,  OFF position)
      pad2 = net_com  (center, COM)
      pad3 = net_vbat (right, ON position)
    """
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
    fp.SetLayer(pcbnew.F_Cu)

    # Reference text
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.4), mm(0.4)))
    fp.Reference().SetTextThickness(mm(0.06))
    fp.Reference().SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy - 1.8)))
    fp.Reference().SetLayer(pcbnew.F_SilkS)

    # Value text
    fp.Value().SetTextSize(pcbnew.VECTOR2I(mm(0.4), mm(0.4)))
    fp.Value().SetTextThickness(mm(0.06))
    fp.Value().SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy + 1.8)))
    fp.Value().SetLayer(pcbnew.F_Fab)

    pad_defs = [
        ("1", -2.0, net_gnd),
        ("2",  0.0, net_com),
        ("3", +2.0, net_vbat),
    ]
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.F_Paste)
    ls.AddLayer(pcbnew.F_Mask)

    for num, x_off, net_name in pad_defs:
        pad = pcbnew.PAD(fp)
        pad.SetNumber(num)
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetLayerSet(ls)
        pad.SetSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
        pad.SetPosition(pcbnew.VECTOR2I(mm(cx + x_off), mm(cy)))
        net = b.FindNet(net_name)
        if net and net.GetNetCode() > 0:
            pad.SetNet(net)
        fp.Add(pad)

    b.Add(fp)
    return fp


def fix_silkscreen(b):
    """Move all reference texts to clear position above the component bbox."""
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        # Skip test pads and mounting holes
        if ref.startswith("TP") or ref.startswith("MH") or ref.startswith("BAT"):
            fp.Reference().SetVisible(False)
            continue

        ref_t = fp.Reference()
        ref_t.SetTextSize(pcbnew.VECTOR2I(mm(0.4), mm(0.4)))
        ref_t.SetTextThickness(mm(0.06))

        # Place reference above component centroid
        cx = pcbnew.ToMM(fp.GetPosition().x)
        cy = pcbnew.ToMM(fp.GetPosition().y)
        ref_t.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy - 1.0)))
        ref_t.SetLayer(pcbnew.F_SilkS)
        ref_t.SetMirrored(False)


def add_short_trace(b, net_name, layer, x1, y1, x2, y2, width=0.15):
    """Add a copper trace segment."""
    net = b.FindNet(net_name)
    if not net or net.GetNetCode() <= 0:
        print(f"  WARNING: net '{net_name}' not found for trace")
        return
    seg = pcbnew.PCB_TRACK(b)
    seg.SetNet(net)
    seg.SetLayer(layer)
    seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    seg.SetWidth(mm(width))
    b.Add(seg)


def main():
    b = pcbnew.LoadBoard(str(BOARD))

    # ── 1. Create new nets ──────────────────────────────────────────────────
    tps_en = add_net(b, "TPS_EN")
    led_wifi = add_net(b, "LED_WIFI")
    led_pwr_a = add_net(b, "LED_PWR_A")
    led_wifi_a = add_net(b, "LED_WIFI_A")
    print("New nets created: TPS_EN, LED_WIFI, LED_PWR_A, LED_WIFI_A")

    # ── 2. Change U2.3 from VBAT → TPS_EN ──────────────────────────────────
    # U2 (TPS63031) pad3 = EN pin (was tied to VBAT for always-on)
    for fp in b.GetFootprints():
        if fp.GetReference() == "U2":
            for pad in fp.Pads():
                if pad.GetNumber() == "3":
                    pad.SetNet(tps_en)
                    print(f"U2.3: VBAT → TPS_EN")

    # ── 3. Assign LED_WIFI to U1 pad36 (adjacent to LED_STATUS=pad37) ──────
    for fp in b.GetFootprints():
        if fp.GetReference() == "U1":
            for pad in fp.Pads():
                if pad.GetNumber() == "36":
                    pad.SetNet(led_wifi)
                    print(f"U1.36: (unassigned) → LED_WIFI")

    # ── 4. SW2: SPDT slide switch for main power ────────────────────────────
    # Placed at bottom-left area, near board edge (y=17.5mm)
    # pad1=GND (OFF), pad2=TPS_EN (COM), pad3=VBAT (ON)
    sw2 = create_switch_fp(b, "SW2", "Power Switch",
                           cx=6.5, cy=17.2,
                           net_gnd="GND", net_com="TPS_EN", net_vbat="VBAT")
    print("SW2 added at (6.5, 17.2)")

    # Short trace: SW2.pad2 (TPS_EN at 6.5,17.2) → up toward U2.3
    # SW2 COM pad is at (6.5, 17.2). U2.3 is at (24.5, 8.7).
    # Leave long route as ratsnest (too far for auto-routing here)
    # Add a short via stub to help DRC connectivity
    # Just connect TPS_EN from SW2 COM pad with a test point marker for now.
    # User will see ratsnest in KiCad and can route or we add a track here.
    # Actually let's add a track going up from SW2 a bit on In2.Cu
    # Then the ratsnest will show the remaining unconnected to U2.3

    # ── 5. LED2 (red, power indicator) + R12 ───────────────────────────────
    # LED2: clone of LED1 (0603 LED), placed at (5.5, 14.80)
    # LED2.1=GND (cathode), LED2.2=LED_PWR_A (anode)
    led2 = clone_fp(b, "LED1", "LED2", "Red Power LED",
                    x=5.50, y=14.80,
                    pad_nets={"1": "GND", "2": "LED_PWR_A"})
    print("LED2 (red power) added at (5.5, 14.8)")

    # R12: clone of R3 (0402 1k), placed at (7.20, 14.80)
    # R12.1=3V3, R12.2=LED_PWR_A
    # Power LED is always-on: 3V3→R12→LED_PWR_A→LED2→GND
    r12 = clone_fp(b, "R3", "R12", "1k",
                   x=7.20, y=14.80,
                   pad_nets={"1": "3V3", "2": "LED_PWR_A"})
    print("R12 (1k, LED_PWR) added at (7.2, 14.8)")

    # Short trace: LED2.pad2 (LED_PWR_A) ↔ R12.pad2 (LED_PWR_A)
    # LED2 center=5.5, pad2 local offset=+0.75 → abs_x=6.25 (approx for 0603)
    # R12 center=7.2, pad2 local offset=+0.45 → abs_x=7.65 (0402)
    # Actually for 0603 LED pad offsets: ±0.75mm
    # For 0402 resistor pad offsets: ±0.45mm
    # LED_PWR_A: LED2.pad2 at x≈6.25 → R12.pad2 at x≈7.65
    # Both at y=14.80 - connect with short trace
    add_short_trace(b, "LED_PWR_A", pcbnew.F_Cu,
                    6.25, 14.80, 6.75, 14.80)

    # ── 6. LED3 (green, WiFi status) + R13 ─────────────────────────────────
    # LED3: clone of LED1, placed at (5.5, 16.30)
    # LED3.1=GND (cathode), LED3.2=LED_WIFI_A (anode)
    led3 = clone_fp(b, "LED1", "LED3", "Green WiFi LED",
                    x=5.50, y=16.30,
                    pad_nets={"1": "GND", "2": "LED_WIFI_A"})
    print("LED3 (green WiFi) added at (5.5, 16.3)")

    # R13: clone of R3 (0402 1k), placed at (3.80, 16.30)
    # R13.1=LED_WIFI (from U1.36), R13.2=LED_WIFI_A (to LED3 anode)
    r13 = clone_fp(b, "R3", "R13", "1k",
                   x=3.80, y=16.30,
                   pad_nets={"1": "LED_WIFI", "2": "LED_WIFI_A"})
    print("R13 (1k, LED_WIFI) added at (3.8, 16.3)")

    # Short trace: R13.pad2 (LED_WIFI_A at x≈4.25) → LED3.pad2 (at x≈4.75)
    add_short_trace(b, "LED_WIFI_A", pcbnew.F_Cu,
                    4.25, 16.30, 4.75, 16.30)

    # ── 7. Silkscreen cleanup ───────────────────────────────────────────────
    fix_silkscreen(b)
    print("Silkscreen cleaned up")

    # ── 8. Zone fill ────────────────────────────────────────────────────────
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    print("Zone fill done")

    # ── 9. Connectivity check ───────────────────────────────────────────────
    conn = b.GetConnectivity()
    conn.RecalculateRatsnest()
    uc = conn.GetUnconnectedCount(False)
    print(f"\nUnconnected count: {uc}")
    if uc > 0:
        print("  (Includes SW2↔U2.3 ratsnest = needs manual route or add trace below)")

    # Report new component positions
    print("\n=== Added components ===")
    for ref in ["SW2", "LED2", "LED3", "R12", "R13"]:
        fp = next((f for f in b.GetFootprints() if f.GetReference() == ref), None)
        if fp:
            p = fp.GetPosition()
            print(f"  {ref}: ({pcbnew.ToMM(p.x):.2f}, {pcbnew.ToMM(p.y):.2f})")

    pcbnew.SaveBoard(str(BOARD), b)
    print(f"\nBoard saved: {BOARD}")


if __name__ == "__main__":
    main()
