// lib/services/secure_storage_service.dart
//
// Wraps flutter_secure_storage for Android Keystore-backed token storage.
// Never stores passwords or encryption keys.

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _tokenKey = 'auth_session_token';
  static const _tokenExpiryKey = 'auth_session_token_expiry';
  static const _usernameKey = 'auth_username';

  final FlutterSecureStorage _storage;

  SecureStorageService()
      : _storage = const FlutterSecureStorage(
          aOptions: AndroidOptions(encryptedSharedPreferences: true),
        );

  Future<void> saveSession({
    required String token,
    required DateTime expiresAt,
    required String username,
  }) async {
    await Future.wait([
      _storage.write(key: _tokenKey, value: token),
      _storage.write(key: _tokenExpiryKey, value: expiresAt.toIso8601String()),
      _storage.write(key: _usernameKey, value: username),
    ]);
  }

  Future<String?> getToken() => _storage.read(key: _tokenKey);
  Future<String?> getUsername() => _storage.read(key: _usernameKey);

  Future<DateTime?> getTokenExpiry() async {
    final s = await _storage.read(key: _tokenExpiryKey);
    return s != null ? DateTime.tryParse(s) : null;
  }

  Future<bool> hasValidSession() async {
    final token = await getToken();
    final expiry = await getTokenExpiry();
    if (token == null || expiry == null) return false;
    return DateTime.now().isBefore(expiry);
  }

  Future<void> clearSession() async {
    await Future.wait([
      _storage.delete(key: _tokenKey),
      _storage.delete(key: _tokenExpiryKey),
      _storage.delete(key: _usernameKey),
    ]);
  }
}
