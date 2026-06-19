# CameraIoT RevA2 correction report

This package fixes the RevA1 fatal inconsistencies.

## Fixed

- ESP32-S3-PICO-1-N8R8 U1 pad net assignment now follows the Espressif package pin numbers.
- Camera D9-D5 are assigned to GPIO10-GPIO14 / U1 pads 15-19.
- U1 pads 38-42, which correspond to GPIO33-GPIO37, are left unconnected because they are used by the N8R8 octal PSRAM.
- CAM_D2 is no longer connected to U1 pad46. U1 pad46 is now 3V3 because it is VDD3P3_CPU.
- U1 pads55/56 are now 3V3 because they are VDDA. They were incorrectly tied to GND in the previous placeholder footprint.
- UART programming pins are now U1 pad49/U0TXD and U1 pad50/U0RXD.
- LED_STATUS is now GPIO47 / U1 pad37.
- Device and cradle pogo pitch remains 4.0 mm: 5V/GND/STAT/WAKE.
- Power, charger, LDO, RF matching, pullups, divider, LED, and passives now have explicit nets.

## Important remaining manufacturing note

This package corrects pad/net assignment. It still must be opened in KiCad and fully routed, DRC/ERC checked, and exported to Gerber before JLCPCB ordering. Do not upload the KiCad PCB directly as a finished production design without routing/DRC.

## Files added

- docs/device_pad_net_assignment_revA2.csv
- docs/cradle_pad_net_assignment_revA2.csv
- docs/revA2_audit_report.md
- docs/revA2_validation_report.txt
