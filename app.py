"""Smart Farming Pakcoy: dashboard realtime, eksplorasi data, monitoring sensor, LSTM, prediksi 4 hari,
CNN (scan foto), dan scan gabungan."""
import hashlib
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

import charts
import ui
import utils
import ai_assistant
import auth

st.set_page_config(page_title="Smart Farming Pakcoy", page_icon=":material/eco:", layout="wide", initial_sidebar_state="expanded")
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
    sim = pd.read_csv(DATA_DIR / "data_training.csv")
    asli = pd.read_csv(DATA_DIR / "data_asli.csv")
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


def label(name):
    return utils.CLASS_LABELS.get(name, name)


def show(fig, key, container=None):
    (container or st).plotly_chart(fig, key=key)


def get_sources():
    sim, asli = load_builtin()
    src = {
        "Siklus Perkembangan Tanaman Pakcoy (30 Siklus)": sim,
        "Data Asli Pengamatan Lapangan (1 Siklus)": asli
    }
    up = st.session_state.get("upload_df")
    if up is not None:
        src[f"Dataset unggahan ({st.session_state.get('upload_name', '')})"] = up
    return src


def pick_dataset(key):
    sim, asli = load_builtin()
    up = st.session_state.get("upload_df")
    
    col_src, col_opt = st.columns([1, 2])
    src_choices = ["Siklus Perkembangan Tanaman Pakcoy (30 Siklus)", "Data Asli Pengamatan Lapangan (1 Siklus)"]
    if up is not None:
        src_choices.append(f"Dataset unggahan ({st.session_state.get('upload_name', '')})")
    
    src_name = col_src.selectbox("Sumber data", src_choices, key=f"{key}_src")
    
    if src_name == "Siklus Perkembangan Tanaman Pakcoy (30 Siklus)":
        df = sim
        all_cycles = sorted(df["Cycle_ID"].unique().tolist())
        mode = col_opt.radio(
            "Tampilkan siklus:",
            ["Semua Siklus (1–30)", "Pilih Bebas Beberapa Siklus", "Pilih 1 Siklus Tertentu"],
            horizontal=True,
            key=f"{key}_cyc_mode"
        )
        if mode == "Pilih Bebas Beberapa Siklus":
            selected = st.multiselect(
                "Pilih satu atau beberapa siklus perkembangan pakcoy yang ingin dilihat:",
                options=all_cycles,
                default=[1, 2, 3],
                format_func=lambda c: f"Siklus ke-{c}",
                key=f"{key}_multi_cycles"
            )
            if not selected:
                st.warning("Silakan pilih minimal 1 siklus.")
                selected = [1]
            df = df[df["Cycle_ID"].isin(selected)]
            st.caption(f"📊 Menampilkan **{len(selected)} siklus terpilih** ({', '.join(f'Siklus {c}' for c in selected)}) — Total: {len(df):,} baris data.")
        elif mode == "Pilih 1 Siklus Tertentu":
            selected_one = st.selectbox(
                "Pilih 1 siklus perkembangan pakcoy yang ingin dilihat:",
                options=all_cycles,
                index=0,
                format_func=lambda c: f"Siklus ke-{c} (Masa Pertumbuhan hingga Siap Panen)",
                key=f"{key}_single_cycle"
            )
            df = df[df["Cycle_ID"] == selected_one]
            st.caption(f"🌱 Menampilkan data **Siklus ke-{selected_one}** ({len(df)} pembacaan sensor selama 40 hari).")
        else:
            st.caption(f"📊 Menampilkan seluruh **30 Siklus Perkembangan Tanaman Pakcoy** ({len(df):,} baris data).")
        return src_name, df
    elif src_name == "Data Asli Pengamatan Lapangan (1 Siklus)":
        st.caption("🌱 Menampilkan data asli hasil pengamatan budidaya lapangan (1 siklus, 40 hari, 120 pembacaan).")
        return src_name, asli
    else:
        return src_name, up


def pick_series(key):
    sim, asli = load_builtin()
    up = st.session_state.get("upload_df")
    
    options = {}
    for c in sorted(sim["Cycle_ID"].unique()):
        options[f"Siklus ke-{c} (Masa Pertumbuhan hingga Siap Panen)"] = sim[sim["Cycle_ID"] == c]
    options["Data Asli Pengamatan Lapangan (1 Siklus - 40 Hari)"] = asli
    if up is not None:
        options[f"Dataset Unggahan ({st.session_state.get('upload_name', '')})"] = up

    labels = list(options.keys())
    default_idx = 1 if len(labels) > 1 else 0
    choice = st.selectbox("Pilih Siklus Perkembangan Tanaman yang Dipantau:", labels, index=default_idx, key=f"{key}_series")
    df = options[choice]
    
    if "Siklus ke-" in choice:
        c_name = choice.split("(")[0].strip()
        st.caption(f"🌱 **{c_name}**: Rekam data perkembangan tanaman pakcoy lengkap mulai dari awal pertumbuhan bibit (DAP 10) hingga masa siap panen (DAP 49).")
    elif "Data Asli" in choice:
        st.caption("🌱 **Data Lapangan**: 40 hari pengamatan sensor kelembapan dan suhu langsung di lapangan.")
        
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
    sb.markdown('<div class="brand"><span class="brand-icon-box">' + ui.icon("sprout", 20, color="var(--primary)") +
                '</span><span>Smart Farming Pakcoy</span></div>'
                '<div class="brand-sub">Monitoring &amp; klasifikasi AI untuk budidaya pakcoy</div>',
                unsafe_allow_html=True)

    sb.markdown('<div class="micro-cap">MENU</div>', unsafe_allow_html=True)
    choice = sb.radio("Menu", list(PAGES.keys()), label_visibility="collapsed", format_func=ui.strip_emoji)

    m = load_models()

    sb.markdown('<div class="micro-cap">DATA</div>', unsafe_allow_html=True)
    f = sb.file_uploader("Ganti dataset (opsional, .xlsx)", type=["xlsx"], key="upl")
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

    if sb.button("Muat ulang model", key="reload_models"):
        _load_models_cached.clear()
        st.rerun()

    sb.divider()
    auth.render_sidebar_user_profile()
    sb.caption("Smart Farming Pakcoy · CNN + LSTM")
    return choice


# ================================================================= dashboard
@st.fragment(run_every=1.5)
def live_panel():
    """Panel yang menyegarkan diri otomatis: grafik bergerak mengikuti pembacaan sensor."""
    df = st.session_state.get("live_df")
    if df is None or len(df) == 0:
        return
    n = len(df)
    i = int(st.session_state.get("live_i", 0))
    if st.session_state.get("live_on", True):
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
        tahap, sumber = f"{label(utils.CLASS_NAMES[k])}", f"LSTM · {p[k]:.0%}"
    else:
        tahap, sumber = label(str(row["Ground Truth Criteria"])), "label data"
    cond_color = {"Optimal": "#34d399", "Dry": "#fb923c", "Wet": "#60a5fa"}.get(str(row["Soil Condition"]), "#e8ecf4")

    ui.kpi_cards([
        dict(icon="calendar", label="Hari / jam", value=f"Hari {int(row['Day'])} · {row['Time']}", color="#a78bfa"),
        dict(icon="droplets", label="Kelembapan tanah", value=f"{row['Soil Moisture (%)']:.0f}%", color="#38bdf8"),
        dict(icon="thermometer", label="Suhu", value=f"{row['Temperature (°C)']:.1f}°C", color="#fb923c"),
        dict(icon="sprout", label="Kondisi tanah", value=str(row["Soil Condition"]), color=cond_color),
        dict(icon="trending-up", label="Tingkat Kematangan", value=f"{row[MAT]:.0f}%", color="#34d399", sub="skala 0–100%"),
        dict(icon="cpu", label="Tahap", value=tahap, color="#e8ecf4", sub=sumber),
    ])
    c1, c2 = st.columns(2)
    show(charts.live_line(hist, "Soil Moisture (%)", "Kelembapan tanah (%)", "#38bdf8", "%", dry=DRY, wet=WET),
         f"lv_m_{i}", c1)
    show(charts.live_line(hist, "Temperature (°C)", "Suhu (°C)", "#fb923c", "°C"), f"lv_t_{i}", c2)
    c3, c4 = st.columns([1, 2])
    show(charts.gauge(row[MAT], "Tingkat Kematangan Tanaman (%)", th), f"lv_g_{i}", c3)
    show(charts.growth_curve(grow, th), f"lv_c_{i}", c4)
    st.progress((i + 1) / n, text=f"Siklus tanam: pembacaan {i + 1} dari {n}")


def live_section():
    left, right = st.columns([3, 1])
    left.markdown('<div class="section-title">Grafik Realtime Perkembangan Pakcoy</div>', unsafe_allow_html=True)
    with right:
        ui.live_badge(st.session_state.get("live_on", True))
    st.caption("Grafik bergerak otomatis. Mode demo: data diputar ulang seperti sensor langsung.")
    df = pick_series("live")
    c1, c2 = st.columns(2)
    c1.toggle("Jalankan realtime", value=True, key="live_on")
    c2.selectbox("Kecepatan (pembacaan per tick)", [1, 2, 3], key="live_step")
    sig = (len(df), int(df["Cycle_ID"].iloc[0]), float(df["Soil Moisture (%)"].sum()))
    if st.session_state.get("live_sig") != sig:
        st.session_state["live_sig"] = sig
        st.session_state["live_i"] = 0
    st.session_state["live_df"] = df
    live_panel()


def page_dashboard():
    ui.hero("Smart Farming Pakcoy — Dashboard",
            "Sistem monitoring kelembapan tanah, suhu, dan kesiapan panen tanaman pakcoy berbasis AI (LSTM dan CNN).",
            "layout-dashboard")
    name, df = pick_dataset("dash")
    ui.kpi_cards([
        dict(icon="database", label="Total Data", value=f"{len(df):,}", color="#60a5fa"),
        dict(icon="droplets", label="Rata-rata Kelembapan", value=f"{df['Soil Moisture (%)'].mean():.1f}%", color="#38bdf8"),
        dict(icon="thermometer", label="Rata-rata Suhu", value=f"{df['Temperature (°C)'].mean():.1f}°C", color="#fb923c"),
        dict(icon="trending-up", label="Rata-rata Kematangan", value=f"{df[MAT].mean():.1f}%", color="#34d399", sub="seluruh siklus"),
        dict(icon="calendar", label="Rentang HST (DAP)", value=f"{int(df['DAP'].min())}–{int(df['DAP'].max())} hari",
             color="#a78bfa"),
    ])
    st.caption("💡 **Tingkat Kematangan Tanaman (%):** Indeks persentase perkembangan fisiologis tanaman pakcoy menuju masa panen: "
               "**Masa Pertumbuhan** (<66.5%), **Mendekati Panen** (66.5–89.0%), dan **Siap Panen** (≥89.0%).")
    st.divider()
    live_section()
    st.divider()
    c1, c2 = st.columns(2)
    show(charts.donut_condition(df), "d_donut", c1)
    show(charts.bar_stage(df), "d_bar", c2)
    show(charts.maturity_curve(df), "d_mat")
    st.markdown('<div class="section-title">Cuplikan Data</div>', unsafe_allow_html=True)
    st.dataframe(df[utils.REQUIRED_COLS].head(10), hide_index=True)


# ================================================================= eksplorasi
def style_table(d):
    try:
        return _style_table(d)
    except Exception:
        return d


def _style_table(d):
    def color(v):
        return {"Wet": "background-color:rgba(102,94,253,.12);color:#533afd;font-weight:600",
                "Optimal": "background-color:rgba(0,135,90,.10);color:#00875a;font-weight:600",
                "Dry": "background-color:rgba(234,34,97,.10);color:#ea2261;font-weight:600"}.get(v, "")
    sty = d.style
    fn = getattr(sty, "map", None) or sty.applymap
    sty = fn(color, subset=["Soil Condition"])
    return sty.format({"Temperature (°C)": "{:.1f}", "Soil Moisture (%)": "{:.0f}"})


def page_eksplorasi():
    ui.hero("Eksplorasi Dataset Pakcoy",
            "Filter, telusuri, dan pahami pola kelembapan, suhu, dan tahap pertumbuhan.",
            "bar-chart-3")
    name, df = pick_dataset("eks")
    dmin, dmax = int(df["DAP"].min()), int(df["DAP"].max())
    with st.expander("Filter Data"):
        c1, c2, c3 = st.columns(3)
        f_stage = c1.multiselect("Tahap pertumbuhan", utils.CLASS_NAMES, default=utils.CLASS_NAMES,
                                 format_func=label, key="eks_stage")
        f_cond = c2.multiselect("Kondisi tanah", ["Wet", "Optimal", "Dry"], default=["Wet", "Optimal", "Dry"],
                                key="eks_cond")
        f_jam = c3.multiselect("Jam pengukuran", utils.JAM_LIST, default=utils.JAM_LIST, key="eks_jam")
        if dmin < dmax:
            f_dap = st.slider("Rentang DAP (hari)", dmin, dmax, (dmin, dmax), key=f"eks_dap_{dmin}_{dmax}")
        else:
            f_dap = (dmin, dmax)
    fdf = df[df["Ground Truth Criteria"].isin(f_stage) & df["Soil Condition"].isin(f_cond)
             & df["Time"].isin(f_jam) & df["DAP"].between(f_dap[0], f_dap[1])]
    ui.banner("info", f"Menampilkan {len(fdf):,} dari {len(df):,} baris data sesuai filter.")
    if len(fdf) == 0:
        st.warning("Tidak ada data yang cocok dengan filter.")
        return
    shown = fdf[utils.REQUIRED_COLS].head(300)
    st.dataframe(style_table(shown), hide_index=True)
    if len(fdf) > 300:
        st.caption("Menampilkan 300 baris pertama. Unduh CSV untuk data lengkap hasil filter.")
    st.download_button("Unduh data hasil filter (CSV)", fdf.to_csv(index=False).encode("utf-8"),
                       file_name="data_pakcoy_filter.csv", mime="text/csv", key="eks_dl")
    c1, c2, c3 = st.columns(3)
    show(charts.hist_moisture(fdf, DRY, WET), "e_hist", c1)
    show(charts.scatter_moist_temp(fdf), "e_scatter", c2)
    show(charts.box_temp_stage(fdf), "e_box", c3)

    shares = fdf["Soil Condition"].value_counts(normalize=True).reindex(["Wet", "Optimal", "Dry"]).fillna(0)
    if shares.min() < 0.10:
        ui.banner("warn", "Kondisi tanah Dry dan Wet jumlahnya sedikit dibanding Optimal (data tidak seimbang). "
                          "Perhatikan hal ini saat menilai akurasi model klasifikasi kondisi tanah.")
    r = fdf[utils.SENSOR_COLS].corr().iloc[0, 1]
    ui.banner("info", f"Korelasi kelembapan dan suhu pada data terfilter: {r:.2f}.")
    with st.expander("Statistik deskriptif"):
        st.dataframe(fdf[utils.SENSOR_COLS + [MAT]].describe().round(2))
        st.dataframe(fdf.groupby("Ground Truth Criteria")[utils.SENSOR_COLS + [MAT]].mean().round(2))


# ================================================================= monitoring realtime
def render_monitor(ph, recs, dry, wet, tag):
    if not recs:
        ph["banner"].markdown(ui.banner_html("info", "Klik Jalankan Monitoring untuk memulai monitoring."),
                              unsafe_allow_html=True)
        return
    h = pd.DataFrame(recs).set_index("idx")
    last = recs[-1]
    slope, fut = utils.linear_trend(h["moist"].tail(6).values, 5)
    trend_txt = "turun" if slope < -0.05 else ("naik" if slope > 0.05 else "stabil")
    trend_icon = "trending-down" if slope < -0.05 else ("trending-up" if slope > 0.05 else "activity")
    pump_txt = "MENYALA" if last["pump"] else "MATI"
    pump_color = "#fb923c" if last["pump"] else "#34d399"
    ph["cards"].markdown(ui.kpi_html([
        dict(icon="droplets", label="Kelembapan tanah", value=f"{last['moist']:.0f}%", color="#38bdf8"),
        dict(icon="thermometer", label="Suhu udara", value=f"{last['temp']:.1f}°C", color="#fb923c"),
        dict(icon="cpu", label="Klasifikasi tahap", value=last["stage"], color="#e8ecf4", sub=last["source"]),
        dict(icon=trend_icon, label="Tren regresi (6 terakhir)", value=f"{slope:+.2f} %/baca ({trend_txt})", color="#facc15",
             sub=f"perkiraan berikutnya {fut[0]:.1f}%"),
        dict(icon="zap", label="Pompa air", value=pump_txt, color=pump_color),
    ]), unsafe_allow_html=True)
    status = last["status"]
    if status in ("dry", "recovering"):
        text = (f"POMPA MENYALA (tanah kering: {last['moist']:.0f}% di bawah batas {dry:.0f}%)" if status == "dry"
                else f"POMPA MASIH MENYALA (kelembapan {last['moist']:.0f}% belum pulih melewati batas aman)")
        ph["banner"].markdown(ui.banner_html("danger", text), unsafe_allow_html=True)
    elif status == "wet":
        ph["banner"].markdown(ui.banner_html("warn", f"Tanah terlalu basah ({last['moist']:.0f}% ≥ {wet:.0f}%). "
                                                      "Pompa mati, periksa drainase."), unsafe_allow_html=True)
    else:
        ph["banner"].markdown(ui.banner_html("ok", f"Kelembapan {last['moist']:.0f}% dalam rentang aman. Pompa mati."),
                              unsafe_allow_html=True)
    hv = pd.DataFrame({"Soil Moisture (%)": h["moist"], "Temperature (°C)": h["temp"]}).tail(60)
    with ph["charts"].container():
        c1, c2 = st.columns(2)
        show(charts.live_line(hv, "Soil Moisture (%)", f"Monitoring Kelembapan Realtime — Log ke-{len(recs)}",
                              "#38bdf8", "%", dry=dry, wet=wet, trend=fut), f"mon_m_{tag}", c1)
        show(charts.live_line(hv, "Temperature (°C)", "Suhu udara (°C)", "#fb923c", "°C"), f"mon_t_{tag}", c2)
    log = pd.DataFrame(recs).tail(12).iloc[::-1]
    ph["table"].dataframe(
        log.rename(columns={"day": "Hari", "time": "Jam", "moist": "Kelembapan (%)", "temp": "Suhu (°C)",
                            "stage": "Tahap", "pump_txt": "Pompa"})[["Hari", "Jam", "Kelembapan (%)", "Suhu (°C)",
                                                                     "Tahap", "Pompa"]], hide_index=True)


def page_monitoring():
    ui.hero("Monitoring Realtime — Siklus Perkembangan Sensor IoT Pakcoy",
            "Pembacaan sensor perkembangan tanaman diputar ulang tiap beberapa detik, diklasifikasikan LSTM, dilengkapi tren regresi "
            "linear dan otomatisasi pompa air.",
            "activity")
    df = pick_series("mon")
    if len(df) == 0:
        ui.banner("warn", "Dataset kosong. Pilih siklus lain.")
        return
    m = load_models()
    c1, c2, c3 = st.columns(3)
    max_steps = min(200, len(df))
    default_steps = min(40, max_steps)
    if "mon_steps" not in st.session_state:
        st.session_state["mon_steps"] = max(1, default_steps)
    if "mon_start" not in st.session_state:
        st.session_state["mon_start"] = 1
    steps = int(c1.number_input("Jumlah langkah pembacaan sensor", min_value=1, max_value=max(1, max_steps), key="mon_steps"))
    delay = c2.slider("Jeda antar-langkah (detik)", 0.05, 1.5, 0.3, 0.05, key="mon_delay")
    start = int(c3.number_input("Mulai dari pembacaan ke-", min_value=1, max_value=max(1, len(df)), key="mon_start"))

    st.caption("⚡ **Pintasan Cepat Titik Awal Monitoring:**")
    m_p1, m_p2, m_p3 = st.columns(3)
    if m_p1.button("🌱 Fase Pertumbuhan (Mulai Baca ke-1)", use_container_width=True, key="mon_btn1"):
        st.session_state["mon_start"] = 1
        st.session_state["mon_steps"] = 35
        st.rerun()
    if m_p2.button("🌿 Transisi Menjelang Panen (Mulai Baca ke-60)", use_container_width=True, key="mon_btn2"):
        st.session_state["mon_start"] = 60
        st.session_state["mon_steps"] = 35
        st.rerun()
    if m_p3.button("🥬 Fase Siap Panen (Mulai Baca ke-85)", use_container_width=True, key="mon_btn3"):
        st.session_state["mon_start"] = min(85, max(1, len(df) - 35))
        st.session_state["mon_steps"] = 35
        st.rerun()

    d1, d2, d3, d4 = st.columns([1, 1, 1, 1])
    dry = float(d1.number_input("Batas kering (%)", 30.0, 70.0, float(DRY), 1.0, key="mon_dry"))
    wet = float(d2.number_input("Batas basah (%)", 60.0, 95.0, float(WET), 1.0, key="mon_wet"))
    run = d3.button("Jalankan Monitoring", type="primary", key="mon_run")
    if d4.button("Reset Riwayat", key="mon_reset"):
        st.session_state["mon_recs"] = []
    ph = {k: st.empty() for k in ("cards", "banner", "charts", "table")}
    recs = st.session_state.get("mon_recs", [])
    if not run:
        render_monitor(ph, recs, dry, wet, "static")
        return
    recs, pump_on = [], False
    w = m["cfg_lstm"]["w_cls"] if m.get("cfg_lstm") else 6
    for i in range(start - 1, min(len(df), start - 1 + steps)):
        row = df.iloc[i]
        moist = float(row["Soil Moisture (%)"])
        pump_on, status = utils.pump_decision(moist, pump_on, dry, wet)
        if lstm_ready(m, "clf") and i + 1 >= w:
            p = predict_stage(m, df.iloc[i - w + 1: i + 1])
            k = int(p.argmax())
            stage, source = label(utils.CLASS_NAMES[k]), f"LSTM · {p[k]:.0%}"
        else:
            stage, source = label(str(row["Ground Truth Criteria"])), "label data"
        recs.append(dict(idx=int(row["Time_Index"]), day=int(row["Day"]), time=row["Time"], moist=moist,
                         temp=float(row["Temperature (°C)"]), stage=stage, source=source, pump=pump_on,
                         pump_txt="MENYALA" if pump_on else "MATI", status=status))
        render_monitor(ph, recs, dry, wet, f"r{i}")
        time.sleep(delay)
    st.session_state["mon_recs"] = recs
    on_cnt = sum(r["pump"] for r in recs)
    ui.banner("info", f"Monitoring siklus selesai: {len(recs)} pembacaan, pompa menyala pada {on_cnt} pembacaan "
                      f"({on_cnt / len(recs):.0%}).")


# ================================================================= model LSTM
def eval_section(ev, names, prefix):
    """ev: dict nama -> {akurasi, cm, report}. Menampilkan metrik, confusion matrix, laporan per kelas."""
    if not ev:
        ui.banner("info", "Hasil evaluasi detail belum tersedia di file konfigurasi. Jalankan notebook terbaru di Colab.")
        return
    cols = st.columns(len(ev))
    for (title, d), c in zip(ev.items(), cols):
        c.markdown(f"**{title}**")
        c.markdown(ui.kpi_html([dict(icon="sparkles", label="Akurasi", value=f"{d.get('akurasi', 0):.1%}", color="#34d399")]),
                   unsafe_allow_html=True)
        if d.get("cm"):
            show(charts.confusion_fig(d["cm"], names, f"Confusion matrix · {title}"), f"{prefix}_cm_{title}", c)
        if d.get("report"):
            rep = pd.DataFrame({k: v for k, v in d["report"].items() if isinstance(v, dict)}).T
            rep = rep.loc[[n for n in names if n in rep.index], ["precision", "recall", "f1-score", "support"]].round(3)
            rep.index = [label(i) for i in rep.index]
            c.dataframe(rep)


def page_lstm():
    ui.hero("Model LSTM — Klasifikasi Tahap Pertumbuhan",
            "LSTM membaca 6 pembacaan sensor terakhir (kelembapan, suhu, jam) dan menentukan tahap pertumbuhan.",
            "cpu")
    m = load_models()
    tab1, tab2 = st.tabs(["Klasifikasi Tahap", "Arsitektur & Evaluasi"])
    with tab1:
        if warn_models(m, ["clf"]) and m.get("cfg_lstm"):
            w = m["cfg_lstm"]["w_cls"]
            mode = st.radio("Sumber masukan", ["Dari dataset", "Input manual"], horizontal=True, key="cls_mode")
            if mode == "Dari dataset":
                df = pick_series("cls")
                if len(df) < w:
                    ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {w} pembacaan berurutan.")
                    return

                st.caption("⚡ **Pintasan Uji Cepat Tiap Tahap Perkembangan:**")
                btn_c1, btn_c2, btn_c3 = st.columns(3)
                if btn_c1.button("🌱 Uji: Masa Pertumbuhan (Baca ke-25)", use_container_width=True, key="btn_cls_p1"):
                    st.session_state["cls_step"] = 25
                    st.rerun()
                if btn_c2.button("🌿 Uji: Mendekati Panen (Baca ke-75)", use_container_width=True, key="btn_cls_p2"):
                    st.session_state["cls_step"] = min(75, len(df))
                    st.rerun()
                if btn_c3.button("🥬 Uji: Siap Panen (Baca ke-100)", use_container_width=True, key="btn_cls_p3"):
                    st.session_state["cls_step"] = min(100, len(df))
                    st.rerun()

                if "cls_step" not in st.session_state or st.session_state["cls_step"] > len(df) or st.session_state["cls_step"] < w:
                    st.session_state["cls_step"] = min(60, len(df))
                step = st.slider("Pembacaan ke-", w, len(df), key="cls_step")
                window = df.iloc[step - w: step]
                row_last = df.iloc[step - 1]
                truth = str(row_last["Ground Truth Criteria"])
                day_val = row_last.get("Day", "?")
                dap_val = row_last.get("DAP", "?")
                time_val = row_last.get("Time", "?")

                dap_badge = f" &nbsp;•&nbsp; 🌱 <b>DAP {dap_val}</b>" if dap_val != "?" else ""
                st.markdown(
                    f"""
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px 16px; margin:6px 0 14px 0; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px;">
                        <div style="font-size:13.5px; color:#334155;">
                            📅 <b>Hari ke-{day_val}</b>{dap_badge} &nbsp;•&nbsp; ⏰ <b>Jam {time_val}</b> &nbsp;•&nbsp; 📍 <b>Pembacaan ke-{step}</b> dari {len(df)}
                        </div>
                        <div style="font-size:12.5px; font-weight:600; padding:3px 12px; border-radius:20px; background:#eef2ff; color:#4338ca; border:1px solid #c7d2fe;">
                            Fase Data Asli: {label(truth)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.caption(f"Isi {w} pembacaan terakhir atau pilih template simulasi kondisi di bawah:")
                m_c1, m_c2, m_c3 = st.columns(3)
                if m_c1.button("🌱 Template: Masa Pertumbuhan (Lembap 70%)", use_container_width=True, key="btn_tmpl_1"):
                    st.session_state["manual_moist"] = 70.0
                    st.session_state["manual_temp"] = 27.0
                    st.rerun()
                if m_c2.button("🌿 Template: Mendekati Panen (Sedang 55%)", use_container_width=True, key="btn_tmpl_2"):
                    st.session_state["manual_moist"] = 55.0
                    st.session_state["manual_temp"] = 27.0
                    st.rerun()
                if m_c3.button("🥬 Template: Siap Panen (Rendah 48%)", use_container_width=True, key="btn_tmpl_3"):
                    st.session_state["manual_moist"] = 48.0
                    st.session_state["manual_temp"] = 26.0
                    st.rerun()

                def_m = st.session_state.get("manual_moist", 70.0)
                def_t = st.session_state.get("manual_temp", 27.0)
                base = pd.DataFrame({"Time": (utils.JAM_LIST * 2)[:w], "Soil Moisture (%)": [def_m] * w,
                                     "Temperature (°C)": [def_t] * w})
                window = st.data_editor(base, num_rows="fixed", key=f"cls_manual_{def_m}_{def_t}", width="stretch")
                truth = None

            preview_cols = []
            rename_map = {
                "Day": "Hari ke-",
                "DAP": "DAP",
                "Time": "Jam",
                "Soil Moisture (%)": "Kelembapan (%)",
                "Temperature (°C)": "Suhu (°C)",
                "Soil Condition": "Kondisi Tanah"
            }
            for c in ["Day", "DAP", "Time", "Soil Moisture (%)", "Temperature (°C)", "Soil Condition"]:
                if c in window.columns:
                    preview_cols.append(c)
            st.caption(f"📊 **Data {w} Pembacaan Sensor Berurutan yang Masuk ke LSTM:**")
            st.dataframe(window[preview_cols].rename(columns=rename_map) if preview_cols else window, hide_index=True, width="stretch")
            try:
                p = predict_stage(m, window)
                k = int(p.argmax())
                name = utils.CLASS_NAMES[k]
                ui.kpi_cards([
                    dict(icon="cpu", label="Prediksi tahap", value=label(name), color=charts.STAGE_COLORS.get(name, "#533afd")),
                    dict(icon="sparkles", label="Keyakinan", value=f"{p[k]:.0%}", color="#34d399"),
                    dict(icon="check-circle", label="Label sebenarnya", value=label(truth) if truth else "-", color="#e8ecf4"),
                ])
                show(charts.prob_bar(p, utils.CLASS_NAMES), "cls_prob")
                if truth and truth != name:
                    ui.banner("warn", "Prediksi berbeda dari label data. Itu wajar pada pembacaan di perbatasan dua tahap.")
            except Exception as e:
                st.error(f"Gagal memprediksi: {e}")
    with tab2:
        st.markdown("**Arsitektur klasifikasi:** `Input (6 × 5)` -> `LSTM 64` -> `Dropout 0,3` -> `LSTM 32` -> "
                    "`Dense 32` -> `Softmax 3 kelas`. Fitur: kelembapan, suhu (skala 0–1), dan one-hot jam.")
        st.markdown("**Arsitektur prediksi:** `Input (12 × 5)` -> `LSTM 96` -> `LSTM 48` -> `Dense 96` -> "
                    "`Dense 36` -> keluaran `12 langkah × (kelembapan, suhu, maturity)`.")
        cfg = m.get("cfg_lstm")
        if cfg:
            st.caption(f"Dilatih dengan TensorFlow {cfg.get('tf_version', '?')}.")
            ev = cfg.get("evaluasi", {})
            eval_section({k: v for k, v in ev.items()}, cfg["class_names"], "lstm")
            mae_sim = cfg.get("metrics", {}).get("mae_forecast_uji_simulasi")
            mae_asli = cfg.get("metrics", {}).get("mae_forecast_data_asli")
            if mae_sim or mae_asli:
                st.markdown('<div class="section-title">Evaluasi Model Prediksi 4 Hari (Mean Absolute Error)</div>', unsafe_allow_html=True)
                if mae_sim:
                    st.caption("📊 **Uji Evaluasi Siklus Simulasi (30 Siklus):**")
                    ui.kpi_cards([
                        dict(icon="droplets", label="MAE kelembapan (simulasi)", value=f"{mae_sim['moisture']:.2f} %", color="#38bdf8"),
                        dict(icon="thermometer", label="MAE suhu (simulasi)", value=f"{mae_sim['temperature']:.2f} °C", color="#fb923c"),
                        dict(icon="trending-up", label="MAE kematangan tanaman (simulasi)", value=f"{mae_sim['maturity']:.2f} %", color="#34d399"),
                    ])
                if mae_asli:
                    st.caption("🌱 **Uji Evaluasi Data Asli Lapangan (1 Siklus - 40 Hari):**")
                    ui.kpi_cards([
                        dict(icon="droplets", label="MAE kelembapan (data asli)", value=f"{mae_asli['moisture']:.2f} %", color="#38bdf8"),
                        dict(icon="thermometer", label="MAE suhu (data asli)", value=f"{mae_asli['temperature']:.2f} °C", color="#fb923c"),
                        dict(icon="trending-up", label="MAE kematangan tanaman (data asli)", value=f"{mae_asli['maturity']:.2f} %", color="#facc15"),
                    ])
        else:
            ui.banner("info", "Konfigurasi model belum ada. Latih model di Colab terlebih dulu.")


# ================================================================= prediksi 4 hari
def page_forecast():
    ui.hero("Prediksi 4 Hari ke Depan",
            "LSTM membaca 12 pembacaan terakhir (4 hari) lalu memprediksi kelembapan, suhu, dan tingkat kematangan tanaman 12 pembacaan berikutnya.",
            "calendar-range")
    m = load_models()
    if not warn_models(m, ["fc"]) or not m.get("cfg_lstm"):
        return
    cfg = m["cfg_lstm"]
    win = cfg["w_in"]
    df = pick_series("fc")
    if len(df) < win:
        ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {win} pembacaan berurutan untuk prediksi 4 hari.")
        return

    st.caption("⚡ **Pintasan Cepat Titik Awal Prediksi 4 Hari:**")
    fc_c1, fc_c2, fc_c3 = st.columns(3)
    if fc_c1.button("🌱 Proyeksi dari Masa Pertumbuhan (Baca ke-25)", use_container_width=True, key="fc_btn1"):
        st.session_state["fc_step"] = 25
        st.rerun()
    if fc_c2.button("🌿 Proyeksi dari Mendekati Panen (Baca ke-75)", use_container_width=True, key="fc_btn2"):
        st.session_state["fc_step"] = min(75, len(df))
        st.rerun()
    if fc_c3.button("🥬 Proyeksi dari Siap Panen (Baca ke-100)", use_container_width=True, key="fc_btn3"):
        st.session_state["fc_step"] = min(100, len(df))
        st.rerun()

    if "fc_step" not in st.session_state or st.session_state["fc_step"] > len(df) or st.session_state["fc_step"] < win:
        st.session_state["fc_step"] = min(60, len(df))
    step = st.slider("Prediksi dari pembacaan ke-", win, len(df), key="fc_step")
    row_fc = df.iloc[step - 1]
    day_fc = row_fc.get("Day", "?")
    dap_fc = row_fc.get("DAP", "?")
    time_fc = row_fc.get("Time", "?")
    dap_fc_badge = f" &nbsp;•&nbsp; 🌱 <b>DAP {dap_fc}</b>" if dap_fc != "?" else ""
    st.markdown(
        f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px 16px; margin:6px 0 14px 0; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px;">
            <div style="font-size:13.5px; color:#334155;">
                📅 <b>Hari ke-{day_fc}</b>{dap_fc_badge} &nbsp;•&nbsp; ⏰ <b>Jam {time_fc}</b> &nbsp;•&nbsp; 📍 <b>Titik Awal Prediksi ke-{step}</b> dari {len(df)}
            </div>
            <div style="font-size:12.5px; font-weight:600; padding:3px 12px; border-radius:20px; background:#eef2ff; color:#4338ca; border:1px solid #c7d2fe;">
                Input: 12 Pembacaan Terakhir (4 Hari)
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
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
        dict(icon="droplets", label="Kelembapan akhir", value=f"{last['Kelembapan (%)']:.0f}%", color="#38bdf8"),
        dict(icon="thermometer", label="Suhu akhir", value=f"{last['Suhu (°C)']:.1f}°C", color="#fb923c"),
        dict(icon="trending-up", label="Tingkat Kematangan Akhir", value=f"{mat_last:.0f}%", color="#34d399", sub="skala 0–100%"),
        dict(icon="sprout", label="Tahap di akhir 4 hari", value=label(end_stage), color=charts.STAGE_COLORS.get(end_stage, "#34d399")),
    ])
    hist_x = window["Time_Index"].tolist()
    pred_x = [hist_x[-1] + i for i in range(1, len(table) + 1)]
    truth = df.iloc[step: step + len(table)] if step + len(table) <= len(df) else None
    c1, c2 = st.columns(2)
    show(charts.forecast_line(hist_x, window["Soil Moisture (%)"].tolist(), pred_x, table["Kelembapan (%)"].tolist(),
                              "Kelembapan tanah (%)", "%", "#38bdf8",
                              None if truth is None else truth["Soil Moisture (%)"].tolist()), "fc_m", c1)
    show(charts.forecast_line(hist_x, window["Temperature (°C)"].tolist(), pred_x, table["Suhu (°C)"].tolist(),
                              "Suhu (°C)", "°C", "#fb923c",
                              None if truth is None else truth["Temperature (°C)"].tolist()), "fc_t", c2)
    pred_mat = table["Tingkat Kematangan (%)"].tolist() if "Tingkat Kematangan (%)" in table.columns else table["Maturity (%)"].tolist()
    show(charts.maturity_forecast(pred_x, pred_mat, th), "fc_mat")
    st.markdown('<div class="section-title">Ringkasan per hari</div>', unsafe_allow_html=True)
    mat_col = "Tingkat Kematangan (%)" if "Tingkat Kematangan (%)" in table.columns else "Maturity (%)"
    daily = (table.groupby("Hari", sort=False)
             .agg({"Kelembapan (%)": "mean", "Suhu (°C)": "mean", mat_col: "last", "Tahap": "last"})
             .round(1).reset_index())
    st.dataframe(daily, hide_index=True)
    with st.expander("Tabel lengkap 12 pembacaan"):
        st.dataframe(table, hide_index=True)
    st.download_button("Unduh prediksi (CSV)", table.to_csv(index=False).encode("utf-8"),
                       file_name="prediksi_4_hari.csv", mime="text/csv", key="fc_dl")
    if truth is not None:
        ui.banner("info", "Garis abu-abu pada grafik adalah nilai sebenarnya dari data, sebagai pembanding.")


# ================================================================= CNN & foto
def photo_panel(m, img, key):
    """Analisis satu foto: CNN + analisis visual daun. Mengembalikan (cnn, green)."""
    with st.expander("📐 Kalibrasi Ukuran Fisik Daun (Satuan cm)", expanded=False):
        st.caption(
            "Secara otomatis sistem mengestimasi ukuran fisik daun dalam **centimeter (cm)** berdasarkan rasio foto standar (jarak kamera ±30–40 cm). "
            "Jika foto memiliki benda pembanding, Anda dapat memilih metode kalibrasi presisi di bawah ini:"
        )
        c_mode, c_val = st.columns([1.2, 1])
        with c_mode:
            calib_choice = st.radio(
                "Metode Penentuan Ukuran:",
                ["Estimasi Otomatis (Standar Foto HP)", "Berdasarkan Diameter Netpot (cm)", "Manual (Piksel per cm)"],
                key=f"{key}_calib_choice"
            )
        scale = 0.0
        with c_val:
            if calib_choice == "Berdasarkan Diameter Netpot (cm)":
                netpot_dia = st.number_input("Diameter netpot hidroponik (cm)", min_value=1.0, max_value=25.0, value=5.0, step=0.5, key=f"{key}_netpot_dia", help="Netpot hidroponik standar berdiameter 5 cm.")
                scale = float(img.width * 0.18 / netpot_dia)
                st.caption(f"Skala terhitung: **{scale:.1f} px/cm**")
            elif calib_choice == "Manual (Piksel per cm)":
                scale = st.number_input("Skala manual (px/cm)", min_value=1.0, max_value=300.0, value=35.0, step=1.0, key=f"{key}_manual_scale")
            else:
                st.info("💡 Mode Otomatis Aktif: Ukuran bentang daun langsung disajikan dalam **centimeter (cm)**.")

    g = utils.green_analysis(img, scale)
    is_plant, plant_reason, _ = utils.validate_plant_image(img, g)
    c1, c2 = st.columns(2)
    c1.image(img, caption="Foto asli")
    c2.image(g["overlay"], caption="Area daun terdeteksi (area lain digelapkan)")
    cnn = None
    if m.get("cnn") is not None:
        names = cnn_names(m)
        p = predict_image(m, img)

        # Validasi ganda: jika citra tidak lolos verifikasi dedaunan (wajah manusia, latar ruangan, objek non-tanaman)
        # langsung tetapkan prediksi ke 'bukan_pakcoy'
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
                dict(icon="alert-triangle", label="Status Objek (CNN)", value=label(names[k]), color=charts.STAGE_COLORS.get(names[k], "#ea2261")),
                dict(icon="sparkles", label="Keyakinan", value=f"{p[k]:.0%}", color="#ea2261"),
                dict(icon="x-circle", label="Kesiapan Panen", value="Tidak Berlaku", color="#ea2261", sub="Bukan tanaman pakcoy"),
            ])
            show(charts.prob_bar(p, names), f"{key}_prob")
            alasan_detail = f" — {plant_reason}" if not is_plant else ""
            ui.banner("danger", f"⚠️ Objek terdeteksi sebagai **BUKAN TANAMAN PAKCOY**{alasan_detail} (Keyakinan: {p[k]:.0%}). "
                                f"Indeks kesiapan panen dan analisis kanopi tanaman tidak berlaku untuk objek ini.")
        else:
            ui.kpi_cards([
                dict(icon="cpu", label="Tahap (CNN)", value=label(names[k]), color=charts.STAGE_COLORS.get(names[k], "#e8ecf4")),
                dict(icon="sparkles", label="Keyakinan", value=f"{p[k]:.0%}", color="#34d399"),
                dict(icon="layers", label="Indeks kesiapan panen", value=f"{idx:.0f}/100", color="#facc15"),
            ])
            g1, g2 = st.columns(2)
            show(charts.prob_bar(p, names), f"{key}_prob", g1)
            show(charts.gauge(idx, "Indeks kesiapan panen", (50, 90)), f"{key}_gauge", g2)
            if p[k] < 0.6:
                ui.banner("warn", "Keyakinan model rendah. Coba foto yang lebih jelas atau dari sudut lain.")
    else:
        ui.banner("warn", "Model CNN belum tersedia. Hanya analisis visual daun yang ditampilkan.")

    if not is_plant or (cnn and cnn[0] == "bukan_pakcoy"):
        cards = [
            dict(icon="alert-triangle", label="Status Validasi Citra", value="Bukan Tanaman", color="#ea2261",
                 sub="Wajah/objek non-tanaman terdeteksi"),
            dict(icon="layers", label="Kerapatan Rumpun Daun", value="Tidak Terdeteksi", color="#94a3b8",
                 sub="Tidak ada roset daun pakcoy"),
            dict(icon="maximize", label="Bentang Daun (Lebar × Panjang)", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="maximize", label="Perkiraan Luas Daun", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan tanaman pakcoy"),
            dict(icon="sprout", label="Tingkat Daun Menguning", value="Tidak Berlaku", color="#94a3b8",
                 sub="Bukan daun pakcoy"),
            dict(icon="sparkles", label="Tutupan Warna Hijau", value=f"{g['coverage_pct']:.1f}%", color="#94a3b8",
                 sub="Hanya pantulan latar belakang"),
        ]
        ui.kpi_cards(cards)
        st.caption(
            "💡 **Pemberitahuan Sistem:** Pengukuran ukuran fisik daun (bentang cm dan perkiraan luas) dinonaktifkan "
            "karena citra terdeteksi bukan tanaman pakcoy. Silakan potret langsung tanaman pakcoy asli dengan pencahayaan yang memadai."
        )
        return cnn, g

    # Status indikator visual yang ramah orang awam (satuan cm & cm²)
    w_raw = g.get("width_cm")
    h_raw = g.get("height_cm")
    a_raw = g.get("area_cm2")
    try:
        w_cm = float(w_raw) if w_raw is not None else 0.0
    except (ValueError, TypeError):
        w_cm = 0.0
    try:
        h_cm = float(h_raw) if h_raw is not None else 0.0
    except (ValueError, TypeError):
        h_cm = 0.0
    try:
        a_cm2 = float(a_raw) if a_raw is not None else 0.0
    except (ValueError, TypeError):
        a_cm2 = 0.0

    is_est = bool(g.get("is_estimated_cm", True))
    prefix_est = "± " if is_est and w_cm > 0 else ""

    bentang_val = f"{prefix_est}{w_cm:.1f} × {h_cm:.1f} cm" if (w_cm > 0 and h_cm > 0) else "Belum terkalibrasi"
    luas_val = f"{prefix_est}{a_cm2:.0f} cm²" if a_cm2 > 0 else "Belum terkalibrasi"

    if g['yellow_pct'] < 2.0:
        yellow_sub = "Sangat segar (bebas klorosis)"
        yellow_col = "#34d399"
    elif g['yellow_pct'] < 8.0:
        yellow_sub = "Normal (sedikit menguning)"
        yellow_col = "#facc15"
    else:
        yellow_sub = "Perhatian: daun menguning"
        yellow_col = "#f87171"

    green_sub = "Klorofil pekat & subur" if g['greenness'] >= 50 else "Cukup segar"

    if g['compactness'] >= 0.75:
        compact_sub = "Rumpun sangat rimbun"
    elif g['compactness'] >= 0.45:
        compact_sub = "Rumpun cukup rimbun"
    else:
        compact_sub = "Rumpun daun renggang"

    cards = [
        dict(icon="sprout", label="Tutupan Daun pada Foto", value=f"{g['coverage_pct']:.1f}%", color="#34d399",
             sub="Persentase area foto terisi daun"),
        dict(icon="layers", label="Kerapatan Rumpun Daun", value=f"{g['compactness']:.0%}", color="#38bdf8",
             sub=compact_sub),
        dict(icon="maximize", label="Bentang Daun (Lebar × Panjang)", value=bentang_val, color="#a78bfa",
             sub="Ukuran fisik terluar tanaman"),
        dict(icon="maximize", label="Perkiraan Luas Daun", value=luas_val, color="#fb923c",
             sub="Total luas bidang daun hijau"),
        dict(icon="sprout", label="Tingkat Daun Menguning", value=f"{g['yellow_pct']:.1f}%", color=yellow_col,
             sub=yellow_sub),
        dict(icon="sparkles", label="Kepekatan Warna Hijau", value=f"{g['greenness']:.0f}%", color="#34d399",
             sub=green_sub),
    ]
    ui.kpi_cards(cards)

    st.caption(
        "💡 **Penjelasan Indikator Visual untuk Orang Awam:**\n"
        "- **Bentang Daun (cm):** Menunjukkan ukuran fisik rentang daun pakcoy terluar (lebar × panjang) dalam satuan centimeter (cm).\n"
        "- **Perkiraan Luas Daun (cm²):** Estimasi total permukaan daun hijau yang aktif melakukan fotosintesis.\n"
        "- **Kerapatan Rumpun Daun:** Mengukur seberapa lebat daun mengisi tanaman (daun rimbun rapat dan tidak bolong-bolong).\n"
        "- **Tingkat Daun Menguning (%):** Mendeteksi tanda klorosis/penuaan dini. Angka mendekati 0% berarti tanaman sangat sehat dan tidak kekurangan nutrisi."
    )
    return cnn, g


def get_image(key):
    mode = st.radio("Sumber foto", ["Unggah foto", "Ambil dari kamera"], horizontal=True, key=f"{key}_mode")
    f = (st.file_uploader("Unggah foto pakcoy", type=["jpg", "jpeg", "png"], key=f"{key}_up")
         if mode == "Unggah foto" else st.camera_input("Ambil foto pakcoy", key=f"{key}_cam"))
    return Image.open(f) if f is not None else None


def page_cnn():
    ui.hero("Model CNN — Deteksi Kesiapan Panen dari Foto",
            "CNN (MobileNetV2) mengenali tahap pertumbuhan dari foto, dilengkapi analisis visual daun: tutupan, kerapatan rimbun, "
            "dan estimasi bentang daun dalam satuan centimeter (cm).",
            "scan-line")
    m = load_models()
    tab1, tab2 = st.tabs(["Scan Foto", "Info & Evaluasi Model"])
    with tab1:
        if not warn_models(m, ["cnn"]):
            st.caption("Analisis visual daun tetap bisa dicoba tanpa model.")
        img = get_image("cnn")
        if img is None:
            st.caption("Tips: foto dari atas, pencahayaan cukup, tanaman memenuhi sebagian besar foto.")
        else:
            cnn, g = photo_panel(m, img, "cnn")
            if cnn:
                if cnn[0] != "bukan_pakcoy":
                    info = utils.STAGE_INFO.get(cnn[0])
                    if info:
                        ui.banner("info", "Ciri umum tahap ini: " + info["ciri"])
                        ui.banner("ok", "Saran umum: " + info["saran"])
                else:
                    ui.banner("danger", "Objek terdeteksi bukan pakcoy. Silakan unggah foto tanaman pakcoy asli.")
    with tab2:
        st.markdown("**Arsitektur:** `Augmentasi` -> `Rescaling` -> `MobileNetV2 (ImageNet)` -> `GlobalAveragePooling` -> "
                    "`Dropout 0,3` -> `Softmax 4 kelas`. Dilatih 2 tahap: kepala klasifikasi, lalu fine-tuning lapisan atas.")
        cfg = m.get("cfg_cnn")
        if cfg:
            st.caption(f"Dilatih dengan TensorFlow {cfg.get('tf_version', '?')}. "
                       f"Jumlah gambar uji: {cfg.get('jumlah_gambar_uji', '?')} (kecil, hasil bersifat kasar).")
            ev = cfg.get("evaluasi", {})
            eval_section(ev, cfg["class_names"], "cnn")
            if not ev:
                ui.kpi_cards([dict(icon="sparkles", label="Akurasi uji", value=f"{cfg.get('akurasi_uji', 0):.1%}",
                                   color="#34d399")])
        else:
            ui.banner("info", "Konfigurasi model belum ada. Latih model di Colab terlebih dulu.")


# ================================================================= scan gabungan
def page_scan():
    ui.hero("Scan Gabungan — Foto + Sensor",
            "Foto dianalisis CNN dan segmentasi daun, data sensor dianalisis LSTM. Keduanya digabung menjadi satu laporan perkembangan.",
            "scan-search")
    m = load_models()
    st.markdown('<div class="section-title">1) Foto tanaman</div>', unsafe_allow_html=True)
    img = get_image("scan")
    st.markdown('<div class="section-title">2) Konteks sensor</div>', unsafe_allow_html=True)
    df = pick_series("scan")
    w_in = m["cfg_lstm"]["w_in"] if m.get("cfg_lstm") else 12
    if len(df) < w_in:
        ui.banner("warn", f"Dataset memiliki {len(df)} pembacaan. Minimal dibutuhkan {w_in} pembacaan berurutan.")
        return

    st.caption("⚡ **Pintasan Konteks Sensor Tanaman:**")
    sc_c1, sc_c2, sc_c3 = st.columns(3)
    if sc_c1.button("🌱 Sensor Masa Pertumbuhan (Baca ke-25)", use_container_width=True, key="scan_btn1"):
        st.session_state["scan_step"] = 25
        st.rerun()
    if sc_c2.button("🌿 Sensor Mendekati Panen (Baca ke-75)", use_container_width=True, key="scan_btn2"):
        st.session_state["scan_step"] = min(75, len(df))
        st.rerun()
    if sc_c3.button("🥬 Sensor Siap Panen (Baca ke-100)", use_container_width=True, key="scan_btn3"):
        st.session_state["scan_step"] = min(100, len(df))
        st.rerun()

    if "scan_step" not in st.session_state or st.session_state["scan_step"] > len(df) or st.session_state["scan_step"] < w_in:
        st.session_state["scan_step"] = min(60, len(df))
    step = st.slider("Gunakan pembacaan sampai ke-", w_in, len(df), key="scan_step")
    row_sc = df.iloc[step - 1]
    day_sc = row_sc.get("Day", "?")
    dap_sc = row_sc.get("DAP", "?")
    time_sc = row_sc.get("Time", "?")
    dap_sc_badge = f" &nbsp;•&nbsp; 🌱 <b>DAP {dap_sc}</b>" if dap_sc != "?" else ""
    st.markdown(
        f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px 16px; margin:6px 0 14px 0; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px;">
            <div style="font-size:13.5px; color:#334155;">
                📅 <b>Hari ke-{day_sc}</b>{dap_sc_badge} &nbsp;•&nbsp; ⏰ <b>Jam {time_sc}</b> &nbsp;•&nbsp; 📍 <b>Sensor ke-{step}</b> dari {len(df)}
            </div>
            <div style="font-size:12.5px; font-weight:600; padding:3px 12px; border-radius:20px; background:#eef2ff; color:#4338ca; border:1px solid #c7d2fe;">
                Fase Sensor: {label(str(row_sc.get("Ground Truth Criteria", "")))}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if img is None:
        ui.banner("info", "Unggah atau ambil foto untuk membuat laporan.")
        return
    st.divider()
    st.markdown('<div class="section-title">Hasil analisis foto</div>', unsafe_allow_html=True)
    cnn, g = photo_panel(m, img, "scan")

    # Gatekeeper penyaring foto: jika terdeteksi bukan pakcoy atau struktur tanaman tidak valid, putus alur LSTM
    is_p_scan, p_reason_scan, _ = utils.validate_plant_image(img, g)
    if (cnn and cnn[0] == "bukan_pakcoy") or not is_p_scan:
        alasan_str = f" ({p_reason_scan})" if not is_p_scan else ""
        ui.banner("danger", f"⛔ **Validasi Foto Gagal: Objek terdeteksi BUKAN TANAMAN PAKCOY{alasan_str}.**\n\n"
                            "Analisis gabungan dan proyeksi sensor 4 hari ke depan **dihentikan** untuk mencegah kesalahan kesimpulan budidaya.")
        return

    st.markdown('<div class="section-title">Hasil analisis sensor (LSTM)</div>', unsafe_allow_html=True)
    lstm, table = None, None
    if lstm_ready(m, "clf"):
        wc = m["cfg_lstm"]["w_cls"]
        pc = predict_stage(m, df.iloc[step - wc: step])
        lstm = (utils.CLASS_NAMES[int(pc.argmax())], float(pc.max()))
        ui.banner("ok", f"LSTM: {label(lstm[0])} (keyakinan {lstm[1]:.0%})")
    else:
        ui.banner("warn", "Model LSTM klasifikasi belum tersedia.")
    if lstm_ready(m, "fc"):
        table = predict_forecast(m, df.iloc[step - w_in: step].reset_index(drop=True))
        st.dataframe(table, hide_index=True)
    st.divider()
    st.markdown('<div class="section-title">3) Laporan perkembangan</div>', unsafe_allow_html=True)
    if cnn and lstm:
        if cnn[0] == lstm[0]:
            ui.banner("ok", f"CNN dan LSTM sepakat: tanaman berada pada tahap {label(cnn[0])}.")
        else:
            ui.banner("warn", f"CNN ({label(cnn[0])}) dan LSTM ({label(lstm[0])}) berbeda. Foto dan sensor belum tentu "
                              "dari tanaman yang sama, jadi periksa tanaman secara langsung.")
    final = (cnn or lstm or [None])[0]
    if final and final in utils.STAGE_INFO and final != "bukan_pakcoy":
        ui.banner("info", "Ciri umum tahap ini: " + utils.STAGE_INFO[final]["ciri"])
        ui.banner("ok", "Saran umum: " + utils.STAGE_INFO[final]["saran"])
    if table is not None:
        mat_scan = table["Tingkat Kematangan (%)"].iloc[-1] if "Tingkat Kematangan (%)" in table.columns else table["Maturity (%)"].iloc[-1]
        ui.banner("info", f"Perkiraan tahap 4 hari ke depan: {table['Tahap'].iloc[-1]} "
                          f"(tingkat kematangan tanaman sekitar {mat_scan:.0f}%).")
    report = utils.build_report(cnn=(cnn[0], cnn[1]) if cnn else None, lstm=lstm, green=g, table=table,
                                sensor=df.iloc[step - 1])
    st.download_button("Unduh laporan (Markdown)", report.encode("utf-8"), file_name="laporan_pakcoy.md",
                       mime="text/markdown", key="scan_dl")


PAGES = {
    "🏠 Dashboard": page_dashboard,
    "📊 Eksplorasi Data": page_eksplorasi,
    "📡 Monitoring Realtime": page_monitoring,
    "🧠 Model LSTM": page_lstm,
    "🔮 Prediksi 4 Hari": page_forecast,
    "🖼️ Model CNN (Scan Foto)": page_cnn,
    "🔍 Scan Gabungan": page_scan,
    "AI Assistant": ai_assistant.render_ai_assistant,
}

choice = sidebar()
if choice == "AI Assistant":
    ai_assistant.render_ai_assistant()
else:
    PAGES[choice]()
ui.footer()
