// lib/widgets/char_choice_widget.dart
//
// Displays K character options when a node is active.
// All nodes have identical visual treatment — no indication of real vs ghost.

import 'package:flutter/material.dart';
import 'package:animate_do/animate_do.dart';

class CharChoiceWidget extends StatelessWidget {
  final List<String> chars;
  final void Function(String) onSelect;

  const CharChoiceWidget({
    super.key,
    required this.chars,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return FadeInUp(
      duration: const Duration(milliseconds: 200),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1B3A),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF6C63FF).withValues(alpha: 0.4)),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF6C63FF).withValues(alpha: 0.15),
              blurRadius: 20,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Select a character',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.6),
                fontSize: 12,
                letterSpacing: 1.2,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              alignment: WrapAlignment.center,
              children: chars.map((c) => _CharButton(char: c, onTap: onSelect)).toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _CharButton extends StatefulWidget {
  final String char;
  final void Function(String) onTap;

  const _CharButton({required this.char, required this.onTap});

  @override
  State<_CharButton> createState() => _CharButtonState();
}

class _CharButtonState extends State<_CharButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 100));
    _scale = Tween<double>(begin: 1.0, end: 0.92).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) {
        _controller.reverse();
        widget.onTap(widget.char);
      },
      onTapCancel: () => _controller.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF6C63FF), Color(0xFF48A8F8)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF6C63FF).withValues(alpha: 0.35),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Center(
            child: Text(
              widget.char,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.bold,
                fontFamily: 'monospace',
              ),
            ),
          ),
        ),
      ),
    );
  }
}
