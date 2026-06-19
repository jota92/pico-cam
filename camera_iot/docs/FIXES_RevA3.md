# FIXES applied in RevA3

RevA3 closes the issues found when auditing RevA2 against the official ESP32-S3-PICO-1
datasheet (Table 2-1) and the TI/USB-C datasheets. All checks below were re-verified in script.

## [CRIT] U1 footprint physical geometry rebuilt to the real LGA56 layout
RevA2 had the correct net<->pad-number mapping, but the placeholder land placed the pads
clockwise (pads 1-14 on the top edge). The official ESP32-S3-PICO-1 LGA56 is numbered
ANTI-CLOCKWISE from pin 1 (top-left): pins 1-14 left edge, 15-28 bottom, 29-42 right,
43-56 top, 57 = center GND. The footprint pads were repositioned to match, with a PIN1
marker at top-left. Net<->pin-number remains 57/57 correct (re-verified vs datasheet).
Because nets are bound to pad NUMBERS, swapping in Espressif's official library footprint
keeps every connection correct.

## [CRIT] Cradle pogo footprints no longer short to GND
RevA2 modeled each pogo as TWO pads with pad2 tied to GND, which shorted 5V (P1), STAT (P3)
and WAKE (P4) to ground. Each pogo is now a SINGLE pad on its own net:
P1=VBUS_PROTECTED, P2=GND, P3=STAT, P4=WAKE_ID.

## [CRIT] TPS63031 (U2) pinout corrected to the real DSK package
RevA2 had an invented pin order. Now matches TI DSK: 1=L1, 2=VIN, 3=VINA, 4=EN, 5=PS/SYNC,
6=GND, 7=L2, 8=VOUT, 9=FB, 10=PGND, thermal=PGND. EN tied to VBAT (always enabled),
PS/SYNC tied to GND (power-save mode for low sleep current), FB tied to GND (fixed-output
3.3 V version), VOUT=3V3, VIN/VINA=VBAT, L1/L2 to the inductor.

## [MAJ] Cradle charge LED put in SERIES (was parallel)
RevA2 had R4 and LED2 both spanning VBUS_PROTECTED<->STAT (parallel, no current limit).
Now: VBUS_PROTECTED -> R4 -> CHG_LED_A -> LED2 -> STAT (series, limited).

## [MAJ] USB-C J1 rebuilt with real pads
RevA2 J1 had only 2 pads, so CC1/CC2 never reached the connector. J1 now uses the KiCad
USB_C_Receptacle_USB2.0_16P pad names: VBUS=A4/A9/B4/B9, GND=A1/A12/B1/B12+shield,
CC1=A5, CC2=B5 (Rd 5.1k on R1/R2), D+/-/SBU left NC (power-only cradle).

## [MIN] VDD_SPI decoupling added
C17 (0.1 uF) on U1 VDD_SPI (pin29) to GND.

## Verified by script in this build
- U1: 57/57 pad nets match datasheet; pads now anti-clockwise, PIN1 top-left.
- TPS63031, MCP73831, TLV70028/70013 pinouts all match their datasheets.
- No pogo GND shorts; charge LED is series; USB-C CC present.
- BOM/CPL regenerated directly from the PCB (no drift); TP*/MH*/BAT* excluded from SMT BOM.

## STILL required before ordering (workflow steps, cannot be pre-baked into this package)
1. Open in KiCad. Replace U1 (and verify all CUSTOM footprints: FPC 24P, pogo, antenna,
   USB-C, inductor) against the manufacturer's official land patterns. Nets are keyed to
   pad numbers/names, so official footprints drop in cleanly.
2. Route all nets, then run ERC and DRC until clean (the package is placement + connectivity,
   not finished copper; device has 2 stub segments, cradle 0).
3. Fill every LCSC/JLC part number in both BOMs (left blank on purpose - do not guess).
4. Export Gerbers; check the JLCPCB preview for component orientation and pin-1.
5. VNA-tune the antenna match (L2/C1/C2) in the assembled enclosure.
