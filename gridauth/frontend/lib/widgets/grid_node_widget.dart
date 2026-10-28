// lib/widgets/grid_node_widget.dart
//
// Displays a single grid node.
// CRITICAL SECURITY: All nodes have IDENTICAL visual treatment.
// No color, size, border, animation, or accessibility metadata difference
// between real and ghost nodes. The node_index and chars are the only data.

import 'package:flutter/material.dart';

enum NodeState { waiting, active, done }

class GridNodeWidget extends StatefulWidget {
  final int nodeIndex;
  final NodeState nodeState;
  final VoidCallback? onTap;

  const GridNodeWidget({
    super.key,
    required this.nodeIndex,
    required this.nodeState,
    this.onTap,
  });

  @override
  State<GridNodeWidget> createState() => _GridNodeWidgetState();
}

class _GridNodeWidgetState extends State<GridNodeWidget>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    if (widget.nodeState == NodeState.active) {
      _pulse.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(GridNodeWidget old) {
    super.didUpdateWidget(old);
    if (widget.nodeState == NodeState.active) {
      _pulse.repeat(reverse: true);
    } else {
      _pulse.stop();
      _pulse.value = 0;
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulse,
      builder: (ctx, _) {
        final isActive = widget.nodeState == NodeState.active;
        final isDone = widget.nodeState == NodeState.done;

        // Identical base appearance for all nodes
        final glowOpacity = isActive ? 0.2 + (_pulse.value * 0.3) : 0.0;
        final borderOpacity = isDone ? 0.3 : (isActive ? 0.8 : 0.2);

        return GestureDetector(
          onTap: isActive ? widget.onTap : null,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: isActive ? 68 : 56,
            height: isActive ? 68 : 56,
            decoration: BoxDecoration(
              // All nodes: same gradient, same border color
              gradient: LinearGradient(
                colors: isDone
                    ? [const Color(0xFF2A2745), const Color(0xFF1E1B38)]
                    : isActive
                        ? [const Color(0xFF3D3680), const Color(0xFF2A2460)]
                        : [const Color(0xFF1E1B38), const Color(0xFF161328)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: const Color(0xFF6C63FF).withValues(alpha: borderOpacity),
                width: 1.5,
              ),
              boxShadow: isActive
                  ? [
                      BoxShadow(
                        color: const Color(0xFF6C63FF).withValues(alpha: glowOpacity),
                        blurRadius: 16,
                        spreadRadius: 2,
                      ),
                    ]
                  : null,
            ),
            child: Center(
              child: isDone
                  ? Icon(Icons.check, color: Colors.white38, size: 20)
                  : isActive
                      ? Icon(
                          Icons.touch_app,
                          color: Colors.white.withValues(alpha: 0.85),
                          size: 24,
                          semanticLabel: 'Active node — tap to expand',
                        )
                      : Text(
                          '${widget.nodeIndex + 1}',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.3),
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                          semanticsLabel: 'Node ${widget.nodeIndex + 1}',
                        ),
            ),
          ),
        );
      },
    );
  }
}
