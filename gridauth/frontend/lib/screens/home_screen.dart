// lib/screens/home_screen.dart
//
// FR-07: Protected home screen after successful authentication.
// Session token is validated server-side. Logout revokes the token.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';
import '../state/auth_state.dart';
import '../widgets/loading_overlay.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Consumer<AuthState>(
      builder: (ctx, auth, _) {
        return LoadingOverlay(
          isLoading: auth.isLoading,
          message: 'Signing out...',
          child: Scaffold(
            backgroundColor: const Color(0xFF0D0B1E),
            body: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 20),
                    // Header
                    FadeInDown(
                      child: Row(
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF6C63FF), Color(0xFF48A8F8)],
                              ),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Center(
                              child: Text(
                                (auth.username ?? 'U')[0].toUpperCase(),
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 22,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Welcome back,',
                                  style: GoogleFonts.outfit(
                                    color: Colors.white54,
                                    fontSize: 13,
                                  ),
                                ),
                                Text(
                                  auth.username ?? 'User',
                                  style: GoogleFonts.outfit(
                                    color: Colors.white,
                                    fontSize: 20,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 32),
                    // Status card
                    FadeInUp(
                      delay: const Duration(milliseconds: 100),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              const Color(0xFF6C63FF).withValues(alpha: 0.15),
                              const Color(0xFF48A8F8).withValues(alpha: 0.08),
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: const Color(0xFF6C63FF).withValues(alpha: 0.3),
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.greenAccent.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(
                                        color: Colors.greenAccent.withValues(alpha: 0.4)),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Container(
                                        width: 6,
                                        height: 6,
                                        decoration: const BoxDecoration(
                                          color: Colors.greenAccent,
                                          shape: BoxShape.circle,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      const Text(
                                        'Authenticated',
                                        style: TextStyle(
                                          color: Colors.greenAccent,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Grid Authentication\nSuccessful',
                              style: GoogleFonts.outfit(
                                color: Colors.white,
                                fontSize: 22,
                                fontWeight: FontWeight.w700,
                                height: 1.3,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'You authenticated through a randomized 2D grid. '
                              'Your password was never transmitted directly.',
                              style: GoogleFonts.outfit(
                                color: Colors.white54,
                                fontSize: 13,
                                height: 1.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    // Info cards
                    FadeInUp(
                      delay: const Duration(milliseconds: 200),
                      child: _InfoCard(
                        icon: Icons.shield_outlined,
                        title: 'Shoulder-Surf Resistant',
                        body:
                            'Each session uses a newly randomized grid. Observers see characters but cannot determine which nodes are real.',
                      ),
                    ),
                    const SizedBox(height: 12),
                    FadeInUp(
                      delay: const Duration(milliseconds: 300),
                      child: _InfoCard(
                        icon: Icons.replay_outlined,
                        title: 'Replay Attack Protected',
                        body:
                            'Grid sessions use single-use nonces that expire after use. Captured sessions cannot be replayed.',
                      ),
                    ),
                    const Spacer(),
                    // Logout
                    FadeInUp(
                      delay: const Duration(milliseconds: 400),
                      child: GestureDetector(
                        onTap: () async {
                          await auth.logout();
                          if (context.mounted) {
                            Navigator.pushNamedAndRemoveUntil(
                              context,
                              '/',
                              (r) => false,
                            );
                          }
                        },
                        child: Container(
                          width: double.infinity,
                          height: 54,
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E1B38),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                                color: Colors.white12),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.logout,
                                  color: Colors.white60, size: 20),
                              const SizedBox(width: 10),
                              Text(
                                'Sign Out',
                                style: GoogleFonts.outfit(
                                  color: Colors.white70,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  const _InfoCard(
      {required this.icon, required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1B38),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: const Color(0xFF9F97FF), size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: GoogleFonts.outfit(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text(body,
                    style: GoogleFonts.outfit(
                        color: Colors.white54,
                        fontSize: 12,
                        height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
