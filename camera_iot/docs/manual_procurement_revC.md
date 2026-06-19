# RevC manual / off-board procurement

この文書は、JLCPCB PCBA の外で調達・手組みする部品を固定するためのメモです。

## Cradle pogo

- Qty: 8
- MPN: `0906-0-15-20-75-14-11-0`
- Manufacturer: Mill-Max
- 用途: クレードル側 8 接点スプリングプローブ
- 実装前提: **手実装**

本 RevC では、この型番をクレードル側の実部品として固定します。  
JLCPCB の通常 PCBA にこの部品をそのまま載せられることは本環境では確認できていないため、
発注上は手実装前提です。

## Device battery connector

- PCB side connector `J2`
- MPN: `BM02B-SRSS-TB(LF)(SN)`
- Manufacturer: JST
- Series: SH, 2-pin, 1.0 mm pitch

### Mating parts

- Housing: `SHR-02V-S-B`
- Crimp terminal: `SSH-003T-P0.2`

## Battery pack

バッテリーセル自体は JLCPCB 実装対象ではありません。  
この設計で固定しているのは、**電気仕様・外形クラス・コネクタ系**です。

### Required battery spec

- 1S LiPo
- nominal `3.7 V`
- **PCM/protected cell required**
- size class: `401230`
- target capacity: `100-120 mAh`
- leadout: JST SH 2-pin mate
- polarity:
  - pin 1 = `VBAT` = red
  - pin 2 = `GND` = black

### Procurement note

この RevC は、特定の 1 SKU の市販電池に固定しないようにしています。  
理由は、保護回路有無、リード長、コネクタ向きの差が大きく、量産時に電池ベンダ変更が起こりやすいためです。

したがって、実調達は次のどちらかにしてください。

1. 上記仕様の完成品バッテリーパックを購入する
2. `401230 protected cell + JST SH mate` のカスタムリード品を作る

設計上の固定点は `J2 = BM02B-SRSS-TB(LF)(SN)` です。
