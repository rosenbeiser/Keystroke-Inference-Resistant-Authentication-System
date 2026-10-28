// lib/state/auth_state.dart
//
// Manages authenticated session state: token storage, login/logout flow.

import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../services/secure_storage_service.dart';

enum AuthStatus {
  unknown,
  authenticated,
  unauthenticated,
}

class AuthState extends ChangeNotifier {
  final ApiService _api;
  final SecureStorageService _storage;

  AuthStatus _status = AuthStatus.unknown;
  String? _username;
  String? _errorMessage;
  bool _isLoading = false;

  AuthState(this._api, this._storage);

  AuthStatus get status => _status;
  String? get username => _username;
  String? get errorMessage => _errorMessage;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  Future<void> initialize() async {
    final valid = await _storage.hasValidSession();
    if (valid) {
      final token = await _storage.getToken();
      _username = await _storage.getUsername();
      try {
        await _api.getStatus(token!);
        _status = AuthStatus.authenticated;
      } catch (_) {
        await _storage.clearSession();
        _status = AuthStatus.unauthenticated;
      }
    } else {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<void> loginSuccess({
    required String token,
    required DateTime expiresAt,
    required String username,
  }) async {
    await _storage.saveSession(
      token: token,
      expiresAt: expiresAt,
      username: username,
    );
    _username = username;
    _status = AuthStatus.authenticated;
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();
    final token = await _storage.getToken();
    if (token != null) {
      await _api.logout(token); // best-effort
    }
    await _storage.clearSession();
    _status = AuthStatus.unauthenticated;
    _username = null;
    _isLoading = false;
    notifyListeners();
  }

  void setError(String message) {
    _errorMessage = message;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
