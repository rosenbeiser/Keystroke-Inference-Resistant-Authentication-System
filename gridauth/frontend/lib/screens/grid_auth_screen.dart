// lib/screens/grid_auth_screen.dart
//
// FR-03 / FR-04: The main grid authentication screen.
//
// Interaction protocol:
//  1. Nodes appear in a grid. All look identical.
//  2. One node activates at a time (index 0 → N-1).
//  3. The active node expands showing K character options.
//  4. User selects one character → recorded in order.
//  5. Next node activates.
//  6. After all N nodes, selections are submitted to the backend.
//  7. Backend extracts selections at REAL node positions (server-known)
//     and compares them against the password IN ORDER.
//  8. Client shows success or failure result.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';
import '../state/grid_state.dart';
import '../state/auth_state.dart';
import '../widgets/grid_node_widget.dart';
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
    // Show the character options after a brief delay for UX
    Future.delayed(const Duration(milliseconds: 400), () {
      if (mounted) setState(() => _showChars = true);
    });
  }

  void _handleResult(BuildContext context) {
    final grid = context.read<GridState>();
    final auth = context.read<AuthState>();

    if (grid.status == GridStatus.success) {
      // Persist session token
      if (grid.sessionToken != null) {
        auth.loginSuccess(
          token: grid.sessionToken!,
          expiresAt: grid.tokenExpiresAt ?? DateTime.now().add(const Duration(hours: 1)),
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
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: [
                    const SizedBox(height: 12),
                    // Progress
                    if (session != null)
                      ProgressDots(
                        total: grid.totalNodes,
                        completed: grid.selections.length,
                      ),
                    const SizedBox(height: 8),
                    Text(
                      session != null
                          ? 'Step ${grid.selections.length + 1} of ${grid.totalNodes}'
                          : '',
                      style: const TextStyle(
                          color: Colors.white38, fontSize: 12),
                    ),
                    const SizedBox(height: 20),
                    // Error/failure banners
                    if (isFailed)
                      ErrorBanner(
                        message: grid.errorMessage ?? 'Authentication failed.',
                        onDismiss: () => grid.reset(),
                      ),
                    if (isError)
                      ErrorBanner(
                        message: grid.errorMessage ?? 'An error occurred.',
                        onDismiss: () => grid.reset(),
                      ),
                    // Grid
                    if (session != null && !isFailed && !isError)
                      Expanded(
                        child: Column(
                          children: [
                            // Node grid
                            Expanded(
                              child: _NodeGrid(
                                nodes: session.nodes,
                                activeIndex: grid.activeNodeIndex,
                                completedCount: grid.selections.length,
                              ),
                            ),
                            // Active node character options
                            if (_showChars && grid.activeNode != null && !isSubmitting)
                              FadeInUp(
                                duration: const Duration(milliseconds: 200),
                                child: CharChoiceWidget(
                                  chars: grid.activeNode!.chars,
                                  onSelect: (c) async {
                                    setState(() => _showChars = false);
                                    await grid.selectChar(c);
                                    if (mounted && grid.status == GridStatus.active) {
                                      Future.delayed(
                                        const Duration(milliseconds: 200),
                                        () {
                                          if (mounted) setState(() => _showChars = true);
                                        },
                                      );
                                    }
                                  },
                                ),
                              ),
                            const SizedBox(height: 20),
                          ],
                        ),
                      ),
                    // Retry button after failure
                    if (isFailed || isError) ...[
                      const SizedBox(height: 16),
                      GestureDetector(
                        onTap: () async {
                          grid.reset();
                          await grid.startSession(widget.username);
                          if (mounted && grid.status == GridStatus.active) {
                            setState(() => _showChars = true);
                          }
                        },
                        child: Container(
                          height: 52,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFF6C63FF), Color(0xFF48A8F8)],
                            ),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Center(
                            child: Text('Try Again',
                                style: GoogleFonts.outfit(
                                    fontSize: 16,
                                    color: Colors.white,
                                    fontWeight: FontWeight.w600)),
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

class _NodeGrid extends StatelessWidget {
  final List nodes;
  final int activeIndex;
  final int completedCount;

  const _NodeGrid({
    required this.nodes,
    required this.activeIndex,
    required this.completedCount,
  });

  @override
  Widget build(BuildContext context) {
    final sorted = List.from(nodes)
      ..sort((a, b) => a.nodeIndex.compareTo(b.nodeIndex));
    final count = sorted.length;
    final cols = count <= 6 ? 3 : 4;

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.all(12),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: cols,
        mainAxisSpacing: 14,
        crossAxisSpacing: 14,
        childAspectRatio: 1,
      ),
      itemCount: count,
      itemBuilder: (ctx, i) {
        final node = sorted[i];
        final idx = node.nodeIndex as int;
        NodeState ns;
        if (idx < completedCount) {
          ns = NodeState.done;
        } else if (idx == activeIndex) {
          ns = NodeState.active;
        } else {
          ns = NodeState.waiting;
        }
        return GridNodeWidget(
          nodeIndex: idx,
          nodeState: ns,
        );
      },
    );
  }
}
