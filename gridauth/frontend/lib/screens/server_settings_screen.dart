// lib/screens/server_settings_screen.dart
//
// Lets the user enter the backend server URL once and saves it locally.
// Never needs a rebuild — the app reads this value at runtime.

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/server_config_service.dart';

class ServerSettingsScreen extends StatefulWidget {
  const ServerSettingsScreen({super.key});

  @override
  State<ServerSettingsScreen> createState() => _ServerSettingsScreenState();
}

class _ServerSettingsScreenState extends State<ServerSettingsScreen> {
  final _controller = TextEditingController();
  bool _isTesting = false;
  String? _testResult;
  bool _testOk = false;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _loadCurrent();
  }

  Future<void> _loadCurrent() async {
    final url = await ServerConfigService.getBaseUrl();
    _controller.text = url;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String _normalize(String raw) =>
      raw.trim().replaceAll(RegExp(r'/+$'), '');

  Future<void> _testConnection() async {
    final url = _normalize(_controller.text);
    if (url.isEmpty) return;

    setState(() {
      _isTesting = true;
      _testResult = null;
      _testOk = false;
      _saved = false;
    });

    try {
      final uri = Uri.parse('$url/health');
      final response =
          await http.get(uri).timeout(const Duration(seconds: 5));
      final ok = response.statusCode == 200;
      if (!mounted) return;
      setState(() {
        _testOk = ok;
        _testResult = ok
            ? '✓ Connected successfully!'
            : '✗ Server responded but /health check failed (${response.statusCode}).';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _testOk = false;
        _testResult = '✗ Cannot reach server. Check the IP and port.';
      });
    } finally {
      if (mounted) {
        setState(() => _isTesting = false);
      }
    }
  }

  Future<void> _save() async {
    final url = _normalize(_controller.text);
    if (url.isEmpty) return;

    await ServerConfigService.setBaseUrl(url);

    // Update the live ApiService instance
    if (mounted) {
      context.read<ApiService>().updateBaseUrl(url);
    }

    setState(() => _saved = true);
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
          'Server Settings',
          style: GoogleFonts.outfit(
              color: Colors.white, fontWeight: FontWeight.w600),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Info card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E1B38),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                      color: const Color(0xFF6C63FF).withValues(alpha: 0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.info_outline,
                            color: Color(0xFF9F97FF), size: 18),
                        const SizedBox(width: 8),
                        Text(
                          'How to find your server IP',
                          style: GoogleFonts.outfit(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    _step('1',
                        'On your PC, open PowerShell and run: ipconfig'),
                    _step('2',
                        'Find "IPv4 Address" under "Wireless LAN adapter Wi-Fi"'),
                    _step('3',
                        'Enter it below as: http://192.168.x.x:8000'),
                    _step('4', 'Tap "Test & Save" — done! No rebuild needed.'),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              Text('Backend Server URL',
                  style: GoogleFonts.outfit(
                      color: Colors.white60, fontSize: 13)),
              const SizedBox(height: 8),
              TextField(
                controller: _controller,
                style: const TextStyle(color: Colors.white, fontSize: 15),
                keyboardType: TextInputType.url,
                autocorrect: false,
                enableSuggestions: false,
                onChanged: (_) => setState(() {
                  _testResult = null;
                  _saved = false;
                }),
                decoration: InputDecoration(
                  filled: true,
                  fillColor: const Color(0xFF1E1B38),
                  hintText: 'http://192.168.x.x:8000',
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
                  prefixIcon: const Icon(Icons.dns_outlined,
                      color: Colors.white38),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your phone and PC must be on the same Wi-Fi network.',
                style: TextStyle(color: Colors.white38, fontSize: 11),
              ),
              const SizedBox(height: 24),

              // Test result banner
              if (_testResult != null)
                AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: _testOk
                        ? const Color(0xFF1A3D1A)
                        : const Color(0xFF3D1A1A),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: _testOk
                          ? Colors.greenAccent.withValues(alpha: 0.4)
                          : Colors.redAccent.withValues(alpha: 0.4),
                    ),
                  ),
                  child: Text(
                    _testResult!,
                    style: TextStyle(
                      color: _testOk ? Colors.greenAccent : Colors.redAccent,
                      fontSize: 13,
                    ),
                  ),
                ),

              if (_saved)
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A3D1A),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                        color: Colors.greenAccent.withValues(alpha: 0.4)),
                  ),
                  child: const Text(
                    '✓ Saved! The app will use this server URL from now on.',
                    style: TextStyle(color: Colors.greenAccent, fontSize: 13),
                  ),
                ),

              // Buttons
              Row(
                children: [
                  Expanded(
                    child: _OutlineBtn(
                      label: _isTesting ? 'Testing…' : 'Test Connection',
                      icon: Icons.wifi_tethering,
                      onTap: _isTesting ? null : _testConnection,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _FilledBtn(
                      label: 'Save',
                      icon: Icons.save_outlined,
                      onTap: _save,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _step(String num, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 20,
            height: 20,
            margin: const EdgeInsets.only(right: 10, top: 1),
            decoration: BoxDecoration(
              color: const Color(0xFF6C63FF).withValues(alpha: 0.25),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(num,
                  style: const TextStyle(
                      color: Color(0xFF9F97FF),
                      fontSize: 11,
                      fontWeight: FontWeight.bold)),
            ),
          ),
          Expanded(
            child: Text(text,
                style:
                    const TextStyle(color: Colors.white60, fontSize: 12.5)),
          ),
        ],
      ),
    );
  }
}

// ── Button widgets ────────────────────────────────────────────────────────
class _FilledBtn extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  const _FilledBtn({required this.label, required this.icon, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
              colors: [Color(0xFF6C63FF), Color(0xFF48A8F8)]),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 18),
            const SizedBox(width: 8),
            Text(label,
                style: const TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}

class _OutlineBtn extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  const _OutlineBtn({required this.label, required this.icon, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          border: Border.all(
              color: const Color(0xFF6C63FF).withValues(alpha: 0.5)),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon,
                color: onTap == null ? Colors.white24 : const Color(0xFF9F97FF),
                size: 18),
            const SizedBox(width: 8),
            Text(label,
                style: TextStyle(
                    color: onTap == null ? Colors.white24 : Colors.white70,
                    fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}

