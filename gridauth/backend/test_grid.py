"""
Quick smoke-test for the new build_grid() algorithm.
Run: python test_grid.py
"""
import sys
sys.path.insert(0, ".")

from app.services.grid_service import build_grid

def verify(password: str, ghost_count: int = 2, k: int = 4):
    password_chars = list(password)
    nodes, real_node_indices = build_grid(password_chars, k, ghost_count)
    total = len(password_chars) + ghost_count

    print(f"\nPassword: {password!r}  ghost={ghost_count}  k={k}")
    print(f"Total nodes: {len(nodes)}  real_node_indices: {real_node_indices}")

    # Print each node
    for node in sorted(nodes, key=lambda n: n.node_index):
        kind = "REAL" if node._is_real else "GHOST"
        expected_char = password_chars[node._password_position] if node._is_real else "-"
        print(f"  Node {node.node_index} [{kind}] pw_pos={node._password_position:2d}  "
              f"expected={expected_char}  options={node.chars}")

    # === Verify exclusion rule ===
    # Track which password chars have been used and when (their real node index)
    # A char is "banned" after its LAST occurrence in password_chars has been placed.
    # For simplicity: check that no char appears in TWO DIFFERENT nodes,
    # UNLESS it's a password char that appears multiple times (it reuses legitimately).
    # Simpler rule: each node's chars must be disjoint from all EARLIER nodes' chars,
    # EXCEPT for password chars that appear multiple times.
    seen_chars: set[str] = set()
    errors = []
    # Build set of chars that can legitimately repeat (pw chars used multiple times)
    pw_char_set = set(password_chars)
    for node in sorted(nodes, key=lambda n: n.node_index):
        for ch in node.chars:
            if ch in seen_chars and ch not in pw_char_set:
                errors.append(
                    f"Node {node.node_index}: non-pw char {ch!r} already appeared in a prior node!"
                )
        seen_chars.update(node.chars)

    # === Verify real nodes appear in password order ===
    for pw_idx, display_idx in enumerate(real_node_indices):
        node = next(n for n in nodes if n.node_index == display_idx)
        expected = password_chars[pw_idx]
        if expected not in node.chars:
            errors.append(
                f"Real node {display_idx} (pw[{pw_idx}]={expected!r}) missing from options {node.chars}"
            )

    # === Verify total node count ===
    if len(nodes) != total:
        errors.append(f"Expected {total} nodes, got {len(nodes)}")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
        return False
    else:
        print("  ✓ All checks passed")
        return True


all_ok = True
all_ok &= verify("12ab", ghost_count=2)
all_ok &= verify("1234abcD", ghost_count=2)
all_ok &= verify("abc123", ghost_count=3)
all_ok &= verify("Aa1Bb2", ghost_count=0)   # no ghost nodes
all_ok &= verify("Pass1!", ghost_count=4)   # more ghosts than real
# Run many times to check randomness doesn't break invariants
import random
for _ in range(50):
    pw = ''.join(random.choices("ABCDEFabcdef0123456789", k=6))
    all_ok &= verify(pw, ghost_count=2)

print("\n" + ("✓ ALL TESTS PASSED" if all_ok else "✗ SOME TESTS FAILED"))
