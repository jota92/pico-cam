# Camera IoT RevC fabrication package

2026-06-16 時点で、RevC の completed routed 版を再構築済みです。  
ただし、この環境では `kicad-cli pcb drc` が異常終了するため、
最終確認は `導通監査 + 局所電源/インターフェース検証 + Gerber再生成` で行っています。

同日付で、新仕様として以下も追加しています。

- 本体ボタン 1 個で `短押し撮影 / 3秒 BLE設定 / 10秒 初期化`
- ステータス LED
- BLE 初期設定前提の `WAKE_ID` 分離
- 充電・書き込みドック用の **8 pogo** (`VBUS/GND/D+/D-/BOOT/RESET/STAT/WAKE_ID`)
- ESP32-S3 native USB (`GPIO19/20`) を使うドック経由書き込み

旧 `RevA*` 一式は監査・修正履歴として残していますが、発注入力には使わないでください。

## 完成物

- デバイス基板: `production_revC/device/CameraIoT_RevC_routed.kicad_pcb`
- クレードル基板: `production_revC/cradle/USB_C_to_Pogo_Cradle_RevC_routed.kicad_pcb`
- JLCPCB 用データ:
  - `production_revC/jlcpcb/device_BOM_JLCPCB_RevC.csv`
  - `production_revC/jlcpcb/device_CPL_JLCPCB_RevC.csv`
  - `production_revC/jlcpcb/device_manual_post_pcba_parts_RevC.csv`
  - `production_revC/jlcpcb/cradle_BOM_JLCPCB_RevC.csv`
  - `production_revC/jlcpcb/cradle_CPL_JLCPCB_RevC.csv`
  - `production_revC/jlcpcb/cradle_manual_post_pcba_parts_RevC.csv`
- Gerber ZIP:
  - `production_revC/device/CameraIoT_RevC_Gerbers.zip`
  - `production_revC/cradle/USB_C_to_Pogo_Cradle_RevC_Gerbers.zip`

## 現在の状態

- デバイス基板:
  - `scripts/build_device_revC_routed.py` で `CameraIoT_RevC_routed.kicad_pcb` を再生成可能
  - `scripts/check_revC_power_cell.py` は routed 完成版で `PASS`
  - `scripts/check_revC_interface_spec.py` は routed 完成版で `PASS`
  - `scripts/audit_connectivity.py` は routed 完成版で `unconnected_edges=0`
- クレードル基板:
  - 新仕様で USB2 D+/D- と 8 pogo、FLASH/RESET ボタンを追加
  - `scripts/audit_connectivity.py` では routed 完成版の `unconnected_edges=0` を確認済み
  - pogo は `Mill-Max 0906-0-15-20-75-14-11-0` を採用し、手実装前提で固定
- クレードルの手差しポゴピンは BOM から除外済み
- デバイスは `J2` LiPo SMT コネクタを追加済みで、電池リードの基板直半田は不要
- デバイスの底面接点とテストパッドは手作業項目として分離済み

## 発注時の注意

- `device_BOM_JLCPCB_RevC.csv` には LCSC 空欄が 9 行あります。これらは
  `JLC global sourcing/consigned` 前提です。
- カメラモジュール、電池、クレードルのポゴピンは PCBA 後の手組みです。
- 電池と pogo の固定品番は `docs/manual_procurement_revC.md` を見てください。
- KiCad 純正 DRC レポートだけは、この環境で `kicad-cli` が exit 134 になるため未取得です。

## 生成スクリプト

- RevC 生成元: `scripts/generate_revC.py`
- routed device 再構築: `scripts/build_device_revC_routed.py`
- 局所検証: `scripts/check_revC_power_cell.py`
- I/O仕様検証: `scripts/check_revC_interface_spec.py`
- 導通監査: `scripts/audit_connectivity.py`
- fabrication 出力再生成: `scripts/export_revC_fab.py`
- 旧 routed 基板局所修復: `scripts/repair_revC_routed_board.py`

KiCad 付属 Python で再生成する場合:

```bash
HOME=/tmp/kicad-home KICAD_CONFIG_HOME=/tmp/kicad-config \
/tmp/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 \
scripts/generate_revC.py
```
