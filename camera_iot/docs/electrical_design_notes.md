# Electrical Design Notes

## Current architecture

- Device board: `40 x 20 mm`, 4-layer, `0.8 mm`
- Dock board: USB-C to 6-wire cable dock, 2-layer, `1.0 mm`
- No pogo pins
- Device charging/programming connector:
  - `J3 = JST SH SM06B-SRSS-TB(LF)(SN) / C160405`
- Battery connector:
  - `J2 = JST SH SM02B-SRSS-TB(LF)(SN) / C160402`

## 6-wire cable pinout

1. `VCHG_5V`
2. `GND`
3. `USB_D+`
4. `USB_D-`
5. `GPIO0`
6. `CHIP_PU`

## Device behavior assumptions

- Charging input is detected by `CHG_DETECT` divider on `GPIO4`
- User button is on `GPIO5`
- Status LED is on `GPIO47`
- Native USB uses `GPIO19/GPIO20`
- `GPIO0` and `CHIP_PU` are exported only to the dock connector for flashing/reset

## Stock-driven substitutions applied

- `R1` charge-program resistor: `20k -> 21k`
- `R2/R9` divider and button pull-up: `100k -> 110k`
- `R4/R5/R6/R7`: `10k -> 12.4k`
- `R10`: `33R -> 30.1R`
- `R3/R11/R12/L2`: moved to `RTT029310FTH / C11715`
- Cradle CC resistors: `5.1k -> 5.11k`
- Removed cradle LEDs and their resistors
- Removed large 47uF output capacitor; output bulk now relies on distributed 10uF network already placed around `3V3`

## Known procurement caveats

- `U1`, `U5`, `LED1` are not closed by the current LCSC-only BOM and remain consign/global-sourcing candidates
- All other changed JST and passive parts were selected from currently in-stock LCSC alternatives during this revision
