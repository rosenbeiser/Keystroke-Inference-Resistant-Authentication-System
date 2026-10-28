// lib/widgets/randomized_keyboard.dart
//
// A keyboard whose keys are randomized on every render/rebuild.
// Used for password entry during registration (FR-01).
// Randomization uses Dart's Random.secure() (CSPRNG).

import 'dart:math';
import 'package:flutter/material.dart';

class RandomizedKeyboard extends StatefulWidget {
  final void Function(String) onChar;
  final VoidCallback onDelete;
  final VoidCallback onConfirm;

  const RandomizedKeyboard({
    super.key,
    required this.onChar,
    required this.onDelete,
    required this.onConfirm,
  });

  @override
  State<RandomizedKeyboard> createState() => _RandomizedKeyboardState();
}

class _RandomizedKeyboardState extends State<RandomizedKeyboard> {
  late List<String> _keys;

  // Character pool: uppercase, lowercase, digits only (62 chars = 7 rows × 9 cols)
  static const _pool =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

  @override
  void initState() {
    super.initState();
    _shuffle();
  }

  void _shuffle() {
    final rng = Random.secure();
    final chars = _pool.split('');
    // Fisher-Yates with secure RNG
    for (int i = chars.length - 1; i > 0; i--) {
      final j = rng.nextInt(i + 1);
      final tmp = chars[i];
      chars[i] = chars[j];
      chars[j] = tmp;
    }
    _keys = chars;
  }

  void _reshuffleAndNotify() {
    setState(() => _shuffle());
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Reshuffle hint
        TextButton.icon(
          onPressed: _reshuffleAndNotify,
          icon: const Icon(Icons.shuffle, size: 14, color: Color(0xFF9F97FF)),
          label: const Text(
            'Shuffle keyboard',
            style: TextStyle(color: Color(0xFF9F97FF), fontSize: 12),
          ),
        ),
        LayoutBuilder(
          builder: (context, constraints) {
            // 9 columns with 4px spacing — compute exact height so last row is never cropped
            const crossAxisCount = 9;
            const spacing = 4.0;
            final cellSize =
                (constraints.maxWidth - spacing * (crossAxisCount - 1)) /
                    crossAxisCount;
            final rowCount = (_keys.length / crossAxisCount).ceil();
            final gridHeight =
                rowCount * cellSize + (rowCount - 1) * spacing;
            return SizedBox(
              height: gridHeight,
              child: GridView.builder(
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: crossAxisCount,
                  mainAxisSpacing: spacing,
                  crossAxisSpacing: spacing,
                ),
                itemCount: _keys.length,
                itemBuilder: (ctx, i) {
                  return _KeyButton(
                    char: _keys[i],
                    onTap: () => widget.onChar(_keys[i]),
                  );
                },
              ),
            );
          },
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _ActionButton(
              label: '⌫',
              color: const Color(0xFF3D3660),
              onTap: widget.onDelete,
            ),
            _ActionButton(
              label: '✓',
              color: const Color(0xFF27AE60),
              onTap: widget.onConfirm,
            ),
          ],
        ),
      ],
    );
  }
}

class _KeyButton extends StatelessWidget {
  final String char;
  final VoidCallback onTap;
  const _KeyButton({required this.char, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1E1B38),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: Colors.white12),
        ),
        child: Center(
          child: Text(
            char,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 11,
              fontFamily: 'monospace',
            ),
          ),
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _ActionButton({required this.label, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 100,
        height: 44,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Center(
          child: Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}
