// lib/screens/registration_screen.dart
//
// FR-01: User registration with randomized on-screen keyboard.
// Shows both Password and Confirm Password fields simultaneously.
// Eye-icon toggles reveal/hide for each field.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/randomized_keyboard.dart';
import '../widgets/error_banner.dart';
import '../widgets/loading_overlay.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _usernameController = TextEditingController();
  String _password = '';
  String _confirmPassword = '';

  /// Which field the keyboard currently types into: 'password' or 'confirm'
  String _activeField = 'password';

  bool _showPassword = false;
  bool _showConfirm = false;
  bool _isLoading = false;
  String? _error;
  String? _success;

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  // ------------------------------------------------------------------ //
  // Display helpers
  // ------------------------------------------------------------------ //

  String _mask(String value, bool visible) =>
      visible ? value : '•' * value.length;

  // ------------------------------------------------------------------ //
  // Keyboard callbacks
  // ------------------------------------------------------------------ //

  void _onChar(String c) {
    setState(() {
      if (_activeField == 'password') {
        _password += c;
      } else {
        _confirmPassword += c;
      }
      _error = null;
    });
  }

  void _onDelete() {
    setState(() {
      if (_activeField == 'password' && _password.isNotEmpty) {
        _password = _password.substring(0, _password.length - 1);
      } else if (_activeField == 'confirm' && _confirmPassword.isNotEmpty) {
        _confirmPassword =
            _confirmPassword.substring(0, _confirmPassword.length - 1);
      }
    });
  }

  void _onConfirm() {
    _submit();
  }

  // ------------------------------------------------------------------ //
  // Validation & submission
  // ------------------------------------------------------------------ //

  String? _validatePassword(String pw) {
    if (pw.length < 8) return 'Password must be at least 8 characters.';
    if (!pw.contains(RegExp(r'[A-Z]'))) {
      return 'Password needs an uppercase letter.';
    }
    if (!pw.contains(RegExp(r'[a-z]'))) {
      return 'Password needs a lowercase letter.';
    }
    if (!pw.contains(RegExp(r'[0-9]'))) return 'Password needs a digit.';
    return null;
  }

  Future<void> _submit() async {
    final pwErr = _validatePassword(_password);
    if (pwErr != null) {
      setState(() => _error = pwErr);
      return;
    }
    if (_password != _confirmPassword) {
      setState(() => _error = 'Passwords do not match.');
      return;
    }
    final username = _usernameController.text.trim();
    if (username.length < 3) {
      setState(() => _error = 'Username must be at least 3 characters.');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final api = context.read<ApiService>();
    try {
      await api.register(username, _password);
      if (mounted) {
        setState(() {
          _isLoading = false;
          _success = 'Account created! You can now sign in.';
          _password = '';
          _confirmPassword = '';
          _activeField = 'password';
        });
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = e.message;
          _password = '';
          _confirmPassword = '';
          _activeField = 'password';
        });
      }
    }
  }

  // ------------------------------------------------------------------ //
  // Password field widget (shared between password & confirm)
  // ------------------------------------------------------------------ //

  Widget _buildPasswordField({
    required String label,
    required String fieldKey,
    required String value,
    required bool visible,
    required VoidCallback onToggleVisibility,
    required String hint,
  }) {
    final isActive = _activeField == fieldKey;
    return GestureDetector(
      onTap: () => setState(() => _activeField = fieldKey),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: GoogleFonts.outfit(color: Colors.white60, fontSize: 13)),
          const SizedBox(height: 6),
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: const Color(0xFF1E1B38),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isActive
                    ? const Color(0xFF6C63FF)
                    : Colors.white.withValues(alpha: 0.06),
                width: isActive ? 1.5 : 1,
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.lock_outline,
                    color: Colors.white38, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: value.isEmpty
                      ? Text(
                          hint,
                          style: const TextStyle(
                              color: Colors.white24, fontSize: 13),
                        )
                      : Text(
                          _mask(value, visible),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            letterSpacing: 4,
                          ),
                        ),
                ),
                // Eye toggle button
                GestureDetector(
                  onTap: onToggleVisibility,
                  child: Icon(
                    visible ? Icons.visibility_off : Icons.visibility,
                    color: Colors.white38,
                    size: 20,
                  ),
                ),
              ],
            ),
          ),
          if (isActive)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                fieldKey == 'password'
                    ? 'Typing here — min 8 chars, upper + lower + digit'
                    : 'Re-enter your password to confirm',
                style: const TextStyle(color: Color(0xFF9F97FF), fontSize: 11),
              ),
            ),
        ],
      ),
    );
  }

  // ------------------------------------------------------------------ //
  // Build
  // ------------------------------------------------------------------ //

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
        title: Text(
          'Create Account',
          style: GoogleFonts.outfit(
            color: Colors.white,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      body: LoadingOverlay(
        isLoading: _isLoading,
        message: 'Creating account...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Success banner
              if (_success != null)
                Container(
                  padding: const EdgeInsets.all(14),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A3D1A),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                        color: Colors.greenAccent.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle, color: Colors.greenAccent),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(_success!,
                            style:
                                const TextStyle(color: Colors.greenAccent)),
                      ),
                    ],
                  ),
                ),

              // Error banner
              if (_error != null) ...[
                ErrorBanner(
                  message: _error!,
                  onDismiss: () => setState(() => _error = null),
                ),
                const SizedBox(height: 16),
              ],

              // Username
              Text('Username',
                  style: GoogleFonts.outfit(
                      color: Colors.white60, fontSize: 13)),
              const SizedBox(height: 6),
              TextField(
                controller: _usernameController,
                style: const TextStyle(color: Colors.white),
                keyboardType: TextInputType.text,
                autocorrect: false,
                decoration: InputDecoration(
                  filled: true,
                  fillColor: const Color(0xFF1E1B38),
                  hintText: 'e.g. john_doe',
                  hintStyle: const TextStyle(color: Colors.white30),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none,
                  ),
                  prefixIcon:
                      const Icon(Icons.person_outline, color: Colors.white38),
                ),
              ),
              const SizedBox(height: 20),

              // Password field
              _buildPasswordField(
                label: 'Set Password',
                fieldKey: 'password',
                value: _password,
                visible: _showPassword,
                onToggleVisibility: () =>
                    setState(() => _showPassword = !_showPassword),
                hint: 'tap keys below to type',
              ),
              const SizedBox(height: 16),

              // Confirm Password field (directly below Password)
              _buildPasswordField(
                label: 'Confirm Password',
                fieldKey: 'confirm',
                value: _confirmPassword,
                visible: _showConfirm,
                onToggleVisibility: () =>
                    setState(() => _showConfirm = !_showConfirm),
                hint: 'tap here, then type to confirm',
              ),
              const SizedBox(height: 20),

              // Randomized keyboard
              RandomizedKeyboard(
                onChar: _onChar,
                onDelete: _onDelete,
                onConfirm: _onConfirm,
              ),
              const SizedBox(height: 20),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text(
                    'Already have an account? Sign in',
                    style: TextStyle(color: Color(0xFF9F97FF)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
