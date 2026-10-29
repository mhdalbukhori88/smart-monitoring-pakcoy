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
                ("admin", "Administrator Pakcoy", pwd_hash, salt, "Administrator")
            )
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

    # CSS Khusus Halaman Autentikasi (SaaS Style, Single Unified Card)
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

    /* Background SaaS Modern dengan micro-dot halus & radial gradient */
    .stApp {
        background-color: #f8fafc !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(83, 58, 253, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
            radial-gradient(#e2e8f0 1.2px, transparent 1.2px) !important;
        background-size: 100% 100%, 100% 100%, 28px 28px !important;
    }

    /* Layout terpusat vertikal dan horizontal */
    .main .block-container {
        max-width: 100% !important;
        padding-top: 4.5rem !important;
        padding-bottom: 3.5rem !important;
    }

    /* Container Kartu Autentikasi Tunggal - Ukuran Proporsional & Elegan */
    .st-key-auth_card,
    div[class*="st-key-auth_card"] {
        max-width: 460px !important;
        width: 100% !important;
        margin: 0 auto !important;
        background-color: #ffffff !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        border-radius: 24px !important;
        padding: 42px 38px 36px 38px !important;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(226, 232, 240, 0.8) !important;
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
        margin-bottom: 26px;
    }
    .auth-icon-circle {
        width: 64px;
        height: 64px;
        border-radius: 20px;
        background: linear-gradient(135deg, #eeedfe 0%, #e0e7ff 100%);
        color: #533afd;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
        border: 1px solid rgba(83, 58, 253, 0.15);
        box-shadow: 0 8px 20px -4px rgba(83, 58, 253, 0.2);
    }
    .auth-title {
        font-size: 24px;
        font-weight: 800;
        color: #0d253d;
        letter-spacing: -0.03em;
        margin-bottom: 6px;
        line-height: 1.25;
    }
    .auth-sub {
        font-size: 14px;
        color: #64748d;
        line-height: 1.5;
        margin: 0;
        font-weight: 400;
    }

    /* Input styling - Nyaman, modern, dan kokoh */
    .st-key-auth_card [data-testid="stTextInput"] {
        margin-bottom: 14px !important;
    }
    .st-key-auth_card [data-testid="stTextInput"] label p {
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-bottom: 6px !important;
    }
    .st-key-auth_card input {
        border-radius: 12px !important;
        border: 1.5px solid #d0d7de !important;
        background-color: #f8fafc !important;
        font-size: 14.5px !important;
        height: 46px !important;
        padding: 0 14px !important;
        color: #0f172a !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .st-key-auth_card input:focus {
        background-color: #ffffff !important;
        border-color: #533afd !important;
        box-shadow: 0 0 0 4px rgba(83, 58, 253, 0.14) !important;
        outline: none !important;
    }

    /* Tombol Utama (Login / Buat Akun) */
    .st-key-auth_card [data-testid="stFormSubmitButton"] button {
        border-radius: 12px !important;
        height: 48px !important;
        padding: 0 18px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        letter-spacing: -0.01em !important;
        background: linear-gradient(135deg, #533afd 0%, #4338ca 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(83, 58, 253, 0.28) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin-top: 10px !important;
        width: 100% !important;
    }
    .st-key-auth_card [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #4732db 0%, #3730a3 100%) !important;
        box-shadow: 0 6px 20px rgba(83, 58, 253, 0.38) !important;
        transform: translateY(-1px) !important;
    }
    .st-key-auth_card [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0px) !important;
    }

    /* Divider Pemisah */
    .auth-divider {
        position: relative;
        text-align: center;
        margin: 22px 0 16px 0;
    }
    .auth-divider::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #e2e8f0;
    }
    .auth-divider span {
        position: relative;
        background: #ffffff;
        padding: 0 14px;
        font-size: 12.5px;
        color: #94a3b8;
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
        border-radius: 10px !important;
        color: #533afd !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        margin: 0 auto !important;
        display: block !important;
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
        background-color: #f5f3ff !important;
        color: #3730a3 !important;
        text-decoration: underline !important;
    }

    /* Catatan Keamanan Footer */
    .auth-security-footer {
        font-size: 12px;
        color: #94a3b8;
        text-align: center;
        margin-top: 24px;
        line-height: 1.5;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_center, col_r = st.columns([1, 1.5, 1])

    with col_center:
        with st.container(key="auth_card"):
            # Tampilkan notifikasi jika ada pesan sukses dari registrasi
            if "registered_success_msg" in st.session_state:
                st.success(st.session_state.pop("registered_success_msg"))

            if is_login_mode:
                # HEADER LOGIN
                st.markdown(
                    f'<div class="auth-header">'
                    f'<div class="auth-icon-circle">{ui.icon("sprout", 28, color="#533afd")}</div>'
                    f'<div class="auth-title">Smart Farming Pakcoy</div>'
                    f'<div class="auth-sub">Masuk ke sistem monitoring sensor &amp; AI budidaya</div>'
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
                    f'<div class="auth-icon-circle">{ui.icon("user-plus", 28, color="#533afd")}</div>'
                    f'<div class="auth-title">Buat Akun Baru</div>'
                    f'<div class="auth-sub">Daftarkan akun untuk mengakses sistem monitoring</div>'
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

        # CATATAN KEAMANAN TERENKRIPSI DI BAWAH KARTU
        st.markdown(
            f'<div class="auth-security-footer">'
            f'{ui.icon("lock", 13, color="#94a3b8")} Enkripsi PBKDF2-HMAC-SHA256 &bull; Smart Farming Pakcoy'
            f'</div>',
            unsafe_allow_html=True
        )


def render_sidebar_user_profile():
    """Menampilkan widget profil pengguna yang aktif dan tombol logout di sidebar."""
    user = get_current_user()
    if not user:
        return

    name = user.get("full_name", "Pengguna")
    username = user.get("username", "user")
    role = user.get("role", "Pengguna")

    # Inisial avatar (2 huruf)
    parts = name.strip().split()
    initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else name[:2].upper()

    st.sidebar.markdown("""
    <style>
    .user-profile-box {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        background: #ffffff;
        border: 1px solid #e3e8ee;
        border-radius: 12px;
        margin-top: 14px;
        margin-bottom: 10px;
    }
    .user-avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #533afd 0%, #665efd 100%);
        color: #ffffff;
        font-size: 13.5px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        letter-spacing: 0.5px;
    }
    .user-info-text {
        overflow: hidden;
        flex-grow: 1;
        line-height: 1.35;
    }
    .user-name-title {
        font-size: 13px;
        font-weight: 600;
        color: #0d253d;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .user-meta-sub {
        font-size: 11.5px;
        color: #64748d;
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<div class="user-profile-box">'
        f'<div class="user-avatar">{initials}</div>'
        f'<div class="user-info-text">'
        f'<div class="user-name-title">{name}</div>'
        f'<div class="user-meta-sub">@{username} · {role}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.sidebar.button("Keluar (Logout)", key="btn_logout", use_container_width=True):
        logout()
