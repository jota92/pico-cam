# Pico-Cam (Camera IoT)

ESP32-S3 (ESP32-S3-PICO-1-N8R8) をベースにした、超小型・低消費電力の IoT カメラプロジェクトです。ディープスリープを活用し、定期的に JPEG 画像を撮影して Wi-Fi 経由でサーバーにアップロードします。

本リポジトリには、デバイス基板、書き込み・充電用のドック基板の KiCad 回路図・レイアウトデータ、PlatformIO 用のファームウェア、およびアップロード受信用サーバーのサンプルコードが含まれています。

---

## プロジェクト構成

```text
pico-cam/
├── camera_iot/                 # メインの開発・製造パッケージ
│   ├── device_kicad/           # デバイス本体の基板データ (38x18mm 版)
│   ├── cradle_kicad/           # 充電・書き込み用クレードル基板データ (RevA)
│   ├── mechanical/             # デバイスおよびクレードルのレイアウト画像・図面
│   ├── firmware_platformio/    # ESP32-S3 ファームウェア (PlatformIO)
│   ├── server_example/         # アップロード受信用 Express.js サーバー
│   ├── docs/                   # ピンマップや電気設計メモ、DRC レポートなどの設計文書
│   ├── scripts/                # 基板生成や監査用の各種 Python スクリプト
│   ├── jlcpcb_38x18/           # 38x18mm 版の製造用 Gerber/BOM/CPL 出力
│   └── jlcpcb_dock/            # ドック基板の製造用 Gerber/BOM/CPL 出力
├── device_kicad_friend/        # 代替・改良版の基板データ
│   ├── CameraIoT_RevF_40x20_ThroughVia_FINAL.kicad_pcb  # RevF 本体基板 (40x20mm、ブラインドビアなしの通常の4層)
│   ├── CameraIoT_USB-C_Programmer_Dock.kicad_pcb        # USB-C プログラマードック基板
│   └── README_HANDOFF.md       # RevF 基板の製造仕様・引き継ぎドキュメント
├── KiCad/                      # 実行環境用の KiCad 設定 / プロファイル
├── .kicad_cli_profile/         # KiCad CLI 用プロファイル
├── freerouting-1.9.0.jar       # 基板配線用オートルーター (FreeRouting)
└── README.md                   # 本ドキュメント
```

---

## ハードウェア仕様

本プロジェクトには、用途や製造コストに合わせて 2 つの基板バリエーションが存在します。

### 1. デバイス本体基板

*   **ESP32-S3-PICO-1-N8R8**: 8MB Quad Flash & 8MB Octal PSRAM 内蔵モジュール
*   **インターフェース**: カメラモジュール (OV2640 等)、充電検出、ステータス LED、操作ボタン
*   **電源**: LiPo バッテリー接続用コネクタ (J2: JST SH 2ピン)

#### バリエーション:
1.  **38x18mm 版 (`camera_iot/device_kicad/`)**:
    *   極小サイズの設計。
    *   製造用データは `camera_iot/jlcpcb_38x18/` にあります。
2.  **40x20mm RevF 版 (`device_kicad_friend/`)**:
    *   ブラインドビア/埋め込みビアを排除し、通常の「4層貫通ビア (Through-Via)」のみで配線した設計。
    *   JLCPCB などの一般的な基板メーカーで安価に製造可能。
    *   外形寸法: 40.0 x 20.0 mm、基板厚: 0.8 mm。

### 2. 充電・書き込み用ドック (クレードル)

デバイス本体には USB コネクタを搭載せず、外部ドック（ポゴピンまたはケーブル接続）を介して充電やファームウェア書き込みを行います。

*   **Pogo ピンまたは 6-Pin ケーブルインターフェース**:
    1.  `VBUS / VCHG_5V` (電源)
    2.  `GND` (グランド)
    3.  `USB_D+` (native USB D+ / GPIO20)
    4.  `USB_D-` (native USB D- / GPIO19)
    5.  `GPIO0 / BOOT` (書き込みモード遷移用)
    6.  `CHIP_PU / RESET` (チップリセット)
    *   (RevC の pogo 設計では、STAT / WAKE_ID を含めた 8 ポゴピン仕様も存在)

---

## ファームウェア (PlatformIO)

`camera_iot/firmware_platformio/` に格納されているファームウェアは、ESP32-S3 の native USB 機能と Wi-Fi 機能、省電力制御を実装しています。

### ピンアサイン (Pin Map)
*   **PSRAM 競合回避**: ESP32-S3-PICO-1-N8R8 は Octal PSRAM のために `GPIO33~37` を占有するため、カメラのデータラインを `GPIO10-14`、`GPIO38-40` にマッピングして競合を回避しています。
*   **主要ピン**:
    *   `PWDN_GPIO_NUM`: GPIO21
    *   `RESET_GPIO_NUM`: GPIO18
    *   `XCLK_GPIO_NUM`: GPIO15
    *   `SIOD_GPIO_NUM` (SDA): GPIO8
    *   `SIOC_GPIO_NUM` (SCL): GPIO9
    *   `Y2 ~ Y9` (カメラデータ D2~D9): GPIO40, 39, 38, 14, 13, 12, 11, 10
    *   `VSYNC_GPIO_NUM`: GPIO16
    *   `HREF_GPIO_NUM`: GPIO17
    *   `PCLK_GPIO_NUM`: GPIO41
    *   `LED_STATUS_GPIO`: GPIO47 (ステータス LED)
    *   `CHG_DETECT_GPIO`: GPIO4 (充電検出ピン、分圧経由)
    *   `WAKE_BUTTON_GPIO`: GPIO5 (操作・スリープ解除ボタン)
    *   `WAKE_ID_GPIO`: GPIO1 (クレードル接続識別)
    *   `USB_DN_GPIO / USB_DP_GPIO`: GPIO19 / GPIO20 (Native USB デバッグ・書き込み用)

### 主な動作フロー:
1.  **起動**: スリープまたは電源 ON で起動。
2.  **充電検出**: `CHG_DETECT_GPIO` が HIGH の場合（ドックで充電中など）、不要なカメラ撮影や Wi-Fi 接続を行わず、充電に専念するために即座に 1 分間のディープスリープに入ります。
3.  **撮影**: カメラを初期化し、JPEG 画像を取得して PSRAM に格納。
4.  **Wi-Fi 送信**: Wi-Fi に接続し、指定された HTTP サーバへ POST リクエストで画像を送信。
5.  **休止**: 送信完了（またはタイムアウト/エラー）後、ステータス LED をパターン点滅させ、10 分間のディープスリープに入ります。

---

## サーバー (server_example)

`camera_iot/server_example/` は Node.js (Express.js) で書かれたシンプルなアップロード受付サーバーです。

*   **動作**: 送信されてきた Raw JPEG データをトークン認証の上で受信し、日時とランダム文字列のファイル名（例: `2026-06-20T01-23-57-123Z-abcd1234.jpg`）で `./uploads` ディレクトリに保存します。
*   **起動方法**:
    ```bash
    cd camera_iot/server_example
    npm install
    # トークンやポートを指定して起動
    PORT=3000 DEVICE_TOKEN="your-secret-token" node server.js
    ```

---

## 開発と製造に関する注意点

*   **BOM の手配**: LCSC などの自動 PCBA を利用する場合、カメラコネクタや一部の IC など、手作業でのマウント (PCBA 後の手半田) が必要な部品が存在します。詳細は `camera_iot/docs/manual_procurement_revC.md` や `device_kicad_friend/README_HANDOFF.md` をご確認ください。
*   **DRC（デザインルールチェック）**:
    *   RevF 基板は KiCad 10.0.1 の DRC にて、重大なエラー・未配線ともに 0 件であることを確認済みです。
