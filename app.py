"""Smart Farming Pakcoy: dashboard realtime, eksplorasi data, monitoring sensor, LSTM, prediksi 4 hari,
CNN (scan foto), dan scan gabungan."""
import hashlib
import importlib
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

import utils
import ui
import charts
import ai_assistant
import auth

importlib.reload(ui)
importlib.reload(charts)
importlib.reload(auth)
importlib.reload(ai_assistant)

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
DRY, WET = utils.DRY_LIMIT, utils.WET_LIMIT
MAT = utils.MATURITY_COL
DEFAULT_THRESH = [66.5, 89.0]


# ================================================================= data & model
@st.cache_data
def load_builtin():
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
        st.error("File dataset tidak ditemukan di folder data/. Jalankan scripts/convert_to_30_days.py terlebih dahulu.")
        sim = pd.DataFrame()
        asli = pd.DataFrame()
    asli["Cycle_ID"] = 0
    asli["Split"] = "asli"
    return sim, asli


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
    df_1400 = load_history_1400()
    if not df_1400.empty and key == "dash":
        sim = df_1400
        cycle_options = [
            "Semua Siklus (1.400 Data Pengamatan)",
            "Siklus 1 (450 Data · 30 Hari)",
            "Siklus 2 (450 Data · 30 Hari)",
            "Siklus 3 (450 Data · 30 Hari)",
            "Siklus 4 (50 Data)"
        ]
    else:
        sim, _ = load_builtin()
        all_cycles = sorted(sim["Cycle_ID"].unique().tolist())
        cycle_options = [f"Siklus {c}" for c in all_cycles] + ["Semua Siklus (1–30)"]

    up = st.session_state.get("upload_df")
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
        if "Semua Siklus" in selected_label:
            df = sim
            src_name = selected_label
            cyc_sig = ("all", len(sim))
        elif selected_label == "Dataset Unggahan" and up is not None:
            df = up
            src_name = "Dataset Unggahan"
            cyc_sig = ("upload", st.session_state.get("upload_name", ""), len(up))
        else:
            try:
                parts = selected_label.split(" ")[1]
                c_num = int(parts)
                df = sim[sim["Cycle_ID"] == c_num]
            except Exception:
                df = sim
                c_num = 1
            src_name = selected_label
            cyc_sig = ("single", c_num, len(df))

        full_sig = (src_name, cyc_sig)

        if clicked or f"{key}_applied_sig" not in st.session_state:
            if not valid_sel or len(df) == 0:
                ui.banner("warn", "Pilihan siklus belum memiliki data. Silakan pilih siklus tanam yang sesuai.")
                return src_name, df, False
            st.session_state[f"{key}_applied_sig"] = full_sig

    is_applied = valid_sel and len(df) > 0
    return src_name, df, is_applied


def _get_series_options():
    df_1400 = load_history_1400()
    options = {}
    if not df_1400.empty:
        for c in sorted(df_1400["Cycle_ID"].unique()):
            sub = df_1400[df_1400["Cycle_ID"] == c].copy()
            options[f"Siklus {c} ({len(sub)} data · 15×/hari)"] = sub
    else:
        sim, _ = load_builtin()
        for c in sorted(sim["Cycle_ID"].unique()):
            options[f"Siklus {c}"] = sim[sim["Cycle_ID"] == c]
    up = st.session_state.get("upload_df")
    if up is not None:
        options["Dataset Unggahan"] = up
    return options


def pick_series(key, container=None):
    if key == "fc":
        sim, _ = load_builtin()
        options = {}
        for c in sorted(sim["Cycle_ID"].unique()):
            options[f"Siklus {c}"] = sim[sim["Cycle_ID"] == c]
        up = st.session_state.get("upload_df")
        if up is not None:
            options["Dataset Unggahan"] = up
    else:
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
    pred = m["fc"](x, training=False).numpy()[0]
    return utils.forecast_table(pred, cfg, utils.JAM_MAP[str(window_df["Time"].iloc[-1])])


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

    sb.markdown('<div class="micro-cap">DATA &amp; SISTEM</div>', unsafe_allow_html=True)
    f = sb.file_uploader("Impor Data Excel (.xlsx)", type=["xlsx"], key="upl")
    if f is not None:
        try:
            st.session_state["upload_df"] = utils.normalize_dataset(pd.read_excel(f))
            st.session_state["upload_name"] = f.name
            sb.success(f"Dataset dimuat: {len(st.session_state['upload_df']):,} baris")
        except Exception as e:
            st.session_state.pop("upload_df", None)
            sb.error(f"Dataset tidak sesuai: {e}")
    else:
        st.session_state.pop("upload_df", None)

    if sb.button("Muat Ulang Model AI", key="reload_models"):
        _load_models_cached.clear()
        st.rerun()

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
            tahap = label(str(row.get("Fase", row.get("Ground Truth Criteria", "Masa Pertumbuhan"))))
            sumber = "Data pengamatan kebun"
    else:
        tahap = label(str(row.get("Fase", row.get("Ground Truth Criteria", "Masa Pertumbuhan"))))
        sumber = "Data pengamatan kebun"
    raw_cond = str(row["Soil Condition"])
    jam_str = JAM_LABELS_ID.get(str(row["Time"]), str(row["Time"]))

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
    )

    c1, c2 = st.columns(2)
    show(charts.live_line(hist, "Soil Moisture (%)", "Grafik Kelembapan Tanah (%)", "#38bdf8", "Kelembapan (%)", dry=DRY, wet=WET),
         f"lv_m_{i}", c1)
    show(charts.live_line(hist, "Temperature (°C)", "Grafik Suhu Udara (°C)", "#fb923c", "Suhu (°C)"), f"lv_t_{i}", c2)
    c3, c4 = st.columns([1, 2])
    show(charts.gauge(row[MAT], "Indikator Kematangan Tanaman (%)", th), f"lv_g_{i}", c3)
    show(charts.growth_curve(grow, th), f"lv_c_{i}", c4)


@st.fragment(run_every=1.5)
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

    df = options[choice].sort_values("Time_Index").reset_index(drop=True)
    sig = (choice, len(df))

    if "live_committed_sig" not in st.session_state:
        st.session_state["live_committed_sig"] = sig
        st.session_state["live_df"] = df
        st.session_state["live_i"] = min(29, max(0, len(df) - 1))
        st.session_state["live_playing"] = False

    if btn_load:
        st.session_state["live_committed_sig"] = sig
        st.session_state["live_df"] = df
        st.session_state["live_i"] = min(29, max(0, len(df) - 1))
        st.session_state["live_playing"] = False
        st.rerun()

    if btn_play:
        st.session_state["live_committed_sig"] = sig
        st.session_state["live_df"] = df
        if st.session_state.get("live_sig") != sig:
            st.session_state["live_sig"] = sig
            st.session_state["live_i"] = 0
        st.session_state["live_playing"] = not is_playing
        st.rerun()

    st.session_state["live_df"] = df
    if st.session_state.get("live_playing", False):
        _live_panel_auto()
    else:
        _render_live_content(advance=False)


def render_pump_automation_control(df):
    ui.section_header(
        "Sistem Kontrol Pompa Air & Otomatisasi Irigasi Cerdas",
        "Pemantauan status tanah dan kendali pompa otomatis berbasis sensor IoT (Kering < 55% pompa menyala, Basah ≥ 76% pompa dimatikan).",
        icon_name="zap"
    )

    if "pump_mode" not in st.session_state:
        st.session_state["pump_mode"] = "Otomatis"
    if "pump_manual_state" not in st.session_state:
        st.session_state["pump_manual_state"] = "MATI"
    if "sim_moist" not in st.session_state:
        st.session_state["sim_moist"] = None

    if st.session_state["sim_moist"] is not None:
        cur_moist = float(st.session_state["sim_moist"])
        cur_temp = 27.2
        sensor_source = "🧪 Mode Simulasi Pengujian Cepat"
    else:
        last_row = df.iloc[-1]
        cur_moist = float(last_row["Soil Moisture (%)"])
        cur_temp = float(last_row["Temperature (°C)"])
        day_val = int(last_row.get("Day", 1))
        time_val = str(last_row.get("Time", "08:00"))
        time_fmt = JAM_LABELS_ID.get(time_val, time_val)
        sensor_source = f"Sensor Riil Kebun: Hari ke-{day_val} · Pukul {time_fmt}"

    mode = st.session_state["pump_mode"]

    if mode == "Manual":
        pump_state = st.session_state["pump_manual_state"]
        if pump_state == "MENYALA":
            pump_status_text = "MENYALA (Penyiraman Aktif)"
            pump_color = "#ea580c"
            banner_kind = "warn"
            banner_msg = "⚠️ <b>KONTROL MANUAL: POMPA AIR MENYALA</b> — Pompa sedang dihidupkan secara manual oleh pengguna untuk menyiram kebun pakcoy. Pastikan mematikan pompa setelah tanah cukup basah."
        else:
            pump_status_text = "MATI (Standby Siaga)"
            pump_color = "#15803d"
            banner_kind = "info"
            banner_msg = "🛑 <b>KONTROL MANUAL: POMPA AIR MATI</b> — Pompa air dinonaktifkan secara manual oleh pengguna."
    else:  # Mode Otomatis
        if cur_moist < 55.0:
            pump_state = "MENYALA"
            pump_status_text = "MENYALA (Otomatis Menyiram)"
            pump_color = "#ea580c"
            banner_kind = "danger"
            banner_msg = f"⚠️ <b>PERINGATAN TANAH KERING ({cur_moist:.0f}% < 55%)</b> — Kelembapan tanah berada di bawah batas aman minimal. Sistem IoT otomatis <b>MENYALAKAN POMPA AIR</b> untuk menyiram tanaman pakcoy agar tidak layu."
        elif cur_moist >= 76.0:
            pump_state = "MATI"
            pump_status_text = "MATI (Proteksi Jenuh Air)"
            pump_color = "#0284c7"
            banner_kind = "warn"
            banner_msg = f"💧 <b>PERINGATAN TANAH TERLALU BASAH ({cur_moist:.0f}% ≥ 76%)</b> — Kadar air tanah melebihi kapasitas optimal. Sistem IoT otomatis <b>MEMATIKAN POMPA AIR</b> untuk mencegah pembusukan akar tanaman pakcoy."
        else:
            pump_state = "MATI"
            pump_status_text = "MATI (Standby / Hemat Air)"
            pump_color = "#15803d"
            banner_kind = "ok"
            banner_msg = f"✅ <b>KONDISI TANAH AMAN & IDEAL ({cur_moist:.0f}%)</b> — Kelembapan tanah berada dalam rentang optimal budidaya pakcoy (55% – 76%). Pompa air dalam mode <b>SIAGA / STANDBY</b> (hemat air & listrik)."

    st.markdown(ui.pump_alert_html(banner_kind, banner_msg), unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:12px;border-bottom:1px solid #edf2ee;padding-bottom:10px;">'
            f'<div style="font-weight:700;font-size:15px;color:#1e293b;display:flex;align-items:center;gap:8px;">'
            f'{ui.icon("cpu", 16, color="#15803d")} Panel Kontrol Irigasi & Status Sensor'
            f'</div>'
            f'<span style="font-size:12px;font-weight:600;color:#64748b;background:#f8fafc;padding:3px 10px;border-radius:6px;border:1px solid #e2e8f0;">'
            f'{sensor_source}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        kp1, kp2, kp3, kp4 = st.columns(4)
        with kp1:
            st.markdown(
                f'<div style="background:#f8faf8;border:1px solid #e2ebe4;border-radius:8px;padding:12px 14px;">'
                f'<div style="font-size:11px;font-weight:600;color:#5c6f64;text-transform:uppercase;">Status Pompa Air</div>'
                f'<div style="font-size:17.5px;font-weight:700;color:{pump_color};margin:4px 0;">{"⚡ MENYALA" if pump_state == "MENYALA" else "🛑 MATI"}</div>'
                f'<div style="font-size:11.5px;color:#64748b;">{pump_status_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with kp2:
            st.markdown(
                f'<div style="background:#f8faf8;border:1px solid #e2ebe4;border-radius:8px;padding:12px 14px;">'
                f'<div style="font-size:11px;font-weight:600;color:#5c6f64;text-transform:uppercase;">Kelembapan Tanah</div>'
                f'<div style="font-size:17.5px;font-weight:700;color:#0284c7;margin:4px 0;">{cur_moist:.0f}%</div>'
                f'<div style="font-size:11.5px;color:#64748b;">Batas: Kering &lt;55% | Basah &ge;76%</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with kp3:
            st.markdown(
                f'<div style="background:#f8faf8;border:1px solid #e2ebe4;border-radius:8px;padding:12px 14px;">'
                f'<div style="font-size:11px;font-weight:600;color:#5c6f64;text-transform:uppercase;">Suhu Udara Kebun</div>'
                f'<div style="font-size:17.5px;font-weight:700;color:#d97706;margin:4px 0;">{cur_temp:.1f}°C</div>'
                f'<div style="font-size:11.5px;color:#64748b;">Suhu ideal 20°C – 30°C</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with kp4:
            st.markdown(
                f'<div style="background:#f8faf8;border:1px solid #e2ebe4;border-radius:8px;padding:12px 14px;">'
                f'<div style="font-size:11px;font-weight:600;color:#5c6f64;text-transform:uppercase;">Mode Sistem</div>'
                f'<div style="font-size:17.5px;font-weight:700;color:#15803d;margin:4px 0;">{"🤖 Otomatis" if mode == "Otomatis" else "🖐️ Manual"}</div>'
                f'<div style="font-size:11.5px;color:#64748b;">{"Sensor IoT Trigger" if mode == "Otomatis" else "Kontrol Petani"}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div style="margin:14px 0 8px 0;border-top:1px solid #edf2ee;"></div>', unsafe_allow_html=True)

        st.markdown('<div style="font-weight:600;font-size:13px;color:#334155;margin-bottom:6px;">Tombol Kontrol Pompa Air:</div>', unsafe_allow_html=True)
        cb1, cb2, cb3 = st.columns([1.2, 1.2, 1.4])
        with cb1:
            if st.button("▶️ Hidupkan Pompa (Manual)", use_container_width=True, key="btn_dash_pump_on",
                         help="Nyalakan pompa air secara manual untuk menyiram tanaman."):
                st.session_state["pump_mode"] = "Manual"
                st.session_state["pump_manual_state"] = "MENYALA"
                st.toast("Pompa air berhasil dinyalakan secara manual.", icon="⚡")
                st.rerun()
        with cb2:
            if st.button("⏹️ Matikan Pompa (Manual)", use_container_width=True, key="btn_dash_pump_off",
                         help="Matikan pompa air secara manual."):
                st.session_state["pump_mode"] = "Manual"
                st.session_state["pump_manual_state"] = "MATI"
                st.toast("Pompa air berhasil dimatikan secara manual.", icon="🛑")
                st.rerun()
        with cb3:
            if st.button("🤖 Aktifkan Mode Otomatis (Sensor)", use_container_width=True, key="btn_dash_pump_auto",
                         help="Serahkan kendali pompa ke sistem sensor otomatis."):
                st.session_state["pump_mode"] = "Otomatis"
                st.session_state["sim_moist"] = None
                st.toast("Mode otomatis aktif: pompa dikontrol penuh oleh ambang batas sensor.", icon="🤖")
                st.rerun()

        st.markdown('<div style="margin:12px 0 6px 0;font-size:12px;font-weight:600;color:#64748b;">🧪 Pengujian Cepat Logika Otomatisasi (Simulasi Skenario Sensor):</div>', unsafe_allow_html=True)
        ts1, ts2, ts3, ts4 = st.columns(4)
        with ts1:
            if st.button("🚨 Uji Tanah Kering (48%)", use_container_width=True, key="btn_t_dry",
                         help="Uji respons sistem saat kelembapan tanah turun di bawah 55% (pompa otomatis MENYALA)."):
                st.session_state["pump_mode"] = "Otomatis"
                st.session_state["sim_moist"] = 48.0
                st.toast("Simulasi tanah kering (48%): Pompa otomatis MENYALA!", icon="🚨")
                st.rerun()
        with ts2:
            if st.button("🌱 Uji Tanah Ideal (65%)", use_container_width=True, key="btn_t_opt",
                         help="Uji respons sistem saat kelembapan berada di rentang optimal 55%–76% (pompa STANDBY)."):
                st.session_state["pump_mode"] = "Otomatis"
                st.session_state["sim_moist"] = 65.0
                st.toast("Simulasi tanah ideal (65%): Pompa STANDBY / MATI.", icon="🌱")
                st.rerun()
        with ts3:
            if st.button("💧 Uji Tanah Basah (82%)", use_container_width=True, key="btn_t_wet",
                         help="Uji respons sistem saat kelembapan tanah berlebih ≥ 76% (pompa otomatis DIMATIKAN)."):
                st.session_state["pump_mode"] = "Otomatis"
                st.session_state["sim_moist"] = 82.0
                st.toast("Simulasi tanah terlalu basah (82%): Pompa otomatis DIMATIKAN!", icon="💧")
                st.rerun()
        with ts4:
            if st.button("↺ Reset ke Sensor Riil", use_container_width=True, key="btn_t_rst",
                         help="Kembalikan nilai kelembapan ke data pembacaan riil siklus tanam."):
                st.session_state["sim_moist"] = None
                st.session_state["pump_mode"] = "Otomatis"
                st.toast("Sensor di-reset ke data riil kebun.", icon="↺")
                st.rerun()


def page_dashboard():
    ui.hero("Dashboard Utama — Pemantauan Tanaman Pakcoy",
            "Ringkasan telemetri sensor tanah, suhu lingkungan, kurva kematangan tanaman pakcoy, dan kontrol otomatis pompa air.",
            "layout-dashboard")
    name, df, is_applied = pick_dataset("dash", extra_filters=False, btn_label="Tampilkan Data Siklus")

    if not is_applied:
        live_section()
        return

    # 1. Kontrol Pompa Air & Otomatisasi
    render_pump_automation_control(df)

    col_age = "Day" if "Day" in df.columns else ("DAP" if "DAP" in df.columns else df.columns[0])
    min_age = int(df[col_age].min()) if len(df) else utils.START_DAY
    max_age = int(df[col_age].max()) if len(df) else utils.HARVEST_DAY
    m = load_models()
    th = thresholds(m)

    total_data_lbl = f"{len(df):,} data"
    sub_pengukuran = "15× sehari (Pukul 06:00 s.d. 20:00)"

    ui.kpi_cards([
        dict(icon="database", label="Total Pengukuran", value=total_data_lbl, color="#15803d", sub=sub_pengukuran),
        dict(icon="droplets", label="Rata-rata Kelembapan", value=f"{df['Soil Moisture (%)'].mean():.1f}%", color="#0284c7", sub="Rentang ideal: 55% – 76%"),
        dict(icon="thermometer", label="Rata-rata Suhu Udara", value=f"{df['Temperature (°C)'].mean():.1f}°C", color="#d97706", sub="Rentang ideal: 20°C – 30°C"),
        dict(icon="trending-up", label="Rata-rata Kematangan", value=f"{df[MAT].mean():.1f}%", color="#15803d", sub="Skala 0% (Bibit) – 100% (Panen)"),
        dict(icon="calendar", label="Rentang Umur Pakcoy", value=f"{min_age}–{max_age} hari", color="#059669", sub="Panen optimal di Hari ke-30"),
    ], cols=5)
    ui.maturity_legend_bar(th)

    ui.section_header(
        "Distribusi Kondisi Kebun & Kurva Pertumbuhan",
        "Ringkasan proporsi kelembapan tanah, distribusi fase pakcoy, dan pola kematangan dari siklus tanam yang ditampilkan.",
        icon_name="bar-chart-3"
    )
    c1, c2 = st.columns(2)
    show(charts.donut_condition(df), "d_donut", c1)
    show(charts.bar_stage(df), "d_bar", c2)
    show(charts.maturity_curve(df), "d_mat")

    ui.section_header(
        "Data Lengkap Pengukuran Sensor Kebun (15× Pengecekan Harian)",
        f"Menampilkan seluruh {len(df):,} catatan pengukuran sensor dari {name} (Pukul 06:00 s.d. 20:00).",
        icon_name="database"
    )
    st.dataframe(style_table(format_display_df(df)), height=380, hide_index=True, width="stretch")

    live_section()


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
def page_forecast():
    ui.hero("Prakiraan Kondisi Kebun & Kematangan 4 Hari ke Depan",
            "Pilih siklus tanam dan titik hari awal di bawah, lalu tekan tombol 'Tampilkan Prakiraan 4 Hari' untuk melihat proyeksi kelembapan, suhu, dan kematangan.",
            "calendar-range")
    m = load_models()
    if not warn_models(m, ["fc"]) or not m.get("cfg_lstm"):
        return
    cfg = m["cfg_lstm"]
    win = cfg["w_in"]

    with st.container(border=True, key="card_fc_ctrl"):
        c_ser, c_sld = st.columns([1.25, 2.75], vertical_alignment="top")
        df = pick_series("fc", c_ser)
        if len(df) < win:
            ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {win} pembacaan berurutan untuk prakiraan 4 hari.")
            return

        max_fc = max(win, min(len(df), utils.CYCLE_LENGTH - cfg.get("h_out", 12)))
        if "fc_step" not in st.session_state or st.session_state["fc_step"] > max_fc or st.session_state["fc_step"] < win:
            st.session_state["fc_step"] = min(45, max_fc)
        step = c_sld.slider("Geser titik waktu awal prakiraan:", win, max_fc, key="fc_step")

        fc_c1, fc_c2, fc_c3, _ = st.columns([1.0, 1.15, 1.05, 1.2])
        if fc_c1.button("Fase Awal · Hari ke-7", use_container_width=True, key="fc_btn1"):
            st.session_state["fc_step"] = min(20, max_fc)
            st.rerun()
        if fc_c2.button("Fase Pertengahan · Hari ke-17", use_container_width=True, key="fc_btn2"):
            st.session_state["fc_step"] = min(50, max_fc)
            st.rerun()
        if fc_c3.button("Menjelang Panen · Hari ke-25", use_container_width=True, key="fc_btn3"):
            st.session_state["fc_step"] = min(75, max_fc)
            st.rerun()

        row_fc = df.iloc[step - 1]
        day_fc = row_fc.get("Day", "?")
        time_fc = str(row_fc.get("Time", "?"))
        fc_sig = (st.session_state.get("fc_series", ""), int(step), len(df))

        st.markdown('<div style="margin-top:8px;border-top:1px solid #edf2ee;padding-top:10px;"></div>', unsafe_allow_html=True)
        b_l, b_r = st.columns([3.4, 1.0], vertical_alignment="center")
        b_l.markdown(
            f'<div class="action-bar-info">'
            f'<strong>Titik Awal:</strong> Hari ke-{day_fc} &middot; Jam {time_fc} &middot; Ukur #{step} &rarr; '
            f'<strong>Proyeksi:</strong> Hari ke-{min(utils.CYCLE_DAYS, int(day_fc) + 1)} s.d. Hari ke-{min(utils.CYCLE_DAYS, int(day_fc) + 4)}'
            f'</div>',
            unsafe_allow_html=True
        )
        if b_r.button("Tampilkan Prakiraan", type="primary", key="btn_fc_run") or "fc_committed_sig" not in st.session_state:
            st.session_state["fc_committed_sig"] = fc_sig

    window = df.iloc[step - win: step].reset_index(drop=True)
    try:
        table = predict_forecast(m, window)
    except Exception as e:
        st.error(f"Gagal memprediksi: {e}")
        return
    th = cfg["maturity_thresholds"]
    last = table.iloc[-1]
    mat_last = float(last["Tingkat Kematangan (%)"]) if "Tingkat Kematangan (%)" in last else float(last["Maturity (%)"])
    end_stage = utils.CLASS_NAMES[utils.stage_from_maturity(mat_last, th)]
    ui.kpi_cards([
        dict(icon="droplets", label="Prakiraan Kelembapan (4 Hari Lagi)", value=f"{last['Kelembapan (%)']:.0f}%", color="#38bdf8", sub="Rentang ideal: 55% – 75%"),
        dict(icon="thermometer", label="Prakiraan Suhu (4 Hari Lagi)", value=f"{last['Suhu (°C)']:.1f}°C", color="#fb923c", sub="Rentang ideal: 20°C – 30°C"),
        dict(icon="trending-up", label="Prakiraan Kematangan (4 Hari Lagi)", value=f"{mat_last:.0f}%", color="#34d399", sub="Siap panen ≥ 89%"),
        dict(icon="sprout", label="Fase Tanaman 4 Hari Lagi", value=label(end_stage), color=charts.STAGE_COLORS.get(end_stage, "#34d399"), sub="Berdasarkan proyeksi AI"),
    ], cols=4)

    v_c1, v_c2 = st.columns([2.8, 1.2], vertical_alignment="bottom")
    with v_c1:
        ui.section_header(
            "Kartu Prakiraan Pertumbuhan Pakcoy 4 Hari ke Depan (AI LSTM)",
            "Visualisasi tanaman pakcoy dan proyeksi kelembapan, suhu, tingkat kematangan, serta estimasi ukuran daun untuk 4 hari ke depan.",
            icon_name="sprout"
        )
    with v_c2:
        vis_mode_sel = st.radio(
            "Mode Gambar:",
            ["Foto Asli Kebun", "Ilustrasi Botani AI"],
            horizontal=True,
            key="fc_vis_mode",
            label_visibility="collapsed"
        )
    vis_mode = "svg" if "Ilustrasi" in vis_mode_sel else "photo"
    ui.forecast_4day_cards(table, start_day=day_fc, thresholds=th, dry=DRY, wet=WET, visual_mode=vis_mode)

    ui.action_guide_card(
        last["Kelembapan (%)"],
        last["Suhu (°C)"],
        mat_last,
        label(end_stage),
        dry=DRY,
        wet=WET,
        title="Persiapan Kebun untuk 4 Hari ke Depan",
        badge_text="Rekomendasi Antisipasi"
    )

    hist_x = window["Time_Index"].tolist()
    pred_x = [hist_x[-1] + i for i in range(1, len(table) + 1)]
    truth = df.iloc[step: step + len(table)] if step + len(table) <= len(df) else None
    c1, c2 = st.columns(2)
    show(charts.forecast_line(hist_x, window["Soil Moisture (%)"].tolist(), pred_x, table["Kelembapan (%)"].tolist(),
                              "Prakiraan Kelembapan Tanah (%)", "Kelembapan (%)", "#38bdf8",
                              None if truth is None else truth["Soil Moisture (%)"].tolist()), "fc_m", c1)
    show(charts.forecast_line(hist_x, window["Temperature (°C)"].tolist(), pred_x, table["Suhu (°C)"].tolist(),
                              "Prakiraan Suhu Udara (°C)", "Suhu (°C)", "#fb923c",
                              None if truth is None else truth["Temperature (°C)"].tolist()), "fc_t", c2)
    pred_mat = table["Tingkat Kematangan (%)"].tolist() if "Tingkat Kematangan (%)" in table.columns else table["Maturity (%)"].tolist()
    show(charts.maturity_forecast(pred_x, pred_mat, th), "fc_mat")
    st.markdown('<div class="section-title">Ringkasan Prakiraan Harian (4 Hari ke Depan)</div>', unsafe_allow_html=True)
    mat_col = "Tingkat Kematangan (%)" if "Tingkat Kematangan (%)" in table.columns else "Maturity (%)"
    daily = (table.groupby("Hari", sort=False)
             .agg({"Kelembapan (%)": "mean", "Suhu (°C)": "mean", mat_col: "last", "Tahap": "last"})
             .round(1).reset_index())
    daily = daily.rename(columns={
        "Hari": "Waktu ke Depan",
        "Kelembapan (%)": "Rata-rata Kelembapan (%)",
        "Suhu (°C)": "Rata-rata Suhu (°C)",
        mat_col: "Tingkat Kematangan (%)",
        "Tahap": "Prakiraan Fase Tanaman"
    })
    st.dataframe(daily, hide_index=True, width="stretch")
    with st.expander("Lihat Tabel Rincian per Waktu Ukur (Pagi 08:00, Siang 12:00, Sore 16:00)"):
        disp_tbl = table.drop(columns=["Maturity (%)"], errors="ignore").rename(columns={
            "Langkah": "Urutan ke-",
            "Hari": "Hari ke Depan",
            "Jam": "Waktu Ukur",
            "Tahap": "Fase Tanaman"
        })
        st.dataframe(disp_tbl, hide_index=True, width="stretch")
    st.download_button("Unduh Tabel Prakiraan 4 Hari (CSV)", table.to_csv(index=False).encode("utf-8"),
                       file_name="prediksi_4_hari.csv", mime="text/csv", key="fc_dl")
    if truth is not None:
        ui.banner("info", "Garis titik-titik abu-abu pada grafik menunjukkan data asli di kebun sebagai pembanding ketepatan prakiraan AI.")


# ================================================================= CNN & foto
def photo_panel(m, img, key, sensor_row=None):
    """Analisis satu foto: CNN + analisis visual daun. Mengembalikan (cnn, green)."""
    with st.expander("Pengaturan Kalibrasi Ukuran Daun (Otomatis Sesuai Standar Morfologi Pakcoy)", expanded=False):
        st.caption(
            "Sistem secara otomatis mengkalibrasi **panjang daun (`cm`)**, **lebar daun (`cm`)**, **luas helaian daun (`cm²`)**, "
            "dan **diameter tajuk rumpun (`cm`)** sesuai standar morfologi tanaman pakcoy asli (*Brassica rapa* subsp. *chinensis*) pada setiap fase. "
            "Jika Anda memotret dengan alat ukur pembanding, Anda juga dapat memilih kalibrasi manual di bawah ini:"
        )
        c_mode, c_val = st.columns([1.2, 1])
        with c_mode:
            calib_choice = st.radio(
                "Metode Penentuan Ukuran Daun:",
                ["Otomatis (Standar Morfologi Pakcoy Asli)", "Berdasarkan Diameter Netpot (cm)", "Manual (Piksel per cm)"],
                key=f"{key}_calib_choice"
            )
        scale = 0.0
        with c_val:
            if calib_choice == "Berdasarkan Diameter Netpot (cm)":
                netpot_dia = st.number_input("Diameter netpot hidroponik (cm)", min_value=1.0, max_value=25.0, value=5.0, step=0.5, key=f"{key}_netpot_dia", help="Netpot hidroponik standar berdiameter 5 cm.")
                scale = float(img.width * 0.28 / netpot_dia)
                st.caption(f"Skala terhitung: **{scale:.1f} px/cm**")
            elif calib_choice == "Manual (Piksel per cm)":
                scale = st.number_input("Skala manual (px/cm)", min_value=1.0, max_value=300.0, value=45.0, step=1.0, key=f"{key}_manual_scale")
            else:
                st.info("Mode Standar Pakcoy Aktif: Ukuran daun dihitung dalam satuan **cm**, **cm²**, dan **SPAD** sesuai fase pertumbuhan.")

    g = utils.green_analysis(img, scale)
    is_plant, plant_reason, _ = utils.validate_plant_image(img, g)
    c1, c2 = st.columns(2)
    c1.image(img, caption="Foto Asli yang Diunggah")
    c2.image(g["overlay"], caption="Deteksi Area Daun Hijau (Latar Belakang Digelapkan Otomatis)")
    cnn = None
    idx = 0.0
    if m.get("cnn") is not None:
        names = cnn_names(m)
        p = predict_image(m, img)

        if not is_plant:
            idx_bukan = names.index("bukan_pakcoy") if "bukan_pakcoy" in names else 0
            p_adj = np.zeros_like(p)
            p_adj[idx_bukan] = 0.99
            others = [i for i in range(len(names)) if i != idx_bukan]
            for i in others:
                p_adj[i] = 0.01 / max(1, len(others))
            p = p_adj
            k = idx_bukan
        else:
            k = int(p.argmax())

        cnn = (names[k], float(p[k]), p, names)
        idx = utils.readiness_index(p, names)
        if names[k] == "bukan_pakcoy":
            ui.kpi_cards([
                dict(icon="alert-triangle", label="Hasil Pemeriksaan Foto", value=label(names[k]), color=charts.STAGE_COLORS.get(names[k], "#dc2626")),
                dict(icon="sparkles", label="Tingkat Keyakinan AI", value=f"{p[k]:.0%}", color="#dc2626"),
                dict(icon="x-circle", label="Status Kesiapan Panen", value="Bukan Pakcoy", color="#dc2626", sub="Silakan unggah foto daun pakcoy"),
            ], cols=3)
            show(charts.prob_bar(p, names), f"{key}_prob")
            alasan_detail = f" — {plant_reason}" if not is_plant else ""
            ui.banner("danger", f"Foto terdeteksi sebagai BUKAN TANAMAN PAKCOY{alasan_detail} (Keyakinan AI: {p[k]:.0%}). "
                                f"Silakan unggah foto tanaman pakcoy asli dari sudut atas.")
        else:
            ui.kpi_cards([
                dict(icon="cpu", label="Fase Tanaman (Dari Foto)", value=label(names[k]), color=charts.STAGE_COLORS.get(names[k], "#15803d"), sub="Deteksi visual daun (CNN)"),
                dict(icon="sparkles", label="Tingkat Keyakinan AI", value=f"{p[k]:.0%}", color="#34d399", sub="Ketepatan pengenalan foto"),
                dict(icon="layers", label="Skor Kesiapan Panen", value=f"{idx:.0f} / 100", color="#facc15", sub="Skor ≥ 85 siap dipanen"),
            ], cols=3)
            g1, g2 = st.columns(2)
            show(charts.prob_bar(p, names), f"{key}_prob", g1)
            show(charts.gauge(idx, "Skor Kesiapan Panen dari Foto (0–100%)", (50, 90)), f"{key}_gauge", g2)
            if p[k] < 0.6:
                ui.banner("warn", "Tingkat keyakinan AI terhadap foto ini cukup rendah. Coba ambil ulang foto dari atas dengan cahaya yang lebih terang.")
    else:
        ui.banner("warn", "Model CNN belum tersedia. Menampilkan hasil pengukuran visual daun.")

    if not is_plant or (cnn and cnn[0] == "bukan_pakcoy"):
        cards = [
            dict(icon="alert-triangle", label="Validasi Objek Foto", value="Bukan Tanaman", color="#dc2626",
                 sub="Objek non-tanaman terdeteksi"),
            dict(icon="maximize", label="Panjang Helaian Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="maximize", label="Lebar Helaian Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="maximize", label="Luas Helaian Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="layers", label="Diameter Tajuk Rumpun", value="Tidak Terdeteksi", color="#94a3b8",
                 sub="Tidak ditemukan rumpun pakcoy"),
            dict(icon="sprout", label="Kesehatan Klorofil Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan daun pakcoy"),
        ]
        ui.kpi_cards(cards, cols=3)
        return cnn, g

    detected_stage = cnn[0] if cnn else "masa_pertumbuhan"
    conf_val = cnn[1] if cnn else 0.85
    metrics = ui.compute_pakcoy_leaf_metrics(g, stage_key=detected_stage, manual_scale=scale)

    # Simpan kembali ke dict g agar laporan unduhan (.md) juga memuat angka morfologi pakcoy yang akurat
    g["width_cm"] = metrics["leaf_wid_cm"]
    g["height_cm"] = metrics["leaf_len_cm"]
    g["area_cm2"] = metrics["leaf_area_cm2"]

    prefix_est = "± " if scale <= 0 else ""

    if g['yellow_pct'] < 2.0:
        yellow_sub = "Daun sangat sehat & segar"
        yellow_col = "#34d399"
    elif g['yellow_pct'] < 8.0:
        yellow_sub = "Normal · sedikit menguning"
        yellow_col = "#facc15"
    else:
        yellow_sub = "Perhatian · gejala klorosis daun"
        yellow_col = "#f87171"

    st.markdown('<div class="section-title">Hasil Pengukuran Fisik & Kesehatan Daun Pakcoy</div>', unsafe_allow_html=True)
    cards = [
        dict(icon="maximize", label="Panjang Helaian Daun", value=f"{prefix_est}{metrics['leaf_len_cm']:.1f} cm", color="#15803d",
             sub=f"Standar fase ini: {metrics['len_std_str']}"),
        dict(icon="maximize", label="Lebar Helaian Daun", value=f"{prefix_est}{metrics['leaf_wid_cm']:.1f} cm", color="#38bdf8",
             sub=f"Standar fase ini: {metrics['wid_std_str']}"),
        dict(icon="layers", label="Luas Helaian Daun", value=f"{prefix_est}{metrics['leaf_area_cm2']:.1f} cm²", color="#fb923c",
             sub=f"Standar fase ini: {metrics['area_std_str']}"),
        dict(icon="maximize", label="Diameter Tajuk Rumpun", value=f"{prefix_est}{metrics['canopy_dia_cm']:.1f} cm", color="#a78bfa",
             sub=f"Standar tajuk: {metrics['canopy_std_str']}"),
        dict(icon="sparkles", label="Indeks Klorofil & Kerapatan", value=f"{metrics['spad_val']:.1f} SPAD · {g['compactness']:.0%}", color="#34d399",
             sub=f"Kepekatan hijau {g['greenness']:.0f}% · Tutupan {g['coverage_pct']:.1f}%"),
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

    with st.expander("Penjelasan Satuan & Standar Ukuran Daun Pakcoy Asli"):
        st.markdown(
            "- **Panjang Helaian Daun (`cm`):** Diukur dari pangkal tangkai putih (*petiole*) hingga ujung helai daun (*lamina*). Ukuran pakcoy asli: **6,5–11,8 cm** (*Masa Pertumbuhan*), **12,5–17,5 cm** (*Mendekati Panen*), dan **18,0–23,5 cm** (*Siap Panen*).\n"
            "- **Lebar Helaian Daun (`cm`):** Diukur pada bagian terlebar helai daun hijau. Ukuran pakcoy asli: **4,0–7,2 cm** (*Masa Pertumbuhan*), **7,5–10,8 cm** (*Mendekati Panen*), dan **11,0–14,5 cm** (*Siap Panen*).\n"
            "- **Luas Helaian Daun (`cm²`):** Dihitung menggunakan rumus morfometri hortikultura $LA = P \\times L \\times k$ ($k \\approx 0{,}68 - 0{,}72$) dalam satuan **centimeter persegi (`cm²`)**.\n"
            "- **Diameter Tajuk Rumpun (`cm`):** Lebar bentang mekarnya roset daun pakcoy dilihat dari sudut atas (**9,5–26,5 cm**).\n"
            "- **Indeks Klorofil (`SPAD`) & Persentase Menguning (`%`):** Satuan standar agronomi (**SPAD**) untuk mengukur kepekatan zat hijau daun, sedangkan persentase menguning mendeteksi gejala klorosis atau kekurangan nutrisi."
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
    file_id = getattr(f, "file_id", None) or getattr(f, "id", None) or getattr(f, "name", "cam")
    sig = (getattr(f, "name", "cam"), getattr(f, "size", 0), str(file_id))
    return Image.open(f), sig


def page_cnn():
    ui.hero("Cek Kesiapan Panen & Kesehatan Daun dari Foto",
            "Unggah foto tanaman pakcoy Anda, lalu tekan tombol 'Analisis Foto Tanaman' untuk memeriksa kesiapan panen dan kesehatan daun.",
            "scan-line")
    m = load_models()
    tab1, tab2 = st.tabs(["Periksa Foto Tanaman", "Tingkat Ketepatan & Info Model Foto"])
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
def load_history_1400():
    p = DATA_DIR / "history_perkembangan_pakcoy_1400.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


@st.cache_data
def load_raw_dataset():
    p = DATA_DIR / "dataset_asli_mentah.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def page_history_perkembangan():
    ui.hero("History Perkembangan Tanaman Pakcoy (Siklus 1–30)",
            "Catatan komprehensif riwayat pertumbuhan tanaman pakcoy dari benih hingga panen raya (1.400 data pengukuran, 15× pengecekan harian).",
            "history")

    df_hist = load_history_1400()
    if df_hist.empty:
        ui.banner("warn", "File dataset riwayat perkembangan (history_perkembangan_pakcoy_1400.csv) belum tersedia.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Riwayat & Analisis Pertumbuhan",
        "📋 Tabel Lengkap (1.400 Data Pengecekan)",
        "📁 Dataset Asli Excel (1.140 Data Mentah)",
        "🌱 Panduan Siklus 1–30 & Standar Panen"
    ])

    with tab1:
        # Filter interaktif
        with st.container(border=True):
            st.markdown('<div class="section-title" style="margin-top:0;">Filter Riwayat Perkembangan Tanaman</div>', unsafe_allow_html=True)
            f1, f2, f3, f4 = st.columns([1.2, 1.1, 1.2, 1.1])
            
            cycle_opts = ["Semua Siklus (1–30)"] + [f"Siklus {i}" for i in range(1, 31)]
            sel_cyc = f1.selectbox("Pilih Siklus Budidaya:", cycle_opts, key="hist_filter_cyc")
            
            day_opts = ["Semua Hari (1–30)"] + [f"Hari ke-{i}" for i in range(1, 31)]
            sel_day = f2.selectbox("Pilih Umur Tanaman:", day_opts, key="hist_filter_day")
            
            times_all = sorted(list(df_hist["Time"].unique()))
            time_opts = ["Semua Jam (15× Pengecekan)"] + times_all
            sel_time = f3.selectbox("Jam Pengukuran:", time_opts, key="hist_filter_time")
            
            fase_opts = ["Semua Fase", "Fase Awal", "Fase Vegetatif", "Mendekati Panen", "Siap Panen"]
            sel_fase = f4.selectbox("Fase Pertumbuhan:", fase_opts, key="hist_filter_fase")

        # Terapkan filter
        df_view = df_hist.copy()
        if sel_cyc != "Semua Siklus (1–30)":
            cyc_num = int(sel_cyc.replace("Siklus ", ""))
            df_view = df_view[df_view["Cycle_ID"] == cyc_num]
        if sel_day != "Semua Hari (1–30)":
            day_num = int(sel_day.replace("Hari ke-", ""))
            df_view = df_view[df_view["Day"] == day_num]
        if sel_time != "Semua Jam (15× Pengecekan)":
            df_view = df_view[df_view["Time"] == sel_time]
        if sel_fase != "Semua Fase":
            df_view = df_view[df_view["Fase"] == sel_fase]

        if df_view.empty:
            ui.banner("warn", "Tidak ada data yang cocok dengan kombinasi filter yang dipilih.")
            return

        # KPI Metrics Cards
        avg_moist = df_view["Soil Moisture (%)"].mean()
        avg_temp = df_view["Temperature (°C)"].mean()
        max_mat = df_view["Ground Truth Maturity Level (%)"].max()

        ui.kpi_cards([
            dict(icon="database", label="Total Data Pengecekan", value=f"{len(df_view):,} Catatan", sub="Dari 1.400 Data Tersedia", color="#15803d"),
            dict(icon="history", label="Frekuensi Pengukuran", value="15× / Hari", sub="Pukul 06:00 s.d. 20:00", color="#0284c7"),
            dict(icon="sprout", label="Siklus Menuju Panen", value="Hari 1–30", sub="Masa Panen Hari ke-30", color="#15803d"),
            dict(icon="droplets", label="Rata-rata Kelembapan", value=f"{avg_moist:.1f}%", sub="Ideal: 55% – 76%", color="#0d9488"),
            dict(icon="thermometer", label="Rata-rata Suhu Udara", value=f"{avg_temp:.1f}°C", sub="Optimal: 22°C – 28°C", color="#d97706"),
            dict(icon="sparkles", label="Tingkat Kematangan Puncak", value=f"{max_mat:.0f}%", sub="100% Siap Panen Raya", color="#15803d"),
        ])

        # Visualisasi Utama
        st.markdown('<div class="section-title">Kurva Pertumbuhan &amp; Kematangan Tanaman Menuju Panen (Hari 1 s.d. 30)</div>', unsafe_allow_html=True)
        show(charts.history_maturity_curve(df_view), "fig_hist_mat")

        st.markdown('<div class="section-title">Profil Fluktuasi Sensor 15 Kali Pengecekan Harian (06:00 – 20:00)</div>', unsafe_allow_html=True)
        show(charts.history_daily_15times(df_view), "fig_hist_daily")

        st.markdown('<div class="section-title">Tren Sensor Lingkungan &amp; Sebaran Kondisi Tanah</div>', unsafe_allow_html=True)
        col_tr1, col_tr2 = st.columns([1.6, 1.0])
        with col_tr1:
            show(charts.history_sensor_trend(df_view), "fig_hist_trend")
        with col_tr2:
            show(charts.donut_condition(df_view), "fig_hist_donut")

    with tab2:
        st.markdown('<div class="section-title" style="margin-top:0;">Tabel Lengkap Riwayat Perkembangan Pakcoy (1.400 Data)</div>', unsafe_allow_html=True)
        st.caption("Data mencakup 30 siklus pertumbuhan pakcoy dari hari ke-1 hingga hari ke-30 (masa panen) dengan frekuensi 15 kali pengecekan setiap harinya.")

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

        csv_1400 = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Unduh Dataset Lengkap 1.400 Data Pengecekan (CSV)",
            data=csv_1400,
            file_name="dataset_history_pakcoy_1400_data.csv",
            mime="text/csv",
            key="btn_dl_1400_csv"
        )

    with tab3:
        ui.banner("info", "Menampilkan dataset asli mentah dari file 'dataset asli/new Dataset_Pakcoy.xlsx' (1.140 baris data observasi kebun dengan interval 3 kali pengukuran per hari: 08:00, 12:00, 16:00).")
        df_raw = load_raw_dataset()
        if not df_raw.empty:
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Data Asli", f"{len(df_raw):,} Baris")
            k2.metric("Rentang Hari", f"Hari {df_raw['Day'].min()} s.d. {df_raw['Day'].max()}")
            k3.metric("Frekuensi Pengecekan Asli", "3× / Hari (08:00, 12:00, 16:00)")
            st.dataframe(df_raw, hide_index=True, width="stretch", height=450)
            csv_raw = df_raw.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Unduh Dataset Asli Mentah (CSV)",
                data=csv_raw,
                file_name="dataset_asli_mentah_pakcoy.csv",
                mime="text/csv",
                key="btn_dl_raw_csv"
            )
        else:
            ui.banner("warn", "File dataset asli mentah belum tersedia.")

    with tab4:
        st.markdown('<div class="section-title" style="margin-top:0;">Standar Agronomi Siklus Tanaman Pakcoy (Hari 1 s.d. 30 Masa Panen)</div>', unsafe_allow_html=True)
        ui.banner("ok", "Tanaman pakcoy (Brassica rapa L.) memiliki siklus budidaya optimal 30 hari sejak pindah tanam (10 HST) hingga panen raya (40 HST).")

        st.markdown(
            """
| Tahap Pertumbuhan | Umur Tanaman (Hari ke-) | Rentang HST | Tingkat Kematangan | Target Kelembapan | Suhu Optimal | Indikator Fisik Daun & Rumpun |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Fase Awal (Initial Stage)** | Hari 1 – 10 | 10 – 19 HST | 5% – 33% | 70% – 80% (Lembap) | 22°C – 26°C | Daun 2–4 helai, adaptasi akar baru setelah pindah tanam dari semai. |
| **2. Fase Vegetatif** | Hari 11 – 20 | 20 – 29 HST | 34% – 66% | 60% – 75% (Optimal) | 22°C – 28°C | Pertumbuhan cepat, daun 6–10 helai, batang mulai kokoh dan hijau cerah. |
| **3. Mendekati Panen (Pre-Harvest)** | Hari 21 – 25 | 30 – 34 HST | 67% – 84% | 55% – 70% (Optimal) | 22°C – 28°C | Daun melebar, tebal, roset terbentuk kompak, tekstur renyah. |
| **4. Siap Panen (Harvest Ready)** | Hari 26 – 30 | 35 – 40 HST | 85% – 100% | 55% – 65% (Optimal) | 20°C – 28°C | **Panen Raya pada Hari ke-30!** Bobot basah 150–250g per rumpun, daun lebat dan segar. |
            """
        )
        st.info("💡 **Tips Panen dari Pakar Agronomi:** Panen pakcoy terbaik dilakukan pada pagi hari (pukul 06:00 – 08:00) saat kelembapan udara masih tinggi dan terik matahari belum membakar daun. Hal ini menjaga kadar air daun tetap tinggi dan menjaga kesegaran lebih lama.")


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
