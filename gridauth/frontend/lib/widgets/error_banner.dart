// lib/widgets/error_banner.dart

import 'package:flutter/material.dart';

class ErrorBanner extends StatelessWidget {
  final String message;
  final VoidCallback? onDismiss;

  const ErrorBanner({super.key, required this.message, this.onDismiss});

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF3D1A1A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE53E3E).withValues(alpha: 0.5)),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded,
              color: Color(0xFFFC8181), size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: Color(0xFFFC8181),
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          if (onDismiss != null)
            GestureDetector(
              onTap: onDismiss,
              child: const Icon(Icons.close,
                  color: Color(0xFFFC8181), size: 18),
            ),
        ],
      ),
    );
  }
}
