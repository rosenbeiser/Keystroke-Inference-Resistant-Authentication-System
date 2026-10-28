// lib/screens/login_screen.dart
//
// FR-02: Login screen — identifier input only, no conventional password field.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../state/grid_state.dart';
import '../widgets/error_banner.dart';
import '../widgets/loading_overlay.dart';
import 'grid_auth_screen.dart';
import 'registration_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  Future<void> _startGrid() async {
    final username = _usernameController.text.trim();
    if (username.isEmpty) {
      setState(() => _error = 'Please enter your username.');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final gridState = context.read<GridState>();
    await gridState.startSession(username);

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (gridState.status == GridStatus.active) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => GridAuthScreen(username: username),
        ),
      );
    } else if (gridState.isLocked) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => LockedScreen(message: gridState.lockedMessage),
        ),
      );
    } else {
      setState(() => _error = gridState.errorMessage ?? 'Authentication failed.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0B1E),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.white70),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: LoadingOverlay(
        isLoading: _isLoading,
        message: 'Building your grid...',
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28),
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 20),
                Text(
                  'Sign In',
                  style: GoogleFonts.outfit(
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Enter your username to begin\ngrid-based authentication.',
                  style: GoogleFonts.outfit(
                    fontSize: 14,
                    color: Colors.white54,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 36),
                if (_error != null)
                  ErrorBanner(
                    message: _error!,
                    onDismiss: () => setState(() => _error = null),
                  ),
                const SizedBox(height: 8),
                Text('Username',
                    style: GoogleFonts.outfit(
                        color: Colors.white60, fontSize: 13)),
                const SizedBox(height: 8),
                TextField(
                  controller: _usernameController,
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                  autocorrect: false,
                  enableSuggestions: false,
                  keyboardType: TextInputType.text,
                  onSubmitted: (_) => _startGrid(),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: const Color(0xFF1E1B38),
                    hintText: 'Your username',
                    hintStyle: const TextStyle(color: Colors.white30),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide.none,
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(
                        color: Color(0xFF6C63FF),
                        width: 1.5,
                      ),
                    ),
                    prefixIcon: const Icon(Icons.person_outline,
                        color: Colors.white38),
                  ),
                ),
                const SizedBox(height: 24),
                // Begin grid button
                GestureDetector(
                  onTap: _startGrid,
                  child: Container(
                    width: double.infinity,
                    height: 56,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF6C63FF), Color(0xFF48A8F8)],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF6C63FF).withValues(alpha: 0.4),
                          blurRadius: 20,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.grid_on, color: Colors.white, size: 22),
                        const SizedBox(width: 10),
                        Text(
                          'Begin Grid Authentication',
                          style: GoogleFonts.outfit(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                Center(
                  child: TextButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const RegistrationScreen()),
                    ),
                    child: const Text(
                      "Don't have an account? Create one",
                      style: TextStyle(color: Color(0xFF9F97FF), fontSize: 14),
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                Center(
                  child: Text(
                    'Your password is never entered directly.\nAuthenticate through a randomized grid.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white24,
                      fontSize: 11,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class LockedScreen extends StatelessWidget {
  final String? message;
  const LockedScreen({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0B1E),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: const Color(0xFF2A1010),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                      color: const Color(0xFFE53E3E).withValues(alpha: 0.3)),
                ),
                child: const Icon(Icons.lock_outline,
                    color: Color(0xFFE53E3E), size: 52),
              ),
              const SizedBox(height: 24),
              Text(
                'Account Locked',
                style: GoogleFonts.outfit(
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                message ?? 'Too many failed attempts.',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white54, fontSize: 14),
              ),
              const SizedBox(height: 32),
              TextButton(
                onPressed: () => Navigator.popUntil(
                    context, (r) => r.isFirst),
                child: const Text(
                  'Back to Welcome',
                  style: TextStyle(color: Color(0xFF9F97FF)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
