#!/usr/bin/env python3
"""Search GND via candidates that reduce zone ratsnest without DRC errors."""
from pathlib import Path
import os
import re
import subprocess
import sys

import pcbnew

import finalize_38x18 as f

ROOT = Path(__file__).resolve().parents[1]
TMP = Path("/tmp/camera_iot_via_search")
TMP.mkdir(exist_ok=True)
KICAD_CLI = "/private/tmp/kicad_mount/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
IN2_CU = 6


def build_board(extra_vias):
    b = pcbnew.LoadBoard(str(f.BOARD))
    f.cleanup_optional_feature_rework(b)
    f.add_pcba_connectivity_fixes(b)
    f.add_seg(b, "VBAT", IN2_CU, 29.1732, 9.7453, 29.8717, 10.4438, width=0.15)
    for _, x, y in extra_vias:
        f.add_via(b, "GND", x, y)
    f.cleanup_board_text(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    return b


def connectivity_count(b):
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    conn.RecalculateRatsnest()
    return conn.GetUnconnectedCount(False)


def drc_counts(path):
    env = os.environ.copy()
    env.update(
        {
            "HOME": "/tmp/kicad-home-via-search",
            "KICAD_CONFIG_HOME": "/tmp/kicad-config-via-search",
            "KICAD_CLI_NO_WINDOW": "1",
            "KICAD_CLI_NO_KEYCHAIN": "1",
            "QT_QPA_PLATFORM": "offscreen",
        }
    )
    proc = subprocess.run(
        [KICAD_CLI, "pcb", "drc", "--severity-error", "--exit-code-violations", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    out = proc.stdout
    violations = re.search(r"([0-9]+) 個の違反", out)
    unconnected = re.search(r"([0-9]+) 個の未配線", out)
    return (
        int(violations.group(1)) if violations else 9999,
        int(unconnected.group(1)) if unconnected else 9999,
        out,
    )


def save_and_check(extra_vias, name):
    b = build_board(extra_vias)
    path = TMP / f"{name}.kicad_pcb"
    pcbnew.SaveBoard(str(path), b)
    return (*drc_counts(path), connectivity_count(b))


def outline_centers():
    b = build_board([])
    centers = []
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for zi, zone in enumerate(b.Zones()):
        if zone.GetNetname() != "GND" or not zone.HasFilledPolysForLayer(pcbnew.F_Cu):
            continue
        polys = zone.GetFilledPolysList(pcbnew.F_Cu)
        for oi in range(1, polys.OutlineCount()):
            outline = polys.COutline(oi)
            pts = []
            for pi in range(outline.PointCount()):
                p = outline.CPoint(pi)
                pts.append((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
            centers.append((f"z{zi}o{oi}", cx, cy, xmin, ymin, xmax, ymax))
    return centers


def candidate_points():
    points = []
    for name, cx, cy, xmin, ymin, xmax, ymax in outline_centers():
        for dx in (0, -0.35, 0.35, -0.7, 0.7):
            for dy in (0, -0.35, 0.35, -0.7, 0.7):
                x, y = round(cx + dx, 3), round(cy + dy, 3)
                if xmin + 0.25 <= x <= xmax - 0.25 and ymin + 0.25 <= y <= ymax - 0.25:
                    points.append((f"{name}_{dx}_{dy}", x, y))
    # Known GND pad-adjacent candidates.
    points += [
        ("C8GND", 30.575, 9.994),
        ("U3GND", 30.300, 7.092),
        ("C15GND", 16.500, 14.000),
        ("U5GND", 13.250, 11.500),
        ("C10GND", 9.950, 12.500),
        ("U2GND5", 24.500, 9.500),
        ("U2GND6", 26.900, 9.500),
        ("U2GND10", 26.900, 7.900),
        ("C7GND", 27.950, 8.725),
        ("C6GND", 27.950, 10.225),
    ]
    seen = set()
    unique = []
    for name, x, y in points:
        key = (round(x, 3), round(y, 3))
        if key in seen:
            continue
        seen.add(key)
        unique.append((name, x, y))
    return unique


def main():
    selected = []
    violations, unconn, _, conn = save_and_check(selected, "base")
    print(f"base violations={violations} unconnected={unconn} conn={conn}")

    candidates = candidate_points()
    while unconn:
        best = None
        for cand in candidates:
            if cand in selected:
                continue
            test_board = build_board(selected + [cand])
            c = connectivity_count(test_board)
            if c >= unconn:
                continue
            path = TMP / "cand.kicad_pcb"
            pcbnew.SaveBoard(str(path), test_board)
            v, u, _ = drc_counts(path)
            if v == 0 and u < unconn:
                score = (u, c, cand)
                if best is None or score < best:
                    best = score
                    print(f"candidate {cand} -> violations={v} unconnected={u} conn={c}", flush=True)
        if best is None:
            break
        _, _, cand = best
        selected.append(cand)
        violations, unconn, _, conn = save_and_check(selected, "selected")
        print(f"SELECT {cand} -> violations={violations} unconnected={unconn} conn={conn}", flush=True)

    print("selected:", flush=True)
    for cand in selected:
        print(cand, flush=True)
    return 0 if unconn == 0 and violations == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
