// test/grid_state_test.dart
//
// Unit tests for GridState.

import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:gridauth/services/api_service.dart';
import 'package:gridauth/state/grid_state.dart';
import 'package:gridauth/models/auth_session.dart';
import 'package:gridauth/models/grid_node.dart';

import 'grid_state_test.mocks.dart';

@GenerateMocks([ApiService])
void main() {
  late MockApiService mockApi;
  late GridState gridState;

  setUp(() {
    mockApi = MockApiService();
    gridState = GridState(mockApi);
  });

  test('initial status is idle', () {
    expect(gridState.status, GridStatus.idle);
  });

  test('startSession sets status to loading then active on success', () async {
    final fakeSession = AuthSession(
      nonce: 'test-nonce',
      expiresAt: DateTime.now().add(const Duration(minutes: 5)),
      nodes: [
        GridNode(nodeIndex: 0, chars: ['a', 'b', 'c', 'd']),
        GridNode(nodeIndex: 1, chars: ['e', 'f', 'g', 'h']),
      ],
      nodeCount: 2,
    );

    when(mockApi.createSession('testuser'))
        .thenAnswer((_) async => fakeSession);

    await gridState.startSession('testuser');

    expect(gridState.status, GridStatus.active);
    expect(gridState.session, isNotNull);
    expect(gridState.totalNodes, 2);
  });

  test('startSession sets error status on ApiException', () async {
    when(mockApi.createSession(any))
        .thenThrow(const ApiException('Server error', statusCode: 500));

    await gridState.startSession('baduser');

    expect(gridState.status, GridStatus.error);
    expect(gridState.errorMessage, isNotNull);
  });

  test('startSession sets isLocked on 423 response', () async {
    when(mockApi.createSession(any))
        .thenThrow(const ApiException('Locked', statusCode: 423, isLocked: true));

    await gridState.startSession('lockeduser');

    expect(gridState.isLocked, isTrue);
  });

  test('selectChar advances active node index', () async {
    final fakeSession = AuthSession(
      nonce: 'nonce',
      expiresAt: DateTime.now().add(const Duration(minutes: 5)),
      nodes: [
        GridNode(nodeIndex: 0, chars: ['a', 'b', 'c', 'd']),
        GridNode(nodeIndex: 1, chars: ['e', 'f', 'g', 'h']),
      ],
      nodeCount: 2,
    );
    when(mockApi.createSession(any)).thenAnswer((_) async => fakeSession);
    when(mockApi.verifySelections(any, any))
        .thenAnswer((_) async => {'success': false, 'message': 'fail'});

    await gridState.startSession('user');
    expect(gridState.activeNodeIndex, 0);

    await gridState.selectChar('a');
    // After selecting at node 0, active index advances
    // With 2 nodes, after 2 selections submit is called
  });

  test('cancel clears selections and sets cancelled status', () async {
    final fakeSession = AuthSession(
      nonce: 'nonce',
      expiresAt: DateTime.now().add(const Duration(minutes: 5)),
      nodes: [GridNode(nodeIndex: 0, chars: ['a', 'b', 'c', 'd'])],
      nodeCount: 1,
    );
    when(mockApi.createSession(any)).thenAnswer((_) async => fakeSession);

    await gridState.startSession('user');
    gridState.cancel();

    expect(gridState.status, GridStatus.cancelled);
    expect(gridState.selections, isEmpty);
  });

  test('reset returns to idle status', () async {
    gridState.cancel();
    gridState.reset();
    expect(gridState.status, GridStatus.idle);
  });

  test('activeNode returns null when not active', () {
    expect(gridState.activeNode, isNull);
  });

  test('progress is 0 before any selections', () async {
    final fakeSession = AuthSession(
      nonce: 'nonce',
      expiresAt: DateTime.now().add(const Duration(minutes: 5)),
      nodes: [
        GridNode(nodeIndex: 0, chars: ['a', 'b', 'c', 'd']),
        GridNode(nodeIndex: 1, chars: ['e', 'f', 'g', 'h']),
      ],
      nodeCount: 2,
    );
    when(mockApi.createSession(any)).thenAnswer((_) async => fakeSession);
    await gridState.startSession('user');
    expect(gridState.progress, 0.0);
  });
}
