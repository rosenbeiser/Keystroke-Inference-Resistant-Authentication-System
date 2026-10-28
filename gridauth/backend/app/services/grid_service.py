"""
app/services/grid_service.py — Randomized grid construction (FR-03).

Design decisions (from spec):
  - Fisher-Yates shuffle using Python's secrets module (not random.shuffle)
  - Markov-based ghost characters: REJECTED (no stable sequential context)
  - PSO layout optimization: REJECTED (introduces bias, reduces permutation space)
  - Ghost characters are drawn uniformly at random from the full printable ASCII
    character pool, independent of the password

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

import secrets
import string
from dataclasses import dataclass


# Default character pool: printable ASCII excluding whitespace
_CHAR_POOL = string.ascii_letters + string.digits + string.punctuation


@dataclass
class GridNode:
    node_index: int          # position in the shuffled grid (0-based)
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
    If the pool is exhausted (unlikely with printable ASCII) duplicate
    decoys are added with a warning — this is documented as a known limitation.
    """
    pool = [c for c in _CHAR_POOL if c != correct_char and c not in exclude]
    if len(pool) < count:
        # Fallback: repeat characters from a wider set (should never happen)
        pool = [c for c in _CHAR_POOL if c != correct_char]
    chosen: list[str] = []
    while len(chosen) < count and pool:
        idx = secrets.randbelow(len(pool))
        chosen.append(pool[idx])
        pool.pop(idx)
    return chosen


def _ghost_chars(count: int) -> list[str]:
    """
    Generate `count` distinct random characters for a ghost node.

    Ghost characters have no relationship to the password.  They are drawn
    uniformly from the full printable ASCII pool.
    """
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
        nodes : list[GridNode] — the shuffled grid in display order
        real_node_indices : list[int] — the positions in `nodes` that are real nodes,
            in password order. MUST NEVER be sent to the client.

    The returned nodes list is already shuffled.  Clients receive only
    node_index and chars; _is_real and _password_position are server-only.
    """
    password_length = len(password_chars)
    total_nodes = password_length + ghost_count  # N = L + G

    # Build real nodes (one per password character)
    real_nodes: list[GridNode] = []
    for pos, char in enumerate(password_chars):
        decoys = _pick_decoys(char, k - 1, exclude=set())
        options = _secure_shuffle([char] + decoys)
        real_nodes.append(GridNode(
            node_index=-1,  # assigned after shuffle
            chars=options,
            _is_real=True,
            _password_position=pos,
        ))

    # Build ghost nodes
    ghost_nodes: list[GridNode] = []
    for _ in range(ghost_count):
        options = _ghost_chars(k)
        ghost_nodes.append(GridNode(
            node_index=-1,
            chars=options,
            _is_real=False,
            _password_position=-1,
        ))

    # Shuffle combined node list (Fisher-Yates via secrets)
    all_nodes = _secure_shuffle(real_nodes + ghost_nodes)

    # Assign final node_index values after shuffle
    for i, node in enumerate(all_nodes):
        node.node_index = i

    # Record which positions in the shuffled grid are real nodes,
    # maintaining password character order.
    real_node_indices: list[int] = []
    real_by_position: dict[int, int] = {}  # password_position -> node_index
    for node in all_nodes:
        if node._is_real:
            real_by_position[node._password_position] = node.node_index
    real_node_indices = [real_by_position[p] for p in range(password_length)]

    return all_nodes, real_node_indices
