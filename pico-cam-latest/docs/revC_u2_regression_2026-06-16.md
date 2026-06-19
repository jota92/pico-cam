# RevC U2 regression audit (2026-06-16)

## 要約

RevC デバイス基板は実際に配線済みで、既存 DRC レポートも `0 violations / 0 unconnected`
でした。  
ただし再監査で、`U2` TPS63031 のネット割当が生成スクリプトで回帰していることを確認しました。

これは **DRC では見抜けない論理結線ミス** です。  
したがって、既存の routed 基板と Gerber は現時点では発注不可です。

## 原因

`scripts/generate_revC.py` の旧実装:

```python
u2_nets = ["3V3", "SW2", "GND", "SW1", "VBAT", "VBAT", "GND", "VBAT", "GND", "3V3"]
```

この割当は TPS63031DSKR の正規 DSK ピン配置と一致しません。

正しい割当:

```python
u2_nets = ["SW1", "VBAT", "VBAT", "VBAT", "GND", "GND", "SW2", "3V3", "GND", "GND"]
```

## 影響

- `U2` 周辺の routed デバイス基板配線は、誤ったネット前提で成立している
- 既存 `production_revC/device/CameraIoT_RevC.kicad_pcb` は再ルーティングが必要
- 既存 Gerber / BOM / CPL / 発注用コピーは、そのまま使えない

## 補足

- `docs/recheck_2026-06-15_device_drc.txt`
- `docs/recheck_2026-06-15_cradle_drc.txt`

これらは RevC ではなく、旧 RevA 配置ファイルに対する再確認レポートです。
RevC の routed 基板評価と混同しないこと。

## 現在の対処

- 生成スクリプトの `U2` ネット割当は修正済み
- `U2` 周辺の固定配線と部品配置も修正済み
- `scripts/check_revC_power_cell.py` を追加し、以下をローカル再検証可能にした
  - `U2` pad1-11 のネット割当
  - `C4/C5/C7/C17/R8/R9/L1/U2` の局所配置
  - `SW1/SW2/VBAT/3V3` の固定配線
  - 電源セル局所クリアランス
- このチェッカーは `CameraIoT_RevC_unrouted.kicad_pcb` では通過し、
  既存 `CameraIoT_RevC.kicad_pcb` では失敗する
- `scripts/repair_revC_routed_board.py` で routed 基板の局所修復版
  `CameraIoT_RevC_repaired_local.kicad_pcb` を生成可能で、これも局所チェッカーを通過する
- ただし、修正後の routed デバイス基板は未再認定
- クレードル基板は今回の回帰の直接対象外
