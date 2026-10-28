// lib/state/grid_state.dart
//
// Manages the grid authentication interaction:
//   - Session creation
//   - Node activation sequence
//   - Selection recording
//   - Submission and result handling
//
// The interaction protocol:
//   Nodes are activated ONE AT A TIME in order (index 0 to N-1).
//   At each active node, the user selects one of K characters.
//   The selection is appended to an ordered list.
//   After all N nodes, selections are submitted to the backend.
//   The backend extracts only the selections at real node positions
//   and compares them against the stored password IN ORDER.

import 'package:flutter/foundation.dart';
import '../models/auth_session.dart';
import '../models/grid_node.dart';
import '../services/api_service.dart';

enum GridStatus {
  idle,
  loading,
  active,
  submitting,
  success,
  failure,
  error,
  cancelled,
}

class GridState extends ChangeNotifier {
  final ApiService _api;

  GridStatus _status = GridStatus.idle;
  AuthSession? _session;
  int _activeNodeIndex = 0;
  final List<String> _selections = [];
  String? _errorMessage;
  String? _sessionToken;
  DateTime? _tokenExpiresAt;
  bool _isLocked = false;
  String? _lockedMessage;

  GridState(this._api);

  GridStatus get status => _status;
  AuthSession? get session => _session;
  int get activeNodeIndex => _activeNodeIndex;
  List<String> get selections => List.unmodifiable(_selections);
  String? get errorMessage => _errorMessage;
  String? get sessionToken => _sessionToken;
  DateTime? get tokenExpiresAt => _tokenExpiresAt;
  bool get isLocked => _isLocked;
  String? get lockedMessage => _lockedMessage;

  /// The node that is currently awaiting user selection.
  GridNode? get activeNode {
    if (_session == null) return null;
    final nodes = _session!.nodes;
    final sorted = List<GridNode>.from(nodes)
      ..sort((a, b) => a.nodeIndex.compareTo(b.nodeIndex));
    if (_activeNodeIndex < sorted.length) {
      return sorted[_activeNodeIndex];
    }
    return null;
  }

  int get totalNodes => _session?.nodeCount ?? 0;
  bool get isComplete => _selections.length == totalNodes && totalNodes > 0;
  double get progress =>
      totalNodes > 0 ? _selections.length / totalNodes : 0.0;

  // ---------------------------------------------------------------- //
  // Start a new grid session
  // ---------------------------------------------------------------- //

  Future<void> startSession(String username) async {
    _status = GridStatus.loading;
    _errorMessage = null;
    _isLocked = false;
    _selections.clear();
    _activeNodeIndex = 0;
    notifyListeners();

    try {
      _session = await _api.createSession(username);
      _status = GridStatus.active;
    } on ApiException catch (e) {
      if (e.isLocked) {
        _isLocked = true;
        _lockedMessage = e.message;
        _status = GridStatus.error;
      } else {
        _errorMessage = e.message;
        _status = GridStatus.error;
      }
    } catch (e) {
      _errorMessage = 'Unexpected error. Please try again.';
      _status = GridStatus.error;
    }
    notifyListeners();
  }

  // ---------------------------------------------------------------- //
  // Record a character selection for the currently active node
  // ---------------------------------------------------------------- //

  Future<void> selectChar(String char) async {
    if (_status != GridStatus.active) return;
    if (activeNode == null) return;

    _selections.add(char);
    _activeNodeIndex++;

    if (isComplete) {
      await _submit();
    } else {
      notifyListeners();
    }
  }

  // ---------------------------------------------------------------- //
  // Submit selections to the backend
  // ---------------------------------------------------------------- //

  Future<void> _submit() async {
    _status = GridStatus.submitting;
    notifyListeners();

    try {
      final result = await _api.verifySelections(
        _session!.nonce,
        List<String>.from(_selections),
      );

      if (result['success'] == true) {
        _sessionToken = result['session_token'] as String?;
        final expiryStr = result['token_expires_at'] as String?;
        if (expiryStr != null) {
          _tokenExpiresAt = DateTime.tryParse(expiryStr);
        }
        _status = GridStatus.success;
      } else {
        _status = GridStatus.failure;
        _errorMessage = result['message'] as String? ?? 'Authentication failed.';
      }
    } on ApiException catch (e) {
      _errorMessage = e.message;
      _status = GridStatus.error;
    } catch (_) {
      _errorMessage = 'Unexpected error during verification.';
      _status = GridStatus.error;
    } finally {
      // Zero selection array after submission
      for (int i = 0; i < _selections.length; i++) {
        _selections[i] = '\x00';
      }
      _selections.clear();
    }
    notifyListeners();
  }

  // ---------------------------------------------------------------- //
  // Cancel and reset
  // ---------------------------------------------------------------- //

  void cancel() {
    for (int i = 0; i < _selections.length; i++) {
      _selections[i] = '\x00';
    }
    _selections.clear();
    _session = null;
    _activeNodeIndex = 0;
    _status = GridStatus.cancelled;
    _errorMessage = null;
    notifyListeners();
  }

  void reset() {
    cancel();
    _status = GridStatus.idle;
    _sessionToken = null;
    _tokenExpiresAt = null;
    _isLocked = false;
    _lockedMessage = null;
    notifyListeners();
  }
}
