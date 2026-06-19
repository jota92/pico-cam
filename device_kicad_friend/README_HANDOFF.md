# CameraIoT device PCB handoff

## Current completed design

- Board: `CameraIoT_RevF_40x20_ThroughVia_FINAL.kicad_pcb`
- KiCad project settings: `CameraIoT_RevF_40x20_ThroughVia_FINAL.kicad_pro`
- Local KiCad preferences: `CameraIoT_RevF_40x20_ThroughVia_FINAL.kicad_prl`
- Latest DRC report: `CameraIoT_RevF_40x20_ThroughVia_FINAL_DRC.rpt`

## Final specification

- Board outline: exactly 40.0 x 20.0 mm
- Layer count: 4
- Board thickness: 0.8 mm
- USB-C and antenna functions retained
- Four mounting holes retained and moved for the smaller outline
- Footprints retained: 54 of 54; no functional component was removed
- Vias: 70 total, all ordinary F.Cu-to-B.Cu through vias
- Blind/buried/microvias: none
- Default clearance: 0.10 mm
- Copper-to-board-edge rule: 0.25 mm
- Minimum through drill: 0.20 mm
- Minimum via diameter: 0.45 mm

KiCad 10.0.1でゾーン再充填後に検証済みです。エラー重大度のDRC違反は0件、未配線は0件です。残る320件はシルク、文字寸法、ライブラリ差異などの警告です。

## Manufacturing note

このRevFはブラインドviaを使用しません。通常の4層・貫通via工程で製造できます。銅箔と基板端の最小設計値は0.25 mmなので、発注先の工程能力が0.25 mm以下に対応することを確認してください。

## PCBA and ordering files

PCBA・発注関連データは削除していません。主な保存場所は次のとおりです。

- `../jlcpcb_order/`
- `../production_revC/`
- `../docs/JLCPCB_ordering_checklist.md`

既存BOM、CPL、Gerberの多くはRevC表記です。RevFを発注する場合、既存RevC Gerberを使用せず、この完成基板からGerberとドリルデータを再生成してください。BOMの部品構成は維持されていますが、部品座標が変わったためCPLは必ずRevF基板から再生成してください。

## Additional retained board

`CameraIoT_USB-C_Programmer_Dock.*` は別用途の完成基板として残しています。

## Final verification command

```powershell
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' pcb drc --severity-error --exit-code-violations 'CameraIoT_RevF_40x20_ThroughVia_FINAL.kicad_pcb'
```

終了コード0、違反0、未配線0になることを確認してください。
