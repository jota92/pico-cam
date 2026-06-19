# RevA1 design summary

Smallest version that still has a reasonable chance to boot, capture JPEG, send via Wi-Fi, and
charge via pogo pins. RevA1 applies the design-review fixes listed in FIXES_RevA1.md.

## What changed from earlier concept

- Camera DOVDD is 2.8 V (not 3.3 V) to match OV2640FSL typical module design.
- Added 2.8 V and 1.3 V LDOs; the camera cannot be powered from 3.3 V only.
- Added bottom programming pads because the final body has no USB-C.
- Battery is bottom-side adhesive/manual assembly, not JLC SMT.
- Antenna is fully inside the 40 x 20 mm outline, chip antenna + keepout.

## RevA1 fixes (key)

- Camera D9..D5 moved off GPIO33-37 (octal-PSRAM pins) -> GPIO10..14.
- Device charge-pad pitch set to 4.0 mm to match the cradle pogo pitch.
- 5V-detect divider re-ratioed (68k/100k -> ~3.0 V) off the logic threshold.
- GND reference zones + narrowed antenna keepout for RF.
- Added ESP32 local decoupling (0.1 uF x2 + 10 uF).
- Battery spec changed to PROTECTED cell; battery area cleared from antenna keepout.
- Cradle gets the charge LED (driven by STAT); redundant device charge LED removed.
- firmware memory_type corrected to qio_opi for N8R8.

## Remaining one-shot risk areas (verify before order)

- ESP32-S3-PICO-1 LGA56 land pattern + pin-1 must be rebuilt from the official Espressif
  drawing. The placeholder footprint's pad-to-function mapping is NOT the real pinout.
- OV2640 FPC connector orientation/contact side must be verified with a real camera module.
- RF match is not guaranteed until VNA tuning in the real case.
- Z-stack: camera (top) over battery (bottom) can reach ~11.85 mm if they overlap in XY.
  Use a <=3.2 mm cell under the camera footprint, a local battery cutout, or push the camera
  fully into the corner so it does not sit over the battery.
- 401230 high-discharge PROTECTED cell; common 1C cells are not enough for Wi-Fi peaks.
- All LCSC/JLC part numbers must be filled before a PCBA order (left blank intentionally).
