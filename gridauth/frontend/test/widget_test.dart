// test/widget_test.dart
//
// Widget tests for key screens.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:mockito/annotations.dart';

import 'package:gridauth/screens/welcome_screen.dart';
import 'package:gridauth/screens/login_screen.dart';
import 'package:gridauth/services/api_service.dart';
import 'package:gridauth/services/secure_storage_service.dart';
import 'package:gridauth/state/auth_state.dart';
import 'package:gridauth/state/grid_state.dart';
import 'package:gridauth/widgets/progress_dots.dart';
import 'package:gridauth/widgets/error_banner.dart';
import 'widget_test.mocks.dart';

@GenerateMocks([ApiService, SecureStorageService])
Widget buildTestApp(Widget child, {ApiService? api, AuthState? auth, GridState? grid}) {
  final mockApi = api ?? MockApiService();
  final mockStorage = MockSecureStorageService();
  final authState = auth ?? AuthState(mockApi, mockStorage);
  final gridState = grid ?? GridState(mockApi);

  return MultiProvider(
    providers: [
      Provider<ApiService>.value(value: mockApi),
      Provider<SecureStorageService>.value(value: mockStorage),
      ChangeNotifierProvider<AuthState>.value(value: authState),
      ChangeNotifierProvider<GridState>.value(value: gridState),
    ],
    child: MaterialApp(home: child),
  );
}

void main() {
  testWidgets('WelcomeScreen shows GridAuth title', (tester) async {
    await tester.pumpWidget(buildTestApp(const WelcomeScreen()));
    await tester.pumpAndSettle();
    expect(find.text('GridAuth'), findsOneWidget);
  });

  testWidgets('WelcomeScreen has Sign In and Create Account buttons', (tester) async {
    await tester.pumpWidget(buildTestApp(const WelcomeScreen()));
    await tester.pumpAndSettle();
    expect(find.text('Sign In'), findsOneWidget);
    expect(find.text('Create Account'), findsOneWidget);
  });

  testWidgets('ProgressDots renders correct number of dots', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: ProgressDots(total: 10, completed: 3)),
      ),
    );
    // 10 animated containers (one per dot)
    expect(find.byType(AnimatedContainer), findsNWidgets(10));
  });

  testWidgets('ErrorBanner shows message and dismiss icon', (tester) async {
    bool dismissed = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ErrorBanner(
            message: 'Test error message',
            onDismiss: () => dismissed = true,
          ),
        ),
      ),
    );
    expect(find.text('Test error message'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.close));
    expect(dismissed, isTrue);
  });

  testWidgets('LoginScreen shows username field and grid button', (tester) async {
    await tester.pumpWidget(buildTestApp(const LoginScreen()));
    await tester.pumpAndSettle();
    expect(find.text('Sign In'), findsOneWidget);
    expect(find.text('Begin Grid Authentication'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
  });
}
