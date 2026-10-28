// lib/config/app_config.dart
// All configurable constants. Change BASE_URL for device/emulator connectivity.

class AppConfig {
  AppConfig._();

  // ------------------------------------------------------------------ //
  // Backend URL
  // ⚠️  PHYSICAL DEVICE: Set this to your PC's LAN IP address.
  //     Find it with: ipconfig (Windows) → "IPv4 Address" under Wi-Fi adapter.
  //     Example: 'http://192.168.1.5:8000'
  //
  // Android emulator only: use 'http://10.0.2.2:8000'
  //
  // Your phone and PC must be on the SAME Wi-Fi network.
  // ------------------------------------------------------------------ //
  static const String baseUrl = 'http://192.168.0.103:8000'; // Your PC's Wi-Fi LAN IP
  static const String apiPrefix = '/api/v1';

  // ------------------------------------------------------------------ //
  // Grid defaults (must match backend config)
  // ------------------------------------------------------------------ //
  static const int defaultTotalNodes = 10;
  static const int defaultRealNodes = 8;
  static const int defaultGhostNodes = 2;
  static const int defaultCharsPerNode = 4;

  // ------------------------------------------------------------------ //
  // UI
  // ------------------------------------------------------------------ //
  static const Duration nodeActivationDelay = Duration(milliseconds: 300);
  static const Duration errorDisplayDuration = Duration(seconds: 4);
  static const int httpTimeoutSeconds = 30;
}
