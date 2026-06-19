#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"

// CameraIoT RevC pin map.
// ESP32-S3-PICO-1-N8R8 reserves GPIO33-37 for octal PSRAM.
// GPIO19/20 are reserved for USB_D-/USB_D+ via the pogo cradle.
// The user button stays on GPIO5; cradle ID is split out to GPIO1.
#define PWDN_GPIO_NUM     21
#define RESET_GPIO_NUM    18
#define XCLK_GPIO_NUM     15
#define SIOD_GPIO_NUM      8
#define SIOC_GPIO_NUM      9
#define Y9_GPIO_NUM       10  // D9 MSB  (was 33 - PSRAM conflict)
#define Y8_GPIO_NUM       11  //         (was 34 - PSRAM conflict)
#define Y7_GPIO_NUM       12  //         (was 35 - PSRAM conflict)
#define Y6_GPIO_NUM       13  //         (was 36 - PSRAM conflict)
#define Y5_GPIO_NUM       14  //         (was 37 - PSRAM conflict)
#define Y4_GPIO_NUM       38
#define Y3_GPIO_NUM       39
#define Y2_GPIO_NUM       40  // D2 LSB
#define VSYNC_GPIO_NUM    16
#define HREF_GPIO_NUM     17
#define PCLK_GPIO_NUM     41

#define LED_STATUS_GPIO   47
#define CHG_DETECT_GPIO    4
#define WAKE_BUTTON_GPIO   5
#define WAKE_ID_GPIO       1
#define USB_DN_GPIO       19
#define USB_DP_GPIO       20

// Fill these in before flashing.
static const char* WIFI_SSID = "YOUR_WIFI_SSID";
static const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
static const char* UPLOAD_URL = "https://your-server.example.com/upload";
static const char* DEVICE_TOKEN = "replace-with-device-token";

static void blink(int n) {
  pinMode(LED_STATUS_GPIO, OUTPUT);
  for (int i=0; i<n; ++i) { digitalWrite(LED_STATUS_GPIO, HIGH); delay(100); digitalWrite(LED_STATUS_GPIO, LOW); delay(100); }
}

static bool init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_SVGA;  // 800x600 first test. Lower to VGA/QVGA if unstable.
    config.jpeg_quality = 12;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 14;
    config.fb_count = 1;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }
  config.fb_location = CAMERA_FB_IN_PSRAM;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }
  sensor_t *s = esp_camera_sensor_get();
  if (s) {
    s->set_framesize(s, FRAMESIZE_VGA); // safer default for first boot
  }
  return true;
}

static bool connect_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 12000) {
    delay(200);
    Serial.print('.');
  }
  Serial.println();
  Serial.print("WiFi status: "); Serial.println(WiFi.status());
  return WiFi.status() == WL_CONNECTED;
}

static bool upload_jpeg(camera_fb_t* fb) {
  if (!fb) return false;
  HTTPClient http;
  http.begin(UPLOAD_URL);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);
  http.addHeader("X-Device-Name", "camera-iot-revA");
  int code = http.POST(fb->buf, fb->len);
  Serial.printf("HTTP code: %d, bytes: %u\n", code, fb->len);
  String resp = http.getString();
  Serial.println(resp);
  http.end();
  return code >= 200 && code < 300;
}

static void sleep_now() {
  digitalWrite(LED_STATUS_GPIO, LOW);
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  esp_sleep_enable_timer_wakeup(10ULL * 60ULL * 1000000ULL); // test: wake every 10 min
  esp_deep_sleep_start();
}

void setup() {
  pinMode(CHG_DETECT_GPIO, INPUT);
  pinMode(WAKE_BUTTON_GPIO, INPUT_PULLUP);
  pinMode(LED_STATUS_GPIO, OUTPUT);
  Serial.begin(115200);
  delay(300);
  Serial.println("CameraIoT RevA boot");

  // If sitting on charger, do not capture or use Wi-Fi. Leave charge current to MCP73831.
  if (digitalRead(CHG_DETECT_GPIO) == HIGH) {
    Serial.println("Charge detected, sleeping.");
    blink(1);
    esp_sleep_enable_timer_wakeup(60ULL * 1000000ULL);
    esp_deep_sleep_start();
  }

  blink(2);
  if (!init_camera()) { blink(5); sleep_now(); }
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) { Serial.println("Camera capture failed"); blink(5); sleep_now(); }
  Serial.printf("Captured: %u bytes\n", fb->len);

  bool ok = false;
  if (connect_wifi()) ok = upload_jpeg(fb);
  esp_camera_fb_return(fb);
  blink(ok ? 3 : 6);
  sleep_now();
}

void loop() {}
