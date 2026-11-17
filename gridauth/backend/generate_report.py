"""
generate_report.py — Generate the GridAuth technical report as a PDF.
Run:  .venv\Scripts\python.exe generate_report.py
Output: GridAuth_Technical_Report.pdf  (same directory)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import ListFlowable, ListItem
import datetime

OUTPUT = "GridAuth_Technical_Report.pdf"

# ── Colour palette ──────────────────────────────────────────────────────────
PURPLE      = colors.HexColor("#6C63FF")
DARK_BG     = colors.HexColor("#0D0B1E")
LIGHT_GREY  = colors.HexColor("#F5F5F5")
MID_GREY    = colors.HexColor("#CCCCCC")
DARK_GREY   = colors.HexColor("#444444")
WHITE       = colors.white
BLACK       = colors.black
ACCENT_BLUE = colors.HexColor("#48A8F8")
GREEN       = colors.HexColor("#27AE60")
RED         = colors.HexColor("#E53E3E")

# ── Style definitions ───────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    """Clone & extend a base style."""
    base = styles[name]
    merged = dict(
        fontName=base.fontName, fontSize=base.fontSize,
        leading=base.leading, textColor=base.textColor,
        spaceAfter=base.spaceAfter, spaceBefore=base.spaceBefore,
        alignment=base.alignment,
    )
    merged.update(kw)
    return ParagraphStyle("_custom_", **merged)

H1 = S("Heading1", fontSize=22, textColor=PURPLE, fontName="Helvetica-Bold",
        spaceBefore=18, spaceAfter=10, leading=28)
H2 = S("Heading2", fontSize=15, textColor=DARK_BG, fontName="Helvetica-Bold",
        spaceBefore=16, spaceAfter=6, leading=20)
H3 = S("Heading3", fontSize=12, textColor=PURPLE, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4, leading=16)
BODY = S("BodyText", fontSize=10, textColor=DARK_GREY, leading=15,
         alignment=TA_JUSTIFY, spaceAfter=6)
BODY_SMALL = S("BodyText", fontSize=9, textColor=DARK_GREY, leading=13,
               alignment=TA_JUSTIFY, spaceAfter=4)
CODE = S("Code", fontSize=8.5, fontName="Courier", textColor=colors.HexColor("#2D2D2D"),
         backColor=LIGHT_GREY, leading=12, spaceAfter=4, leftIndent=12, rightIndent=12)
CAPTION = S("BodyText", fontSize=8.5, textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER, spaceAfter=8)
TITLE_MAIN = S("Title", fontSize=30, textColor=WHITE, fontName="Helvetica-Bold",
               alignment=TA_CENTER, leading=38, spaceAfter=6)
SUBTITLE = S("Title", fontSize=14, textColor=colors.HexColor("#B0ACFF"),
             alignment=TA_CENTER, fontName="Helvetica", leading=20, spaceAfter=4)
LABEL = S("BodyText", fontSize=9, textColor=PURPLE, fontName="Helvetica-Bold",
          spaceAfter=2, leading=12)

# ── Helper builders ─────────────────────────────────────────────────────────
def p(text, style=BODY):
    return Paragraph(text, style)

def h1(text): return Paragraph(text, H1)
def h2(text): return Paragraph(text, H2)
def h3(text): return Paragraph(text, H3)
def code(text): return Paragraph(text.replace("\n","<br/>").replace(" ","&nbsp;"), CODE)
def hr(): return HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=8, spaceBefore=4)
def thin_hr(): return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD"), spaceAfter=4, spaceBefore=4)
def sp(h=8): return Spacer(1, h)

def bullet_list(items, style=BODY_SMALL):
    return ListFlowable(
        [ListItem(p(i, style), leftIndent=12, bulletColor=PURPLE, bulletFontSize=10) for i in items],
        bulletType="bullet", leftIndent=20, spaceAfter=6
    )

def info_table(rows, col_widths=None):
    """Two-column key/value table."""
    if col_widths is None:
        col_widths = [5*cm, 11*cm]
    data = [[p(f"<b>{k}</b>", BODY_SMALL), p(v, BODY_SMALL)] for k,v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), LIGHT_GREY),
        ("TEXTCOLOR",  (0,0), (0,-1), PURPLE),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, colors.HexColor("#FAFAFA")]),
        ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
    ]))
    return t

def section_header(number, title, subtitle=""):
    items = [
        HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=4, spaceBefore=12),
        Paragraph(f"<font color='#{PURPLE.hexval()[2:]}'>Section {number}</font>&nbsp;&nbsp;{title}", H1),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, S("BodyText", fontSize=10, textColor=colors.HexColor("#888888"),
                                           spaceAfter=8, fontName="Helvetica-Oblique")))
    items.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=10))
    return items

def cover_page():
    """Return flowables for the cover page."""
    # Dark banner
    banner = Table(
        [[Paragraph("GridAuth", TITLE_MAIN)],
         [Paragraph("Graphical Grid Authentication System", SUBTITLE)],
         [Paragraph("Technical Architecture &amp; Design Report", SUBTITLE)],
         [sp(12)],
         [Paragraph("VR Edition — Deployed on Meta Quest 2", S("Title", fontSize=11,
                     textColor=colors.HexColor("#9F97FF"), alignment=TA_CENTER, leading=16))]],
        colWidths=[17*cm]
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK_BG),
        ("ROUNDEDCORNERS", [8,8,8,8]),
        ("TOPPADDING",    (0,0), (-1,-1), 20),
        ("BOTTOMPADDING", (0,0), (-1,-1), 20),
        ("LEFTPADDING",   (0,0), (-1,-1), 24),
        ("RIGHTPADDING",  (0,0), (-1,-1), 24),
    ]))

    meta = Table([
        [p("<b>Version</b>", BODY_SMALL), p("1.0.0", BODY_SMALL)],
        [p("<b>Date</b>", BODY_SMALL),    p(datetime.date.today().strftime("%B %d, %Y"), BODY_SMALL)],
        [p("<b>Platform</b>", BODY_SMALL),p("Meta Quest 2 (Android) · FastAPI Python Backend", BODY_SMALL)],
        [p("<b>Tech Stack</b>", BODY_SMALL), p("Flutter (Dart 3) · FastAPI · SQLite · AES-256-GCM · Argon2id", BODY_SMALL)],
        [p("<b>Target</b>", BODY_SMALL),  p("VR / Mobile · Research &amp; Proof-of-Concept", BODY_SMALL)],
    ], colWidths=[4*cm, 13*cm])
    meta.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ("BACKGROUND", (0,0), (0,-1), LIGHT_GREY),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))

    return [
        sp(30),
        banner,
        sp(28),
        meta,
        PageBreak(),
    ]

# ── Document builder ────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        rightMargin=2.2*cm, leftMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="GridAuth Technical Report",
        author="GridAuth Development Team",
        subject="Graphical Grid Authentication System — Architecture & Design",
    )

    story = []

    # ═══════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════
    story += cover_page()

    # ═══════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS (manual)
    # ═══════════════════════════════════════════════════════════════
    story += [
        h1("Table of Contents"),
        hr(),
    ]
    toc_items = [
        ("1", "Introduction & Problem Statement"),
        ("2", "System Architecture Overview"),
        ("3", "Module Descriptions"),
        ("4", "How the Modules Work Together"),
        ("5", "The Core Algorithm — Node Generation"),
        ("6", "Password Storage, Encryption & Decryption"),
        ("7", "The Authentication Flow — Step by Step"),
        ("8", "Security Properties & Threat Model"),
        ("9", "VR Deployment on Meta Quest 2"),
        ("10","Future Work & Integration Potential"),
    ]
    toc_data = [[p(f"<b>{n}.</b>", BODY), p(title, BODY)] for n, title in toc_items]
    toc_table = Table(toc_data, colWidths=[1.5*cm, 15*cm])
    toc_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-1), 0.3, colors.HexColor("#EEEEEE")),
        ("TEXTCOLOR", (0,0), (0,-1), PURPLE),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
    ]))
    story += [toc_table, PageBreak()]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1 — Introduction
    # ═══════════════════════════════════════════════════════════════
    story += section_header("1", "Introduction &amp; Problem Statement",
                            "What GridAuth solves and why it was built")
    story += [
        p("GridAuth is a <b>graphical, grid-based authentication system</b> designed to protect users "
          "against a class of attacks that traditional text-based passwords cannot defend against. "
          "When a person types a password on a keyboard — whether on a smartphone, laptop, or inside a "
          "Virtual Reality headset — an attacker nearby can watch the screen, record their hand movements, "
          "or use malicious software to log every keystroke. This is known as <b>shoulder surfing</b> and "
          "<b>keylogging</b>, and they are particularly serious in public or shared environments like "
          "offices, cafes, university labs, and VR arcades."),
        p("GridAuth eliminates this vulnerability by ensuring that the user's real password is <b>never "
          "typed, spoken aloud, or entered directly</b> during the login process. Instead, the system "
          "presents a series of panels called <b>nodes</b>, each showing four characters. The user "
          "simply selects one character per node. Only the system knows which nodes are real "
          "(containing a password character) and which are ghost nodes (decoys). An observer watching "
          "the screen sees only a series of random taps — they cannot determine the password."),
        h3("1.1 Key Design Goals"),
        bullet_list([
            "<b>Shoulder-surfing resistance:</b> An observer watching the screen cannot reconstruct the password.",
            "<b>Keylogger resistance:</b> The password is never typed, so keystroke loggers capture nothing useful.",
            "<b>Screen recording resistance:</b> Even a full video recording of the session cannot reveal the password.",
            "<b>Cryptographically secure randomness:</b> All shuffles and selections use hardware-grade random number generation.",
            "<b>Server-side verification:</b> The client device never knows which nodes are real or ghost.",
            "<b>VR-ready interaction:</b> The node-tap interaction maps directly to VR controller pointing and selection.",
        ]),
        sp(6),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2 — Architecture
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("2", "System Architecture Overview",
                            "High-level structure of the client and server")
    story += [
        p("GridAuth follows a classic <b>client-server architecture</b> split across two independent "
          "components. The client runs on the user's device (Meta Quest 2 / Android), and the server "
          "runs on a PC or cloud host that is reachable over Wi-Fi or the internet."),
        h3("2.1 Component Overview"),
    ]

    arch_data = [
        [p("<b>Component</b>", BODY_SMALL), p("<b>Technology</b>", BODY_SMALL), p("<b>Role</b>", BODY_SMALL)],
        [p("Frontend App", BODY_SMALL), p("Flutter (Dart 3)", BODY_SMALL),
         p("User interface — renders nodes, handles input, communicates with backend", BODY_SMALL)],
        [p("Backend API", BODY_SMALL), p("FastAPI (Python 3.13)", BODY_SMALL),
         p("Business logic — grid generation, password encryption, session management", BODY_SMALL)],
        [p("Database", BODY_SMALL), p("SQLite + SQLAlchemy ORM", BODY_SMALL),
         p("Persistent storage — encrypted password characters, sessions, audit log", BODY_SMALL)],
        [p("Crypto Layer", BODY_SMALL), p("AES-256-GCM + Argon2id", BODY_SMALL),
         p("Encrypts password characters; hashes the full password for integrity check", BODY_SMALL)],
        [p("VR Runtime", BODY_SMALL), p("Meta Quest 2 (Android 10)", BODY_SMALL),
         p("Runs the Flutter APK as a 2D panel in the VR environment", BODY_SMALL)],
    ]
    arch_table = Table(arch_data, colWidths=[3.5*cm, 3.5*cm, 10*cm])
    arch_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PURPLE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [arch_table, sp(10)]

    story += [
        h3("2.2 Communication Flow"),
        p("All communication between the client and server uses <b>HTTP REST API calls</b> over the "
          "local Wi-Fi network. When deployed on Meta Quest 2, the headset connects to the same Wi-Fi "
          "network as the PC running the backend server, and all API calls go to the server's IP address "
          "and port 8000."),
        p("The key principle is that <b>sensitive information never leaves the server</b>. The client "
          "only receives the list of character options for each node — it never receives information about "
          "which node is real, which character is the correct one, or what the user's password is."),
        sp(6),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3 — Module Descriptions
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("3", "Module Descriptions",
                            "Detailed description of each software component")

    story += [
        h2("3.1 Frontend — Flutter Application"),
        p("The frontend is a Flutter application written in Dart 3. Flutter is a cross-platform UI "
          "framework that compiles to native Android code, which is what allows it to run on the "
          "Meta Quest 2 headset without any modifications, since the Quest runs Android 10 internally."),
    ]

    fe_modules = [
        ("Welcome Screen", "The entry point of the app. Contains buttons to navigate to Login or Registration, and a gear icon (⚙) to open the Server Settings screen."),
        ("Login Screen", "Accepts the user's username and starts a grid authentication session by calling the backend. Navigates to the Grid Auth Screen on success."),
        ("Registration Screen", "Uses the device's standard QWERTY keyboard for password entry. Collects username, password, and confirmation, then sends them to the backend."),
        ("Grid Auth Screen", "The main authentication screen. Displays one node at a time — four character buttons. User taps one per node until all nodes are completed."),
        ("Server Settings Screen", "Allows the user to configure the backend server's IP address and port. Includes a 'Test Connection' button. Essential for VR use, since the IP may change."),
        ("Home Screen", "Shown after successful authentication. Displays the authenticated username and a logout button."),
        ("GridState (State Manager)", "Uses the Provider pattern to manage authentication session state — the list of nodes, current step, selections, and final result."),
        ("ApiService", "Handles all HTTP communication with the backend. Implements register, startSession, submitSelections, and logout endpoints."),
        ("SecureStorageService", "Uses flutter_secure_storage (backed by Android Keystore) to persist the server URL securely on the device."),
    ]

    for module, desc in fe_modules:
        story += [
            KeepTogether([
                p(f"<b>{module}</b>", LABEL),
                p(desc, BODY_SMALL),
                thin_hr(),
            ])
        ]

    story += [
        sp(6),
        h2("3.2 Backend — FastAPI Python Server"),
        p("The backend is a Python application built with <b>FastAPI</b>, a modern high-performance "
          "web framework. It runs using <b>Uvicorn</b>, an ASGI server. The backend exposes a REST API "
          "and handles all security-critical logic."),
    ]

    be_modules = [
        ("auth_service.py", "The core business logic engine. Handles user registration (encrypting passwords), creating grid sessions (building node layouts), and verifying user selections against the stored password."),
        ("grid_service.py", "The node generation algorithm. Takes the decrypted password characters, decides which positions are real or ghost using a cryptographic shuffle, generates the character options for each node with global uniqueness guarantees, and returns the final node list."),
        ("aes_gcm.py", "The encryption helper. Implements AES-256-GCM authenticated encryption and decryption. Each password character is encrypted individually with a unique 96-bit random nonce."),
        ("key_manager.py", "Manages the AES master encryption key. Loads the key from an environment variable. In production, this can be replaced with an HSM or cloud Key Management Service."),
        ("models.py", "SQLAlchemy ORM models defining the database tables: Users, PasswordCharacter, PasswordHash, AuthSession, SessionToken, LockoutState, and AuditEvent."),
        ("config.py", "Application configuration loaded from environment variables. Controls grid size, session timeouts, password policy, and rate limiting."),
        ("lockout_service.py", "Tracks failed authentication attempts per user. After a configured number of failures, the account is temporarily locked to prevent brute-force attacks."),
        ("routers/", "FastAPI route handlers for /register, /auth/session, /auth/verify, /auth/logout. Each router validates inputs, calls the appropriate service, and returns structured JSON responses."),
    ]

    for module, desc in be_modules:
        story += [
            KeepTogether([
                p(f"<b>{module}</b>", LABEL),
                p(desc, BODY_SMALL),
                thin_hr(),
            ])
        ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4 — How Modules Work Together
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("4", "How the Modules Work Together",
                            "Data flow during registration and authentication")

    story += [
        h2("4.1 Registration Flow"),
        p("When a new user creates an account, the following sequence of events occurs across the frontend and backend:"),
    ]

    reg_steps = [
        ("Step 1 — User Input", "The user opens the Registration Screen on their device or VR headset and types their username and password using the standard QWERTY keyboard. The password must be at least 6 characters and contain at least one uppercase letter, one lowercase letter, and one digit."),
        ("Step 2 — Client Sends to Backend", "The ApiService module sends an HTTPS POST request to /api/v1/auth/register containing the username and plaintext password. This is the only time the plaintext password ever travels across the network."),
        ("Step 3 — Server Validates", "The backend checks that the username is not already taken and that the password meets the minimum policy requirements."),
        ("Step 4 — Argon2id Hashing", "The auth_service hashes the entire password string using Argon2id (a memory-hard hashing algorithm) and stores the hash in the password_hashes table. This hash is used only as a secondary integrity check."),
        ("Step 5 — AES-256-GCM Encryption", "Each individual password character is encrypted separately using AES-256-GCM with a unique 96-bit random nonce. Each encrypted character (ciphertext + nonce + authentication tag, encoded as Base64) is stored as a separate row in the password_characters table."),
        ("Step 6 — Memory Zeroing", "Immediately after encryption is complete, the plaintext password and the AES key bytes are overwritten with zeros in memory and garbage-collected. This minimises the window during which sensitive data exists in RAM."),
        ("Step 7 — Success Response", "The server returns a success response. The client shows a confirmation message. The user can now log in."),
    ]

    for title, desc in reg_steps:
        story += [KeepTogether([p(f"<b>{title}:</b> {desc}", BODY_SMALL), sp(4)])]

    story += [sp(8), h2("4.2 Authentication Flow"), p("During login, the modules collaborate in a more complex sequence:")]

    auth_steps = [
        ("Step 1 — Username Entry", "The user enters their username on the Login Screen and taps 'Begin Grid Authentication'."),
        ("Step 2 — Session Request", "ApiService sends POST /api/v1/auth/session with the username."),
        ("Step 3 — Password Decryption (Server)", "auth_service fetches the user's encrypted password characters from the database, loads the AES key from the key manager, and decrypts each character. The plaintext characters exist in server RAM only for the duration of the next step."),
        ("Step 4 — Grid Generation", "grid_service.build_grid() receives the decrypted password characters and builds the full node layout. This is described in detail in Section 5."),
        ("Step 5 — Memory Zeroing Again", "Immediately after the grid is built, the decrypted password characters are zeroed from memory."),
        ("Step 6 — Session Stored", "The server saves the session nonce and the real_node_indices (the secret map of which nodes are real) in the database. The client receives only the node list (character options) — the real_node_indices are never sent."),
        ("Step 7 — User Navigates Nodes", "The Grid Auth Screen displays each node one at a time. The user taps a character per node. For real nodes, they tap their next password character. For ghost nodes, they tap anything."),
        ("Step 8 — Selections Submitted", "After all nodes, ApiService sends POST /api/v1/auth/verify with the nonce and the full list of selected characters."),
        ("Step 9 — Verification", "The server retrieves the session, extracts the selections at the real_node_indices positions, decrypts the stored password, and compares using a constant-time algorithm. If they match, a session token is issued."),
        ("Step 10 — Home Screen", "The client stores the session token securely and navigates the user to the Home Screen."),
    ]

    for title, desc in auth_steps:
        story += [KeepTogether([p(f"<b>{title}:</b> {desc}", BODY_SMALL), sp(3)])]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5 — The Core Algorithm
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("5", "The Core Algorithm — Node Generation",
                            "How real nodes and ghost nodes are built and merged")

    story += [
        p("The node generation algorithm is the heart of GridAuth's security. It is implemented in "
          "<b>grid_service.py</b>. The goal is to produce a sequence of N nodes where:"),
        bullet_list([
            "Real nodes each contain exactly one password character (hidden among 3 decoys).",
            "Ghost nodes contain 4 entirely random characters with no connection to the password.",
            "Ghost nodes appear at random positions — not at the end.",
            "No character ever appears in more than one node (global uniqueness).",
            "No future password character can appear as a decoy before its designated real node.",
            "All randomness is cryptographically secure.",
        ]),
        h3("5.1 Algorithm Parameters"),
        info_table([
            ("N", "Total number of nodes = password length + ghost count"),
            ("L", "Number of real nodes = password length"),
            ("G", "Number of ghost nodes (default: 2)"),
            ("K", "Number of character options shown per node (default: 4)"),
            ("CHAR_POOL", "94 printable ASCII characters (letters, digits, punctuation)"),
        ]),
        sp(8),
        h3("5.2 Step-by-Step Algorithm"),
        p("<b>Step 1 — Reserve future password characters.</b> Before any nodes are built, all password "
          "characters are placed in a 'reserved' set. This prevents any future password character from "
          "accidentally appearing as a decoy or ghost character in an earlier node — which would give "
          "away information about the password sequence."),
        p("<b>Step 2 — Shuffle the position assignments.</b> A boolean list is created: "
          "[True, True, ..., False, False] — one True per password character and one False per ghost node. "
          "This list is shuffled using the <b>Fisher-Yates algorithm</b> with Python's "
          "<b>secrets.randbelow()</b> as the random number source. This determines which display "
          "positions (0 through N-1) are real and which are ghost. The shuffling happens before "
          "any characters are assigned, so the layout is decided by pure randomness."),
        p("<b>Why Fisher-Yates with secrets?</b> Python's built-in random.shuffle() uses the Mersenne "
          "Twister — a fast but <i>not cryptographically secure</i> pseudo-random number generator. "
          "Its output can be predicted if an attacker observes enough samples. GridAuth uses "
          "secrets.randbelow(), which reads from the operating system's hardware entropy source "
          "(os.urandom on Windows/Linux/macOS), making it computationally infeasible to predict."),
        p("<b>Step 3 — Generate nodes in display order.</b> The algorithm walks through the shuffled "
          "position sequence from index 0 to N-1, building each node one at a time. This sequential "
          "generation is crucial because it allows the exclusion set to grow correctly."),
        p("<b>For each Real Node:</b>"),
        bullet_list([
            "Remove the current password character from the reserve set.",
            "Build the full exclusion set: all previously used characters + all still-reserved future password characters.",
            "Pick 3 decoy characters from the character pool, excluding the full exclusion set.",
            "Add the password character and its 3 decoys to the global 'excluded' set.",
            "Shuffle the 4 characters using Fisher-Yates to randomise their display order.",
        ]),
        p("<b>For each Ghost Node:</b>"),
        bullet_list([
            "Build the full exclusion set: all previously used characters + all still-reserved password characters.",
            "Pick 4 random characters from the pool, excluding the full set.",
            "Add all 4 characters to the global 'excluded' set.",
        ]),
        h3("5.3 Worked Example"),
        p("Suppose the password is <b>1a2b</b> (4 characters) with <b>2 ghost nodes</b>, giving 6 total nodes."),
    ]

    example_data = [
        [p("<b>Display Index</b>", BODY_SMALL), p("<b>Node Type</b>", BODY_SMALL),
         p("<b>Password Char</b>", BODY_SMALL), p("<b>Options Shown</b>", BODY_SMALL),
         p("<b>Excluded After</b>", BODY_SMALL)],
        [p("0", BODY_SMALL), p("Real (pw[0])", BODY_SMALL), p("'1'", BODY_SMALL),
         p("['P', '1', 'V', 'D'] (shuffled)", BODY_SMALL), p("{'1','P','V','D'}", BODY_SMALL)],
        [p("1", BODY_SMALL), p("Ghost", BODY_SMALL), p("—", BODY_SMALL),
         p("['A', 'f', ']', 'g'] (random)", BODY_SMALL), p("+ {'A','f',']','g'}", BODY_SMALL)],
        [p("2", BODY_SMALL), p("Real (pw[1])", BODY_SMALL), p("'a'", BODY_SMALL),
         p("['~', 'a', 'C', 'm'] (shuffled)", BODY_SMALL), p("+ {'a','~','C','m'}", BODY_SMALL)],
        [p("3", BODY_SMALL), p("Real (pw[2])", BODY_SMALL), p("'2'", BODY_SMALL),
         p("['2', 'k', '&', 'X'] (shuffled)", BODY_SMALL), p("+ {'2','k','&','X'}", BODY_SMALL)],
        [p("4", BODY_SMALL), p("Ghost", BODY_SMALL), p("—", BODY_SMALL),
         p("['u', '+', 'J', 'j'] (random)", BODY_SMALL), p("+ {'u','+','J','j'}", BODY_SMALL)],
        [p("5", BODY_SMALL), p("Real (pw[3])", BODY_SMALL), p("'b'", BODY_SMALL),
         p("['b', 'z', '9', 'Q'] (shuffled)", BODY_SMALL), p("+ {'b','z','9','Q'}", BODY_SMALL)],
    ]
    ex_table = Table(example_data, colWidths=[2.5*cm, 2.8*cm, 2.5*cm, 5*cm, 4.2*cm])
    ex_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PURPLE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [ex_table, sp(6)]
    story += [
        p("The key observation from this example: a hypothetical attacker who watches all 6 steps sees "
          "the user tap a character in each of 6 panels. They see 24 characters in total. They cannot "
          "tell which panels were real, which 4 characters in each panel was the correct one, or what "
          "the password is. Even recording the full session on video provides no useful information."),
        h3("5.4 What the Client Receives vs. What the Server Keeps"),
        info_table([
            ("Client receives", "node_index (0–5), chars (the 4 displayed characters) — for each node"),
            ("Client does NOT receive", "Whether the node is real or ghost, which character is correct, real_node_indices"),
            ("Server keeps secret", "real_node_indices — the list of display positions that are real, in password order"),
        ]),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6 — Password Storage, Encryption, Decryption
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("6", "Password Storage, Encryption &amp; Decryption",
                            "How passwords are secured at rest and in memory")

    story += [
        h2("6.1 Why Encryption Instead of Hashing?"),
        p("Traditional web applications store passwords as <b>one-way hashes</b> (using algorithms like "
          "bcrypt or Argon2id). A one-way hash cannot be reversed — the system only checks if the hash "
          "of what the user typed matches the stored hash. This is secure because the server never needs "
          "to know the original password."),
        p("GridAuth has a fundamentally different requirement: during authentication, the server must "
          "know the <i>actual password characters</i> in order to construct the real nodes. If the "
          "password were hashed, it would be impossible to generate the correct node layout. Therefore, "
          "GridAuth must store the password in a <b>reversible encrypted form</b>."),
        p("To compensate for this requirement, GridAuth applies multiple layers of protection, as "
          "described below."),
        h2("6.2 Dual Storage Strategy"),
        p("The password is stored in <b>two independent forms</b> for two different purposes:"),
    ]

    dual_data = [
        [p("<b>Form</b>", BODY_SMALL), p("<b>Algorithm</b>", BODY_SMALL), p("<b>Purpose</b>", BODY_SMALL), p("<b>Table</b>", BODY_SMALL)],
        [p("Individual character encryption", BODY_SMALL), p("AES-256-GCM", BODY_SMALL),
         p("Allows the server to retrieve individual characters for grid generation", BODY_SMALL), p("password_characters", BODY_SMALL)],
        [p("Full password hash", BODY_SMALL), p("Argon2id", BODY_SMALL),
         p("Secondary integrity check; makes offline attacks against the DB expensive", BODY_SMALL), p("password_hashes", BODY_SMALL)],
    ]
    dual_table = Table(dual_data, colWidths=[4*cm, 3*cm, 7*cm, 3*cm])
    dual_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [dual_table, sp(8)]

    story += [
        h2("6.3 AES-256-GCM: The Encryption Algorithm"),
        p("<b>AES-256-GCM</b> (Advanced Encryption Standard with 256-bit key in Galois/Counter Mode) is "
          "an <b>authenticated encryption</b> algorithm. 'Authenticated' means it does two things at once: "
          "it encrypts the data (so it cannot be read without the key) and it generates a "
          "cryptographic tag (so any tampering with the data can be detected)."),
        h3("6.3.1 How Each Character Is Encrypted"),
        p("GridAuth encrypts each password character <b>individually and independently</b>. For a "
          "6-character password like 'Secret1', there will be 6 separate encrypted values in the "
          "database — one per character. This design means the server can decrypt individual characters "
          "as needed without decrypting the entire password at once."),
        p("For each character, the encryption process is:"),
        bullet_list([
            "Generate a fresh <b>96-bit (12-byte) random nonce</b> using the operating system's hardware entropy source (os.urandom). A new nonce is generated for every single encryption call — no two characters share the same nonce.",
            "Encrypt the character using AES-256-GCM with the master key and the nonce. This produces a <b>ciphertext</b> and a <b>128-bit authentication tag</b> (appended automatically by the library).",
            "Concatenate: <b>nonce (12 bytes) + ciphertext + tag (16 bytes)</b>.",
            "Encode the whole thing as <b>Base64</b> (a text-safe encoding) and store it in the database as a text string.",
        ]),
        p("The stored string looks like random characters, for example: "
          "<font name='Courier'>dGhpcyBpcyBhIGZha2UgY2lwaGVydGV4dA==</font>. "
          "Without the master encryption key, it is computationally infeasible to decode."),
        h3("6.3.2 How Decryption Works"),
        p("During authentication, the server reverses the process:"),
        bullet_list([
            "Load the Base64 string from the database and decode it back to raw bytes.",
            "Extract the first 12 bytes as the nonce.",
            "Pass the remaining bytes (ciphertext + tag) to the AES-256-GCM decryption function along with the nonce and the master key.",
            "The function verifies the authentication tag first — if the data has been tampered with or the wrong key is used, it raises an InvalidTag exception and refuses to return any data.",
            "If the tag is valid, it decrypts and returns the original character.",
        ]),
        h2("6.4 The Master Encryption Key"),
        p("The 32-byte (256-bit) AES master key is the most sensitive piece of data in the system. "
          "It is <b>never stored in the database</b>. It is loaded from an environment variable "
          "(<font name='Courier'>AES_KEY_B64</font>) at server startup. This means:"),
        bullet_list([
            "If an attacker steals the SQLite database file, they obtain only Base64-encoded ciphertexts. Without the key, these are useless.",
            "The key and the data it protects are stored separately — a fundamental principle of secure key management.",
            "In a production environment, the environment variable can be replaced with a Hardware Security Module (HSM) or a cloud Key Management Service (AWS KMS, Google Cloud KMS, HashiCorp Vault).",
        ]),
        h2("6.5 Memory Safety"),
        p("GridAuth is careful about how long sensitive data lives in RAM. After completing any "
          "operation that uses the plaintext password or the AES key, the server immediately:"),
        bullet_list([
            "Overwrites the key byte array with zeros: <font name='Courier'>aes_key = b'\\x00' * len(aes_key)</font>",
            "Deletes the reference: <font name='Courier'>del aes_key</font>",
            "Calls the garbage collector: <font name='Courier'>gc.collect()</font>",
            "Does the same for the decrypted password character list after grid construction.",
        ]),
        p("This minimises the window during which sensitive data exists in RAM and reduces the risk "
          "of memory-scanning attacks."),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7 — Full Auth Flow Step by Step
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("7", "The Authentication Flow — Step by Step",
                            "Complete technical walkthrough of a login session")

    story += [
        p("This section traces a complete login session for a user with password <b>'Secure1'</b> "
          "(7 characters) and 2 ghost nodes (9 total nodes)."),
        sp(4),
    ]

    flow_steps = [
        ("1. Username Submitted", "blue",
         "User enters 'alice' on the Login Screen and taps 'Begin Grid Authentication'. "
         "The app calls POST /api/v1/auth/session with body {\"username\": \"alice\"}."),
        ("2. User Lookup & Lockout Check", "blue",
         "The server looks up 'alice' in the database. If the account does not exist, the server "
         "performs a dummy Argon2id hash computation (to take the same amount of time as a real lookup) "
         "and returns a generic error — this prevents an attacker from guessing valid usernames by "
         "timing the response. If the account is locked due to too many recent failures, an error is returned."),
        ("3. Decrypt Password Characters", "blue",
         "The server loads the 7 AES-256-GCM encrypted character records for 'alice', loads the master "
         "key from the environment, and decrypts each character. The 7 plaintext characters exist in "
         "RAM only for the next step."),
        ("4. Build Grid", "blue",
         "grid_service.build_grid() is called with the 7 characters, K=4, and ghost_count=2. "
         "It generates 9 nodes using the algorithm described in Section 5. The function returns "
         "two things: (a) the 9 nodes with their character options, and (b) real_node_indices — "
         "a list of 7 display positions that are real nodes, in password order."),
        ("5. Zero Password Characters", "blue",
         "Immediately after build_grid() returns, the plaintext characters are overwritten with "
         "'\\x00' and garbage-collected."),
        ("6. Store Session", "blue",
         "A unique session nonce is generated using secrets.token_urlsafe(32). The nonce, "
         "real_node_indices (as JSON), node_count, and expiry time (5 minutes from now) are saved "
         "to the auth_sessions table. The session expires automatically if not completed in time."),
        ("7. Send Nodes to Client", "blue",
         "The server sends the 9 nodes to the client. Each node contains only: node_index (0-8) "
         "and chars (4 character options). real_node_indices is NOT included in the response."),
        ("8. User Navigates Nodes", "green",
         "The Grid Auth Screen shows node 0 first. The user sees 4 characters and taps one. "
         "The app records the selection and shows node 1. This continues for all 9 nodes. "
         "For real nodes, the user spots their next password character and taps it. "
         "For ghost nodes, the user taps any character — it does not matter which one."),
        ("9. Selections Submitted", "green",
         "After all 9 nodes, the app sends POST /api/v1/auth/verify with the session nonce "
         "and the full list of 9 selected characters."),
        ("10. Server Verification", "blue",
         "The server retrieves the session by nonce, checks it is not expired or already used, "
         "and atomically marks it as consumed (preventing replay attacks). "
         "It then decrypts the stored password characters again, extracts the user's selections at "
         "positions real_node_indices (e.g., [0, 2, 4, 5, 6, 7, 8]) to get a 7-character sequence, "
         "and compares this sequence against the decrypted password using secrets.compare_digest() "
         "(a constant-time comparison that prevents timing attacks)."),
        ("11. Result", "green",
         "If the sequences match: a session token is issued and sent to the client. The client "
         "stores it securely and navigates to the Home Screen. "
         "If they do not match: a failure is recorded. After 5 consecutive failures, the account "
         "is locked for 15 minutes. A generic 'Authentication failed' message is returned — "
         "the server never reveals which node or character was wrong."),
    ]

    for title, colour, desc in flow_steps:
        col = GREEN if colour == "green" else PURPLE
        step_table = Table(
            [[Paragraph(f"<b>{title}</b>", S("BodyText", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold", leading=12)),
              Paragraph(desc, BODY_SMALL)]],
            colWidths=[4*cm, 13*cm]
        )
        step_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,0), col),
            ("BACKGROUND", (1,0), (1,0), colors.HexColor("#FAFAFA")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ]))
        story += [step_table, sp(3)]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8 — Security Properties
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("8", "Security Properties &amp; Threat Model",
                            "What attacks GridAuth defends against and how")

    story += [
        p("The table below summarises the threats GridAuth is designed to handle and the specific "
          "mechanism that defends against each one."),
        sp(6),
    ]

    threats = [
        ("Shoulder Surfing", "An attacker watches the user's screen during login.",
         "Even with full visibility of the screen, the attacker sees only random character buttons being tapped. Without knowing which nodes are real and which position is correct, the information is useless."),
        ("Keylogging", "Malicious software records every key typed on the device.",
         "The user never types their password during login. The only keyboard input is the username. Ghost node selections carry no password information."),
        ("Video Recording", "The session is recorded and replayed later.",
         "Each session generates a completely new random node layout. Recording one session provides zero information about future sessions."),
        ("Database Theft", "Attacker steals the SQLite database file.",
         "All password characters are AES-256-GCM encrypted. Without the master key (stored externally), the ciphertexts are computationally infeasible to decrypt. The Argon2id hash adds further resistance."),
        ("Brute-Force Login", "Attacker attempts many login guesses.",
         "Account lockout after 5 consecutive failures, with a 15-minute lock. Rate limiting on the API endpoints prevents automated attacks."),
        ("Replay Attack", "Attacker captures a network request and re-sends it.",
         "Each session nonce is single-use. The server atomically marks the nonce as 'consumed' on first use. Any subsequent request with the same nonce is rejected."),
        ("Timing Attack", "Attacker measures response time to deduce whether a character was correct.",
         "Password comparison uses secrets.compare_digest() (constant-time). User lookup uses a dummy hash computation to equalise timing for missing vs. present accounts."),
        ("Memory Scraping", "Attacker reads server RAM to extract plaintext passwords.",
         "Plaintext characters and the AES key are zeroed and garbage-collected immediately after use. The window of exposure is minimised to microseconds."),
        ("Username Enumeration", "Attacker determines whether a username exists by observing the response.",
         "The server returns the same generic error and takes the same amount of time whether the username exists or not."),
    ]

    threat_data = [[p("<b>Threat</b>",BODY_SMALL), p("<b>Description</b>",BODY_SMALL), p("<b>Defence</b>",BODY_SMALL)]]
    for t, d, def_ in threats:
        threat_data.append([p(t,BODY_SMALL), p(d,BODY_SMALL), p(def_,BODY_SMALL)])

    threat_table = Table(threat_data, colWidths=[3.5*cm, 5.5*cm, 8*cm])
    threat_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.4, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    story += [threat_table, sp(10)]

    story += [
        h2("8.1 Known Limitations"),
        bullet_list([
            "<b>Password must be reversibly encrypted:</b> Unlike pure-hash systems, an attacker who steals both the database AND the AES key can decrypt all passwords. Key management hygiene is therefore critical.",
            "<b>Pattern analysis over many sessions:</b> A very sophisticated attacker with access to many recorded sessions might attempt statistical analysis. Ghost nodes reduce this risk but do not eliminate it entirely for very short passwords.",
            "<b>Minimum password length:</b> Short passwords (6–7 characters) with only 2 ghost nodes provide a smaller anonymity set than longer passwords. Users are encouraged to use longer passwords.",
        ]),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9 — VR on Meta Quest 2
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("9", "VR Deployment on Meta Quest 2",
                            "How GridAuth runs on the VR headset and why it works without modification")

    story += [
        h2("9.1 Why Meta Quest 2?"),
        p("The Meta Quest 2 is a standalone VR headset that runs a customised version of <b>Android 10</b> "
          "as its underlying operating system. This is the same Android platform that standard Flutter "
          "applications target. As a result, the GridAuth Flutter APK can be installed and executed on "
          "the Quest 2 without any code changes."),
        h2("9.2 2D Panel Mode"),
        p("When a standard Android app (not built with the Meta XR SDK for native VR) is installed "
          "on the Quest, it runs in <b>2D panel mode</b>. The app appears as a floating rectangular "
          "screen in the user's virtual space — similar to how you might pin a browser tab to a wall "
          "in virtual space. The user can reposition this panel."),
        p("For GridAuth's authentication flow, this mode is highly effective: "
          "the 4-character node buttons are large, clearly visible, and easily tappable using "
          "the Quest controller's laser pointer. The user points the controller at a character "
          "button and squeezes the trigger to select it — a natural and intuitive interaction."),
        h2("9.3 Installation Process"),
        info_table([
            ("Prerequisite 1", "Enable Developer Mode on the Quest 2 via the Meta companion app on a smartphone"),
            ("Prerequisite 2", "Connect the Quest 2 to a PC via USB-C cable"),
            ("Prerequisite 3", "Accept the 'Allow USB Debugging' prompt inside the headset"),
            ("Install command", "adb install -r build\\app\\outputs\\flutter-apk\\app-debug.apk"),
            ("Launch", "Find the app under 'Unknown Sources' in the Quest 2 app library"),
        ]),
        h2("9.4 Network Configuration"),
        p("Since the backend server runs on a PC and the Quest 2 connects over Wi-Fi, both devices "
          "must be on the same local network. The app includes a <b>Server Settings screen</b> (accessible "
          "via the ⚙ gear icon) where the user enters the server's IP address and port. This was "
          "implemented specifically to handle VR deployment scenarios where the network IP may change."),
        h2("9.5 Virtual Keyboard for Registration"),
        p("The Meta Quest 2 provides its own <b>system virtual keyboard</b> that appears automatically "
          "whenever a Flutter TextField widget is focused. The registration flow uses standard Flutter "
          "TextField widgets, so the Quest's virtual keyboard appears naturally for entering the username "
          "and password during account creation — no special VR keyboard code was needed."),
        h2("9.6 VR-Specific Advantages of GridAuth"),
        p("GridAuth's design is particularly well-suited to VR environments:"),
        bullet_list([
            "<b>No physical keyboard required:</b> The node-tap interaction uses only the VR controller — the user never needs to reach for a physical keyboard to authenticate.",
            "<b>Shoulder-surfing is amplified in VR:</b> In a VR environment, bystanders can even see what is on the user's virtual screen. GridAuth's design means that even with full screen visibility, an observer learns nothing about the password.",
            "<b>Large touch targets:</b> The 4 character buttons per node are large enough to be easily selected with controller precision, even with the minor jitter typical of VR controllers.",
            "<b>Immersive future potential:</b> A future native VR version could display the nodes as 3D floating orbs in space, making the authentication experience feel deeply integrated into the VR environment.",
        ]),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SECTION 10 — Future Work
    # ═══════════════════════════════════════════════════════════════
    story += [PageBreak()]
    story += section_header("10", "Future Work &amp; Integration Potential",
                            "Planned improvements and integration pathways")

    story += [
        h2("10.1 Native VR Application"),
        p("The current implementation runs as a 2D panel in VR. A future version could be built as a "
          "fully native VR application using the <b>Meta XR SDK for Unity</b> or <b>Godot 4 with OpenXR</b>. "
          "In this version, the authentication nodes would be rendered as 3D objects floating in virtual "
          "space, and the user would physically reach out or point to select them. The backend API would "
          "remain unchanged — only the frontend would be rebuilt."),
        h2("10.2 Integration as an Identity Provider"),
        p("GridAuth can be extended to function as an <b>OpenID Connect (OIDC) Identity Provider</b>, "
          "allowing third-party applications to delegate authentication to GridAuth. A user on a website "
          "would click 'Sign in with GridAuth', be redirected to the GridAuth portal, complete the grid "
          "authentication, and receive a signed JWT token that the website can verify — the same pattern "
          "used by 'Sign in with Google' or 'Sign in with Apple'."),
        h2("10.3 Two-Factor Authentication (2FA) Plugin"),
        p("GridAuth can serve as a high-security visual second factor alongside traditional password "
          "systems. After entering a primary credential, the user completes a GridAuth node sequence on "
          "their VR headset or mobile device to approve the login — replacing less secure methods like "
          "SMS codes."),
        h2("10.4 Cloud Backend Deployment"),
        p("The FastAPI backend can be containerised with Docker and deployed to a cloud provider "
          "(AWS, Google Cloud, Azure). This would make the system accessible from any network without "
          "requiring the user to run a local server, and would enable the VR headset to authenticate "
          "independently of a nearby PC."),
        h2("10.5 Biometric Enhancement"),
        p("A future version could combine the grid authentication with biometric data "
          "(gaze tracking patterns unique to the user, controller movement signatures, or hand tracking) "
          "available on modern VR headsets, creating a multi-factor authentication system that is both "
          "highly secure and entirely frictionless."),
        sp(16),
        HRFlowable(width="100%", thickness=1.5, color=PURPLE, spaceAfter=10),
        p("End of Report", S("BodyText", fontSize=10, textColor=colors.HexColor("#888888"),
                              alignment=TA_CENTER, fontName="Helvetica-Oblique")),
        p(f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}",
          S("BodyText", fontSize=9, textColor=MID_GREY, alignment=TA_CENTER)),
    ]

    # ── Build ────────────────────────────────────────────────────────────────
    def on_first_page(canvas, doc):
        pass

    def on_later_pages(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#AAAAAA"))
        canvas.drawString(2.2*cm, 1.3*cm, "GridAuth — Technical Architecture & Design Report")
        canvas.drawRightString(A4[0] - 2.2*cm, 1.3*cm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f"✓ PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
