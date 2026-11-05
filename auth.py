"""Modul Otentikasi & Manajemen Pengguna (Login & Registrasi) Smart Farming Pakcoy.
Menggunakan database SQLite lokal, PBKDF2-HMAC-SHA256 untuk hashing password,
dan antarmuka Streamlit yang profesional sesuai DESIGN.md.
"""
import hmac
import hashlib
import os
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
import streamlit as st
import ui

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "users.db"


# ================================================================= Database & Security
def get_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt_hex: str = None) -> tuple[str, str]:
    """Hash password menggunakan PBKDF2-HMAC-SHA256 dengan 100.000 iterasi dan salt unik."""
    if salt_hex is None:
        salt_hex = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000).hex()
    return pwd_hash, salt_hex


def verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    """Verifikasi kecocokan password dengan perbandingan konstan (constant-time comparison)."""
    calculated_hash, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(calculated_hash, expected_hash)


def init_db():
    """Inisialisasi tabel pengguna dan buat akun default pertama jika database masih baru."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'Pengguna',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        conn.commit()

        # Seed akun default jika belum ada user sama sekali
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        if count == 0:
            pwd_hash, salt = hash_password("admin123")
            conn.execute(
                "INSERT INTO users (username, full_name, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
                ("admin", "Admin", pwd_hash, salt, "Administrator")
            )
            conn.commit()
        else:
            conn.execute("UPDATE users SET full_name = 'Admin' WHERE username = 'admin' AND full_name = 'Administrator Pakcoy'")
            conn.commit()


def register_user(username: str, full_name: str, password: str, role: str = "Pengguna") -> tuple[bool, str]:
    """Mendaftarkan akun baru ke database dengan validasi ketat."""
    username = username.strip().lower()
    full_name = full_name.strip()

    if not username or not full_name or not password:
        return False, "Semua bidang formulir wajib diisi."
    if len(username) < 3 or len(username) > 30:
        return False, "Username harus terdiri dari 3 hingga 30 karakter."
    if not re.match(r"^[a-z0-9_.]+$", username):
        return False, "Username hanya boleh memuat huruf kecil, angka, titik, atau garis bawah (_)."
    if len(full_name) < 2:
        return False, "Nama lengkap minimal 2 karakter."
    if len(password) < 6:
        return False, "Kata sandi minimal 6 karakter demi keamanan akun."

    pwd_hash, salt = hash_password(password)
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, full_name, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
                (username, full_name, pwd_hash, salt, role)
            )
            conn.commit()
        return True, "Akun berhasil dibuat! Silakan masuk menggunakan username dan kata sandi Anda."
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' sudah digunakan. Silakan pilih username lain."
    except Exception as e:
        return False, f"Gagal mendaftarkan akun: {e}"


def authenticate(username: str, password: str) -> tuple[bool, dict | None, str]:
    """Validasi login username dan password."""
    username = username.strip().lower()
    if not username or not password:
        return False, None, "Username dan kata sandi wajib diisi."

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()

        if not row:
            return False, None, "Username atau kata sandi tidak cocok."

        if verify_password(password, row["salt"], row["password_hash"]):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
            conn.commit()
            user_data = {
                "id": row["id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "created_at": row["created_at"],
                "last_login": now
            }
            return True, user_data, "Login berhasil."
        else:
            return False, None, "Username atau kata sandi tidak cocok."


# ================================================================= Session Management
def is_logged_in() -> bool:
    return st.session_state.get("authenticated", False) and st.session_state.get("user") is not None


def get_current_user() -> dict | None:
    return st.session_state.get("user")


def login_user(user_dict: dict):
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_dict
    st.rerun()


def logout():
    st.session_state["authenticated"] = False
    st.session_state.pop("user", None)
    st.session_state.pop("upload_df", None)
    st.session_state.pop("mon_recs", None)
    st.session_state.pop("ai_chat_history", None)
    st.rerun()


# ================================================================= UI Tampilan
def render_auth_page():
    """Menampilkan halaman Login dan Registrasi Akun yang profesional, bersih, dan terpusat dalam satu kartu tunggal."""
    init_db()

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    is_login_mode = st.session_state["auth_mode"] == "login"

    # CSS Khusus Halaman Autentikasi (Tema Agronomi Hijau Pakcoy, Single Unified Card)
    st.markdown("""
    <style>
    /* Sembunyikan sidebar, kontrol sidebar, header deploy, dan menu atas saat login */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    .stDeployButton,
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Background Agronomi Bersih dengan pola grid halus */
    .stApp {
        background-color: #f4f7f4 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(21, 128, 61, 0.06) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(13, 148, 136, 0.05) 0px, transparent 50%),
            radial-gradient(#d5e0d8 1.1px, transparent 1.1px) !important;
        background-size: 100% 100%, 100% 100%, 26px 26px !important;
    }

    /* Layout terpusat vertikal dan horizontal penuh (Desktop, Android, iOS) */
    [data-testid="stMainBlockContainer"],
    .block-container {
        max-width: 100% !important;
        min-height: 100vh !important;
        min-height: 100dvh !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 24px 16px !important;
        margin: 0 auto !important;
        box-sizing: border-box !important;
    }

    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
        width: 100% !important;
        max-width: 425px !important;
        margin: auto !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }

    /* Container Kartu Autentikasi Tunggal */
    .st-key-auth_card,
    div[class*="st-key-auth_card"] {
        max-width: 425px !important;
        width: 100% !important;
        margin: 0 auto !important;
        background-color: #ffffff !important;
        border: 1px solid #d5e2d9 !important;
        border-top: 4px solid #15803d !important;
        border-radius: 14px !important;
        padding: 34px 32px 26px 32px !important;
        box-shadow: 0 14px 34px -8px rgba(17, 28, 22, 0.08) !important;
        box-sizing: border-box !important;
    }

    @media (max-width: 480px) {
        [data-testid="stMainBlockContainer"],
        .block-container {
            padding: 16px 12px !important;
        }
        .st-key-auth_card,
        div[class*="st-key-auth_card"] {
            padding: 26px 20px 22px 20px !important;
            border-radius: 12px !important;
        }
        .auth-title {
            font-size: 19px !important;
        }
        .auth-sub {
            font-size: 12.5px !important;
        }
        /* Cegah auto-zoom pada iOS Safari saat mengetuk input */
        .st-key-auth_card input {
            font-size: 16px !important;
        }
    }

    /* Hilangkan border dan padding bawaan stForm di dalam kartu */
    .st-key-auth_card [data-testid="stForm"],
    div[class*="st-key-auth_card"] [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Header di dalam kartu */
    .auth-header {
        text-align: center;
        margin-bottom: 22px;
    }
    .auth-icon-circle {
        width: 60px;
        height: 60px;
        border-radius: 14px;
        background-color: #ffffff;
        color: #15803d;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        padding: 4px;
        overflow: hidden;
        border: 1.5px solid #bbf7d0;
        box-shadow: 0 4px 12px rgba(21, 128, 61, 0.10);
    }
    .auth-title {
        font-size: 21px;
        font-weight: 700;
        color: #111c16;
        letter-spacing: -0.02em;
        margin-bottom: 5px;
        line-height: 1.25;
    }
    .auth-sub {
        font-size: 13px;
        color: #5c6f64;
        line-height: 1.45;
        margin: 0;
        font-weight: 400;
    }

    /* Input styling (Single Clean Border on Root Element) */
    .st-key-auth_card [data-testid="stTextInput"] {
        margin-bottom: 12px !important;
    }
    .st-key-auth_card [data-testid="stTextInput"] label p {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #26382f !important;
        margin-bottom: 4px !important;
    }
    .st-key-auth_card [data-testid="stTextInput"] [data-testid="stTextInputRootElement"],
    .st-key-auth_card [data-testid="stTextInput"] [class*="e1bh1cux2"] {
        border-radius: 9px !important;
        border: 1px solid #b8c9be !important;
        background-color: #f9fbf9 !important;
        height: 42px !important;
        min-height: 42px !important;
        box-shadow: 0 1px 2px rgba(17, 28, 22, 0.02) !important;
        transition: all 0.18s ease !important;
    }
    .st-key-auth_card [data-testid="stTextInput"] [data-testid="stTextInputRootElement"]:focus-within,
    .st-key-auth_card [data-testid="stTextInput"] [class*="e1bh1cux2"]:focus-within {
        background-color: #ffffff !important;
        border-color: #15803d !important;
        box-shadow: 0 0 0 3px rgba(21, 128, 61, 0.14) !important;
    }
    .st-key-auth_card input {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        font-size: 13.8px !important;
        height: 40px !important;
        padding: 0 13px !important;
        color: #111c16 !important;
    }

    /* Tombol Utama (Login / Buat Akun) */
    .st-key-auth_card [data-testid="stFormSubmitButton"] button {
        border-radius: 9px !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        padding: 0 18px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        background-color: #15803d !important;
        color: #ffffff !important;
        border: 1px solid #166534 !important;
        box-shadow: 0 2px 6px rgba(20, 83, 45, 0.18) !important;
        transition: all 0.18s ease !important;
        margin-top: 6px !important;
        width: 100% !important;
    }
    .st-key-auth_card [data-testid="stFormSubmitButton"] button:hover {
        background-color: #166534 !important;
        border-color: #14532d !important;
        box-shadow: 0 4px 12px rgba(20, 83, 45, 0.26) !important;
    }

    /* Divider Pemisah */
    .auth-divider {
        position: relative;
        text-align: center;
        margin: 18px 0 10px 0;
    }
    .auth-divider::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #dce5de;
    }
    .auth-divider span {
        position: relative;
        background: #ffffff;
        padding: 0 14px;
        font-size: 12px;
        color: #6b7f73;
        font-weight: 500;
        text-transform: lowercase;
    }

    /* Tombol Switch Mode (Link Style di bawah tombol form) */
    .stApp [data-testid="stMainBlockContainer"] div.st-key-btn_toggle_mode > .stButton > button,
    .stApp [data-testid="stMainBlockContainer"] .st-key-btn_toggle_mode button,
    .stApp .st-key-btn_toggle_mode button,
    .st-key-btn_toggle_mode button,
    div[class*="st-key-btn_toggle_mode"] button {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        color: #15803d !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        padding: 6px 14px !important;
        height: 36px !important;
        min-height: 36px !important;
        max-height: 36px !important;
        margin: 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: color 0.15s ease, background-color 0.15s ease !important;
    }
    .stApp [data-testid="stMainBlockContainer"] div.st-key-btn_toggle_mode > .stButton > button:hover,
    .stApp [data-testid="stMainBlockContainer"] .st-key-btn_toggle_mode button:hover,
    .stApp .st-key-btn_toggle_mode button:hover,
    .st-key-btn_toggle_mode button:hover,
    div[class*="st-key-btn_toggle_mode"] button:hover {
        background-color: #f0fdf4 !important;
        color: #14532d !important;
        text-decoration: underline !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="auth_card"):
        # Tampilkan notifikasi jika ada pesan sukses dari registrasi
        if "registered_success_msg" in st.session_state:
            st.success(st.session_state.pop("registered_success_msg"))

        if is_login_mode:
            # HEADER LOGIN
            st.markdown(
                f'<div class="auth-header">'
                f'<div class="auth-icon-circle">{ui.brand_logo_html(52)}</div>'
                f'<div class="auth-title">Smart Farming Pakcoy</div>'
                f'<div class="auth-sub">Sistem Monitoring Sensor &amp; Analitik Budidaya Tanaman Pakcoy</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # FORM LOGIN
            with st.form("form_login", clear_on_submit=False):
                username_in = st.text_input(
                    "Username",
                    placeholder="Masukkan username Anda",
                    key="login_username"
                ).strip()
                password_in = st.text_input(
                    "Kata Sandi",
                    type="password",
                    placeholder="Masukkan kata sandi",
                    key="login_password"
                )

                btn_login = st.form_submit_button("Masuk ke Sistem", type="primary", use_container_width=True)

                if btn_login:
                    success, user_data, msg = authenticate(username_in, password_in)
                    if success:
                        st.success(f"Selamat datang kembali, {user_data['full_name']}!")
                        login_user(user_data)
                    else:
                        st.error(msg)

            # DIVIDER
            st.markdown(
                '<div class="auth-divider"><span>atau</span></div>',
                unsafe_allow_html=True
            )

            # TULISAN BUAT AKUN DI BAWAH TOMBOL LOGIN
            if st.button("Belum punya akun? Buat Akun Baru →", key="btn_toggle_mode", use_container_width=True):
                st.session_state["auth_mode"] = "register"
                st.rerun()

        else:
            # HEADER REGISTRASI
            st.markdown(
                f'<div class="auth-header">'
                f'<div class="auth-icon-circle">{ui.brand_logo_html(52)}</div>'
                f'<div class="auth-title">Buat Akun Baru</div>'
                f'<div class="auth-sub">Daftarkan akun untuk mengakses sistem monitoring pakcoy</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # FORM REGISTRASI
            with st.form("form_register", clear_on_submit=False):
                reg_name = st.text_input("Nama Lengkap", placeholder="Contoh: Muhammad Bukhori", key="reg_name").strip()
                reg_user = st.text_input("Username", placeholder="Contoh: bukhori (huruf kecil & angka)", key="reg_user").strip()
                reg_pwd = st.text_input("Kata Sandi", type="password", placeholder="Minimal 6 karakter", key="reg_pwd")
                reg_pwd2 = st.text_input("Konfirmasi Kata Sandi", type="password", placeholder="Ketik ulang kata sandi", key="reg_pwd2")

                btn_register = st.form_submit_button("Buat Akun Sekarang", type="primary", use_container_width=True)

                if btn_register:
                    if reg_pwd != reg_pwd2:
                        st.error("Konfirmasi kata sandi tidak cocok. Silakan periksa kembali.")
                    else:
                        ok, msg = register_user(reg_user, reg_name, reg_pwd)
                        if ok:
                            st.session_state["registered_success_msg"] = "Akun berhasil dibuat! Silakan masuk dengan akun baru Anda."
                            st.session_state["login_username"] = reg_user
                            st.session_state["auth_mode"] = "login"
                            st.rerun()
                        else:
                            st.error(msg)

            # DIVIDER
            st.markdown(
                '<div class="auth-divider"><span>atau</span></div>',
                unsafe_allow_html=True
            )

            # TULISAN KEMBALI KE LOGIN
            if st.button("Sudah punya akun? Masuk ke Akun ←", key="btn_toggle_mode", use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()


def render_sidebar_user_profile():
    """Menampilkan widget profil pengguna yang aktif dan tombol logout di sidebar."""
    user = get_current_user()
    if not user:
        return

    raw_name = user.get("full_name", "Admin")
    username = user.get("username", "admin")
    role = user.get("role", "Administrator")
    if username == "admin" or raw_name == "Administrator Pakcoy":
        name = "Admin"
        user["full_name"] = "Admin"
    else:
        name = raw_name
    user_icon_svg = ui.icon("user", 18, color="#15803d")

    st.sidebar.markdown("""
    <style>
    .user-profile-box {
        display: flex;
        align-items: center;
        gap: 11px;
        padding: 10px 12px;
        background: #ffffff;
        border: 1px solid #d5e0d8;
        border-radius: 10px;
        margin-top: 2px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(17, 28, 22, 0.03);
    }
    .user-avatar {
        width: 36px;
        height: 36px;
        border-radius: 9px;
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .user-avatar svg {
        stroke: #15803d !important;
    }
    .user-info-text {
        overflow: hidden;
        flex-grow: 1;
        line-height: 1.3;
    }
    .user-name-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 6px;
    }
    .user-name-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #111c16;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .user-online-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 10px;
        font-weight: 600;
        color: #15803d;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 1px 7px;
        border-radius: 999px;
        flex-shrink: 0;
    }
    .user-online-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #22c55e;
    }
    .user-meta-sub {
        font-size: 11.5px;
        color: #5c6f64;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<div class="user-profile-box">'
        f'<div class="user-avatar">{user_icon_svg}</div>'
        f'<div class="user-info-text">'
        f'<div class="user-name-row">'
        f'<span class="user-name-title">{ui._e(name)}</span>'
        f'<span class="user-online-pill"><span class="user-online-dot"></span>Aktif</span>'
        f'</div>'
        f'<div class="user-meta-sub">@{ui._e(username)} &middot; {ui._e(role)}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.sidebar.button("Keluar Akun", key="btn_logout", use_container_width=True):
        logout()
