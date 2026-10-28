// lib/widgets/progress_dots.dart
// Progress indicator showing how many nodes have been completed.

import 'package:flutter/material.dart';

class ProgressDots extends StatelessWidget {
  final int total;
  final int completed;

  const ProgressDots({
    super.key,
    required this.total,
    required this.completed,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(total, (i) {
        final done = i < completed;
        final active = i == completed;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          margin: const EdgeInsets.symmetric(horizontal: 3),
          width: active ? 14 : 8,
          height: 8,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            color: done
                ? const Color(0xFF6C63FF)
                : active
                    ? const Color(0xFF9F97FF)
                    : Colors.white24,
          ),
        );
      }),
    );
  }
}
