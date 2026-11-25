"""Smart Farming Pakcoy: dashboard realtime, eksplorasi data, monitoring sensor, LSTM, prediksi 4 hari,
CNN (scan foto), dan scan gabungan."""
import hashlib
import importlib
import io
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

import utils
import ui
import charts
import ai_assistant
import auth


def _reload_local_modules_if_changed():
    """Reload submodul lokal hanya saat file berubah di disk (aman untuk hot-reload Streamlit Cloud tanpa overhead rerun)."""
    tracked = getattr(sys, "_pakcoy_mod_mtimes", None)
    first_boot = tracked is None
    if tracked is None:
        tracked = {}
        sys._pakcoy_mod_mtimes = tracked

    ordered = [
        ("utils", utils),
        ("ui", ui),
        ("charts", charts),
        ("auth", auth),
        ("ai_assistant", ai_assistant),
    ]
    reloaded_any = False
    for name, mod in ordered:
        mod_file = getattr(mod, "__file__", None)
        if not mod_file:
            continue
        try:
            mtime_ns = Path(mod_file).stat().st_mtime_ns
        except OSError:
            continue
        prev = tracked.get(name)
        # Reload jika belum pernah dilacak pada proses hot-reload atau file berubah (atau dependensi sebelumnya baru di-reload)
        if first_boot or prev != mtime_ns or reloaded_any:
            try:
                importlib.reload(mod)
                reloaded_any = True
            except Exception:
                pass
            tracked[name] = mtime_ns


_reload_local_modules_if_changed()

_LOGO_FILE = Path(__file__).parent / "assets" / "logo_pakcoy.png"
st.set_page_config(
    page_title="Smart Farming Pakcoy",
    page_icon=str(_LOGO_FILE) if _LOGO_FILE.exists() else ":material/eco:",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.inject_css()

# Gerbang Keamanan Otentikasi (Login & Registrasi Pengguna)
auth.init_db()
if not auth.is_logged_in():
    auth.render_auth_page()
    st.stop()

ROOT = Path(__file__).parent
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"
DRY = float(getattr(utils, "DRY_LIMIT", 55.0))
WET = float(getattr(utils, "WET_LIMIT", 76.0))
TEMP_OPT_MIN = float(getattr(utils, "TEMP_OPT_MIN", 22.0))
TEMP_OPT_MAX = float(getattr(utils, "TEMP_OPT_MAX", 28.0))
MAT = utils.MATURITY_COL
DEFAULT_THRESH = [66.5, 89.0]


def _file_fingerprint(*paths):
    """Sidik jari mtime+size agar cache data otomatis ter-invalidasi saat file CSV diperbarui."""
    parts = []
    for p in paths:
        if p.exists():
            st_i = p.stat()
            parts.append(f"{p.name}:{st_i.st_mtime_ns}:{st_i.st_size}")
    return "|".join(parts)


# ================================================================= data & model
@st.cache_data
def _load_builtin_cached(_fp: str):
    train_30 = DATA_DIR / "data_training_30hari.csv"
    asli_30 = DATA_DIR / "data_asli_30hari.csv"
    if train_30.exists() and asli_30.exists():
        sim = pd.read_csv(train_30)
        asli = pd.read_csv(asli_30)
    elif (DATA_DIR / "data_training.csv").exists() and (DATA_DIR / "data_asli.csv").exists():
        st.warning("Dataset 30 hari belum dibuat. Menggunakan dataset cadangan lama.")
        sim = pd.read_csv(DATA_DIR / "data_training.csv")
        asli = pd.read_csv(DATA_DIR / "data_asli.csv")
    else:
        st.error("File dataset tidak ditemukan di folder data/.")
        sim = pd.DataFrame()
        asli = pd.DataFrame()
    asli["Cycle_ID"] = 0
    asli["Split"] = "asli"
    return sim, asli


def load_builtin():
    fp = _file_fingerprint(DATA_DIR / "data_training_30hari.csv", DATA_DIR / "data_asli_30hari.csv")
    return _load_builtin_cached(fp)


def get_models_fingerprint():
    """Menghasilkan sidik jari (hash) dari semua file model agar cache Streamlit ter-invalidasi otomatis saat file berubah."""
    sig = ["v5_cnn_4class_gatekeeper_2026"]
    for fname in ["config_cnn.json", "config_lstm.json", "model_cnn.keras", "model_lstm_klasifikasi.keras", "model_lstm_forecast.keras"]:
        p = MODELS_DIR / fname
        if p.exists():
            st_info = p.stat()
            sig.append(f"{fname}:{st_info.st_mtime_ns}:{st_info.st_size}")
    return hashlib.md5(";".join(sig).encode("utf-8")).hexdigest()


@st.cache_resource(show_spinner="Memuat model AI (pertama kali bisa beberapa detik)...")
def _load_models_cached(_fp):
    res = {"cnn": None, "clf": None, "fc": None, "cfg_lstm": None, "cfg_cnn": None, "error": None}
    try:
        from tensorflow import keras
    except Exception as e:
        res["error"] = f"TensorFlow tidak dapat dimuat: {e}"
        return res
    try:
        if (MODELS_DIR / "config_lstm.json").exists():
            res["cfg_lstm"] = utils.load_json(MODELS_DIR / "config_lstm.json")
        if (MODELS_DIR / "config_cnn.json").exists():
            res["cfg_cnn"] = utils.load_json(MODELS_DIR / "config_cnn.json")
        for key, fname in [("clf", "model_lstm_klasifikasi.keras"), ("fc", "model_lstm_forecast.keras"),
                           ("cnn", "model_cnn.keras")]:
            p = MODELS_DIR / fname
            if p.exists():
                res[key] = keras.models.load_model(p, compile=False)
    except Exception as e:
        res["error"] = f"Gagal memuat model (cek versi TensorFlow di requirements.txt): {e}"
    return res


def load_models():
    fp = get_models_fingerprint()
    return _load_models_cached(fp)


def lstm_ready(m, kind):
    return m.get(kind) is not None and m.get("cfg_lstm") is not None


def thresholds(m):
    return m["cfg_lstm"]["maturity_thresholds"] if m.get("cfg_lstm") else DEFAULT_THRESH


COND_LABELS_ID = {
    "Optimal": "Ideal (Optimal)",
    "Dry": "Kering (Butuh Air)",
    "Wet": "Terlalu Basah",
}
JAM_LABELS_ID = {
    "06:00": "06:00 (Pagi)",
    "07:00": "07:00 (Pagi)",
    "08:00": "08:00 (Pagi)",
    "09:00": "09:00 (Pagi)",
    "10:00": "10:00 (Pagi)",
    "11:00": "11:00 (Siang)",
    "12:00": "12:00 (Siang)",
    "13:00": "13:00 (Siang)",
    "14:00": "14:00 (Siang)",
    "15:00": "15:00 (Sore)",
    "16:00": "16:00 (Sore)",
    "17:00": "17:00 (Sore)",
    "18:00": "18:00 (Malam)",
    "19:00": "19:00 (Malam)",
    "20:00": "20:00 (Malam)",
}


def label(name):
    return utils.CLASS_LABELS.get(name, name)


def cond_label(cond):
    return COND_LABELS_ID.get(str(cond), str(cond))


def format_display_df(df):
    """Ubah kolom dan isi tabel menjadi Bahasa Indonesia yang mudah dipahami orang awam (hanya untuk tampilan)."""
    has_multi_cycle = "Cycle_ID" in df.columns and df["Cycle_ID"].nunique() > 1
    base_cols = (["Cycle_ID"] if has_multi_cycle else []) + [c for c in utils.REQUIRED_COLS if c in df.columns]
    if "Status Pompa" in df.columns and "Status Pompa" not in base_cols:
        base_cols.append("Status Pompa")
    out = df[base_cols].copy()
    if "Cycle_ID" in out.columns:
        out["Cycle_ID"] = out["Cycle_ID"].apply(lambda c: f"Siklus {int(c)}")
    if "Day" in out.columns:
        out["Day"] = out["Day"].apply(lambda d: f"Hari ke-{int(d)}")
    if "Time" in out.columns:
        out["Time"] = out["Time"].astype(str).map(lambda t: JAM_LABELS_ID.get(t, t))
    if "Soil Condition" in out.columns:
        out["Soil Condition"] = out["Soil Condition"].astype(str).map(cond_label)
    if "Ground Truth Criteria" in out.columns:
        out["Ground Truth Criteria"] = out["Ground Truth Criteria"].astype(str).map(label)
    if MAT in out.columns:
        out[MAT] = out[MAT].round(1)
    return out.rename(columns={
        "Cycle_ID": "Siklus Tanam",
        "Day": "Umur Tanaman",
        "Time": "Waktu Ukur",
        "Soil Moisture (%)": "Kelembapan Tanah (%)",
        "Temperature (°C)": "Suhu Udara (°C)",
        "Soil Condition": "Kondisi Tanah",
        MAT: "Tingkat Kematangan (%)",
        "Ground Truth Criteria": "Fase Pertumbuhan",
    })


def show(fig, key, container=None):
    (container or st).plotly_chart(
        fig,
        key=key,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "staticPlot": False,
            "responsive": True,
        }
    )


def get_sources():
    sim, asli = load_builtin()
    src = {
        "Data Siklus Tanaman Pakcoy": sim,
        "Data Asli Pengamatan Lapangan": asli
    }
    up = st.session_state.get("upload_df")
    if up is not None:
        src["Dataset Unggahan"] = up
    return src


def pick_dataset(key, extra_filters=False, btn_label="Tampilkan Data Siklus"):
    sim, _ = load_builtin()
    up = st.session_state.get("upload_df")

    all_cycles = sorted(sim["Cycle_ID"].unique().tolist())
    cycle_options = [f"Siklus {c}" for c in all_cycles] + ["Semua Siklus (1–30)"]
    if up is not None:
        cycle_options.append("Dataset Unggahan")

    with st.container(border=True, key=f"card_ds_{key}"):
        c_sel, c_btn = st.columns([4.5, 1.0], vertical_alignment="bottom")
        selected_label = c_sel.selectbox(
            "Pilih Siklus Tanam",
            options=cycle_options,
            index=0,
            key=f"{key}_single_cycle"
        )
        clicked = c_btn.button(btn_label, type="primary", use_container_width=True, key=f"{key}_apply_btn")

        valid_sel = True
        if selected_label == "Semua Siklus (1–30)":
            df = sim
            src_name = "Semua Siklus (1–30)"
            cyc_sig = ("all",)
        elif selected_label == "Dataset Unggahan" and up is not None:
            df = up
            src_name = "Dataset Unggahan"
            cyc_sig = ("upload", st.session_state.get("upload_name", ""), len(up))
        else:
            c_num = int(selected_label.replace("Siklus ", ""))
            df = sim[sim["Cycle_ID"] == c_num]
            src_name = selected_label
            cyc_sig = ("single", c_num)

        full_sig = (src_name, cyc_sig)

        if clicked or f"{key}_applied_sig" not in st.session_state:
            if not valid_sel or len(df) == 0:
                ui.banner("warn", "Pilihan siklus belum memiliki data. Silakan pilih siklus tanam yang sesuai.")
                return src_name, df, False
            st.session_state[f"{key}_applied_sig"] = full_sig

    is_applied = valid_sel and len(df) > 0
    return src_name, df, is_applied


def _get_series_options():
    sim, _ = load_builtin()
    up = st.session_state.get("upload_df")
    options = {}
    for c in sorted(sim["Cycle_ID"].unique()):
        options[f"Siklus {c}"] = sim[sim["Cycle_ID"] == c]
    if up is not None:
        options["Dataset Unggahan"] = up
    return options


def pick_series(key, container=None):
    options = _get_series_options()
    labels = list(options.keys())
    default_idx = 0
    host = container if container is not None else st
    choice = host.selectbox("Pilih Siklus Tanam", labels, index=default_idx, key=f"{key}_series")
    df = options[choice]
    return df.sort_values("Time_Index").reset_index(drop=True)


def warn_models(m, needed):
    if m.get("error"):
        st.error(m["error"])
    missing = [k for k in needed if m.get(k) is None]
    if missing:
        ui.banner("warn", "Model belum tersedia (" + ", ".join(missing) +
                  "). Latih di Google Colab, lalu taruh file hasilnya di folder models/.")
        return False
    return True


# ================================================================= prediksi
def predict_stage(m, window_df):
    x = utils.make_features(window_df, m["cfg_lstm"])[None]
    return m["clf"](x, training=False).numpy()[0]


def predict_forecast(m, window_df):
    cfg = m["cfg_lstm"]
    x = utils.make_features(window_df, cfg)[None]
    last_time = str(window_df["Time"].iloc[-1])
    if last_time not in utils.JAM_MAP:
        raise ValueError(f"Waktu pengukuran terakhir '{last_time}' tidak didukung model LSTM (harus 08:00, 12:00, atau 16:00).")
    pred = m["fc"](x, training=False).numpy()[0]
    return utils.forecast_table(pred, cfg, utils.JAM_MAP[last_time])


def predict_image(m, img):
    size = tuple(m["cfg_cnn"]["img_size"]) if m.get("cfg_cnn") else (224, 224)
    x = np.asarray(img.convert("RGB").resize(size), dtype="float32")[None]
    raw_p = m["cnn"](x, training=False).numpy()[0]
    if len(raw_p) == 3:
        p = np.array([0.0, raw_p[0], raw_p[1], raw_p[2]], dtype="float32")
    elif len(raw_p) == 4:
        p = np.array(raw_p, dtype="float32")
    else:
        p = np.array(raw_p, dtype="float32")
    return p


def cnn_names(m):
    cfg_names = m.get("cfg_cnn", {}).get("class_names") if m.get("cfg_cnn") else None
    if cfg_names and len(cfg_names) == 4:
        return cfg_names
    return utils.CNN_CLASS_NAMES


@st.cache_data(show_spinner="Memvalidasi file Excel...")
def _parse_uploaded_excel(file_bytes: bytes, file_name: str):
    """Membaca dan memvalidasi file Excel unggahan dengan caching berbasis konten file."""
    if not file_bytes:
        raise ValueError("File Excel kosong (0 byte).")
    if len(file_bytes) > 10 * 1024 * 1024:
        raise ValueError("Ukuran file Excel melebihi batas maksimal 10 MB.")
    try:
        raw_df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"File '{file_name}' tidak dapat dibaca sebagai workbook Excel valid: {exc}") from exc
    return utils.normalize_dataset(raw_df)


# ================================================================= sidebar
def sidebar():
    sb = st.sidebar
    sb.markdown(
        '<div class="brand-header-card">'
        '<span class="brand-icon-box">' + ui.brand_logo_html(36) + '</span>'
        '<div class="brand-text-col">'
        '<div class="brand-title">Smart Farming Pakcoy</div>'
        '<div class="brand-sub">Monitoring &amp; Agronomi Presisi</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    sb.markdown('<div class="micro-cap">MENU NAVIGASI</div>', unsafe_allow_html=True)
    choice = sb.radio("Menu", list(PAGES.keys()), label_visibility="collapsed", format_func=ui.strip_emoji)

    m = load_models()
    if st.session_state.pop("_models_reloaded", False):
        ready_cnt = sum(1 for k in ("clf", "fc", "cnn") if m.get(k) is not None)
        if m.get("error"):
            st.toast(f"Gagal memuat ulang model: {m['error']}")
        else:
            st.toast(f"Model AI berhasil dimuat ulang ({ready_cnt}/3 model siap).")

    sb.markdown('<div class="micro-cap">DATA &amp; SISTEM</div>', unsafe_allow_html=True)
    f = sb.file_uploader("Impor Data Excel (.xlsx)", type=["xlsx"], key="upl")
    if f is not None:
        try:
            up_df = _parse_uploaded_excel(f.getvalue(), f.name)
            st.session_state["upload_df"] = up_df
            st.session_state["upload_name"] = f.name
            sb.success(f"Dataset dimuat: {len(up_df):,} baris")
            bad_times = sorted(set(up_df["Time"].astype(str)) - set(utils.JAM_LIST))
            if bad_times:
                sb.caption(
                    "Catatan: Jam di luar 08:00/12:00/16:00 terdeteksi; "
                    "data tetap tampil di Dashboard, namun Prakiraan LSTM butuh jam 08:00, 12:00, 16:00."
                )
        except Exception as e:
            st.session_state.pop("upload_df", None)
            st.session_state.pop("upload_name", None)
            sb.error(f"Dataset tidak sesuai: {e}")
    else:
        st.session_state.pop("upload_df", None)
        st.session_state.pop("upload_name", None)

    if sb.button("Muat Ulang Model AI", key="reload_models"):
        _load_models_cached.clear()
        st.session_state["_models_reloaded"] = True
        st.rerun()

    ready_items = [
        ("LSTM Klasifikasi", m.get("clf") is not None),
        ("LSTM Prakiraan", m.get("fc") is not None),
        ("CNN Citra", m.get("cnn") is not None),
    ]
    ready_count = sum(1 for _, ok in ready_items if ok)
    if ready_count < len(ready_items):
        missing_lbl = ", ".join(name for name, ok in ready_items if not ok)
        sb.markdown(
            f'<div class="sb-status-pill warn"><span class="sb-status-dot"></span>'
            f'<span>{ready_count}/3 Model Aktif &middot; Kurang: {ui._e(missing_lbl)}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        sb.markdown(
            '<div class="sb-status-pill ok"><span class="sb-status-dot"></span>'
            '<span>3/3 Model AI Aktif &middot; LSTM + CNN</span></div>',
            unsafe_allow_html=True,
        )

    sb.markdown('<div class="micro-cap">AKUN PENGGUNA</div>', unsafe_allow_html=True)
    auth.render_sidebar_user_profile()
    return choice


# ================================================================= dashboard
def _render_live_content(advance=False):
    """Render isi konsol telemetri dan grafik live."""
    df = st.session_state.get("live_df")
    if df is None or len(df) == 0:
        return
    n = len(df)
    i = int(st.session_state.get("live_i", 0))
    if i >= n or i < 0:
        i = 0
    if advance:
        i = (i + int(st.session_state.get("live_step", 1))) % n
        st.session_state["live_i"] = i
    row = df.iloc[i]
    hist = df.iloc[max(0, i - 35): i + 1].set_index("Time_Index")
    grow = df.iloc[: i + 1].set_index("Time_Index")

    m = load_models()
    th = thresholds(m)
    w = m["cfg_lstm"]["w_cls"] if m.get("cfg_lstm") else 6
    if lstm_ready(m, "clf") and i + 1 >= w:
        try:
            p = predict_stage(m, df.iloc[i - w + 1: i + 1])
            k = int(p.argmax())
            tahap, sumber = f"{label(utils.CLASS_NAMES[k])}", f"Deteksi AI · Yakin {p[k]:.0%}"
        except Exception:
            tahap = label(str(row.get("Ground Truth Criteria", "Masa Pertumbuhan")))
            sumber = "Data catatan kebun"
    else:
        tahap = label(str(row.get("Ground Truth Criteria", "Masa Pertumbuhan")))
        sumber = "Data catatan kebun"
    raw_cond = str(row["Soil Condition"])
    jam_str = JAM_LABELS_ID.get(str(row["Time"]), str(row["Time"]))

    override = st.session_state.get("pump_override", "AUTO")
    was_on = bool(st.session_state.get("pump_was_on", False))
    pump_is_on, pump_status = utils.pump_decision(
        float(row["Soil Moisture (%)"]),
        was_on,
        dry=DRY,
        wet=WET,
        margin=5.0,
    )
    if override == "ON":
        st.session_state["pump_was_on"] = True
    elif override == "OFF":
        st.session_state["pump_was_on"] = False
    else:
        st.session_state["pump_was_on"] = pump_is_on

    ui.live_telemetry_console(
        day=int(row["Day"]),
        cycle_days=utils.CYCLE_DAYS,
        jam_str=jam_str,
        step_idx=i + 1,
        total_steps=n,
        moist=row["Soil Moisture (%)"],
        temp=row["Temperature (°C)"],
        cond_str=cond_label(raw_cond),
        mat=row[MAT],
        stage_str=tahap,
        stage_source=sumber,
        dry=DRY,
        wet=WET,
        override=override,
        pump_is_on=pump_is_on,
        pump_status=pump_status,
    )

    c1, c2 = st.columns(2)
    show(charts.live_line(hist, "Soil Moisture (%)", "Grafik Kelembapan Tanah (%)", "#38bdf8", "Kelembapan (%)", dry=DRY, wet=WET),
         "live_moist_chart", c1)
    show(charts.live_line(hist, "Temperature (°C)", "Grafik Suhu Udara (°C)", "#fb923c", "Suhu (°C)"), "live_temp_chart", c2)
    c3, c4 = st.columns([1, 2])
    show(charts.gauge(row[MAT], "Indikator Kematangan Tanaman (%)", th), "live_gauge_chart", c3)
    show(charts.growth_curve(grow, th), "live_growth_chart", c4)


@st.fragment(run_every=1.0)
def _live_panel_auto():
    _render_live_content(advance=True)


def live_section():
    is_playing = bool(st.session_state.get("live_playing", False))
    ui.section_header(
        "Konsol Pemantauan Sensor Kebun (Live Telemetry)",
        "Pilih siklus tanam lalu tekan tombol 'Tampilkan Konsol Sensor' atau 'Jalankan Simulasi Live' untuk memantau pergerakan sensor.",
        icon_name="activity",
        right_html=ui.live_badge_html(is_playing)
    )

    options = _get_series_options()
    labels = list(options.keys())
    default_idx = 0

    with st.container(border=True, key="card_live_ctrl"):
        c_cy, c_spd, c_btn1, c_btn2 = st.columns([1.6, 1.3, 0.95, 0.85], vertical_alignment="bottom")
        choice = c_cy.selectbox("Pilih Siklus Tanam", labels, index=default_idx, key="live_series")
        c_spd.selectbox(
            "Kecepatan Simulasi",
            [1, 2, 3],
            format_func=lambda s: f"{s}x ukur / detik",
            key="live_step"
        )
        btn_load = c_btn1.button("Tampilkan Konsol", type="primary", use_container_width=True, key="btn_live_load")
        toggle_lbl = "Hentikan Live" if is_playing else "Jalankan Live"
        btn_play = c_btn2.button(toggle_lbl, use_container_width=True, key="btn_live_play")

        st.markdown('<div style="margin:10px 0 6px 0;border-top:1px dashed #e2ebe4;padding-top:8px;"></div>', unsafe_allow_html=True)
        p_c1, p_c2, p_c3, p_c4 = st.columns([1.5, 0.95, 0.95, 1.15], vertical_alignment="center")

        override = st.session_state.get("pump_override", "AUTO")
        if override == "ON":
            p_badge_txt = '<span class="pump-ctrl-badge on"><span class="pump-ctrl-dot"></span>Manual Hidup</span>'
        elif override == "OFF":
            p_badge_txt = '<span class="pump-ctrl-badge off"><span class="pump-ctrl-dot"></span>Manual Mati</span>'
        else:
            p_badge_txt = '<span class="pump-ctrl-badge auto"><span class="pump-ctrl-dot"></span>Otomatis (Sensor)</span>'

        p_c1.markdown(f'<div class="pump-ctrl-row"><span>Kontrol Pompa:</span> {p_badge_txt}</div>', unsafe_allow_html=True)
        if p_c2.button("Hidupkan", use_container_width=True, key="btn_live_pump_on", help="Nyalakan pompa air secara manual"):
            st.session_state["pump_override"] = "ON"
            st.rerun()
        if p_c3.button("Matikan", use_container_width=True, key="btn_live_pump_off", help="Matikan pompa air secara manual"):
            st.session_state["pump_override"] = "OFF"
            st.rerun()
        if p_c4.button("Otomatis", use_container_width=True, key="btn_live_pump_auto", help="Kembalikan kontrol pompa otomatis berbasis ambang batas kelembapan sensor (Kering <55% hidup, Basah ≥76% mati)"):
            st.session_state["pump_override"] = "AUTO"
            st.rerun()

    df = options[choice].sort_values("Time_Index").reset_index(drop=True)
    sig = (choice, len(df))

    if st.session_state.get("live_committed_sig") != sig:
        st.session_state["live_committed_sig"] = sig
        st.session_state["live_df"] = df
        st.session_state["live_i"] = min(29, max(0, len(df) - 1))
        st.session_state["live_playing"] = False
        st.session_state["pump_was_on"] = False

    if btn_load:
        st.session_state["live_committed_sig"] = sig
        st.session_state["live_df"] = df
        st.session_state["live_i"] = min(29, max(0, len(df) - 1))
        st.session_state["live_playing"] = False
        st.session_state["pump_was_on"] = False
        st.rerun()

    if btn_play:
        st.session_state["live_committed_sig"] = sig
        st.session_state["live_df"] = df
        if st.session_state.get("live_sig") != sig:
            st.session_state["live_sig"] = sig
            st.session_state["live_i"] = 0
            st.session_state["pump_was_on"] = False
        st.session_state["live_playing"] = not is_playing
        st.rerun()

    st.session_state["live_df"] = df
    if st.session_state.get("live_playing", False):
        _live_panel_auto()
    else:
        _render_live_content(advance=False)


def page_dashboard():
    ui.hero("Dashboard Utama — Pemantauan Tanaman Pakcoy",
            "Ringkasan telemetri sensor tanah, suhu lingkungan, kurva kematangan tanaman pakcoy, dan konsol pemantauan live.",
            "layout-dashboard")
    name, df, is_applied = pick_dataset("dash", extra_filters=False, btn_label="Tampilkan Data Siklus")

    if not is_applied:
        live_section()
        return

    col_age = "Day" if "Day" in df.columns else ("DAP" if "DAP" in df.columns else df.columns[0])
    min_age = int(df[col_age].min()) if len(df) else utils.START_DAY
    max_age = int(df[col_age].max()) if len(df) else utils.HARVEST_DAY
    n_days = int(df[col_age].nunique()) if len(df) else utils.CYCLE_DAYS
    m = load_models()
    th = thresholds(m)

    times_u = sorted(df["Time"].astype(str).unique().tolist()) if "Time" in df.columns and len(df) else utils.JAM_LIST
    freq_per_day = len(times_u)
    time_range_str = f"Pukul {times_u[0]} s.d. {times_u[-1]}" if len(times_u) >= 2 else (f"Pukul {times_u[0]}" if times_u else "-")
    avg_moist = float(df["Soil Moisture (%)"].mean())
    avg_temp = float(df["Temperature (°C)"].mean())
    max_mat = float(df[MAT].max()) if MAT in df.columns else 0.0
    avg_mat = float(df[MAT].mean()) if MAT in df.columns else 0.0

    ui.kpi_cards([
        dict(icon="database", label="Total Data Pengecekan", value=f"{len(df):,} Catatan", sub=f"Sumber: {name}", color="#15803d"),
        dict(icon="history", label="Frekuensi Pengukuran", value=f"{freq_per_day}× / Hari", sub=time_range_str, color="#0284c7"),
        dict(icon="sprout", label="Rentang Umur Siklus", value=f"Hari {min_age}–{max_age}", sub=f"{n_days} hari pengamatan", color="#15803d"),
        dict(icon="droplets", label="Rata-rata Kelembapan", value=f"{avg_moist:.1f}%", sub=f"Ideal: {DRY:.0f}% – {WET:.0f}%", color="#0d9488"),
        dict(icon="thermometer", label="Rata-rata Suhu Udara", value=f"{avg_temp:.1f}°C", sub=f"Optimal: {TEMP_OPT_MIN:.0f}°C – {TEMP_OPT_MAX:.0f}°C", color="#d97706"),
        dict(icon="sparkles", label="Tingkat Kematangan Puncak", value=f"{max_mat:.0f}%", sub=f"Rata-rata {avg_mat:.0f}% · Panen ≥ {th[1]:.0f}%", color="#15803d"),
    ])
    ui.maturity_legend_bar(th)

    tab_ringkasan, tab_live, tab_data = st.tabs([
        "Ringkasan & Grafik",
        "Konsol Live Telemetry",
        f"Data Sensor Lengkap ({len(df):,})",
    ])

    with tab_ringkasan:
        ui.section_header(
            "Distribusi Kondisi Kebun & Kurva Pertumbuhan",
            "Ringkasan proporsi kelembapan tanah, distribusi fase pakcoy, dan pola kematangan dari siklus tanam yang ditampilkan.",
            icon_name="bar-chart-3"
        )
        c1, c2 = st.columns(2, gap="medium")
        show(charts.donut_condition(df), "d_donut", c1)
        show(charts.bar_stage(df), "d_bar", c2)
        show(charts.maturity_curve(df), "d_mat")

    with tab_live:
        live_section()

    with tab_data:
        d_head, d_dl = st.columns([2.8, 1.1], vertical_alignment="center")
        d_head.markdown(
            f'<div class="section-title" style="margin:0;">Data Lengkap Pengukuran Sensor ({len(df):,} Catatan &middot; Hari {min_age}–{max_age})</div>',
            unsafe_allow_html=True,
        )
        with d_dl:
            st.download_button(
                "Unduh Data Siklus (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                file_name=f"data_sensor_{str(name).lower().replace(' ', '_')}.csv",
                mime="text/csv",
                key="btn_dash_dl_csv",
                use_container_width=True,
            )
        st.dataframe(style_table(format_display_df(df)), height=440, hide_index=True, width="stretch")


# ================================================================= eksplorasi
def style_table(d):
    try:
        return _style_table(d)
    except Exception:
        return d


def _style_table(d):
    def color(v):
        v_str = str(v)
        if "Wet" in v_str or "Basah" in v_str:
            return "background-color:rgba(2,132,199,.10);color:#0369a1;font-weight:600"
        if "Optimal" in v_str or "Ideal" in v_str:
            return "background-color:rgba(21,128,61,.10);color:#15803d;font-weight:600"
        if "Dry" in v_str or "Kering" in v_str:
            return "background-color:rgba(220,38,38,.10);color:#dc2626;font-weight:600"
        if "Menyiram" in v_str or "Menyala" in v_str:
            return "background-color:rgba(249,115,22,.12);color:#c2410c;font-weight:700"
        if "Mati" in v_str or "Siaga" in v_str:
            return "background-color:rgba(21,128,61,.08);color:#15803d;font-weight:600"
        return ""
    sty = d.style
    fn = getattr(sty, "map", None) or sty.applymap
    cond_col = "Kondisi Tanah" if "Kondisi Tanah" in d.columns else ("Soil Condition" if "Soil Condition" in d.columns else None)
    if cond_col:
        sty = fn(color, subset=[cond_col])
    if "Status Pompa" in d.columns:
        sty = fn(color, subset=["Status Pompa"])
    fmt = {}
    for tc in ["Temperature (°C)", "Suhu Udara (°C)"]:
        if tc in d.columns:
            fmt[tc] = "{:.1f}"
    for mc in ["Soil Moisture (%)", "Kelembapan Tanah (%)"]:
        if mc in d.columns:
            fmt[mc] = "{:.0f}"
    for mat_c in [MAT, "Tingkat Kematangan (%)"]:
        if mat_c in d.columns:
            fmt[mat_c] = "{:.1f}"
    return sty.format(fmt)


# ================================================================= model LSTM
def eval_section(ev, names, prefix):
    """ev: dict nama -> {akurasi, cm, report}. Menampilkan metrik, confusion matrix, laporan per kelas."""
    if not ev:
        ui.banner("info", "Hasil evaluasi detail belum tersedia di file konfigurasi. Jalankan notebook terbaru di Colab.")
        return
    st.caption(
        "**Cara Membaca Tabel Ketepatan Tebakan AI (Confusion Matrix):** "
        "Kotak berwarna **hijau tua pada garis miring (diagonal)** menunjukkan jumlah tebakan AI yang **tepat sesuai kondisi tanaman sebenarnya**. "
        "Semakin besar angka di kotak hijau tua, semakin pintar dan akurat model AI."
    )
    cols = st.columns(len(ev))
    for (title, d), c in zip(ev.items(), cols):
        acc = float(d.get("akurasi", 0))
        c.markdown(f"**Pengujian pada: {title}**")
        c.markdown(
            ui.kpi_html([
                dict(
                    icon="sparkles",
                    label="Tingkat Ketepatan (Akurasi)",
                    value=f"{acc:.1%}",
                    color="#34d399",
                    sub=f"Tepat ~{int(round(acc * 100))} dari 100 pengecekan"
                )
            ]),
            unsafe_allow_html=True
        )
        if d.get("cm"):
            show(charts.confusion_fig(d["cm"], names, f"Tabel Ketepatan Tebakan AI · {title}"), f"{prefix}_cm_{title}", c)
        if d.get("report"):
            with c.expander("Lihat Rincian Statistik per Fase (Untuk Peneliti)"):
                rep = pd.DataFrame({k: v for k, v in d["report"].items() if isinstance(v, dict)}).T
                rep = rep.loc[[n for n in names if n in rep.index], ["precision", "recall", "f1-score", "support"]].round(3)
                rep.index = [label(i) for i in rep.index]
                rep = rep.rename(columns={
                    "precision": "Ketepatan (Precision)",
                    "recall": "Kepekaan (Recall)",
                    "f1-score": "Skor F1",
                    "support": "Jumlah Data Uji"
                })
                st.dataframe(rep, width="stretch")


# ================================================================= prediksi 4 hari
def _fc_day_offset(hari_val):
    """Ubah label kolom 'Hari' ('Hari ini', 'Hari +1', ...) menjadi offset hari integer (0..4)."""
    txt = str(hari_val).strip()
    if "+" in txt:
        try:
            return int(txt.split("+")[1].strip())
        except Exception:
            return 0
    return 0


def page_forecast():
    ui.hero(
        "Prakiraan Kondisi Kebun & Kematangan 4 Hari ke Depan",
        "Proyeksi kelembapan tanah, suhu udara, dan kematangan tanaman pakcoy berbasis model AI LSTM.",
        "calendar-range",
    )
    m = load_models()
    if not warn_models(m, ["fc"]) or not m.get("cfg_lstm"):
        return
    cfg = m["cfg_lstm"]
    win = cfg["w_in"]

    with st.container(border=True, key="card_fc_ctrl"):
        c_ser, c_sld, c_run = st.columns([1.15, 2.05, 0.95], vertical_alignment="bottom")
        df = pick_series("fc", c_ser)
        if len(df) < win:
            ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {win} pembacaan berurutan untuk prakiraan 4 hari.")
            return

        max_fc = max(win, min(len(df), utils.CYCLE_LENGTH - cfg.get("h_out", 12)))
        if "fc_step" not in st.session_state or st.session_state["fc_step"] > max_fc or st.session_state["fc_step"] < win:
            st.session_state["fc_step"] = min(45, max_fc)

        cur_row = df.iloc[int(st.session_state["fc_step"]) - 1]
        cur_day = int(cur_row.get("Day", 1))
        cur_time = str(cur_row.get("Time", "08:00"))
        if max_fc > win:
            step = c_sld.slider(
                f"Titik Awal Prakiraan (Hari ke-{cur_day} · {cur_time})",
                win,
                max_fc,
                key="fc_step",
                help="Geser untuk mengubah hari dan sesi pengukuran awal prakiraan (3 sesi/hari: 08:00, 12:00, 16:00).",
            )
        else:
            step = win
            c_sld.info(f"Titik Awal Prakiraan: Hari ke-{cur_day} · {cur_time} (1 jendela input tersedia)")
        run_clicked = c_run.button("Tampilkan Prakiraan", type="primary", use_container_width=True, key="btn_fc_run")

        row_fc = df.iloc[step - 1]
        day_fc = int(row_fc.get("Day", 1))
        time_fc = str(row_fc.get("Time", "08:00"))
        max_cycle_day = max(utils.CYCLE_DAYS, int(df["Day"].max())) if "Day" in df.columns else utils.CYCLE_DAYS
        next_day = min(max_cycle_day, day_fc + 1)
        end_day = min(max_cycle_day, day_fc + 4)
        fc_sig = (st.session_state.get("fc_series", ""), int(step), len(df))
        if run_clicked or "fc_committed_sig" not in st.session_state:
            st.session_state["fc_committed_sig"] = fc_sig
        if run_clicked:
            st.toast(f"Prakiraan diperbarui untuk Hari ke-{next_day}–{end_day}.")

        st.markdown('<div class="fc-ctrl-divider"></div>', unsafe_allow_html=True)

        def _set_fc_step(target_step):
            st.session_state["fc_step"] = target_step

        p_c1, p_c2, p_c3, p_info = st.columns([0.95, 1.05, 1.05, 1.55], vertical_alignment="center")
        p_c1.button(
            "Fase Awal · Hari ke-7",
            use_container_width=True,
            key="fc_btn1",
            on_click=_set_fc_step,
            args=(min(20, max_fc),),
        )
        p_c2.button(
            "Fase Pertengahan · Hari ke-17",
            use_container_width=True,
            key="fc_btn2",
            on_click=_set_fc_step,
            args=(min(50, max_fc),),
        )
        p_c3.button(
            "Menjelang Panen · Hari ke-25",
            use_container_width=True,
            key="fc_btn3",
            on_click=_set_fc_step,
            args=(min(75, max_fc),),
        )
        p_info.markdown(
            f'<div class="fc-origin-pill">'
            f'<span class="fc-origin-item"><span>Awal:</span> <strong>Hari ke-{day_fc} ({ui._e(time_fc)})</strong></span>'
            f'<span class="fc-origin-arrow">&rarr;</span>'
            f'<span class="fc-origin-item"><span>Proyeksi:</span> <strong>Hari ke-{next_day}–{end_day}</strong></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    window = df.iloc[step - win: step].reset_index(drop=True)
    try:
        table = predict_forecast(m, window)
    except Exception as e:
        st.error(f"Gagal memprediksi: {e}")
        return

    th = cfg["maturity_thresholds"]
    mat_col = "Tingkat Kematangan (%)" if "Tingkat Kematangan (%)" in table.columns else "Maturity (%)"
    last = table.iloc[-1]
    moist_last = float(last["Kelembapan (%)"])
    temp_last = float(last["Suhu (°C)"])
    mat_last = float(last[mat_col])
    end_stage = utils.CLASS_NAMES[utils.stage_from_maturity(mat_last, th)]

    moist_tag = "Kering" if moist_last < DRY else ("Basah" if moist_last >= WET else "Ideal")
    temp_tag = "Terik" if temp_last > 30.0 else ("Sejuk" if temp_last < 18.0 else "Ideal")

    ui.kpi_cards([
        dict(icon="droplets", label="Kelembapan (H+4)", value=f"{moist_last:.0f}%", color="#38bdf8", sub=f"{moist_tag} · Ideal {DRY:.0f}–{WET:.0f}%"),
        dict(icon="thermometer", label="Suhu Udara (H+4)", value=f"{temp_last:.1f}°C", color="#fb923c", sub=f"{temp_tag} · Ideal 22–28°C"),
        dict(icon="trending-up", label="Kematangan (H+4)", value=f"{mat_last:.0f}%", color="#34d399", sub=f"Siap panen ≥ {th[1]:.0f}%"),
        dict(icon="sprout", label="Fase Tanaman (H+4)", value=label(end_stage), color=charts.STAGE_COLORS.get(end_stage, "#34d399"), sub=f"Target Hari ke-{end_day}"),
    ], cols=4)

    # Ringkasan 4 hari proyeksi (H+1 s.d. H+4) untuk tampilan ringkasan, grafik harian, dan rekomendasi
    tbl_calc = table.copy()
    tbl_calc["_offset"] = tbl_calc["Hari"].map(_fc_day_offset)
    daily_proj = (
        tbl_calc[tbl_calc["_offset"] > 0]
        .groupby("_offset", sort=True)
        .agg({"Kelembapan (%)": "mean", "Suhu (°C)": "mean", mat_col: "last", "Tahap": "last"})
        .round(1)
        .reset_index()
    )
    if daily_proj.empty:
        daily_proj = (
            tbl_calc.groupby("_offset", sort=True)
            .agg({"Kelembapan (%)": "mean", "Suhu (°C)": "mean", mat_col: "last", "Tahap": "last"})
            .round(1)
            .reset_index()
        )
    daily_proj["Actual_Day"] = daily_proj["_offset"].apply(lambda off: min(max_cycle_day, day_fc + int(off)))
    truth = df.iloc[step: step + len(table)].reset_index(drop=True) if step + len(table) <= len(df) else None

    with st.container(key="fc_tabs_wrap"):
        tab_ringkasan, tab_grafik, tab_tabel, tab_rekom = st.tabs([
            "Ringkasan",
            "Grafik Tren",
            "Tabel Data",
            "Rekomendasi",
        ])

    # ------------------------------------------------------------------ TAB 1: RINGKASAN
    with tab_ringkasan:
        r_left, r_right = st.columns([2.6, 1.4], vertical_alignment="center")
        r_left.markdown(
            '<div class="section-title" style="margin:0;">Proyeksi Harian 4 Hari ke Depan</div>',
            unsafe_allow_html=True,
        )
        with r_right:
            vis_mode_sel = st.radio(
                "Mode Gambar:",
                ["Foto Asli Kebun", "Ilustrasi Botani AI"],
                horizontal=True,
                key="fc_vis_mode",
                label_visibility="collapsed",
            )
        vis_mode = "svg" if "Ilustrasi" in vis_mode_sel else "photo"

        mat_first = float(daily_proj[mat_col].iloc[0]) if len(daily_proj) else mat_last
        ui.forecast_preview_card(
            start_day=day_fc,
            end_day=end_day,
            first_mat=mat_first,
            last_mat=mat_last,
            end_stage_key=end_stage,
            end_stage_label=label(end_stage),
            thresholds=th,
            visual_mode=vis_mode,
        )
        ui.forecast_4day_cards(table, start_day=day_fc, thresholds=th, dry=DRY, wet=WET, visual_mode=vis_mode)
        with st.expander("Estimasi Ukuran Daun & Diameter Tajuk (4 Hari ke Depan)", expanded=False):
            st.caption("Estimasi morfologi dihitung dari proyeksi tingkat kematangan harian sebagai referensi visual.")
            ui.forecast_morphology_grid(table, start_day=day_fc)

    # ------------------------------------------------------------------ TAB 2: GRAFIK TREN
    with tab_grafik:
        g_ctrl1, g_ctrl2 = st.columns([2.2, 1.3], vertical_alignment="center")
        with g_ctrl1:
            chart_mode = st.radio(
                "Tampilan Grafik",
                ["Rata-rata Harian", "Per Sesi (Pagi · Siang · Sore)"],
                horizontal=True,
                key="fc_chart_mode",
                label_visibility="collapsed",
            )
        with g_ctrl2:
            show_actual = st.toggle(
                "Tampilkan data asli pembanding",
                value=False,
                key="fc_show_actual",
                disabled=(truth is None),
                help="Aktifkan untuk menampilkan garis titik-titik data sensor asli kebun sebagai pembanding.",
            )

        if chart_mode == "Rata-rata Harian":
            hist_daily = (
                window.groupby("Day", sort=True)
                .agg({"Soil Moisture (%)": "mean", "Temperature (°C)": "mean", MAT: "last"})
                .round(1)
                .reset_index()
            )
            h_days = [int(d) for d in hist_daily["Day"].tolist()]
            p_days = [int(d) for d in daily_proj["Actual_Day"].tolist()]
            p_offs = [int(o) for o in daily_proj["_offset"].tolist()]

            hist_x = list(range(len(h_days)))
            pred_x = list(range(len(h_days), len(h_days) + len(p_days)))

            hist_moist = hist_daily["Soil Moisture (%)"].tolist()
            hist_temp = hist_daily["Temperature (°C)"].tolist()
            hist_mat = hist_daily[MAT].tolist()

            pred_moist = daily_proj["Kelembapan (%)"].tolist()
            pred_temp = daily_proj["Suhu (°C)"].tolist()
            pred_mat = daily_proj[mat_col].tolist()

            hist_hover = [f"Hari ke-{d} (Historis)" for d in h_days]
            pred_hover = [f"Hari ke-{d} (H+{o})" for d, o in zip(p_days, p_offs)]

            tickvals = hist_x + pred_x
            ticktext = (
                [f"Hari {d}" for d in h_days[:-1]]
                + ([f"Hari {h_days[-1]}<br>(Hari Ini)"] if h_days else [])
                + [f"Hari {d}<br>(H+{o})" for d, o in zip(p_days, p_offs)]
            )

            actual_moist = None
            actual_temp = None
            if show_actual and truth is not None:
                truth_daily = (
                    truth.groupby("Day", sort=True)
                    .agg({"Soil Moisture (%)": "mean", "Temperature (°C)": "mean"})
                    .round(1)
                )
                actual_moist = [
                    float(truth_daily.loc[d, "Soil Moisture (%)"]) if d in truth_daily.index else None
                    for d in p_days
                ]
                actual_temp = [
                    float(truth_daily.loc[d, "Temperature (°C)"]) if d in truth_daily.index else None
                    for d in p_days
                ]
            show_pts = True
            x_axis_title = "Umur Tanaman & Hari Proyeksi (Rata-rata Harian)"
        else:
            n_h = len(window)
            n_p = len(table)
            hist_x = list(range(n_h))
            pred_x = list(range(n_h, n_h + n_p))

            hist_moist = window["Soil Moisture (%)"].tolist()
            hist_temp = window["Temperature (°C)"].tolist()
            hist_mat = window[MAT].tolist()

            pred_moist = table["Kelembapan (%)"].tolist()
            pred_temp = table["Suhu (°C)"].tolist()
            pred_mat = table[mat_col].tolist()

            h_days_seq = [int(d) for d in window["Day"].tolist()]
            h_times_seq = [str(t) for t in window["Time"].tolist()]
            p_offs_seq = [int(o) for o in tbl_calc["_offset"].tolist()]
            p_days_seq = [min(max_cycle_day, day_fc + o) for o in p_offs_seq]
            p_times_seq = [str(t) for t in table["Jam"].tolist()]

            hist_hover = [f"Hari ke-{d} · {JAM_LABELS_ID.get(t, t)}" for d, t in zip(h_days_seq, h_times_seq)]
            pred_hover = [
                f"Hari ke-{d} ({'Hari Ini' if o == 0 else f'H+{o}'}) · {JAM_LABELS_ID.get(t, t)}"
                for d, o, t in zip(p_days_seq, p_offs_seq, p_times_seq)
            ]

            # Bangun label tick sumbu X per pergantian hari (bersih & tanpa tumpukan angka mentah)
            all_days_seq = h_days_seq + p_days_seq
            all_offs_seq = [None] * n_h + p_offs_seq
            tickvals, ticktext = [], []
            seen_days = set()
            for idx_pos, (d_val, off_val) in enumerate(zip(all_days_seq, all_offs_seq)):
                if d_val not in seen_days:
                    seen_days.add(d_val)
                    if tickvals and idx_pos - tickvals[-1] < 2:
                        continue
                    tickvals.append(idx_pos)
                    if off_val is not None and off_val > 0:
                        ticktext.append(f"Hari {d_val}<br>(H+{off_val})")
                    else:
                        ticktext.append(f"Hari {d_val}")

            actual_moist = truth["Soil Moisture (%)"].tolist() if (show_actual and truth is not None) else None
            actual_temp = truth["Temperature (°C)"].tolist() if (show_actual and truth is not None) else None
            show_pts = False
            x_axis_title = "Umur Tanaman (Pengukuran Pagi 08:00 · Siang 12:00 · Sore 16:00)"

        c1, c2 = st.columns(2, gap="medium")
        show(
            charts.forecast_line(
                hist_x,
                hist_moist,
                pred_x,
                pred_moist,
                "Tren & Prakiraan Kelembapan Tanah (%)",
                "Kelembapan (%)",
                "#38bdf8",
                actual_y=actual_moist,
                ideal_range=(DRY, WET),
                ideal_label=f"Zona Ideal ({DRY:.0f}–{WET:.0f}%)",
                hist_hover=hist_hover,
                pred_hover=pred_hover,
                tickvals=tickvals,
                ticktext=ticktext,
                xtitle=x_axis_title,
                unit="%",
                show_markers=show_pts,
                height=370,
            ),
            "fc_m",
            c1,
        )
        show(
            charts.forecast_line(
                hist_x,
                hist_temp,
                pred_x,
                pred_temp,
                "Tren & Prakiraan Suhu Udara (°C)",
                "Suhu (°C)",
                "#fb923c",
                actual_y=actual_temp,
                ideal_range=(22.0, 28.0),
                ideal_label="Zona Ideal (22–28°C)",
                hist_hover=hist_hover,
                pred_hover=pred_hover,
                tickvals=tickvals,
                ticktext=ticktext,
                xtitle=x_axis_title,
                unit="°C",
                show_markers=show_pts,
                height=370,
            ),
            "fc_t",
            c2,
        )
        show(
            charts.maturity_forecast(
                pred_x,
                pred_mat,
                th,
                hist_x=hist_x,
                hist_y=hist_mat,
                tickvals=tickvals,
                ticktext=ticktext,
                hist_hover=hist_hover,
                pred_hover=pred_hover,
                xtitle=x_axis_title,
                show_markers=show_pts,
                height=345,
            ),
            "fc_mat",
        )
        if show_actual and truth is not None:
            st.caption("Garis titik-titik abu-abu menampilkan data sensor aktual di kebun sebagai pembanding akurasi prakiraan AI.")

    # ------------------------------------------------------------------ TAB 3: TABEL DATA
    with tab_tabel:
        t_head, t_dl = st.columns([2.6, 1.2], vertical_alignment="center")
        t_head.markdown(
            '<div class="section-title" style="margin:0;">Ringkasan Prakiraan Harian (4 Hari ke Depan)</div>',
            unsafe_allow_html=True,
        )
        with t_dl:
            st.download_button(
                "Unduh Tabel Prakiraan 4 Hari (CSV)",
                table.to_csv(index=False).encode("utf-8"),
                file_name="prediksi_4_hari.csv",
                mime="text/csv",
                key="fc_dl",
                use_container_width=True,
            )

        daily = (
            table.groupby("Hari", sort=False)
            .agg({"Kelembapan (%)": "mean", "Suhu (°C)": "mean", mat_col: "last", "Tahap": "last"})
            .round(1)
            .reset_index()
        )
        daily.insert(
            0,
            "Umur Tanaman",
            daily["Hari"].map(lambda h: f"Hari ke-{min(max_cycle_day, day_fc + _fc_day_offset(h))}"),
        )
        daily = daily.rename(columns={
            "Hari": "Waktu ke Depan",
            "Kelembapan (%)": "Rata-rata Kelembapan (%)",
            "Suhu (°C)": "Rata-rata Suhu (°C)",
            mat_col: "Tingkat Kematangan (%)",
            "Tahap": "Prakiraan Fase Tanaman",
        })
        st.dataframe(daily, hide_index=True, width="stretch")

        with st.expander("Tabel Rincian per Waktu Ukur (Pagi 08:00, Siang 12:00, Sore 16:00)", expanded=True):
            disp_tbl = table.drop(columns=["Maturity (%)"], errors="ignore").copy()
            disp_tbl.insert(
                1,
                "Umur Tanaman",
                disp_tbl["Hari"].map(lambda h: f"Hari ke-{min(max_cycle_day, day_fc + _fc_day_offset(h))}"),
            )
            disp_tbl = disp_tbl.rename(columns={
                "Langkah": "Urutan ke-",
                "Hari": "Hari ke Depan",
                "Jam": "Waktu Ukur",
                "Tahap": "Fase Tanaman",
            })
            st.dataframe(disp_tbl, hide_index=True, width="stretch")

    # ------------------------------------------------------------------ TAB 4: REKOMENDASI
    with tab_rekom:
        ui.banner(
            "info",
            f"Rekomendasi berikut disusun dari proyeksi kondisi kebun hingga Hari ke-{end_day} (+4 hari). "
            f"Gunakan sebagai panduan persiapan penyiraman, suhu, dan panen bersama pengamatan langsung di kebun.",
        )
        ui.forecast_recommendation_card(
            moist_last,
            temp_last,
            mat_last,
            label(end_stage),
            daily_df=daily_proj,
            start_day=day_fc,
            thresholds=th,
            dry=DRY,
            wet=WET,
        )


# ================================================================= CNN & foto
def photo_panel(m, img, key, sensor_row=None):
    """Analisis satu foto: CNN + analisis visual daun. Mengembalikan (cnn, green)."""
    with st.expander("Pengaturan Kalibrasi Ukuran Daun (Estimasi Otomatis / Kalibrasi Skala)", expanded=False):
        st.caption(
            "Pada mode otomatis, sistem menghitung **estimasi morfologi daun (`cm`, `cm²`)** berdasarkan rentang fase pertumbuhan pakcoy "
            "(*Brassica rapa* subsp. *chinensis*) dan proporsi tutupan hijau kanopi (bukan pengukuran mistar langsung). "
            "Untuk pengukuran fisik aktual, gunakan opsi kalibrasi skala (`px/cm`) bersama objek pembanding pada foto:"
        )
        c_mode, c_val = st.columns([1.2, 1])
        with c_mode:
            calib_choice = st.radio(
                "Metode Penentuan Ukuran Daun:",
                ["Otomatis (Estimasi Morfologi per Fase)", "Berdasarkan Diameter Netpot (cm)", "Manual (Piksel per cm)"],
                key=f"{key}_calib_choice"
            )
        scale = 0.0
        with c_val:
            if calib_choice == "Berdasarkan Diameter Netpot (cm)":
                netpot_dia = st.number_input("Diameter netpot hidroponik (cm)", min_value=1.0, max_value=25.0, value=5.0, step=0.5, key=f"{key}_netpot_dia", help="Netpot hidroponik standar berdiameter 5 cm (asumsi lebar netpot ≈ 28% lebar bingkai foto).")
                scale = float(img.width * 0.28 / netpot_dia)
                st.caption(f"Skala estimasi netpot: **{scale:.1f} px/cm** (asumsi proporsi 28% bingkai)")
            elif calib_choice == "Manual (Piksel per cm)":
                scale = st.number_input("Skala manual (px/cm)", min_value=1.0, max_value=300.0, value=45.0, step=1.0, key=f"{key}_manual_scale")
            else:
                st.info("Mode Estimasi Otomatis aktif: ukuran daun & proksi SPAD dihitung sebagai estimasi visual berdasarkan fase CNN dan analisis warna HSV.")

    g = utils.green_analysis(img, scale)
    is_plant, plant_reason, _ = utils.validate_plant_image(img, g)
    c1, c2 = st.columns(2, gap="medium")
    c1.image(img, caption="Foto Asli yang Diunggah")
    c2.image(g["overlay"], caption="Deteksi Area Daun Hijau (Segmentasi HSV)")
    cnn = None
    idx = 0.0
    if m.get("cnn") is not None:
        names = cnn_names(m)
        try:
            p = predict_image(m, img)
        except Exception as exc:
            ui.banner("danger", f"Gagal menjalankan inferensi model CNN pada foto ini: {exc}")
            return None, g
        raw_k = int(p.argmax())

        if not is_plant:
            # Transparan secara ilmiah: jangan menimpa vektor softmax CNN dengan nilai buatan 99%.
            # Tandai keputusan akhir sebagai ditolak oleh pra-validasi HSV dan tampilkan probabilitas mentah CNN apa adanya.
            cnn = ("bukan_pakcoy", float(p[raw_k]), p, names)
            idx = 0.0
            ui.kpi_cards([
                dict(icon="alert-triangle", label="Pra-Validasi Citra (HSV)", value="Bukan Daun", color="#dc2626", sub="Ditolak sebelum tahap panen"),
                dict(icon="cpu", label="Prediksi Mentah CNN", value=f"{label(names[raw_k])} ({p[raw_k]:.0%})", color="#94a3b8", sub="Output softmax asli tanpa modifikasi"),
                dict(icon="x-circle", label="Status Kesiapan Panen", value="Tidak Berlaku", color="#dc2626", sub="Unggah foto daun pakcoy yang jelas"),
            ], cols=3)
            show(charts.prob_bar(p, names, title="Probabilitas Mentah Model CNN (Sebelum Pra-Validasi HSV)"), f"{key}_prob")
            ui.banner("danger", f"Foto ditolak oleh pra-validasi citra (HSV): {plant_reason} "
                                f"Silakan unggah foto tanaman pakcoy asli dari sudut atas dengan pencahayaan cukup.")
        else:
            k = raw_k
            cnn = (names[k], float(p[k]), p, names)
            idx = utils.readiness_index(p, names)
            if names[k] == "bukan_pakcoy":
                ui.kpi_cards([
                    dict(icon="alert-triangle", label="Hasil Pemeriksaan Foto", value=label(names[k]), color=charts.STAGE_COLORS.get(names[k], "#dc2626")),
                    dict(icon="sparkles", label="Tingkat Keyakinan AI", value=f"{p[k]:.0%}", color="#dc2626"),
                    dict(icon="x-circle", label="Status Kesiapan Panen", value="Bukan Pakcoy", color="#dc2626", sub="Silakan unggah foto daun pakcoy"),
                ], cols=3)
                show(charts.prob_bar(p, names), f"{key}_prob")
                ui.banner("danger", f"Model CNN mendeteksi foto sebagai BUKAN TANAMAN PAKCOY (Keyakinan AI: {p[k]:.0%}). "
                                    f"Silakan unggah foto tanaman pakcoy asli dari sudut atas.")
            else:
                ui.kpi_cards([
                    dict(icon="cpu", label="Fase Tanaman (Dari Foto)", value=label(names[k]), color=charts.STAGE_COLORS.get(names[k], "#15803d"), sub="Deteksi visual daun (CNN)"),
                    dict(icon="sparkles", label="Tingkat Keyakinan AI", value=f"{p[k]:.0%}", color="#34d399", sub="Ketepatan pengenalan foto"),
                    dict(icon="layers", label="Skor Kesiapan Panen", value=f"{idx:.0f} / 100", color="#facc15", sub="Skor ≥ 85 siap dipanen"),
                ], cols=3)
                g1, g2 = st.columns(2, gap="medium")
                show(charts.prob_bar(p, names), f"{key}_prob", g1)
                show(charts.gauge(idx, "Skor Kesiapan Panen dari Foto (0–100%)", (50, 90)), f"{key}_gauge", g2)
                if p[k] < 0.6:
                    ui.banner("warn", "Tingkat keyakinan AI terhadap foto ini cukup rendah. Coba ambil ulang foto dari atas dengan cahaya yang lebih terang.")
    else:
        ui.banner("warn", "Model CNN belum tersedia. Menampilkan hasil analisis warna daun (HSV).")

    if not is_plant or (cnn and cnn[0] == "bukan_pakcoy"):
        cards = [
            dict(icon="alert-triangle", label="Validasi Objek Foto", value="Bukan Tanaman", color="#dc2626",
                 sub="Objek non-tanaman terdeteksi"),
            dict(icon="maximize", label="Estimasi Panjang Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="maximize", label="Estimasi Lebar Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="maximize", label="Estimasi Luas Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="layers", label="Estimasi Diameter Tajuk", value="Tidak Terdeteksi", color="#94a3b8",
                 sub="Tidak ditemukan rumpun pakcoy"),
            dict(icon="sprout", label="Proksi Klorofil Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan daun pakcoy"),
        ]
        ui.kpi_cards(cards, cols=3)
        return cnn, g

    detected_stage = cnn[0] if cnn else "masa_pertumbuhan"
    conf_val = cnn[1] if cnn else 0.85
    metrics = ui.compute_pakcoy_leaf_metrics(g, stage_key=detected_stage, manual_scale=scale)

    # Simpan kembali ke dict g agar laporan unduhan (.md) juga memuat angka estimasi morfologi pakcoy
    g["width_cm"] = metrics["leaf_wid_cm"]
    g["height_cm"] = metrics["leaf_len_cm"]
    g["area_cm2"] = metrics["leaf_area_cm2"]

    is_manual_calib = scale > 0
    prefix_est = "" if is_manual_calib else "± "
    sec_title = (
        "Pengukuran Morfologi Daun (Terkalibrasi Skala) &amp; Kesehatan Warna"
        if is_manual_calib else
        "Estimasi Morfologi Daun (Berbasis Fase &amp; Kanopi) &amp; Kesehatan Warna"
    )

    if g['yellow_pct'] < 2.0:
        yellow_sub = "Daun sangat sehat & segar"
        yellow_col = "#34d399"
    elif g['yellow_pct'] < 8.0:
        yellow_sub = "Normal · sedikit menguning"
        yellow_col = "#facc15"
    else:
        yellow_sub = "Perhatian · gejala klorosis daun"
        yellow_col = "#f87171"

    st.markdown(f'<div class="section-title">{sec_title}</div>', unsafe_allow_html=True)
    cards = [
        dict(icon="maximize", label="Estimasi Panjang Daun" if not is_manual_calib else "Panjang Helaian Daun", value=f"{prefix_est}{metrics['leaf_len_cm']:.1f} cm", color="#15803d",
             sub=f"Referensi fase: {metrics['len_std_str']}"),
        dict(icon="maximize", label="Estimasi Lebar Daun" if not is_manual_calib else "Lebar Helaian Daun", value=f"{prefix_est}{metrics['leaf_wid_cm']:.1f} cm", color="#38bdf8",
             sub=f"Referensi fase: {metrics['wid_std_str']}"),
        dict(icon="layers", label="Estimasi Luas Daun" if not is_manual_calib else "Luas Helaian Daun", value=f"{prefix_est}{metrics['leaf_area_cm2']:.1f} cm²", color="#fb923c",
             sub=f"Referensi fase: {metrics['area_std_str']}"),
        dict(icon="maximize", label="Estimasi Diameter Tajuk" if not is_manual_calib else "Diameter Tajuk Rumpun", value=f"{prefix_est}{metrics['canopy_dia_cm']:.1f} cm", color="#a78bfa",
             sub=f"Referensi tajuk: {metrics['canopy_std_str']}"),
        dict(icon="sparkles", label="Proksi SPAD (HSV) & Kerapatan", value=f"±{metrics['spad_val']:.1f} SPAD · {g['compactness']:.0%}", color="#34d399",
             sub=f"Estimasi visual (non-alat) · Hijau {g['greenness']:.0f}%"),
        dict(icon="sprout", label="Persentase Daun Menguning", value=f"{g['yellow_pct']:.1f}%", color=yellow_col,
             sub=yellow_sub),
    ]
    ui.kpi_cards(cards, cols=3)

    # Tampilkan Analisis AI & Rekomendasi Perawatan Lengkap dalam Bentuk Paragraf
    ui.ai_plant_analysis_card(
        stage_key=detected_stage,
        stage_label=label(detected_stage),
        confidence=conf_val,
        readiness_idx=idx,
        metrics=metrics,
        g=g,
        sensor_row=sensor_row,
    )

    with st.expander("Metodologi & Keterbatasan Estimasi Ukuran Daun dan Proksi SPAD"):
        st.markdown(
            "- **Mode Estimasi Otomatis (`cm`, `cm²`):** Panjang daun, lebar daun, luas daun ($LA = P \\times L \\times k$, $k \\in [0{,}68; 0{,}72]$), dan diameter tajuk diestimasi secara heuristik dari rentang morfologi standar fase prediksi CNN yang dikombinasikan dengan proporsi tutupan hijau & kerapatan kanopi pada foto. Nilai ini bersifat **estimasi visual**, bukan pengukuran mistar langsung.\n"
            "- **Mode Kalibrasi Manual (`px/cm`):** Menghitung dimensi fisik dari piksel bounding box daun menggunakan skala `px/cm` yang dimasukkan pengguna bersama benda pembanding.\n"
            "- **Proksi SPAD (HSV):** Dihitung secara heuristik dari tingkat kepekatan hijau (saturasi HSV) dan persentase kuning daun. Angka ini adalah **proksi kehijauan visual**, bukan pembacaan terkalibrasi dari alat klorofil meter SPAD-502.\n"
            "- **Referensi Morfologi Pakcoy:** *Masa Pertumbuhan* (panjang 6,5–11,8 cm; lebar 4,0–7,2 cm), *Mendekati Panen* (12,5–17,5 cm; 7,5–10,8 cm), dan *Siap Panen* (18,0–23,5 cm; 11,0–14,5 cm)."
        )
    return cnn, g


def get_image(key):
    mode = st.radio("Pilih cara memasukkan foto tanaman:", ["Unggah file foto dari HP/Komputer", "Ambil foto langsung dengan kamera"], horizontal=True, key=f"{key}_mode")
    f = (st.file_uploader(
            "Pilih foto tanaman pakcoy (JPG / PNG)",
            type=["jpg", "jpeg", "png"],
            key=f"{key}_up"
         )
         if mode == "Unggah file foto dari HP/Komputer" else st.camera_input("Arahkan kamera ke tanaman pakcoy", key=f"{key}_cam"))
    if f is None:
        return None, None
    max_bytes = 10 * 1024 * 1024
    if getattr(f, "size", 0) > max_bytes:
        ui.banner("warn", f"Ukuran file foto terlalu besar ({f.size / (1024 * 1024):.1f} MB). Batas maksimal ukuran foto adalah 10 MB. Silakan pilih foto dengan ukuran lebih kecil.")
        return None, None
    try:
        Image.MAX_IMAGE_PIXELS = 40_000_000
        raw_img = Image.open(f)
        img = ImageOps.exif_transpose(raw_img).convert("RGB")
        if img.width < 32 or img.height < 32:
            ui.banner("warn", f"Resolusi foto terlalu kecil ({img.width}×{img.height} px). Gunakan foto minimal 32×32 piksel.")
            return None, None
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, Exception) as exc:
        ui.banner("danger", f"File foto tidak valid atau rusak sehingga tidak dapat dibuka ({type(exc).__name__}). Silakan unggah file JPG/PNG yang sah.")
        return None, None
    file_id = getattr(f, "file_id", None) or getattr(f, "id", None) or getattr(f, "name", "cam")
    sig = (getattr(f, "name", "cam"), getattr(f, "size", 0), str(file_id))
    return img, sig


def page_cnn():
    ui.hero("Cek Kesiapan Panen & Kesehatan Daun dari Foto",
            "Unggah foto tanaman pakcoy Anda, lalu tekan tombol 'Analisis Foto Tanaman' untuk memeriksa kesiapan panen dan kesehatan daun.",
            "scan-line")
    m = load_models()
    tab1, tab2 = st.tabs(["Periksa Foto Tanaman", "Evaluasi & Info Model CNN"])
    with tab1:
        if not warn_models(m, ["cnn"]):
            st.caption("Pengukuran fisik dan warna daun tetap dapat digunakan.")
        ui.photo_guide_card()
        with st.container(border=True, key="card_cnn_ctrl"):
            img, img_sig = get_image("cnn")
            st.markdown('<div style="margin-top:8px;border-top:1px solid #edf2ee;padding-top:10px;"></div>', unsafe_allow_html=True)
            b_l, b_r = st.columns([3.4, 1.0], vertical_alignment="center")
            status_txt = f"Foto siap dianalisis ({img.width}×{img.height} px)" if img is not None else "Belum ada foto yang diunggah"
            b_l.markdown(f'<div class="action-bar-info"><strong>Status Foto:</strong> {ui._e(status_txt)}</div>', unsafe_allow_html=True)
            if b_r.button("Analisis Foto Tanaman", type="primary", key="btn_cnn_run"):
                if img is None:
                    ui.banner("warn", "Silakan unggah atau ambil foto tanaman terlebih dahulu sebelum menekan tombol analisis.")
                else:
                    st.session_state["cnn_committed_sig"] = img_sig

        if img is None:
            st.session_state.pop("cnn_committed_sig", None)
            ui.pending_action_card(
                "Unggah atau Ambil Foto Tanaman Pakcoy",
                "Pilih file foto pakcoy (JPG/PNG) atau gunakan kamera di atas untuk melihat hasil deteksi fase pertumbuhan (CNN), pengukuran fisik daun (cm, cm², SPAD), dan rekomendasi perawatan AI.",
                icon_name="scan-line"
            )
        elif st.session_state.get("cnn_committed_sig") != img_sig:
            ui.pending_action_card(
                "Tekan Tombol 'Analisis Foto Tanaman' untuk Memulai Analisis",
                "Foto tanaman pakcoy telah siap dianalisis. Silakan tekan tombol hijau 'Analisis Foto Tanaman' di atas untuk melihat hasil deteksi fase pertumbuhan (CNN), pengukuran fisik daun (cm, cm², SPAD), dan rekomendasi perawatan AI.",
                icon_name="scan-line"
            )
        else:
            cnn, g = photo_panel(m, img, "cnn")
            if cnn and cnn[0] == "bukan_pakcoy":
                ui.banner("danger", "Objek pada foto terdeteksi bukan tanaman pakcoy. Silakan unggah foto daun pakcoy yang jelas.")
    with tab2:
        ui.banner("info", "Model pengenalan foto (CNN MobileNetV2) dilatih untuk membedakan 4 kategori: Bukan Pakcoy, Masa Pertumbuhan, Mendekati Panen, dan Siap Panen.")
        cfg = m.get("cfg_cnn")
        if cfg:
            ev = cfg.get("evaluasi", {})
            eval_section(ev, cfg["class_names"], "cnn")
            if not ev:
                ui.kpi_cards([dict(icon="sparkles", label="Tingkat Ketepatan Uji Foto", value=f"{cfg.get('akurasi_uji', 0):.1%}",
                                   color="#34d399")])
            with st.expander("Lihat Detail Arsitektur Model Foto CNN (Untuk Peneliti)"):
                st.markdown("- **Arsitektur:** `Augmentasi Citra` → `Rescaling` → `MobileNetV2 (ImageNet)` → `GlobalAveragePooling` → `Dropout 0,3` → `Softmax 4 kelas`.")
                st.caption(f"Dilatih dengan TensorFlow {cfg.get('tf_version', '?')} · Jumlah gambar uji: {cfg.get('jumlah_gambar_uji', '?')} foto.")
        else:
            ui.banner("info", "Konfigurasi model belum ada. Latih model di Colab terlebih dulu.")


# ================================================================= history perkembangan
@st.cache_data
def _load_history_1400_cached(_fp: str):
    p = DATA_DIR / "history_perkembangan_pakcoy_1400.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_history_1400():
    fp = _file_fingerprint(DATA_DIR / "history_perkembangan_pakcoy_1400.csv")
    return _load_history_1400_cached(fp)


@st.cache_data
def _load_raw_dataset_cached(_fp: str):
    p = DATA_DIR / "dataset_asli_mentah.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_raw_dataset():
    fp = _file_fingerprint(DATA_DIR / "dataset_asli_mentah.csv")
    return _load_raw_dataset_cached(fp)


def page_history_perkembangan():
    df_hist = load_history_1400()
    if df_hist.empty:
        ui.hero("History Perkembangan Tanaman Pakcoy",
                "Catatan riwayat pertumbuhan tanaman pakcoy resolusi tinggi (15× pengecekan harian).",
                "history")
        ui.banner("warn", "File dataset riwayat perkembangan (history_perkembangan_pakcoy_1400.csv) belum tersedia.")
        return

    avail_cycles = sorted(int(c) for c in df_hist["Cycle_ID"].dropna().unique())
    min_cyc, max_cyc = avail_cycles[0], avail_cycles[-1]
    all_cyc_label = f"Semua Siklus ({min_cyc}–{max_cyc})"
    avail_days = sorted(int(d) for d in df_hist["Day"].dropna().unique())
    min_day_h, max_day_h = avail_days[0], avail_days[-1]
    n_times_h = int(df_hist["Time"].nunique()) if "Time" in df_hist.columns else 15

    ui.hero(
        f"History Perkembangan Tanaman Pakcoy ({len(df_hist):,} Data · {n_times_h}×/Hari)",
        f"Riwayat pertumbuhan pakcoy resolusi tinggi (06:00–20:00, {n_times_h}×/hari) mencakup {len(avail_cycles)} siklus pengamatan (Siklus 1–3 penuh Hari 1–30 & awal Siklus 4).",
        "history",
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Riwayat & Analisis",
        f"Tabel Lengkap ({len(df_hist):,} Data)",
        "Dataset Asli Mentah",
        "Panduan Agronomi 30 Hari"
    ])

    with tab1:
        # Filter interaktif (dinamis sesuai isi aktual dataset agar tidak ada opsi kosong)
        with st.container(border=True, key="card_hist_filter"):
            st.markdown('<div class="section-title" style="margin-top:0;">Filter Riwayat Perkembangan Tanaman</div>', unsafe_allow_html=True)
            f1, f2, f3, f4 = st.columns([1.2, 1.1, 1.2, 1.1])

            cycle_opts = [all_cyc_label] + [f"Siklus {i}" for i in avail_cycles]
            sel_cyc = f1.selectbox("Pilih Siklus Budidaya:", cycle_opts, key="hist_filter_cyc")

            day_opts = [f"Semua Hari ({min_day_h}–{max_day_h})"] + [f"Hari ke-{i}" for i in avail_days]
            sel_day = f2.selectbox("Pilih Umur Tanaman:", day_opts, key="hist_filter_day")

            times_all = sorted(list(df_hist["Time"].unique()))
            time_opts = [f"Semua Jam ({n_times_h}× Pengecekan)"] + times_all
            sel_time = f3.selectbox("Jam Pengukuran:", time_opts, key="hist_filter_time")

            fase_avail = [f for f in ["Fase Awal", "Fase Vegetatif", "Mendekati Panen", "Siap Panen"] if f in set(df_hist["Fase"].unique())]
            fase_opts = ["Semua Fase"] + fase_avail
            sel_fase = f4.selectbox("Fase Pertumbuhan:", fase_opts, key="hist_filter_fase")

        # Terapkan filter
        df_view = df_hist.copy()
        if sel_cyc != all_cyc_label:
            cyc_num = int(sel_cyc.replace("Siklus ", ""))
            df_view = df_view[df_view["Cycle_ID"] == cyc_num]
        if sel_day != f"Semua Hari ({min_day_h}–{max_day_h})":
            day_num = int(sel_day.replace("Hari ke-", ""))
            df_view = df_view[df_view["Day"] == day_num]
        if sel_time != f"Semua Jam ({n_times_h}× Pengecekan)":
            df_view = df_view[df_view["Time"] == sel_time]
        if sel_fase != "Semua Fase":
            df_view = df_view[df_view["Fase"] == sel_fase]

        if df_view.empty:
            ui.banner("warn", "Tidak ada data yang cocok dengan kombinasi filter yang dipilih. Ubah kombinasi filter di atas untuk menampilkan grafik.")
        else:
            # KPI Metrics Cards
            avg_moist = df_view["Soil Moisture (%)"].mean()
            avg_temp = df_view["Temperature (°C)"].mean()
            max_mat = df_view["Ground Truth Maturity Level (%)"].max()
            v_min_d, v_max_d = int(df_view["Day"].min()), int(df_view["Day"].max())

            ui.kpi_cards([
                dict(icon="database", label="Total Data Pengecekan", value=f"{len(df_view):,} Catatan", sub=f"Dari {len(df_hist):,} data ({len(avail_cycles)} siklus)", color="#15803d"),
                dict(icon="history", label="Frekuensi Pengukuran", value=f"{n_times_h}× / Hari", sub="Pukul 06:00 s.d. 20:00", color="#0284c7"),
                dict(icon="sprout", label="Rentang Umur Terfilter", value=f"Hari {v_min_d}–{v_max_d}", sub="Siklus Panen Hari ke-30", color="#15803d"),
                dict(icon="droplets", label="Rata-rata Kelembapan", value=f"{avg_moist:.1f}%", sub=f"Ideal: {DRY:.0f}% – {WET:.0f}%", color="#0d9488"),
                dict(icon="thermometer", label="Rata-rata Suhu Udara", value=f"{avg_temp:.1f}°C", sub=f"Optimal: {TEMP_OPT_MIN:.0f}°C – {TEMP_OPT_MAX:.0f}°C", color="#d97706"),
                dict(icon="sparkles", label="Tingkat Kematangan Puncak", value=f"{max_mat:.0f}%", sub="Panen optimal 85–100%", color="#15803d"),
            ])

            # Visualisasi Utama
            st.markdown('<div class="section-title">Kurva Pertumbuhan &amp; Kematangan Tanaman Menuju Panen (Hari 1 s.d. 30)</div>', unsafe_allow_html=True)
            show(charts.history_maturity_curve(df_view), "fig_hist_mat")

            st.markdown('<div class="section-title">Profil Fluktuasi Sensor 15 Kali Pengecekan Harian (06:00 – 20:00)</div>', unsafe_allow_html=True)
            show(charts.history_daily_15times(df_view), "fig_hist_daily")

            st.markdown('<div class="section-title">Tren Sensor Lingkungan &amp; Sebaran Kondisi Tanah</div>', unsafe_allow_html=True)
            col_tr1, col_tr2 = st.columns([1.6, 1.0], gap="medium")
            with col_tr1:
                show(charts.history_sensor_trend(df_view), "fig_hist_trend")
            with col_tr2:
                show(charts.donut_condition(df_view), "fig_hist_donut")

    with tab2:
        t2_head, t2_dl = st.columns([2.6, 1.2], vertical_alignment="center")
        t2_head.markdown(
            f'<div class="section-title" style="margin:0;">Tabel Lengkap Riwayat Perkembangan Pakcoy ({len(df_hist):,} Data)</div>',
            unsafe_allow_html=True,
        )
        csv_1400 = df_hist.to_csv(index=False).encode("utf-8")
        with t2_dl:
            st.download_button(
                label="Unduh Dataset 1.400 Data (CSV)",
                data=csv_1400,
                file_name="dataset_history_pakcoy_1400_data.csv",
                mime="text/csv",
                key="btn_dl_1400_csv",
                use_container_width=True,
            )
        st.caption(
            f"Data mencakup {len(avail_cycles)} siklus pengamatan (Siklus 1–3 penuh Hari 1–30 @ 450 baris, "
            f"serta awal Siklus 4 sebanyak 50 baris) dengan frekuensi {n_times_h} kali pengecekan per hari."
        )

        tbl_show = df_hist.copy()
        disp_cols = {
            "No": "No",
            "Siklus": "Siklus",
            "Day": "Hari ke-",
            "DAP": "HST",
            "Time": "Waktu Cek",
            "Soil Moisture (%)": "Kelembapan (%)",
            "Temperature (°C)": "Suhu (°C)",
            "Soil Condition": "Kondisi Tanah",
            "Ground Truth Maturity Level (%)": "Kematangan (%)",
            "Fase": "Fase Pertumbuhan",
            "Status Pompa": "Status Pompa"
        }
        present_cols = [c for c in disp_cols.keys() if c in tbl_show.columns]
        tbl_disp = tbl_show[present_cols].rename(columns=disp_cols)

        st.dataframe(tbl_disp, hide_index=True, width="stretch", height=500)

    with tab3:
        ui.banner(
            "info",
            "Menampilkan dataset asli mentah dari 'dataset asli/new Dataset_Pakcoy.xlsx' (1.140 baris, 3×/hari: 08:00, 12:00, 16:00). "
            "Catatan pra-pemrosesan: data mentah ini memiliki rentang Hari 1–380 (93,4% berlabel Harvest Ready) dan beberapa anomali label kondisi tanah, "
            "sehingga dibersihkan & dibatasi ke siklus 30 hari sebelum digunakan untuk pemodelan LSTM.",
        )
        df_raw = load_raw_dataset()
        if not df_raw.empty:
            ui.kpi_cards([
                dict(icon="database", label="Total Data Asli Mentah", value=f"{len(df_raw):,} Baris", sub="File new Dataset_Pakcoy.xlsx", color="#15803d"),
                dict(icon="calendar", label="Rentang Hari Mentah", value=f"Hari {int(df_raw['Day'].min())}–{int(df_raw['Day'].max())}", sub="Sebelum pemotongan siklus 30 hari", color="#0284c7"),
                dict(icon="history", label="Frekuensi Pengukuran Asli", value="3× / Hari", sub="Pukul 08:00, 12:00, dan 16:00", color="#0d9488"),
            ], cols=3)
            t3_head, t3_dl = st.columns([2.6, 1.2], vertical_alignment="center")
            t3_head.markdown(
                '<div class="section-title" style="margin:0;">Pratinjau Data Asli Mentah (Excel)</div>',
                unsafe_allow_html=True,
            )
            csv_raw = df_raw.to_csv(index=False).encode("utf-8")
            with t3_dl:
                st.download_button(
                    label="Unduh Dataset Asli Mentah (CSV)",
                    data=csv_raw,
                    file_name="dataset_asli_mentah_pakcoy.csv",
                    mime="text/csv",
                    key="btn_dl_raw_csv",
                    use_container_width=True,
                )
            st.dataframe(df_raw, hide_index=True, width="stretch", height=450)
        else:
            ui.banner("warn", "File dataset asli mentah belum tersedia.")

    with tab4:
        st.markdown('<div class="section-title" style="margin-top:0;">Standar Agronomi Siklus Tanaman Pakcoy (Hari 1 s.d. 30 Masa Panen)</div>', unsafe_allow_html=True)
        ui.banner("ok", "Tanaman pakcoy (Brassica rapa L.) memiliki siklus budidaya optimal 30 hari sejak pindah tanam (10 HST) hingga panen raya (40 HST).")

        st.markdown(
            """
| Tahap Pertumbuhan (4 Fase Agronomi) | Pemetaan Kelas Model AI (3 Kelas) | Umur Tanaman (Hari ke-) | Rentang HST | Kematangan (Riwayat 15×/Hari) | Ambang Model LSTM | Target Kelembapan | Suhu Optimal |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Fase Awal (Initial)** | `Masa Pertumbuhan` | Hari 1 – 10 | 10 – 19 HST | 5% – 33% | < 66,5% | 70% – 76% | 22°C – 26°C |
| **2. Fase Vegetatif** | `Masa Pertumbuhan` | Hari 11 – 20 | 20 – 29 HST | 34% – 66% | < 66,5% | 60% – 75% | 22°C – 28°C |
| **3. Mendekati Panen** | `Mendekati Panen` | Hari 21 – 25 | 30 – 34 HST | 67% – 84% | 66,5% – 89,0% | 55% – 70% | 22°C – 28°C |
| **4. Siap Panen** | `Siap Panen` | Hari 26 – 30 | 35 – 40 HST | 85% – 100% | ≥ 89,0% | 55% – 65% | 22°C – 28°C |
            """
        )
        ui.banner("info", "Tips Panen Agronomi: Panen pakcoy terbaik dilakukan pada pagi hari (pukul 06:00–08:00) saat kelembapan udara masih tinggi dan terik matahari belum membakar daun, sehingga kadar air daun tetap tinggi dan kesegaran bertahan lebih lama.")


PAGES = {
    "🏠 Dashboard Utama": page_dashboard,
    "🔮 Prakiraan 4 Hari": page_forecast,
    "🖼️ Analisis Tanaman (CNN)": page_cnn,
    "📜 History Perkembangan": page_history_perkembangan,
    "Asisten Kebun AI": ai_assistant.render_ai_assistant,
}

choice = sidebar()
PAGES[choice]()
ui.footer()
