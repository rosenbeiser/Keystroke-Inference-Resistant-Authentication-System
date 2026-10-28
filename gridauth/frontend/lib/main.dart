// lib/main.dart
//
// Application entry point.
// Sets up Provider state management and initializes auth state from storage.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'screens/welcome_screen.dart';
import 'screens/home_screen.dart';
import 'services/api_service.dart';
import 'services/secure_storage_service.dart';
import 'state/auth_state.dart';
import 'state/grid_state.dart';

void main() {
  runApp(const GridAuthApp());
}

class GridAuthApp extends StatelessWidget {
  const GridAuthApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiService();
    final storage = SecureStorageService();

    return MultiProvider(
      providers: [
        Provider<ApiService>.value(value: api),
        Provider<SecureStorageService>.value(value: storage),
        ChangeNotifierProvider<AuthState>(
          create: (_) => AuthState(api, storage),
        ),
        ChangeNotifierProvider<GridState>(
          create: (_) => GridState(api),
        ),
      ],
      child: MaterialApp(
        title: 'GridAuth',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF0D0B1E),
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF6C63FF),
            brightness: Brightness.dark,
          ),
          textTheme: GoogleFonts.outfitTextTheme(
            ThemeData.dark().textTheme,
          ),
          appBarTheme: const AppBarTheme(
            backgroundColor: Colors.transparent,
            elevation: 0,
            iconTheme: IconThemeData(color: Colors.white),
          ),
        ),
        home: const _AppRoot(),
      ),
    );
  }
}

/// Determines initial route based on persisted session state.
class _AppRoot extends StatefulWidget {
  const _AppRoot();

  @override
  State<_AppRoot> createState() => _AppRootState();
}

class _AppRootState extends State<_AppRoot> {
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    await context.read<AuthState>().initialize();
    if (mounted) setState(() => _initialized = true);
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialized) {
      return const Scaffold(
        backgroundColor: Color(0xFF0D0B1E),
        body: Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF6C63FF)),
          ),
        ),
      );
    }
    final auth = context.watch<AuthState>();
    if (auth.isAuthenticated) {
      return const HomeScreen();
    }
    return const WelcomeScreen();
  }
}
