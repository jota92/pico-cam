# RevC Release Status

最終更新: 2026-06-17

## 結論

RevC は `pogo` を廃止し、6線 JST-SH ケーブル経由の USB-C ドック構成へ更新済みです。

- 本体: `production_revC/device/CameraIoT_RevC_routed.kicad_pcb`
- ドック: `production_revC/cradle/USB_C_to_Cable_Dock_RevC_routed.kicad_pcb`
- Gerber:
  - `production_revC/device/CameraIoT_RevC_Gerbers.zip`
  - `production_revC/cradle/USB_C_to_Cable_Dock_RevC_Gerbers.zip`

## 確認済み

- `scripts/check_revC_interface_spec.py`:
  - 6線ケーブル割当 `VCHG_5V / GND / USB_D+ / USB_D- / GPIO0 / CHIP_PU` を確認
- `scripts/audit_connectivity.py`:
  - device routed: `split_nets none`
  - cradle routed: `split_nets none`
- TPS63031 ピン割当は修正済み
- バッテリコネクタは LCSC 在庫ありの `SM02B-SRSS-TB(LF)(SN) / C160402` に変更済み
- ドック/本体ケーブルコネクタは `SM06B-SRSS-TB(LF)(SN) / C160405` に変更済み
- クレードル CC 抵抗は `5.11k / C25904` へ変更済み

## BOM 上の注意

以下は BOM 上で `consign` 扱いです。

- `U1` ESP32-S3-PICO-1-N8R8
- `U5` TLV70013DDCR
- `LED1` XL-1608UBC

つまり、**Gerber/BOM/CPL は生成済みだが、全点が LCSC 通常在庫だけで閉じているわけではありません。**
JLCPCB へはそのまま提出可能ですが、上記 3 点は JLC 側の実装可否確認または consign/global sourcing 前提です。
