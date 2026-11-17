// lib/screens/registration_screen.dart
//
// FR-01: User registration with the device's standard QWERTY keyboard.
// Shows both Password and Confirm Password fields simultaneously.
// Eye-icon toggles reveal/hide for each field.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/error_banner.dart';
import '../widgets/loading_overlay.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();

  final _passwordFocus = FocusNode();
  final _confirmFocus = FocusNode();

  // Security level chosen by the user: 'normal' | 'strong' | 'powerful'
  String _securityLevel = 'normal';

  bool _showPassword = false;
  bool _showConfirm = false;
  bool _isLoading = false;
  String? _error;
  String? _success;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _passwordFocus.dispose();
    _confirmFocus.dispose();
    super.dispose();
  }

  // ------------------------------------------------------------------ //
  // Validation & submission
  // ------------------------------------------------------------------ //

  String? _validatePassword(String pw) {
    if (pw.length < 6) return 'Password must be at least 6 characters.';
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
    final password = _passwordController.text;
    final confirm = _confirmController.text;

    final pwErr = _validatePassword(password);
    if (pwErr != null) {
      setState(() => _error = pwErr);
      return;
    }
    if (password != confirm) {
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
      await api.register(username, password, securityLevel: _securityLevel);
      if (mounted) {
        setState(() {
          _isLoading = false;
          _success = 'Account created! You can now sign in.';
          _passwordController.clear();
          _confirmController.clear();
        });
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = e.message;
          _passwordController.clear();
          _confirmController.clear();
        });
      }
    }
  }

  // ------------------------------------------------------------------ //
  // Build
  // ------------------------------------------------------------------ //

  InputDecoration _fieldDecoration({
    required String hint,
    required IconData prefixIcon,
    required bool visible,
    required VoidCallback onToggle,
  }) {
    return InputDecoration(
      filled: true,
      fillColor: const Color(0xFF1E1B38),
      hintText: hint,
      hintStyle: const TextStyle(color: Colors.white30),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF6C63FF), width: 1.5),
      ),
      prefixIcon: Icon(prefixIcon, color: Colors.white38, size: 20),
      suffixIcon: IconButton(
        icon: Icon(
          visible ? Icons.visibility_off : Icons.visibility,
          color: Colors.white38,
          size: 20,
        ),
        onPressed: onToggle,
      ),
    );
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
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Success banner ──────────────────────────────────────
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
                        const Icon(Icons.check_circle,
                            color: Colors.greenAccent),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(_success!,
                              style:
                                  const TextStyle(color: Colors.greenAccent)),
                        ),
                      ],
                    ),
                  ),

                // ── Error banner ────────────────────────────────────────
                if (_error != null) ...[
                  ErrorBanner(
                    message: _error!,
                    onDismiss: () => setState(() => _error = null),
                  ),
                  const SizedBox(height: 16),
                ],

                // ── Username ────────────────────────────────────────────
                Text('Username',
                    style: GoogleFonts.outfit(
                        color: Colors.white60, fontSize: 13)),
                const SizedBox(height: 6),
                TextField(
                  controller: _usernameController,
                  style: const TextStyle(color: Colors.white),
                  keyboardType: TextInputType.text,
                  autocorrect: false,
                  enableSuggestions: false,
                  textInputAction: TextInputAction.next,
                  onSubmitted: (_) =>
                      FocusScope.of(context).requestFocus(_passwordFocus),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: const Color(0xFF1E1B38),
                    hintText: 'e.g. john_doe',
                    hintStyle: const TextStyle(color: Colors.white30),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none,
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(
                          color: Color(0xFF6C63FF), width: 1.5),
                    ),
                    prefixIcon: const Icon(Icons.person_outline,
                        color: Colors.white38),
                  ),
                ),
                const SizedBox(height: 20),

                // ── Password ────────────────────────────────────────────
                Text('Set Password',
                    style: GoogleFonts.outfit(
                        color: Colors.white60, fontSize: 13)),
                const SizedBox(height: 6),
                TextField(
                  controller: _passwordController,
                  focusNode: _passwordFocus,
                  style: const TextStyle(color: Colors.white),
                  obscureText: !_showPassword,
                  autocorrect: false,
                  enableSuggestions: false,
                  textInputAction: TextInputAction.next,
                  onSubmitted: (_) =>
                      FocusScope.of(context).requestFocus(_confirmFocus),
                  decoration: _fieldDecoration(
                    hint: 'Min 6 chars, upper + lower + digit',
                    prefixIcon: Icons.lock_outline,
                    visible: _showPassword,
                    onToggle: () =>
                        setState(() => _showPassword = !_showPassword),
                  ),
                ),
                const SizedBox(height: 16),

                // ── Confirm Password ────────────────────────────────────
                Text('Confirm Password',
                    style: GoogleFonts.outfit(
                        color: Colors.white60, fontSize: 13)),
                const SizedBox(height: 6),
                TextField(
                  controller: _confirmController,
                  focusNode: _confirmFocus,
                  style: const TextStyle(color: Colors.white),
                  obscureText: !_showConfirm,
                  autocorrect: false,
                  enableSuggestions: false,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _submit(),
                  decoration: _fieldDecoration(
                    hint: 'Re-enter your password',
                    prefixIcon: Icons.lock_outline,
                    visible: _showConfirm,
                    onToggle: () =>
                        setState(() => _showConfirm = !_showConfirm),
                  ),
                ),
                const SizedBox(height: 8),

                // ── Password rules hint ─────────────────────────────────
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 4),
                  child: Text(
                    'At least 6 characters · one uppercase · one lowercase · one digit',
                    style: TextStyle(color: Color(0xFF9F97FF), fontSize: 11),
                  ),
                ),
                const SizedBox(height: 24),

                // ── Security Level Selector ─────────────────────────────
                Text('Authentication Security Level',
                    style: GoogleFonts.outfit(
                        color: Colors.white60, fontSize: 13)),
                const SizedBox(height: 10),
                _SecurityLevelSelector(
                  selected: _securityLevel,
                  onChanged: (level) =>
                      setState(() => _securityLevel = level),
                ),
                const SizedBox(height: 28),

                // ── Submit button ───────────────────────────────────────
                GestureDetector(
                  onTap: _submit,
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
                    child: Center(
                      child: Text(
                        'Create Account',
                        style: GoogleFonts.outfit(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                Center(
                  child: TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text(
                      'Already have an account? Sign in',
                      style:
                          TextStyle(color: Color(0xFF9F97FF), fontSize: 14),
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

// ─────────────────────────────────────────────────────────────────────────────
// Security Level Selector Widget
// ─────────────────────────────────────────────────────────────────────────────

class _SecurityLevelOption {
  final String value;
  final String label;
  final String subtitle;
  final String example; // ghost count example for a 6-char password
  final IconData icon;
  const _SecurityLevelOption({
    required this.value,
    required this.label,
    required this.subtitle,
    required this.example,
    required this.icon,
  });
}

const _kLevels = [
  _SecurityLevelOption(
    value: 'normal',
    label: 'Normal',
    subtitle: 'Balanced security & speed',
    example: '~2 ghost nodes per 6 chars',
    icon: Icons.shield_outlined,
  ),
  _SecurityLevelOption(
    value: 'strong',
    label: 'Strong',
    subtitle: 'More ghost nodes, harder to guess',
    example: '~3 ghost nodes per 6 chars',
    icon: Icons.security,
  ),
  _SecurityLevelOption(
    value: 'powerful',
    label: 'Powerful',
    subtitle: 'Equal ghost & real nodes',
    example: '~6 ghost nodes per 6 chars',
    icon: Icons.verified_user,
  ),
];

class _SecurityLevelSelector extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;

  const _SecurityLevelSelector({
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _kLevels.map((opt) {
        final isSelected = selected == opt.value;
        return GestureDetector(
          onTap: () => onChanged(opt.value),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: isSelected
                  ? const Color(0xFF6C63FF).withValues(alpha: 0.15)
                  : const Color(0xFF1E1B38),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: isSelected
                    ? const Color(0xFF6C63FF)
                    : Colors.white.withValues(alpha: 0.08),
                width: isSelected ? 1.5 : 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: isSelected
                        ? const Color(0xFF6C63FF).withValues(alpha: 0.25)
                        : Colors.white.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    opt.icon,
                    color: isSelected
                        ? const Color(0xFF6C63FF)
                        : Colors.white38,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        opt.label,
                        style: GoogleFonts.outfit(
                          color:
                              isSelected ? Colors.white : Colors.white70,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        opt.subtitle,
                        style: TextStyle(
                          color: isSelected
                              ? Colors.white60
                              : Colors.white38,
                          fontSize: 11,
                        ),
                      ),
                      Text(
                        opt.example,
                        style: TextStyle(
                          color: isSelected
                              ? const Color(0xFF9F97FF)
                              : Colors.white24,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ),
                if (isSelected)
                  const Icon(Icons.check_circle,
                      color: Color(0xFF6C63FF), size: 20)
                else
                  const Icon(Icons.radio_button_unchecked,
                      color: Colors.white24, size: 20),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}
