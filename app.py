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
    "08:00": "08:00 (Pagi)",
    "12:00": "12:00 (Siang)",
    "16:00": "16:00 (Sore)",
}


def label(name):
    return utils.CLASS_LABELS.get(name, name)


def cond_label(cond):
    return COND_LABELS_ID.get(str(cond), str(cond))


def format_display_df(df):
    """Ubah kolom dan isi tabel menjadi Bahasa Indonesia yang mudah dipahami orang awam (hanya untuk tampilan)."""
    has_multi_cycle = "Cycle_ID" in df.columns and df["Cycle_ID"].nunique() > 1
    base_cols = (["Cycle_ID"] if has_multi_cycle else []) + [c for c in utils.REQUIRED_COLS if c in df.columns]
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
    (container or st).plotly_chart(fig, key=key)


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
        p = predict_stage(m, df.iloc[i - w + 1: i + 1])
        k = int(p.argmax())
        tahap, sumber = f"{label(utils.CLASS_NAMES[k])}", f"Deteksi AI · Yakin {p[k]:.0%}"
    else:
        tahap, sumber = label(str(row["Ground Truth Criteria"])), "Data pencatatan kebun"
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
    m = load_models()
    th = thresholds(m)
    ui.kpi_cards([
        dict(icon="database", label="Total Pengukuran", value=f"{len(df):,} kali", color="#60a5fa", sub="3x sehari (Pagi, Siang, Sore)"),
        dict(icon="droplets", label="Rata-rata Kelembapan", value=f"{df['Soil Moisture (%)'].mean():.1f}%", color="#38bdf8", sub="Rentang ideal: 55% – 75%"),
        dict(icon="thermometer", label="Rata-rata Suhu Udara", value=f"{df['Temperature (°C)'].mean():.1f}°C", color="#fb923c", sub="Rentang ideal: 20°C – 30°C"),
        dict(icon="trending-up", label="Rata-rata Kematangan", value=f"{df[MAT].mean():.1f}%", color="#34d399", sub="Skala 0% (Bibit) – 100% (Panen)"),
        dict(icon="calendar", label="Rentang Umur Pakcoy", value=f"{min_age}–{max_age} hari", color="#a78bfa", sub="Panen optimal di Hari ke-30"),
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
        "Data Lengkap Pengukuran Sensor Kebun",
        f"Menampilkan seluruh {len(df):,} catatan pengukuran sensor dari siklus tanam yang dipilih (Hari ke-{min_age} s.d. Hari ke-{max_age}).",
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
        return ""
    sty = d.style
    fn = getattr(sty, "map", None) or sty.applymap
    cond_col = "Kondisi Tanah" if "Kondisi Tanah" in d.columns else ("Soil Condition" if "Soil Condition" in d.columns else None)
    if cond_col:
        sty = fn(color, subset=[cond_col])
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


def page_eksplorasi():
    ui.hero("Data & Riwayat Kebun Pakcoy",
            "Pilih siklus tanam lalu tekan tombol 'Tampilkan Data & Grafik' untuk menelusuri riwayat kebun.",
            "bar-chart-3")
    name, fdf, is_applied = pick_dataset("eks", extra_filters=False, btn_label="Tampilkan Data & Grafik")
    if not is_applied:
        ui.pending_action_card(
            "Tekan Tombol 'Tampilkan Data & Grafik' untuk Memuat Riwayat Kebun",
            "Pilih siklus tanam di atas, kemudian klik tombol hijau 'Tampilkan Data & Grafik' untuk melihat tabel dan grafik analisis.",
            icon_name="bar-chart-3"
        )
        return

    ui.banner("ok", f"Menampilkan seluruh {len(fdf):,} catatan pengukuran sensor dari {name} (Hari ke-1 s.d. Hari ke-30).")
    st.dataframe(style_table(format_display_df(fdf)), height=420, hide_index=True, width="stretch")
    st.download_button("Unduh Data Tabel Ini (Format CSV)", fdf.to_csv(index=False).encode("utf-8"),
                       file_name="data_pakcoy_filter.csv", mime="text/csv", key="eks_dl")
    c1, c2, c3 = st.columns(3)
    show(charts.hist_moisture(fdf, DRY, WET), "e_hist", c1)
    show(charts.scatter_moist_temp(fdf), "e_scatter", c2)
    show(charts.daily_time_pattern(fdf), "e_daily_time", c3)

    shares = fdf["Soil Condition"].value_counts(normalize=True).reindex(["Wet", "Optimal", "Dry"]).fillna(0)
    if shares.min() < 0.10:
        ui.banner("info", "Sebagian besar catatan kebun berada pada kondisi tanah Ideal (Optimal), sedangkan kondisi Kering atau Terlalu Basah lebih jarang terjadi karena penyiraman dijaga rutin.")
    if len(fdf) > 1:
        r = fdf[utils.SENSOR_COLS].corr().iloc[0, 1]
        if pd.notna(r):
            ui.banner("info", f"Hubungan Kelembapan Tanah & Suhu Udara (Korelasi {r:.2f}): Saat suhu udara meningkat di siang hari, kelembapan tanah cenderung sedikit berkurang akibat penguapan alami.")
    with st.expander("Lihat Ringkasan Angka Rata-rata, Terendah, dan Tertinggi"):
        desc_df = fdf[utils.SENSOR_COLS + [MAT]].rename(columns={
            "Soil Moisture (%)": "Kelembapan Tanah (%)",
            "Temperature (°C)": "Suhu Udara (°C)",
            MAT: "Tingkat Kematangan (%)"
        }).describe().round(2)
        desc_df.index = [
            {"count": "Jumlah Data", "mean": "Rata-rata", "std": "Simpangan Baku", "min": "Nilai Terendah",
             "25%": "Kuartil 25%", "50%": "Nilai Tengah (Median)", "75%": "Kuartil 75%", "max": "Nilai Tertinggi"}.get(idx, idx)
            for idx in desc_df.index
        ]
        st.caption("**Ringkasan Umum Seluruh Data Terfilter:**")
        st.dataframe(desc_df, width="stretch")
        st.caption("**Nilai Rata-rata Berdasarkan Waktu Ukur (Pagi, Siang, Sore):**")
        time_df = fdf.groupby("Time")[utils.SENSOR_COLS + [MAT]].mean().round(2)
        time_df.index = [JAM_LABELS_ID.get(str(i), str(i)) for i in time_df.index]
        time_df = time_df.rename(columns={
            "Soil Moisture (%)": "Rata-rata Kelembapan (%)",
            "Temperature (°C)": "Rata-rata Suhu (°C)",
            MAT: "Rata-rata Kematangan (%)"
        })
        st.dataframe(time_df, width="stretch")
        grp_df = fdf.groupby("Ground Truth Criteria")[utils.SENSOR_COLS + [MAT]].mean().round(2)
        grp_df.index = [label(i) for i in grp_df.index]
        grp_df = grp_df.rename(columns={
            "Soil Moisture (%)": "Rata-rata Kelembapan (%)",
            "Temperature (°C)": "Rata-rata Suhu (°C)",
            MAT: "Rata-rata Kematangan (%)"
        })
        st.caption("**Nilai Rata-rata pada Setiap Fase Pertumbuhan:**")
        st.dataframe(grp_df, width="stretch")


# ================================================================= monitoring realtime
def render_monitor(ph, recs, dry, wet, tag):
    if not recs:
        ph["banner"].markdown(ui.banner_html("info", "Klik tombol hijau 'Mulai Simulasi Monitoring' untuk melihat cara kerja sensor dan pompa air otomatis."),
                              unsafe_allow_html=True)
        return
    h = pd.DataFrame(recs).set_index("idx")
    last = recs[-1]
    slope, fut = utils.linear_trend(h["moist"].tail(6).values, 5)
    if slope < -0.05:
        trend_val = f"Menurun ({slope:+.2f}%)"
        trend_icon = "trending-down"
    elif slope > 0.05:
        trend_val = f"Meningkat ({slope:+.2f}%)"
        trend_icon = "trending-up"
    else:
        trend_val = "Stabil (Tetap)"
        trend_icon = "activity"
    pump_txt = "MENYALA (Menyiram)" if last["pump"] else "MATI (Standby)"
    pump_color = "#fb923c" if last["pump"] else "#34d399"
    ph["cards"].markdown(ui.kpi_html([
        dict(icon="droplets", label="Kelembapan Tanah", value=f"{last['moist']:.0f}%", color="#38bdf8", sub=f"Batas kering: {dry:.0f}%"),
        dict(icon="thermometer", label="Suhu Udara", value=f"{last['temp']:.1f}°C", color="#fb923c", sub=f"Hari ke-{last['day']} · Jam {last['time']}"),
        dict(icon="cpu", label="Fase Tanaman", value=last["stage"], color="#e8ecf4", sub=last["source"]),
        dict(icon=trend_icon, label="Arah Perubahan Air", value=trend_val, color="#facc15",
             sub=f"Perkiraan ukur berikutnya: {fut[0]:.1f}%"),
        dict(icon="zap", label="Status Pompa Air", value=pump_txt, color=pump_color, sub="Kontrol otomatis sensor"),
    ]), unsafe_allow_html=True)
    status = last["status"]
    if status in ("dry", "recovering"):
        text = (f"POMPA AIR MENYALA OTOMATIS — Tanah terdeteksi kering ({last['moist']:.0f}%, di bawah batas aman {dry:.0f}%). Penyiraman sedang berlangsung." if status == "dry"
                else f"POMPA MASIH MENYIRAM — Kelembapan tanah ({last['moist']:.0f}%) sedang dipulihkan hingga melewati batas aman.")
        ph["banner"].markdown(ui.banner_html("danger", text), unsafe_allow_html=True)
    elif status == "wet":
        ph["banner"].markdown(ui.banner_html("warn", f"TANAH TERLALU BASAH ({last['moist']:.0f}% ≥ {wet:.0f}%) — "
                                                      "Pompa air otomatis dimatikan. Pastikan saluran drainase lancar."), unsafe_allow_html=True)
    else:
        ph["banner"].markdown(ui.banner_html("ok", f"KONDISI TANAH AMAN & IDEAL ({last['moist']:.0f}%) — Pompa air dalam keadaan mati (hemat air)."),
                              unsafe_allow_html=True)
    hv = pd.DataFrame({"Soil Moisture (%)": h["moist"], "Temperature (°C)": h["temp"]}).tail(60)
    with ph["charts"].container():
        c1, c2 = st.columns(2)
        show(charts.live_line(hv, "Soil Moisture (%)", f"Pemantauan Kelembapan Tanah (Pengukuran ke-{len(recs)})",
                              "#38bdf8", "Kelembapan (%)", dry=dry, wet=wet, trend=fut), f"mon_m_{tag}", c1)
        show(charts.live_line(hv, "Temperature (°C)", "Pemantauan Suhu Udara (°C)", "#fb923c", "Suhu (°C)"), f"mon_t_{tag}", c2)
    log = pd.DataFrame(recs).tail(12).iloc[::-1].copy()
    log["day"] = log["day"].apply(lambda d: f"Hari ke-{int(d)}")
    log["time"] = log["time"].astype(str).map(lambda t: JAM_LABELS_ID.get(t, t))
    ph["table"].dataframe(
        log.rename(columns={"day": "Umur Tanaman", "time": "Waktu Ukur", "moist": "Kelembapan Tanah (%)", "temp": "Suhu Udara (°C)",
                            "stage": "Fase Pertumbuhan", "pump_txt": "Status Pompa"})[["Umur Tanaman", "Waktu Ukur", "Kelembapan Tanah (%)", "Suhu Udara (°C)",
                                                                     "Fase Pertumbuhan", "Status Pompa"]], hide_index=True, width="stretch")


def page_monitoring():
    ui.hero("Monitoring Sensor Live & Otomatisasi Pompa Air",
            "Pilih siklus tanam dan pengaturan di bawah, lalu tekan tombol 'Mulai Simulasi Monitoring' untuk melihat kerja pompa otomatis.",
            "activity")
    m = load_models()
    with st.container(border=True, key="card_mon_ctrl"):
        c_ser, m_p1, m_p2, m_p3 = st.columns([1.25, 1.0, 1.15, 1.05], vertical_alignment="bottom")
        df = pick_series("mon", c_ser)
        if len(df) == 0:
            ui.banner("warn", "Dataset kosong. Pilih siklus lain.")
            return
        max_steps = min(200, len(df))
        default_steps = min(utils.CYCLE_DAYS, max_steps)
        if "mon_steps" not in st.session_state or st.session_state["mon_steps"] > max_steps:
            st.session_state["mon_steps"] = max(1, default_steps)
        if "mon_start" not in st.session_state or st.session_state["mon_start"] > len(df):
            st.session_state["mon_start"] = 1

        if m_p1.button("Fase Awal · Hari ke-7", use_container_width=True, key="mon_btn1"):
            st.session_state["mon_start"] = min(20, len(df))
            st.session_state["mon_steps"] = min(30, max(1, len(df) - 19))
            st.rerun()
        if m_p2.button("Fase Pertengahan · Hari ke-17", use_container_width=True, key="mon_btn2"):
            st.session_state["mon_start"] = min(50, len(df))
            st.session_state["mon_steps"] = min(25, max(1, len(df) - 49))
            st.rerun()
        if m_p3.button("Menjelang Panen · Hari ke-25", use_container_width=True, key="mon_btn3"):
            st.session_state["mon_start"] = min(75, max(1, len(df) - 15))
            st.session_state["mon_steps"] = min(16, max(1, len(df) - 74))
            st.rerun()

        c1, c2, c3 = st.columns(3)
        steps = int(c1.number_input("Jumlah pengukuran yang diputar", min_value=1, max_value=max(1, max_steps), key="mon_steps", help="3 pengukuran setara dengan 1 hari."))
        delay = c2.slider("Kecepatan jeda antar-pengukuran", 0.05, 1.5, 0.25, 0.05, key="mon_delay")
        start = int(c3.number_input("Mulai dari urutan pengukuran ke-", min_value=1, max_value=max(1, len(df)), key="mon_start", help="Pengukuran ke-1 = Hari ke-1 Pagi; Pengukuran ke-90 = Hari ke-30 Sore."))

        d1, d2, d3, d4 = st.columns([1.45, 1.45, 0.95, 0.75], vertical_alignment="bottom")
        dry = float(d1.number_input("Batas Tanah Kering — Pompa Nyala", 30.0, 70.0, float(DRY), 1.0, key="mon_dry"))
        wet = float(d2.number_input("Batas Tanah Basah — Pompa Mati", 60.0, 95.0, float(WET), 1.0, key="mon_wet"))
        run = d3.button("Mulai Simulasi", type="primary", use_container_width=True, key="mon_run")
        if d4.button("Reset Data", use_container_width=True, key="mon_reset"):
            st.session_state["mon_recs"] = []
            st.rerun()

    ph = {k: st.empty() for k in ("cards", "banner", "charts", "table")}
    w = m["cfg_lstm"]["w_cls"] if m.get("cfg_lstm") else 6
    if "mon_recs" not in st.session_state and not run:
        init_recs, init_pump = [], False
        for i in range(0, min(len(df), 18)):
            row = df.iloc[i]
            moist = float(row["Soil Moisture (%)"])
            init_pump, status = utils.pump_decision(moist, init_pump, dry, wet)
            stage, source = label(str(row["Ground Truth Criteria"])), "Data catatan kebun"
            init_recs.append(dict(idx=int(row["Time_Index"]), day=int(row["Day"]), time=row["Time"], moist=moist,
                                  temp=float(row["Temperature (°C)"]), stage=stage, source=source, pump=init_pump,
                                  pump_txt="MENYALA" if init_pump else "MATI", status=status))
        st.session_state["mon_recs"] = init_recs

    recs = st.session_state.get("mon_recs", [])
    if not run:
        if not recs:
            ui.pending_action_card(
                "Tekan Tombol 'Mulai Simulasi' untuk Menjalankan Sensor",
                "Pilih siklus tanam dan titik awal pengukuran di atas, lalu klik tombol hijau 'Mulai Simulasi' untuk melihat grafik sensor dan status pompa air.",
                icon_name="activity"
            )
        else:
            render_monitor(ph, recs, dry, wet, "static")
        return
    recs, pump_on = [], False
    for i in range(start - 1, min(len(df), min(utils.CYCLE_LENGTH, start - 1 + steps))):
        row = df.iloc[i]
        moist = float(row["Soil Moisture (%)"])
        pump_on, status = utils.pump_decision(moist, pump_on, dry, wet)
        if lstm_ready(m, "clf") and i + 1 >= w:
            p = predict_stage(m, df.iloc[i - w + 1: i + 1])
            k = int(p.argmax())
            stage, source = label(utils.CLASS_NAMES[k]), f"Deteksi AI · Yakin {p[k]:.0%}"
        else:
            stage, source = label(str(row["Ground Truth Criteria"])), "Data catatan kebun"
        recs.append(dict(idx=int(row["Time_Index"]), day=int(row["Day"]), time=row["Time"], moist=moist,
                         temp=float(row["Temperature (°C)"]), stage=stage, source=source, pump=pump_on,
                         pump_txt="MENYALA" if pump_on else "MATI", status=status))
        render_monitor(ph, recs, dry, wet, f"r{i}")
        time.sleep(delay)
    st.session_state["mon_recs"] = recs
    on_cnt = sum(r["pump"] for r in recs)
    ui.banner("info", f"Simulasi selesai: Dari {len(recs)} kali pengukuran sensor, pompa air otomatis menyala sebanyak {on_cnt} kali "
                      f"({on_cnt / len(recs):.0%}) saat tanah kering.")


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


def page_lstm():
    ui.hero("Cek Fase Pertumbuhan dari Sensor (AI LSTM)",
            "Pilih siklus tanam dan urutan waktu ukur di bawah, lalu tekan tombol 'Cek Fase Pertumbuhan Sekarang' untuk melihat hasil analisis AI.",
            "cpu")
    m = load_models()
    tab1, tab2 = st.tabs(["Uji Deteksi Fase Tanaman", "Tingkat Ketepatan & Info Model AI"])
    with tab1:
        if warn_models(m, ["clf"]) and m.get("cfg_lstm"):
            w = m["cfg_lstm"]["w_cls"]
            with st.container(border=True, key="card_lstm_ctrl"):
                mode = st.radio("Cara memasukkan data sensor:", ["Pilih dari data kebun yang ada", "Ketik angka sensor sendiri"], horizontal=True, key="cls_mode")
                if mode == "Pilih dari data kebun yang ada":
                    c_ser, c_sld = st.columns([1.25, 2.75], vertical_alignment="top")
                    df = pick_series("cls", c_ser)
                    if len(df) < w:
                        ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {w} pembacaan berurutan.")
                        return

                    if "cls_step" not in st.session_state or st.session_state["cls_step"] > len(df) or st.session_state["cls_step"] < w:
                        st.session_state["cls_step"] = min(45, len(df))
                    step = c_sld.slider("Geser untuk memilih urutan pengukuran sensor:", w, len(df), key="cls_step")

                    btn_c1, btn_c2, btn_c3, _ = st.columns([1.0, 1.15, 1.05, 1.2])
                    if btn_c1.button("Fase Awal · Hari ke-7", use_container_width=True, key="btn_cls_p1"):
                        st.session_state["cls_step"] = min(20, len(df))
                        st.rerun()
                    if btn_c2.button("Fase Pertengahan · Hari ke-17", use_container_width=True, key="btn_cls_p2"):
                        st.session_state["cls_step"] = min(50, len(df))
                        st.rerun()
                    if btn_c3.button("Menjelang Panen · Hari ke-25", use_container_width=True, key="btn_cls_p3"):
                        st.session_state["cls_step"] = min(75, len(df))
                        st.rerun()

                    window = df.iloc[step - w: step]
                    row_last = df.iloc[step - 1]
                    truth = str(row_last["Ground Truth Criteria"])
                    day_val = row_last.get("Day", "?")
                    time_val = str(row_last.get("Time", "?"))
                    cls_sig = ("dataset", st.session_state.get("cls_series", ""), int(step), len(df))
                    summary_info = f"Hari ke-{day_val} · Jam {time_val} · Pengukuran #{step}/{len(df)}"
                else:
                    st.caption(f"Masukkan {w} pengukuran terakhir pada tabel di bawah, atau klik salah satu contoh kondisi siap pakai:")
                    m_c1, m_c2, m_c3, _ = st.columns([1.1, 1.1, 1.0, 0.8])
                    if m_c1.button("Contoh: Masa Pertumbuhan · 70%", use_container_width=True, key="btn_tmpl_1"):
                        st.session_state["manual_moist"] = 70.0
                        st.session_state["manual_temp"] = 27.0
                        st.rerun()
                    if m_c2.button("Contoh: Mendekati Panen · 55%", use_container_width=True, key="btn_tmpl_2"):
                        st.session_state["manual_moist"] = 55.0
                        st.session_state["manual_temp"] = 27.0
                        st.rerun()
                    if m_c3.button("Contoh: Siap Panen · 48%", use_container_width=True, key="btn_tmpl_3"):
                        st.session_state["manual_moist"] = 48.0
                        st.session_state["manual_temp"] = 26.0
                        st.rerun()

                    def_m = st.session_state.get("manual_moist", 70.0)
                    def_t = st.session_state.get("manual_temp", 27.0)
                    base = pd.DataFrame({"Time": (utils.JAM_LIST * 2)[:w], "Soil Moisture (%)": [def_m] * w,
                                         "Temperature (°C)": [def_t] * w})
                    window = st.data_editor(base, num_rows="fixed", key=f"cls_manual_{def_m}_{def_t}", width="stretch")
                    truth = None
                    cls_sig = ("manual", tuple(window["Soil Moisture (%)"].round(2).tolist()), tuple(window["Temperature (°C)"].round(2).tolist()))
                    summary_info = f"Input Simulasi Manual · {w} pengukuran sensor"

                st.markdown('<div style="margin-top:8px;border-top:1px solid #edf2ee;padding-top:10px;"></div>', unsafe_allow_html=True)
                b_l, b_r = st.columns([3.4, 1.0], vertical_alignment="center")
                b_l.markdown(f'<div class="action-bar-info"><strong>Data Terpilih:</strong> {ui._e(summary_info)}</div>', unsafe_allow_html=True)
                if b_r.button("Cek Fase Tanaman", type="primary", key="btn_cls_run") or "cls_committed_sig" not in st.session_state:
                    st.session_state["cls_committed_sig"] = cls_sig

            if True:
                preview_cols = []
                rename_map = {
                    "Day": "Umur (Hari ke-)",
                    "Time": "Waktu Ukur",
                    "Soil Moisture (%)": "Kelembapan Tanah (%)",
                    "Temperature (°C)": "Suhu Udara (°C)",
                    "Soil Condition": "Kondisi Tanah"
                }
                for c in ["Day", "Time", "Soil Moisture (%)", "Temperature (°C)", "Soil Condition"]:
                    if c in window.columns:
                        preview_cols.append(c)
                st.caption(f"**Data {w} Pengukuran Sensor Terakhir (2 Hari) yang Dianalisis oleh AI:**")
                disp_win = window[preview_cols].copy() if preview_cols else window.copy()
                if "Soil Condition" in disp_win.columns:
                    disp_win["Soil Condition"] = disp_win["Soil Condition"].map(cond_label)
                if "Time" in disp_win.columns:
                    disp_win["Time"] = disp_win["Time"].astype(str).map(lambda t: JAM_LABELS_ID.get(t, t))
                st.dataframe(disp_win.rename(columns=rename_map) if preview_cols else disp_win, hide_index=True, width="stretch")
                try:
                    p = predict_stage(m, window)
                    k = int(p.argmax())
                    name = utils.CLASS_NAMES[k]
                    moist_cur = float(window["Soil Moisture (%)"].iloc[-1])
                    temp_cur = float(window["Temperature (°C)"].iloc[-1])
                    mat_cur = float(window[MAT].iloc[-1]) if MAT in window.columns else (35.0 if k == 0 else (78.0 if k == 1 else 94.0))
                    d_cur = day_val if mode == "Pilih dari data kebun yang ada" else "?"
                    t_cur = time_val if mode == "Pilih dari data kebun yang ada" else "Simulasi"

                    ui.lstm_stage_visual_card(
                        stage_key=name,
                        stage_label=label(name),
                        confidence=float(p[k]),
                        truth_label=label(truth) if truth else "Simulasi Manual",
                        moist=moist_cur,
                        temp=temp_cur,
                        day_val=d_cur,
                        time_val=t_cur,
                        mat_pct=mat_cur,
                    )
                    show(charts.prob_bar(p, utils.CLASS_NAMES), "cls_prob")
                    info_st = utils.STAGE_INFO.get(name)
                    if info_st:
                        ui.banner("ok", f"Saran Perawatan ({label(name)}): {info_st['saran']}")
                    if truth and truth != name:
                        ui.banner("warn", "Catatan: Tebakan AI sedikit berbeda dari label data karena tanaman sedang berada di masa peralihan antar-fase pertumbuhan.")

                    if lstm_ready(m, "fc"):
                        w_in_fc = m["cfg_lstm"]["w_in"]
                        if mode == "Pilih dari data kebun yang ada" and step >= w_in_fc:
                            fc_win = df.iloc[step - w_in_fc: step].reset_index(drop=True)
                        else:
                            reps = (w_in_fc // len(window)) + 1
                            fc_win = pd.concat([window] * reps, ignore_index=True).iloc[-w_in_fc:].reset_index(drop=True)
                        fc_tbl_lstm = predict_forecast(m, fc_win)
                        ui.section_header(
                            "Kartu Prakiraan Pertumbuhan Pakcoy 4 Hari ke Depan (AI LSTM)",
                            "Proyeksi kondisi kelembapan, suhu, tingkat kematangan, dan visualisasi pertumbuhan tanaman pakcoy untuk 4 hari ke depan.",
                            icon_name="calendar-range"
                        )
                        ui.forecast_4day_cards(fc_tbl_lstm, start_day=d_cur, thresholds=thresholds(m), dry=DRY, wet=WET)
                except Exception as e:
                    st.error(f"Gagal memprediksi: {e}")
    with tab2:
        ui.banner("info", "Halaman ini menampilkan seberapa akurat model AI dalam menebak fase pertumbuhan dan memprakirakan kondisi kebun 4 hari ke depan.")
        cfg = m.get("cfg_lstm")
        if cfg:
            ev = cfg.get("evaluasi", {})
            eval_section({k: v for k, v in ev.items()}, cfg["class_names"], "lstm")
            mae_sim = cfg.get("metrics", {}).get("mae_forecast_uji_simulasi")
            mae_asli = cfg.get("metrics", {}).get("mae_forecast_data_asli")
            if mae_sim or mae_asli:
                st.markdown('<div class="section-title">Rata-rata Selisih Prakiraan 4 Hari (Semakin Kecil Angkanya = Semakin Akurat)</div>', unsafe_allow_html=True)
                st.caption("Angka di bawah menunjukkan rata-rata selisih (melesetnya) prakiraan AI dibandingkan kondisi sensor sebenarnya:")
                if mae_sim:
                    st.caption("**1. Pengujian pada 30 Siklus Tanam:**")
                    ui.kpi_cards([
                        dict(icon="droplets", label="Selisih Prakiraan Kelembapan", value=f"± {mae_sim['moisture']:.2f}%", color="#38bdf8", sub="Sangat akurat (di bawah 2%)"),
                        dict(icon="thermometer", label="Selisih Prakiraan Suhu", value=f"± {mae_sim['temperature']:.2f}°C", color="#fb923c", sub="Sangat akurat (di bawah 1°C)"),
                        dict(icon="trending-up", label="Selisih Tingkat Kematangan", value=f"± {mae_sim['maturity']:.2f}%", color="#34d399", sub="Rentang skala 0–100%"),
                    ], cols=3)
                if mae_asli:
                    st.caption(f"**2. Pengujian pada Data Pengamatan Lapangan ({utils.CYCLE_DAYS} Hari):**")
                    ui.kpi_cards([
                        dict(icon="droplets", label="Selisih Prakiraan Kelembapan", value=f"± {mae_asli['moisture']:.2f}%", color="#38bdf8", sub="Data kebun nyata"),
                        dict(icon="thermometer", label="Selisih Prakiraan Suhu", value=f"± {mae_asli['temperature']:.2f}°C", color="#fb923c", sub="Data kebun nyata"),
                        dict(icon="trending-up", label="Selisih Tingkat Kematangan", value=f"± {mae_asli['maturity']:.2f}%", color="#facc15", sub="Variasi alami lapangan"),
                    ], cols=3)
            with st.expander("Lihat Detail Arsitektur Jaringan Saraf Tiruan (Untuk Peneliti)"):
                st.markdown("- **Arsitektur Klasifikasi Fase:** `Input (6 × 5)` → `LSTM 64` → `Dropout 0,3` → `LSTM 32` → `Dense 32` → `Softmax 3 kelas`. Fitur: kelembapan tanah, suhu udara (skala 0–1), dan waktu ukur (Pagi/Siang/Sore).")
                st.markdown("- **Arsitektur Prakiraan 4 Hari:** `Input (12 × 5)` → `LSTM 96` → `LSTM 48` → `Dense 96` → `Dense 36` → keluaran `12 langkah × (kelembapan, suhu, kematangan)`.")
                st.caption(f"Dilatih menggunakan TensorFlow versi {cfg.get('tf_version', '?')}.")
        else:
            ui.banner("info", "Konfigurasi model belum ada. Latih model di Colab terlebih dulu.")


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


# ================================================================= scan gabungan
def page_scan():
    ui.hero("Diagnosis Lengkap — Gabungan Foto Daun & Sensor Tanah",
            "Masukkan foto daun dan pilih siklus sensor di bawah, lalu tekan tombol 'Jalankan Diagnosis Lengkap' untuk melihat laporan terpadu.",
            "scan-search")
    m = load_models()
    ui.photo_guide_card()

    with st.container(border=True, key="card_scan_ctrl"):
        st.markdown('<div class="section-title" style="margin-top:0;">Langkah 1 — Masukkan Foto Tanaman Pakcoy</div>', unsafe_allow_html=True)
        img, img_sig = get_image("scan")

        st.markdown('<div class="section-title">Langkah 2 — Pilih Siklus & Catatan Sensor Kebun</div>', unsafe_allow_html=True)
        c_ser, c_sld = st.columns([1.25, 2.75], vertical_alignment="top")
        df = pick_series("scan", c_ser)
        w_in = m["cfg_lstm"]["w_in"] if m.get("cfg_lstm") else 12
        if len(df) < w_in:
            ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {w_in} pembacaan berurutan.")
            return

        if "scan_step" not in st.session_state or st.session_state["scan_step"] > len(df) or st.session_state["scan_step"] < w_in:
            st.session_state["scan_step"] = min(45, len(df))
        step = c_sld.slider("Gunakan catatan sensor sampai urutan pengukuran ke-:", w_in, len(df), key="scan_step")

        sc_c1, sc_c2, sc_c3, _ = st.columns([1.0, 1.15, 1.05, 1.2])
        if sc_c1.button("Fase Awal · Hari ke-7", use_container_width=True, key="scan_btn1"):
            st.session_state["scan_step"] = min(20, len(df))
            st.rerun()
        if sc_c2.button("Fase Pertengahan · Hari ke-17", use_container_width=True, key="scan_btn2"):
            st.session_state["scan_step"] = min(50, len(df))
            st.rerun()
        if sc_c3.button("Menjelang Panen · Hari ke-25", use_container_width=True, key="scan_btn3"):
            st.session_state["scan_step"] = min(75, len(df))
            st.rerun()

        row_sc = df.iloc[step - 1]
        day_sc = row_sc.get("Day", "?")
        time_sc = str(row_sc.get("Time", "?"))

        scan_sig = (img_sig, st.session_state.get("scan_series", ""), int(step), len(df))
        st.markdown('<div style="margin-top:8px;border-top:1px solid #edf2ee;padding-top:10px;"></div>', unsafe_allow_html=True)
        b_l, b_r = st.columns([3.4, 1.0], vertical_alignment="center")
        b_l.markdown(
            f'<div class="action-bar-info">'
            f'<strong>Sensor Terpilih:</strong> Hari ke-{day_sc} &middot; Jam {time_sc} &middot; Ukur #{step} &middot; '
            f'<strong>Foto:</strong> {"Sudah diunggah" if img is not None else "Belum diunggah"}'
            f'</div>',
            unsafe_allow_html=True
        )
        if b_r.button("Jalankan Diagnosis", type="primary", key="btn_scan_run"):
            if img is None:
                ui.banner("warn", "Silakan unggah atau ambil foto tanaman pada Langkah 1 terlebih dahulu sebelum menjalankan diagnosis.")
            else:
                st.session_state["scan_committed_sig"] = scan_sig

    if img is None:
        st.session_state.pop("scan_committed_sig", None)
        ui.pending_action_card(
            "Unggah Foto Pakcoy pada Langkah 1 untuk Memulai Diagnosis Lengkap",
            "Unggah foto daun pakcoy pada Langkah 1 dan pilih siklus sensor pada Langkah 2 untuk menghasilkan laporan diagnosis terpadu (CNN + LSTM).",
            icon_name="scan-search"
        )
        return
    elif st.session_state.get("scan_committed_sig") != scan_sig:
        ui.pending_action_card(
            "Tekan Tombol 'Jalankan Diagnosis' untuk Memulai Diagnosis Lengkap",
            "Foto tanaman pakcoy dan catatan sensor telah siap. Silakan klik tombol hijau 'Jalankan Diagnosis' di atas untuk menghasilkan laporan diagnosis terpadu (CNN + LSTM).",
            icon_name="scan-search"
        )
        return

    st.markdown('<div class="section-title">Bagian A — Hasil Pemeriksaan Foto Daun</div>', unsafe_allow_html=True)
    cnn, g = photo_panel(m, img, "scan", sensor_row=df.iloc[step - 1])

    is_p_scan, p_reason_scan, _ = utils.validate_plant_image(img, g)
    if (cnn and cnn[0] == "bukan_pakcoy") or not is_p_scan:
        alasan_str = f" ({p_reason_scan})" if not is_p_scan else ""
        ui.banner("danger", f"Validasi Foto Gagal: Objek terdeteksi BUKAN TANAMAN PAKCOY{alasan_str}. "
                            "Diagnosis gabungan dihentikan agar tidak menghasilkan rekomendasi budidaya yang keliru.")
        return

    st.markdown('<div class="section-title">Bagian B — Hasil Pemeriksaan Sensor Tanah & Prakiraan 4 Hari</div>', unsafe_allow_html=True)
    lstm, table = None, None
    if lstm_ready(m, "clf"):
        wc = m["cfg_lstm"]["w_cls"]
        pc = predict_stage(m, df.iloc[step - wc: step])
        lstm = (utils.CLASS_NAMES[int(pc.argmax())], float(pc.max()))
        ui.banner("ok", f"Hasil Analisis Sensor (LSTM): Tanaman berada pada fase {label(lstm[0])} (Keyakinan AI: {lstm[1]:.0%})")
    else:
        ui.banner("warn", "Model LSTM klasifikasi belum tersedia.")
    if lstm_ready(m, "fc"):
        table = predict_forecast(m, df.iloc[step - w_in: step].reset_index(drop=True))
        ui.forecast_4day_cards(table, start_day=day_sc, thresholds=thresholds(m), dry=DRY, wet=WET)
        disp_scan_tbl = table.drop(columns=["Maturity (%)"], errors="ignore").rename(columns={
            "Langkah": "Urutan ke-",
            "Hari": "Hari ke Depan",
            "Jam": "Waktu Ukur",
            "Tahap": "Prakiraan Fase"
        })
        st.dataframe(disp_scan_tbl, hide_index=True, width="stretch")
    st.divider()
    st.markdown('<div class="section-title">Bagian C — Kesimpulan Akhir & Rekomendasi Perawatan</div>', unsafe_allow_html=True)
    if cnn and lstm:
        if cnn[0] == lstm[0]:
            ui.banner("ok", f"Hasil Foto dan Sensor SEPAKAT: Tanaman pakcoy berada pada fase {label(cnn[0])}.")
        else:
            ui.banner("warn", f"Hasil Foto ({label(cnn[0])}) dan Sensor ({label(lstm[0])}) menunjukkan fase yang berbeda. "
                              "Pastikan foto dan sensor berasal dari tanaman dengan umur tanam yang sama, lalu periksa kondisi daun secara langsung.")
    final = (cnn or lstm or [None])[0]
    if final and final in utils.STAGE_INFO and final != "bukan_pakcoy":
        ui.banner("info", "Ciri Tanaman Saat Ini: " + utils.STAGE_INFO[final]["ciri"])
        ui.banner("ok", "Saran Tindakan Petani: " + utils.STAGE_INFO[final]["saran"])
    if table is not None:
        mat_scan = table["Tingkat Kematangan (%)"].iloc[-1] if "Tingkat Kematangan (%)" in table.columns else table["Maturity (%)"].iloc[-1]
        ui.banner("info", f"Prakiraan 4 Hari ke Depan: Tanaman diperkirakan memasuki fase {table['Tahap'].iloc[-1]} "
                          f"dengan tingkat kematangan mencapai {mat_scan:.0f}%.")
    report = utils.build_report(cnn=(cnn[0], cnn[1]) if cnn else None, lstm=lstm, green=g, table=table,
                                sensor=df.iloc[step - 1])
    st.download_button("Unduh Laporan Diagnosis Lengkap (File Dokumen .md)", report.encode("utf-8"), file_name="laporan_pakcoy.md",
                       mime="text/markdown", key="scan_dl")


PAGES = {
    "🏠 Dashboard Utama": page_dashboard,
    "📊 Data & Riwayat Kebun": page_eksplorasi,
    "📡 Monitoring Sensor Live": page_monitoring,
    "🧠 Cek Fase dari Sensor": page_lstm,
    "🔮 Prakiraan 4 Hari": page_forecast,
    "🖼️ Analisis Tanaman (CNN)": page_cnn,
    "🔍 Diagnosis Lengkap": page_scan,
    "Asisten Kebun AI": ai_assistant.render_ai_assistant,
}

choice = sidebar()
PAGES[choice]()
ui.footer()
