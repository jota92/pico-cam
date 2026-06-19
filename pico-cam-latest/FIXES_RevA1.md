# FIXES applied in RevA1

Result of the RevA design review. Severity: [CRIT] won't work, [MAJ] reliability, [DOC] consistency.

## [CRIT] 1. Camera data bus collided with octal PSRAM
ESP32-S3-PICO-1-N8R8 uses octal PSRAM; on any ESP32-S3R8, GPIO33-37 are wired to the PSRAM and
must not be used. Camera D9..D5 were on GPIO33..37.
FIX: D9..D5 -> GPIO10..14 (D4..D2 stay 38/39/40). Updated pin_map, netlist, BOM-notes, firmware.
Firmware memory_type also corrected opi_opi -> qio_opi (N8R8 flash is quad, PSRAM is octal).

## [CRIT] 2. Pogo pitch mismatch (device vs cradle)
Device charge pads were 3.3 mm pitch; cradle pogos 4.0 mm -> pins 3 and 4 would miss the pads.
FIX: device charge pads moved to 4.0 mm pitch (5V=5.0, GND=9.0, STAT=13.0, WAKE=17.0).
Cradle pogos already 4.0 mm. Note added: confirm the mirror/order for the actual dock orientation.

## [MAJ] 3. 5V-detect divider sat on the logic threshold
100k/100k = 2.5 V ~= ESP32-S3 VIH (2.48 V) -> could read LOW under tolerance.
FIX: R8 100k -> 68k. Vdet = 5*100/(68+100) = 2.98 V.

## [MAJ] 4. No RF reference plane / over-broad antenna keepout
FIX: added solid GND zones (F.Cu, In1.Cu, B.Cu). Antenna keepout narrowed to the radiator only
(35.0-38.0 x 13.5-18.0) so the pi-match stays over ground. Keep the feed short when routing.

## [MAJ] 5. Battery fouled the antenna keepout (and camera Z-stack)
FIX: battery adhesive area moved to (4.0,2.0)-(34.0,14.0), clear of the antenna keepout.
Camera-over-battery worst-case Z (~11.85 mm) documented in mechanical_fit + summary - still must
be resolved mechanically (thin/short cell under the camera or a battery cutout).

## [MAJ] 6. Unprotected LiPo + no system UVLO
TPS63031 UVLO is far below LiPo-safe 3.0 V. FIX: battery spec changed to PROTECTED (PCM) cell;
production option to add a 3.0 V load switch noted.

## [MAJ] 7. Thin ESP32 decoupling
FIX: added C14/C15 (0.1 uF) + C16 (10 uF) close to the ESP32 3V3 pins.

## [DOC] 8. Charge LED location
Report wanted the charge LED on the cradle. FIX: charge LED (LED2 + R4) added to the cradle,
driven by the STAT pogo; the redundant in-case device charge LED (LED2/R2) was removed.

## [DOC] 9. Antenna / USB-C naming
Package standardized on antenna 2450AT18B100E (match its footprint+keepout) and cradle
USB4105-GF-A 16P (matches the 16P footprint; USB4125-GF-A 6P is an alternative).

## NOT auto-fixed (require your action before ordering) — see JLCPCB_ordering_checklist.md
- Fill all LCSC/JLC part numbers (left blank; do not guess).
- Rebuild the ESP32-S3-PICO-1 LGA56 footprint from the official Espressif drawing and map nets
  to the real pin functions (placeholder footprint).
- Build schematic, ERC, route, DRC, JLCPCB preview, VNA antenna tuning.
