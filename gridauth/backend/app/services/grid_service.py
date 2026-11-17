"""
app/services/grid_service.py — Randomized grid construction (FR-03).

Design decisions (from spec):
  - Fisher-Yates shuffle using Python's secrets module (not random.shuffle)
  - Ghost nodes are randomly interspersed with real nodes (not all at end).
  - Nodes are generated sequentially in DISPLAY ORDER so that the exclusion
    set grows correctly: a character used in node i is excluded from all
    subsequent nodes i+1 … N-1, regardless of whether those are real or ghost.
  - Real nodes appear in password character order (real node 0 = pw[0], etc.)
    but their POSITIONS among all nodes are randomly assigned.
  - Decoy characters are globally unique across ALL nodes.
  - Ghost characters are drawn uniformly at random from the remaining pool.

Configuration:
  N = total nodes   (grid_total_nodes, default 10)
  L = real nodes    (grid_real_nodes, default 8)  = password_length
  G = ghost nodes   (grid_ghost_nodes, default 2)
  K = chars/node    (grid_chars_per_node, default 4)
  Invariant: N = L + G

If the actual password length differs from the configured L, N adjusts
so that L always equals password_length and G remains grid_ghost_nodes.
"""
from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass


# Character pool: all printable ASCII except whitespace (95 characters).
# Registration now uses the device's standard QWERTY keyboard, which can
# produce letters, digits, and punctuation — so the grid must draw decoys
# from the same expanded set so that any character the user typed can appear
# as a node option without exhausting the pool.
_CHAR_POOL = string.ascii_letters + string.digits + string.punctuation


# Security level labels exposed to the API.
SECURITY_LEVELS = frozenset({"normal", "strong", "powerful"})


def ghost_count_for_level(password_length: int, security_level: str) -> int:
    """
    Calculate the number of ghost nodes based on the user's chosen security level
    and the length of their password.

    Security levels and their ghost-node formulas:

      normal   — ceil(password_length / 3)   minimum 2
                 Roughly one ghost per three real nodes.
                 Good for quick logins with moderate protection.

      strong   — ceil(password_length / 2)   minimum 3
                 One ghost for every two real nodes.
                 Doubles the guessing effort for an attacker.

      powerful — password_length              minimum 4
                 Equal number of ghost and real nodes (50/50 split).
                 Maximum shoulder-surfing resistance; longer to complete.

    Example for a 6-character password:
      normal   → 2 ghosts  (8 nodes total)
      strong   → 3 ghosts  (9 nodes total)
      powerful → 6 ghosts  (12 nodes total)

    Example for a 10-character password:
      normal   → 4 ghosts  (14 nodes total)
      strong   → 5 ghosts  (15 nodes total)
      powerful → 10 ghosts (20 nodes total)
    """
    level = security_level.lower() if security_level else "normal"
    if level == "strong":
        return max(3, math.ceil(password_length / 2))
    if level == "powerful":
        return max(4, password_length)
    # default: normal
    return max(2, math.ceil(password_length / 3))


@dataclass
class GridNode:
    node_index: int          # sequential display position (0-based)
    chars: list[str]         # K character options shown to the user
    _is_real: bool           # NEVER sent to client
    _password_position: int  # index into password; -1 for ghost nodes


def _secure_shuffle(items: list) -> list:
    """
    Fisher-Yates shuffle using secrets.randbelow as the RNG.

    Python's random.shuffle uses the Mersenne Twister (not cryptographically
    secure).  This implementation uses os.urandom via secrets.randbelow,
    providing a uniformly random permutation suitable for security-critical use.
    """
    items = list(items)  # copy
    n = len(items)
    for i in range(n - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def _pick_decoys(correct_char: str, count: int, exclude: set[str]) -> list[str]:
    """
    Select `count` unique decoy characters from the pool.

    The correct character and any characters in `exclude` are not eligible.
    `exclude` carries all characters that have appeared in ANY previous node,
    enforcing the global no-repeat guarantee.
    """
    pool = [c for c in _CHAR_POOL if c != correct_char and c not in exclude]
    if len(pool) < count:
        # Fallback: relax exclude (should never happen with printable ASCII)
        pool = [c for c in _CHAR_POOL if c != correct_char]
    chosen: list[str] = []
    while len(chosen) < count and pool:
        idx = secrets.randbelow(len(pool))
        chosen.append(pool[idx])
        pool.pop(idx)
    return chosen


def _ghost_chars(count: int, exclude: set[str]) -> list[str]:
    """
    Generate `count` distinct random characters for a ghost node.

    Ghost characters have no relationship to the password.  They are drawn
    uniformly from the remaining pool (characters not yet seen in any node).
    """
    pool = [c for c in _CHAR_POOL if c not in exclude]
    if len(pool) < count:
        pool = list(_CHAR_POOL)
    chosen: list[str] = []
    while len(chosen) < count and pool:
        idx = secrets.randbelow(len(pool))
        chosen.append(pool[idx])
        pool.pop(idx)
    return chosen


def build_grid(
    password_chars: list[str],
    k: int,
    ghost_count: int,
) -> tuple[list[GridNode], list[int]]:
    """
    Build the complete randomized grid.

    Parameters
    ----------
    password_chars : list[str]
        Decrypted password characters in order.
    k : int
        Number of character options per node (K).
    ghost_count : int
        Number of ghost nodes to add (G).

    Returns
    -------
    (nodes, real_node_indices)
        nodes : list[GridNode] — ALL nodes in display order (index 0 … N-1).
            Ghost nodes appear at random positions mixed with real nodes.
        real_node_indices : list[int] — the display positions of real nodes,
            in password character order.
            MUST NEVER be sent to the client.

    Algorithm
    ---------
    1. Decide the real/ghost SEQUENCE first by shuffling a boolean mask
       (True=real, False=ghost). This determines the display position of
       every real and ghost node without yet knowing their characters.

    2. Walk through the shuffled sequence in display order (0 → N-1),
       building each node one at a time.  The global `excluded` set grows
       with every character that appears in any node, so later nodes —
       whether real or ghost — can never show a character from an earlier node.

    Security properties
    -------------------
    - Ghost nodes are randomly interspersed with real nodes (not at end).
    - Within each node the correct character's POSITION among the K options
      is randomly shuffled (the user still has to find it).
    - Characters are globally unique: a character shown in node i will
      never appear in nodes i+1 … N-1 (enforced in display order).
    - Ghost nodes draw from the remaining unused character pool.
    """
    password_length = len(password_chars)

    # ------------------------------------------------------------------ #
    # Step 1: Decide display positions for real vs ghost nodes
    # ------------------------------------------------------------------ #
    # True = real node, False = ghost node (in PASSWORD order for Trues).
    node_type_sequence: list[bool] = (
        [True] * password_length + [False] * ghost_count
    )
    node_type_sequence = _secure_shuffle(node_type_sequence)

    # ------------------------------------------------------------------ #
    # Step 2: Generate nodes in DISPLAY ORDER; exclusion set grows as we go
    # ------------------------------------------------------------------ #
    # Pre-reserve all password characters so they can never appear as decoys
    # or ghost chars in any node that precedes their designated real node.
    # They are removed from this reserve set as each real node is generated.
    reserved_pw_chars: set[str] = set(password_chars)

    excluded: set[str] = set()   # chars already used; excluded from all future nodes
    real_pw_idx: int = 0         # which password character comes next
    all_nodes: list[GridNode] = []
    real_positions_by_pw_idx: dict[int, int] = {}

    for display_idx, is_real in enumerate(node_type_sequence):
        if is_real:
            char = password_chars[real_pw_idx]
            # Release this char from the reserve so decoys for THIS node
            # don't need to avoid it; all OTHER reserved chars stay forbidden.
            reserved_pw_chars.discard(char)
            # Combined exclusion: already-used chars + still-reserved pw chars
            full_exclude = excluded | reserved_pw_chars
            full_exclude.add(char)  # decoys must not equal the correct char
            decoys = _pick_decoys(char, k - 1, exclude=full_exclude)
            excluded.add(char)
            excluded.update(decoys)
            options = _secure_shuffle([char] + decoys)
            node = GridNode(
                node_index=display_idx,
                chars=options,
                _is_real=True,
                _password_position=real_pw_idx,
            )
            real_positions_by_pw_idx[real_pw_idx] = display_idx
            real_pw_idx += 1
        else:
            # Ghost node: chars must not be in excluded OR still-reserved pw chars
            full_exclude = excluded | reserved_pw_chars
            options = _ghost_chars(k, exclude=full_exclude)
            excluded.update(options)
            node = GridNode(
                node_index=display_idx,
                chars=options,
                _is_real=False,
                _password_position=-1,
            )
        all_nodes.append(node)

    # real_node_indices[i] = display index of the node containing pw[i]
    real_node_indices = [
        real_positions_by_pw_idx[p] for p in range(password_length)
    ]

    return all_nodes, real_node_indices
