// lib/models/auth_session.dart

import 'grid_node.dart';

/// Represents a grid authentication session returned from the server.
class AuthSession {
  final String nonce;
  final DateTime expiresAt;
  final List<GridNode> nodes;
  final int nodeCount;

  const AuthSession({
    required this.nonce,
    required this.expiresAt,
    required this.nodes,
    required this.nodeCount,
  });

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      nonce: json['nonce'] as String,
      expiresAt: DateTime.parse(json['expires_at'] as String),
      nodes: (json['nodes'] as List)
          .map((n) => GridNode.fromJson(n as Map<String, dynamic>))
          .toList(),
      nodeCount: json['node_count'] as int,
    );
  }

  bool get isExpired => DateTime.now().isAfter(expiresAt);
}

/// Post-login authenticated session.
class UserSession {
  final String sessionToken;
  final DateTime expiresAt;

  const UserSession({required this.sessionToken, required this.expiresAt});

  bool get isExpired => DateTime.now().isAfter(expiresAt);
}
