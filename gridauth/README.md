# GridAuth — 2D Grid-Based Authentication System

## Overview

GridAuth is a mobile authentication system that lets registered users prove their identity through a **randomized two-dimensional grid** instead of a conventional password field. The goal is to reduce the effectiveness of shoulder surfing, video observation, replay attacks, and repeated guessing.

The password itself remains a conventional ordered character sequence. Only the **entry mechanism** changes.

---

## Interaction Protocol

### How Grid Authentication Works

1. The user submits their username (no password field).
2. The server decrypts the stored password characters and builds a randomized grid of N nodes:
   - **L real nodes** — one per password character. Each real node contains the correct character plus K−1 random decoys.
   - **G ghost nodes** — contain K entirely random characters with no relationship to the password.
3. The server Fisher-Yates shuffles all N nodes using `secrets.randbelow` (CSPRNG), assigns positions, and creates a single-use nonce.
4. The server returns the grid layout (node_index + K chars per node) and the nonce. **No role labels, no real/ghost identifiers, no password information is returned.**
5. The client displays nodes one at a time. The user taps their active node to see K character options, selects one, and advances to the next node.
6. **At real nodes**: the correct password character is always present in the K options, so a legitimate user naturally selects it.
7. **At ghost nodes**: the next expected password character is NOT present, so the user selects freely (any character).
8. After all N nodes, the ordered selection array is submitted with the nonce.
9. The server validates the nonce, atomically marks it consumed, extracts selections at the **server-known real node positions in password order**, and compares them against the stored password character-by-character.
10. Result (pass/fail) is returned. The nonce is permanently consumed regardless of outcome.

### Assumptions and Limitations

- **Ordering is critical**: The server enforces ordering. Selections at real nodes must match the password in order. Dropping ordering would reduce theoretical entropy from ~73 bits to ~53 bits.
- **Ghost node effectiveness**: Ghost nodes provide plausible deniability — observers cannot determine which nodes are real. This is only effective when real and ghost nodes are visually indistinguishable (enforced by design).
- **Character pool**: Uses printable ASCII. If password characters are not in the pool, behavior is documented and a fallback is implemented.
- **Repeated characters**: A password character can appear in multiple real nodes; each position is independently encrypted and independently verified.
- **Not production-ready**: The AES key is stored in an environment variable (development substitute for HSM). Use a proper KMS in production.

---

## Architecture

```
gridauth/
├── backend/          Python FastAPI backend
│   ├── app/
│   │   ├── crypto/       AES-256-GCM + key manager (swap for HSM)
│   │   ├── repositories/ Data access layer (DB-agnostic)
│   │   ├── services/     Business logic (auth, grid, lockout, alerts)
│   │   └── routers/      REST endpoints (/api/v1/...)
│   └── tests/            pytest test suite
└── frontend/         Flutter Android app
    └── lib/
        ├── config/   Base URL, grid defaults
        ├── models/   GridNode, AuthSession, UserSession
        ├── services/ HTTP client, secure storage
        ├── state/    AuthState, GridState (ChangeNotifier)
        ├── screens/  Welcome, Login, Registration, Grid, Home, Locked
        └── widgets/  GridNode, CharChoice, RandomizedKeyboard, ...
```

### Key Security Components

| Component | Implementation | Production Replacement |
|-----------|---------------|------------------------|
| Password hashing | Argon2id (argon2-cffi) | Same |
| Character encryption | AES-256-GCM (cryptography lib) | Same algorithm, different key source |
| Key management | `EnvVarKeyManager` reads env var | `HSMKeyManager` from AWS CloudHSM / Azure Key Vault |
| Randomization | Fisher-Yates + `secrets.randbelow` | Same |
| Alert delivery | `LoggingAlertAdapter` (console only) | `TwilioSmsProvider` or `FirebasePushProvider` |
| Token storage | Android Keystore via `flutter_secure_storage` | Same |

---

## Setup — Windows / Android Studio

### Prerequisites

- Flutter SDK ≥ 3.3.0 (add to PATH)
- Android Studio with Android SDK
- Python ≥ 3.11
- Git

### Backend Setup

```powershell
# 1. Navigate to backend
cd gridauth\backend

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env and set AES_KEY_B64:
python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
# Paste the output as AES_KEY_B64= in .env

# 5. Initialize database
python init_db.py

# 6. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API documentation: http://localhost:8000/docs

### Android Emulator (reaches backend via 10.0.2.2)

The `AppConfig.baseUrl` is pre-configured to `http://10.0.2.2:8000` which maps to your host's localhost from the Android emulator.

### Physical Device (LAN)

1. Find your host machine's LAN IP: `ipconfig` → IPv4 Address (e.g. 192.168.1.50)
2. Edit `frontend/lib/config/app_config.dart`:
   ```dart
   static const String baseUrl = 'http://192.168.1.50:8000';
   ```
3. Update `frontend/android/app/src/main/res/xml/network_security_config.xml` to include that IP.

### Flutter App

```powershell
cd gridauth\frontend

# Get dependencies
flutter pub get

# Generate mocks for tests
dart run build_runner build --delete-conflicting-outputs

# Run on emulator/device
flutter run

# Run tests
flutter test

# Build debug APK
flutter build apk --debug
```

### Run Backend Tests

```powershell
cd gridauth\backend
.venv\Scripts\activate
pytest tests/ -v --tb=short
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/register` | Register new user |
| POST | `/api/v1/auth/session` | Create grid session |
| POST | `/api/v1/auth/verify` | Submit ordered selections |
| POST | `/api/v1/auth/logout` | Revoke session token |
| GET | `/api/v1/auth/status` | Check session status |

Full interactive docs: http://localhost:8000/docs

---

## Lockout Policy

| Consecutive Failures | Action |
|---------------------|--------|
| 3 | Secondary channel alert (dev: console log) |
| 5 | Lock account for 10 minutes |
| 10 | Lock account for 20 minutes |
| 15 | Lock account for 24 hours |
| Success | Reset counter to 0 |

Lockouts are server-side timestamp based and persist through server restarts.

---

## Known Limitations

1. **AES key in env var**: Development only. Must use an HSM or cloud KMS in production.
2. **Alert delivery**: `LoggingAlertAdapter` prints to console — does NOT deliver to the user. Replace with a real SMS/push provider.
3. **SQLite**: Uses WAL mode for local dev. PostgreSQL is supported by changing `DATABASE_URL`.
4. **No TLS**: Development uses HTTP. Enable HTTPS before any external deployment.
5. **Ghost node character pool collision**: If the password contains all characters in the pool (extremely unlikely with printable ASCII), decoy generation falls back to duplicates. This is documented and logged.
6. **Python memory zeroing**: Python's garbage collector does not guarantee immediate memory reclamation. The `gc.collect()` calls minimize but cannot eliminate sensitive data residency time in CPython. A production system should use a language with deterministic memory management or a C extension for credential handling.
7. **Client-side selections are not authenticated**: The selection array is signed only by nonce association. A man-in-the-middle could modify selections in transit — use HTTPS to prevent this.

---

## Security Design Decisions (Rejected Approaches)

- **Markov-based ghost characters**: Rejected. The 2D randomized grid has no stable linear character sequence for transition probability analysis. The Markov model would add complexity without security benefit.
- **PSO layout optimization**: Rejected. PSO introduces bias that reduces the permutation space and provides structural information to an attacker. Fisher-Yates with a CSPRNG provides a uniformly random permutation.
- **`random.shuffle`**: Rejected. Uses Mersenne Twister (not cryptographically secure). All shuffling uses `secrets.randbelow`.
