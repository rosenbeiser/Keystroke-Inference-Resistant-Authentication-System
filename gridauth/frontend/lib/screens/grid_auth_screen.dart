// lib/screens/grid_auth_screen.dart
//
// FR-03 / FR-04: Sequential grid authentication screen.
//
// Interaction protocol:
//  1. Nodes are presented ONE AT A TIME in order (node 0 first, then 1, …).
//  2. Each node shows K character options. The user picks one.
//  3. The selected character is recorded and the next node appears.
//  4. After all N nodes, selections are submitted to the backend.
//  5. The backend checks selections at real node positions against the password.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';
import '../state/grid_state.dart';
import '../state/auth_state.dart';
import '../widgets/char_choice_widget.dart';
import '../widgets/progress_dots.dart';
import '../widgets/loading_overlay.dart';
import '../widgets/error_banner.dart';
import 'home_screen.dart';

class GridAuthScreen extends StatefulWidget {
  final String username;
  const GridAuthScreen({super.key, required this.username});

  @override
  State<GridAuthScreen> createState() => _GridAuthScreenState();
}

class _GridAuthScreenState extends State<GridAuthScreen> {
  bool _showChars = false;

  @override
  void initState() {
    super.initState();
    // Brief delay before showing first node choices for UX polish
    Future.delayed(const Duration(milliseconds: 350), () {
      if (mounted) setState(() => _showChars = true);
    });
  }

  void _handleResult(BuildContext context) {
    final grid = context.read<GridState>();
    final auth = context.read<AuthState>();

    if (grid.status == GridStatus.success) {
      if (grid.sessionToken != null) {
        auth.loginSuccess(
          token: grid.sessionToken!,
          expiresAt: grid.tokenExpiresAt ??
              DateTime.now().add(const Duration(hours: 1)),
          username: widget.username,
        );
      }
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
        (r) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GridState>(
      builder: (ctx, grid, _) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (grid.status == GridStatus.success) {
            _handleResult(context);
          }
        });

        final isSubmitting = grid.status == GridStatus.submitting;
        final isFailed = grid.status == GridStatus.failure;
        final isError = grid.status == GridStatus.error;
        final session = grid.session;
        final step = grid.selections.length; // 0-based current step
        final total = grid.totalNodes;

        return Scaffold(
          backgroundColor: const Color(0xFF0D0B1E),
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            title: Text(
              'Grid Authentication',
              style: GoogleFonts.outfit(color: Colors.white, fontSize: 18),
            ),
            actions: [
              TextButton.icon(
                onPressed: () {
                  grid.cancel();
                  Navigator.pop(context);
                },
                icon: const Icon(Icons.close, color: Colors.white54, size: 18),
                label: const Text('Cancel',
                    style: TextStyle(color: Colors.white54)),
              ),
            ],
          ),
          body: LoadingOverlay(
            isLoading: isSubmitting,
            message: 'Verifying...',
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 16),

                    // ── Progress bar & step label ──────────────────────
                    if (session != null) ...[
                      ProgressDots(total: total, completed: step),
                      const SizedBox(height: 10),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Character ${step + 1} of $total',
                            style: const TextStyle(
                                color: Colors.white54, fontSize: 13),
                          ),
                          // Filled dots progress indicator
                          Text(
                            '${((step / total) * 100).round()}%',
                            style: const TextStyle(
                                color: Color(0xFF9F97FF), fontSize: 13),
                          ),
                        ],
                      ),
                    ],

                    const SizedBox(height: 32),

                    // ── Instruction card ───────────────────────────────
                    if (session != null && !isFailed && !isError)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 20, vertical: 16),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E1B38),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                              color: Colors.white.withValues(alpha: 0.06)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Step ${step + 1} of $total',
                              style: GoogleFonts.outfit(
                                color: const Color(0xFF9F97FF),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 1.2,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Select a character',
                              style: GoogleFonts.outfit(
                                color: Colors.white,
                                fontSize: 17,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'If you see your next password character, tap it. Otherwise pick any.',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.45),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),

                    const SizedBox(height: 28),

                    // ── Error / failure banners ────────────────────────
                    if (isFailed)
                      ErrorBanner(
                        message:
                            grid.errorMessage ?? 'Authentication failed.',
                        onDismiss: () => grid.reset(),
                      ),
                    if (isError)
                      ErrorBanner(
                        message: grid.errorMessage ?? 'An error occurred.',
                        onDismiss: () => grid.reset(),
                      ),

                    // ── Character choice panel ─────────────────────────
                    if (session != null &&
                        !isFailed &&
                        !isError &&
                        _showChars &&
                        grid.activeNode != null &&
                        !isSubmitting)
                      FadeInUp(
                        duration: const Duration(milliseconds: 220),
                        child: CharChoiceWidget(
                          chars: grid.activeNode!.chars,
                          onSelect: (c) async {
                            setState(() => _showChars = false);
                            await grid.selectChar(c);
                            if (mounted &&
                                grid.status == GridStatus.active) {
                              Future.delayed(
                                const Duration(milliseconds: 200),
                                () {
                                  if (mounted) {
                                    setState(() => _showChars = true);
                                  }
                                },
                              );
                            }
                          },
                        ),
                      ),

                    const Spacer(),

                    // ── Retry button after failure ─────────────────────
                    if (isFailed || isError) ...[
                      GestureDetector(
                        onTap: () async {
                          grid.reset();
                          await grid.startSession(widget.username);
                          if (mounted &&
                              grid.status == GridStatus.active) {
                            setState(() => _showChars = true);
                          }
                        },
                        child: Container(
                          width: double.infinity,
                          height: 52,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [
                                Color(0xFF6C63FF),
                                Color(0xFF48A8F8)
                              ],
                            ),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Center(
                            child: Text(
                              'Try Again',
                              style: GoogleFonts.outfit(
                                  fontSize: 16,
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                    ],
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
