#!/usr/bin/env python3
"""Generate JLCPCB Gerbers + BOM + CPL for the USB-C Programmer Dock PCB.

P1-P8 pogo pads are SMD contact pads (no component to solder) — excluded from BOM.
All other components have LCSC part numbers verified against JLCPCB library.
"""
from pathlib import Path
import csv
import zipfile
from collections import defaultdict
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "device_kicad" / "CameraIoT_USB-C_Programmer_Dock.kicad_pcb"
OUT = ROOT / "jlcpcb_dock"

# Part database: (value_lower, package_hint) -> (mfr, mpn, lcsc, notes)
PART_DB = {
    # Resistors
    ("5.1k", "0402"):  ("UNI-ROYAL", "0402WGF5101TCE", "C25905", "JLCPCB SMT"),
    ("2.2k", "0402"):  ("UNI-ROYAL", "0402WGF2201TCE", "C25879", "JLCPCB SMT"),
    # LEDs
    ("charge led", ""):  ("Everlight", "19-21SURC/S530-A2/TR8", "C72039", "JLCPCB SMT"),
    ("power led", ""):   ("Everlight", "19-213SURC/S350-A3/TR8", "C72043", "JLCPCB SMT"),
    # Protection
    ("500ma ptc", ""):   ("Bourns", "MF-MSMF050-2", "C70069", "JLCPCB SMT"),
    ("5v tvs", ""):      ("Littelfuse", "PRTR5V0U2X,215", "C302007", "JLCPCB SMT"),
    # Connectors / Switches
    ("usb-c power+usb2", ""):  ("G-Switch", "TYPE-C-31-M-12", "C165948", "JLCPCB SMT"),
    ("flash button", ""):      ("ALPS Alpine", "SKRPACE010", "C139797", "JLCPCB SMT"),
    ("reset button", ""):      ("ALPS Alpine", "SKRPACE010", "C139797", "JLCPCB SMT"),
}

# Components to skip (pogo contact pads - no part to solder)
SKIP_REFS = {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"}


def gf(fp, n):
    return fp.GetFieldText(n) if fp.HasField(n) else ""


def main():
    OUT.mkdir(exist_ok=True)
    b = pcbnew.LoadBoard(str(BOARD))

    # Fill LCSC / Mfr / MPN fields
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref in SKIP_REFS:
            fp.SetField("Assembly", "Do not place")
            continue
        if gf(fp, "LCSC"):
            continue
        val = fp.GetValue().lower()
        fp_id = fp.GetFPIDAsString().lower()
        for (v, f_hint), (mfr, mpn, lcsc, asm) in PART_DB.items():
            if v in val and (f_hint == "" or f_hint in fp_id):
                fp.SetField("Manufacturer", mfr)
                fp.SetField("MPN", mpn)
                fp.SetField("LCSC", lcsc)
                fp.SetField("Assembly", asm)
                break

    # Gerbers
    gdir = OUT / "gerbers"
    gdir.mkdir(exist_ok=True)
    ctl = pcbnew.PLOT_CONTROLLER(b)
    o = ctl.GetPlotOptions()
    o.SetOutputDirectory(str(gdir))
    o.SetPlotFrameRef(False)
    o.SetPlotValue(True)
    o.SetPlotReference(True)
    o.SetSubtractMaskFromSilk(True)
    o.SetDrillMarksType(pcbnew.DRILL_MARKS_NO_DRILL_SHAPE)
    layers = [
        (pcbnew.F_Cu,     "F.Cu"),
        (pcbnew.B_Cu,     "B.Cu"),
        (pcbnew.F_SilkS,  "F.Silkscreen"),
        (pcbnew.B_SilkS,  "B.Silkscreen"),
        (pcbnew.F_Mask,   "F.Mask"),
        (pcbnew.B_Mask,   "B.Mask"),
        (pcbnew.Edge_Cuts, "Edge.Cuts"),
    ]
    for lid, name in layers:
        ctl.SetLayer(lid)
        ctl.OpenPlotfile(name, pcbnew.PLOT_FORMAT_GERBER, name)
        ctl.PlotLayer()
        ctl.ClosePlot()
    dw = pcbnew.EXCELLON_WRITER(b)
    dw.SetOptions(False, True, pcbnew.VECTOR2I(0, 0), True)
    dw.SetFormat(True)
    dw.CreateDrillandMapFilesSet(str(gdir), True, False)
    zp = OUT / "CameraIoT_Dock_Gerbers.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in gdir.iterdir():
            zf.write(f, f.name)
    print("Gerbers:", zp)

    # BOM
    groups = defaultdict(list)
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        asm = gf(fp, "Assembly") or "JLCPCB SMT"
        if asm == "Do not place" or ref in SKIP_REFS:
            continue
        key = (fp.GetValue(), fp.GetFPIDAsString(),
               gf(fp, "Manufacturer"), gf(fp, "MPN"), gf(fp, "LCSC"), asm)
        groups[key].append(ref)
    bom = OUT / "CameraIoT_Dock_BOM_JLCPCB.csv"
    with bom.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "Manufacturer",
                    "Manufacturer Part Number", "LCSC Part #", "Quantity", "Notes"])
        for (val, fpid, mfr, mpn, lcsc, asm), refs in sorted(groups.items(), key=lambda x: x[1][0]):
            w.writerow([val, ",".join(sorted(refs)), fpid, mfr, mpn, lcsc, len(refs), asm])
    print("BOM:", bom)

    # CPL
    cpl = OUT / "CameraIoT_Dock_CPL_JLCPCB.csv"
    with cpl.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
        for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
            ref = fp.GetReference()
            if ref in SKIP_REFS:
                continue
            asm = gf(fp, "Assembly") or "JLCPCB SMT"
            if asm == "Do not place":
                continue
            p = fp.GetPosition()
            w.writerow([ref, fp.GetValue(), fp.GetFPIDAsString(),
                        f"{pcbnew.ToMM(p.x):.4f}mm", f"{-pcbnew.ToMM(p.y):.4f}mm",
                        f"{fp.GetOrientationDegrees():.2f}",
                        "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom"])
    print("CPL:", cpl)

    # Summary
    print("\n=== BOM Summary ===")
    with bom.open() as f:
        for row in csv.DictReader(f):
            lcsc = row.get('LCSC Part #', '')
            flag = '' if lcsc else ' ← NO LCSC'
            print(f"  {row['Designator']:20} LCSC={lcsc!r}{flag}")


if __name__ == "__main__":
    main()
