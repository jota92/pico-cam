# JLCPCB Ordering Checklist

## 提出ファイル

本体:

1. `production_revC/device/CameraIoT_RevC_Gerbers.zip`
2. `production_revC/jlcpcb/device_BOM_JLCPCB_RevC.csv`
3. `production_revC/jlcpcb/device_CPL_JLCPCB_RevC.csv`

ドック:

1. `production_revC/cradle/USB_C_to_Cable_Dock_RevC_Gerbers.zip`
2. `production_revC/jlcpcb/cradle_BOM_JLCPCB_RevC.csv`
3. `production_revC/jlcpcb/cradle_CPL_JLCPCB_RevC.csv`

補助:

- `production_revC/jlcpcb/device_manual_post_pcba_parts_RevC.csv`
- `production_revC/jlcpcb/cradle_manual_post_pcba_parts_RevC.csv`

## 実装前提

- 本体は 4 層 0.8 mm
- ドックは 2 層 1.0 mm
- pogo は廃止済み
- 本体とドックの接続は `JST SH 6-pin (SM06B-SRSS-TB)` ケーブル

## ドック配線仕様

1. `pin1 = VCHG_5V`
2. `pin2 = GND`
3. `pin3 = USB_D+`
4. `pin4 = USB_D-`
5. `pin5 = GPIO0 / FLASH`
6. `pin6 = CHIP_PU / RESET`

## 発注時の注意

- `U1`, `U5`, `LED1` は BOM 上 consign 扱い
- それ以外の置換済み受動部品と JST コネクタは、2026-06-17 時点で LCSC 在庫確認済み
- 本体の `TP1/TP2/TP3` は銅パッドで、追加部品実装は不要

## 最終確認コマンド

```bash
/private/tmp/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 scripts/check_revC_interface_spec.py production_revC/device/CameraIoT_RevC_routed.kicad_pcb production_revC/cradle/USB_C_to_Cable_Dock_RevC_routed.kicad_pcb
/private/tmp/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 scripts/audit_connectivity.py production_revC/device/CameraIoT_RevC_routed.kicad_pcb production_revC/cradle/USB_C_to_Cable_Dock_RevC_routed.kicad_pcb
```
