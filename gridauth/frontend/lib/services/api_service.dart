// lib/services/api_service.dart
//
// All network calls to the backend REST API.
// Never logs passwords, tokens, or encryption keys.

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/auth_session.dart';

class ApiException implements Exception {
  final int? statusCode;
  final String message;
  final bool isLocked;

  const ApiException(this.message, {this.statusCode, this.isLocked = false});

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiService {
  final String _base;
  final http.Client _client;

  ApiService({String? baseUrl, http.Client? client})
      : _base = (baseUrl ?? AppConfig.baseUrl) + AppConfig.apiPrefix,
        _client = client ?? http.Client();

  Duration get _timeout =>
      const Duration(seconds: AppConfig.httpTimeoutSeconds);

  Map<String, String> _headers({String? bearerToken}) => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        if (bearerToken != null) 'Authorization': 'Bearer $bearerToken',
      };

  Future<Map<String, dynamic>> _parse(http.Response response) async {
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }
    final detail = body['detail']?.toString() ?? 'Unknown error';
    final locked = response.statusCode == 423;
    throw ApiException(detail, statusCode: response.statusCode, isLocked: locked);
  }

  // ---------------------------------------------------------------- //
  // Registration
  // ---------------------------------------------------------------- //

  Future<void> register(String username, String password) async {
    try {
      final response = await _client
          .post(
            Uri.parse('$_base/register'),
            headers: _headers(),
            body: jsonEncode({'username': username, 'password': password}),
          )
          .timeout(_timeout);
      await _parse(response);
    } on SocketException {
      throw const ApiException('Cannot reach the server. Check your network and make sure the backend is running.');
    } on HttpException {
      throw const ApiException('Network error. Try again.');
    } on TimeoutException {
      throw const ApiException('Request timed out. Is the server running and reachable from your device?');
    }
  }

  // ---------------------------------------------------------------- //
  // Grid session creation
  // ---------------------------------------------------------------- //

  Future<AuthSession> createSession(String username) async {
    try {
      final response = await _client
          .post(
            Uri.parse('$_base/auth/session'),
            headers: _headers(),
            body: jsonEncode({'username': username}),
          )
          .timeout(_timeout);
      final body = await _parse(response);
      return AuthSession.fromJson(body);
    } on SocketException {
      throw const ApiException('Cannot reach the server. Check network.');
    } on HttpException {
      throw const ApiException('Network error. Try again.');
    } on TimeoutException {
      throw const ApiException('Request timed out. Check your server connection.');
    }
  }

  // ---------------------------------------------------------------- //
  // Grid selection verification
  // ---------------------------------------------------------------- //

  Future<Map<String, dynamic>> verifySelections(
      String nonce, List<String> selections) async {
    try {
      final response = await _client
          .post(
            Uri.parse('$_base/auth/verify'),
            headers: _headers(),
            body: jsonEncode({'nonce': nonce, 'selections': selections}),
          )
          .timeout(_timeout);
      return await _parse(response);
    } on SocketException {
      throw const ApiException('Cannot reach the server. Check network.');
    } on HttpException {
      throw const ApiException('Network error. Try again.');
    } on TimeoutException {
      throw const ApiException('Request timed out. Check your server connection.');
    }
  }

  // ---------------------------------------------------------------- //
  // Logout
  // ---------------------------------------------------------------- //

  Future<void> logout(String sessionToken) async {
    try {
      await _client
          .post(
            Uri.parse('$_base/auth/logout'),
            headers: _headers(bearerToken: sessionToken),
          )
          .timeout(_timeout);
    } catch (_) {
      // Best-effort logout — always clear local state regardless
    }
  }

  // ---------------------------------------------------------------- //
  // Auth status check
  // ---------------------------------------------------------------- //

  Future<Map<String, dynamic>> getStatus(String sessionToken) async {
    try {
      final response = await _client
          .get(
            Uri.parse('$_base/auth/status'),
            headers: _headers(bearerToken: sessionToken),
          )
          .timeout(_timeout);
      return await _parse(response);
    } on SocketException {
      throw const ApiException('Cannot reach the server. Check network.');
    }
  }
}
