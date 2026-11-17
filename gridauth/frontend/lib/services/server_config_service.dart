// lib/services/server_config_service.dart
//
// Persists the backend server URL using FlutterSecureStorage so the user
// only needs to enter it once in the app — no rebuilds required.

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/app_config.dart';

class ServerConfigService {
  static const _key = 'server_base_url';
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  /// Returns the stored server URL, or the compile-time default from AppConfig.
  static Future<String> getBaseUrl() async {
    final value = await _storage.read(key: _key);
    return value ?? AppConfig.baseUrl;
  }

  /// Persists a new server URL.
  static Future<void> setBaseUrl(String url) async {
    await _storage.write(
      key: _key,
      value: url.trimRight().replaceAll(RegExp(r'/+$'), ''),
    );
  }

  /// True if a custom URL has been stored.
  static Future<bool> hasCustomUrl() async {
    return await _storage.containsKey(key: _key);
  }

  /// Clears any stored URL (revert to compile-time default).
  static Future<void> reset() async {
    await _storage.delete(key: _key);
  }
}
