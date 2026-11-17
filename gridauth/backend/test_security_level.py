from app.services.grid_service import ghost_count_for_level
from app.schemas import RegisterRequest

tests = [
    (6,  "normal",   2),
    (6,  "strong",   3),
    (6,  "powerful", 6),
    (8,  "normal",   3),
    (8,  "strong",   4),
    (8,  "powerful", 8),
    (10, "normal",   4),
    (10, "strong",   5),
    (10, "powerful", 10),
    (12, "normal",   4),
    (12, "strong",   6),
    (12, "powerful", 12),
]

all_ok = True
for pw_len, level, expected in tests:
    result = ghost_count_for_level(pw_len, level)
    ok = result == expected
    if not ok:
        all_ok = False
    status = "OK" if ok else "FAIL (expected " + str(expected) + ")"
    print(f"  pw_len={pw_len:2d}  level={level:8s}  ghosts={result:2d}  total={pw_len+result:2d}  {status}")

print()
r = RegisterRequest(username="alice", password="Secret1", security_level="strong")
print(f"Schema OK: level={r.security_level}")

try:
    RegisterRequest(username="alice", password="Secret1", security_level="invalid")
    print("FAIL: should have rejected invalid level")
except Exception:
    print("Validation correct: invalid level rejected")

print()
print("ALL OK" if all_ok else "SOME FAILURES")
