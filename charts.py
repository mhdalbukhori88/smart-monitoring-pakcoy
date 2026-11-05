"""Pembuat grafik Plotly untuk aplikasi Smart Farming Pakcoy."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils import CLASS_NAMES, CLASS_LABELS, MATURITY_COL, LABEL_UMUR, MATURITY_THRESHOLDS

# Warna tema Agronomi Pakcoy (Botanical Green Palette)
STAGE_COLORS = {
    "bukan_pakcoy": "#dc2626",      # Signal Red (Objek Bukan Pakcoy / Peringatan)
    "masa_pertumbuhan": "#0d9488",  # Vegetative Teal-Green
    "mendekati_panen": "#d97706",   # Harvest Amber
    "siap_panen": "#15803d"         # Pakcoy Leaf Green
}
COND_COLORS = {
    "Optimal": "#15803d",           # Pakcoy Leaf Green
    "Dry": "#dc2626",               # Signal Red
    "Wet": "#0284c7"                # Hydro Blue
}
COND_LABELS = {
    "Optimal": "Ideal (Optimal)",
    "Dry": "Kering (Butuh Air)",
    "Wet": "Terlalu Basah"
}
GRID = "#ebf1ed"
BORDER = "#d5e0d8"


def _idx_to_day_label(idx):
    """Ubah nomor urut pembacaan (1..90) menjadi teks ramah awam 'Hari ke-X (Jam)'."""
    try:
        i = int(idx)
        day = (i - 1) // 3 + 1
        jam = ["08:00 Pagi", "12:00 Siang", "16:00 Sore"][(i - 1) % 3]
        return f"Hari ke-{day} ({jam})"
    except Exception:
        return f"Pengukuran #{idx}"


def _layout(fig, title=None, height=340, legend=True, xtitle=None, ytitle=None):
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.01, font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)) if title else None,
        height=height,
        margin=dict(l=14, r=14, t=50 if title else 18, b=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=12, color="#2c3e35"),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.22, font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#5c6f64")),
        hovermode="closest",
    )
    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor=BORDER,
        linecolor=BORDER,
        tickfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#5c6f64"),
        title=dict(text=xtitle, font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=12, color="#2c3e35")) if xtitle else None
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor=BORDER,
        linecolor=BORDER,
        tickfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#5c6f64"),
        title=dict(text=ytitle, font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=12, color="#2c3e35")) if ytitle else None
    )
    return fig


def donut_condition(df):
    counts = df["Soil Condition"].value_counts().reindex(["Optimal", "Dry", "Wet"]).fillna(0)
    fig = go.Figure(go.Pie(
        labels=[COND_LABELS.get(k, k) for k in counts.index],
        values=counts.values.tolist(), hole=0.62,
        marker=dict(colors=[COND_COLORS[k] for k in counts.index]),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        sort=False,
        direction="clockwise"))
    fig.update_layout(
        legend=dict(orientation="h", y=-0.20, x=0.5, xanchor="center",
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#5c6f64")),
        margin=dict(l=14, r=14, t=55, b=35)
    )
    return _layout(fig, "Proporsi Kondisi Kelembapan Tanah", height=360, legend=True)


def bar_stage(df):
    counts = df["Ground Truth Criteria"].value_counts().reindex(CLASS_NAMES).fillna(0)
    fig = go.Figure(go.Bar(
        x=[CLASS_LABELS[k] for k in counts.index], y=counts.values.tolist(),
        marker_color=[STAGE_COLORS[k] for k in counts.index],
        text=[int(v) for v in counts.values], textposition="outside"))
    return _layout(fig, "Jumlah Data per Fase Pertumbuhan", height=360, legend=False, ytitle="Jumlah Pengukuran")


def maturity_curve(df):
    """Maturity terhadap Umur Tanaman, diwarnai per tahap (rata-rata jika ada banyak siklus)."""
    col_age = "Day" if "Day" in df.columns else ("DAP" if "DAP" in df.columns else df.columns[0])
    g = df.groupby([col_age, "Ground Truth Criteria"])[MATURITY_COL].mean().reset_index()
    fig = go.Figure()
    for k in CLASS_NAMES:
        d = g[g["Ground Truth Criteria"] == k]
        if len(d):
            fig.add_trace(go.Scatter(x=d[col_age], y=d[MATURITY_COL], mode="lines+markers", name=CLASS_LABELS[k],
                                     line=dict(color=STAGE_COLORS[k], width=3), marker=dict(size=6)))
    return _layout(fig, "Rata-rata Kematangan Tanaman dari Hari ke-1 hingga Panen (Hari ke-30)", height=380,
                   xtitle="Umur Tanaman (Hari ke-)", ytitle="Tingkat Kematangan (%)")


def hist_moisture(df, dry, wet):
    fig = go.Figure(go.Histogram(x=df["Soil Moisture (%)"], nbinsx=30, marker_color="#15803d"))
    fig.add_vline(x=dry, line_dash="dash", line_color="#dc2626", annotation_text="Batas Kering (<55%)", annotation_font_color="#dc2626")
    fig.add_vline(x=wet, line_dash="dash", line_color="#0284c7", annotation_text="Batas Basah (≥76%)", annotation_font_color="#0284c7")
    return _layout(fig, "Sebaran Kelembapan Tanah", legend=False, xtitle="Kelembapan Tanah (%)", ytitle="Frekuensi Data")


def scatter_moist_temp(df, max_points=1500):
    d = df if len(df) <= max_points else df.sample(max_points, random_state=0)
    fig = go.Figure()
    for k in ["Wet", "Optimal", "Dry"]:
        s = d[d["Soil Condition"] == k]
        if len(s):
            fig.add_trace(go.Scatter(x=s["Soil Moisture (%)"], y=s["Temperature (°C)"], mode="markers",
                                     name=COND_LABELS.get(k, k),
                                     marker=dict(color=COND_COLORS[k], size=6, opacity=0.8)))
    return _layout(fig, "Hubungan Kelembapan Tanah vs Suhu Udara", xtitle="Kelembapan Tanah (%)", ytitle="Suhu Udara (°C)")


def daily_time_pattern(df):
    """Grafik perbandingan rata-rata Kelembapan Tanah (%) dan Suhu Udara (°C) pada Pagi (08:00), Siang (12:00), dan Sore (16:00)."""
    jam_order = ["08:00", "12:00", "16:00"]
    jam_labels = {"08:00": "08:00 Pagi", "12:00": "12:00 Siang", "16:00": "16:00 Sore"}
    if "Time" in df.columns and len(df) > 0:
        g = df.groupby("Time")[["Soil Moisture (%)", "Temperature (°C)"]].mean().reindex(jam_order).dropna(how="all")
    else:
        g = pd.DataFrame(columns=["Soil Moisture (%)", "Temperature (°C)"])

    x_lbls = [jam_labels.get(str(t), str(t)) for t in g.index]
    moist_vals = g["Soil Moisture (%)"].round(1).tolist() if len(g) else []
    temp_vals = g["Temperature (°C)"].round(1).tolist() if len(g) else []

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_lbls,
        y=moist_vals,
        name="Kelembapan Tanah (%)",
        marker_color="#15803d",
        text=[f"{v:.1f}%" for v in moist_vals],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Rata-rata Kelembapan: <b>%{y:.1f}%</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=x_lbls,
        y=temp_vals,
        name="Suhu Udara (°C)",
        marker_color="#d97706",
        text=[f"{v:.1f}°C" for v in temp_vals],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Rata-rata Suhu Udara: <b>%{y:.1f}°C</b><extra></extra>",
    ))
    max_y = max(moist_vals + temp_vals + [70.0])
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, max_y * 1.22])
    return _layout(fig, "Pola Harian Sensor: Pagi, Siang & Sore", legend=True, xtitle="Waktu Pengukuran Harian", ytitle="Rata-rata Nilai Sensor")


def box_temp_stage(df):
    return daily_time_pattern(df)


def live_line(hist, col, title, color, ytitle, dry=None, wet=None, trend=None, height=300):
    """Garis sensor yang bergerak. hist: dataframe ber-indeks Time_Index. trend: prediksi regresi (opsional)."""
    x = hist.index.tolist()
    y = hist[col].tolist()
    hover_txt = [_idx_to_day_label(i) for i in x]
    line_col = "#15803d" if "Moisture" in col or color == "#38bdf8" else "#d97706"
    fill_col = "rgba(21, 128, 61, 0.08)" if line_col == "#15803d" else "rgba(217, 119, 6, 0.07)"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name="Data Sensor",
        text=hover_txt,
        hovertemplate="%{text}<br>Nilai: <b>%{y:.1f}</b><extra></extra>",
        line=dict(color=line_col, width=2.8),
        fill="tozeroy", fillcolor=fill_col
    ))
    if x:
        fig.add_trace(go.Scatter(
            x=[x[-1]], y=[y[-1]], mode="markers", name="Saat Ini",
            text=[hover_txt[-1]],
            hovertemplate="%{text}<br>Saat ini: <b>%{y:.1f}</b><extra></extra>",
            marker=dict(color=line_col, size=9)
        ))
    if trend is not None and len(trend) and x:
        tx = [x[-1] + i for i in range(1, len(trend) + 1)]
        t_hover = [_idx_to_day_label(i) for i in tx]
        fig.add_trace(go.Scatter(
            x=tx, y=list(trend), mode="lines", name="Arah Tren",
            text=t_hover,
            hovertemplate="%{text}<br>Perkiraan: <b>%{y:.1f}</b><extra></extra>",
            line=dict(color="#dc2626", width=2, dash="dash")
        ))
    if dry is not None:
        fig.add_hline(y=dry, line_dash="dot", line_color="#dc2626", annotation_text="Batas Kering (Pompa Nyala)", annotation_position="top left",
                      annotation_font_color="#dc2626")
    if wet is not None:
        fig.add_hline(y=wet, line_dash="dot", line_color="#0284c7", annotation_text="Batas Basah (Pompa Mati)", annotation_position="top left",
                      annotation_font_color="#0284c7")
    return _layout(fig, title, height=height, xtitle="Urutan Pengukuran (3x Sehari · 90 Ukur = 30 Hari)", ytitle=ytitle)


def growth_curve(grow, thresholds):
    """Kurva maturity sejak awal tanam, dengan zona tahap."""
    x = grow.index.tolist()
    y = grow[MATURITY_COL].tolist()
    hover_txt = [_idx_to_day_label(i) for i in x]
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=thresholds[0], fillcolor="#0d9488", opacity=0.06, line_width=0)
    fig.add_hrect(y0=thresholds[0], y1=thresholds[1], fillcolor="#d97706", opacity=0.06, line_width=0)
    fig.add_hrect(y0=thresholds[1], y1=100, fillcolor="#15803d", opacity=0.09, line_width=0)
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name="Tingkat Kematangan",
        text=hover_txt,
        hovertemplate="%{text}<br>Kematangan: <b>%{y:.1f}%</b><extra></extra>",
        line=dict(color="#15803d", width=3)
    ))
    if x:
        fig.add_trace(go.Scatter(
            x=[x[-1]], y=[y[-1]], mode="markers", name="Sekarang",
            text=[hover_txt[-1]],
            hovertemplate="%{text}<br>Sekarang: <b>%{y:.1f}%</b><extra></extra>",
            marker=dict(color="#15803d", size=9)
        ))
    fig.update_yaxes(range=[0, 100])
    return _layout(fig, "Kurva Pertumbuhan & Kematangan Sejak Awal Tanam", height=300, legend=False,
                   xtitle="Urutan Pengukuran (3x Sehari · 90 Ukur = 30 Hari)", ytitle="Tingkat Kematangan (%)")


def gauge(value, title, thresholds=(66.5, 89.0)):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=float(value), number=dict(suffix="%", font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#111c16")),
        title=dict(text=title, font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14, color="#111c16")),
        gauge=dict(axis=dict(range=[0, 100], tickfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#5c6f64")),
                   bar=dict(color="#15803d", thickness=0.26),
                   steps=[dict(range=[0, thresholds[0]], color="rgba(13, 148, 136, 0.14)"),
                          dict(range=[thresholds[0], thresholds[1]], color="rgba(217, 119, 6, 0.18)"),
                          dict(range=[thresholds[1], 100], color="rgba(21, 128, 61, 0.24)")])))
    fig.update_layout(template="plotly_white", height=280, margin=dict(l=20, r=20, t=60, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=13, color="#111c16"))
    return fig


def prob_bar(probs, names, title="Tingkat Keyakinan AI untuk Tiap Fase"):
    order = list(range(len(names)))
    fig = go.Figure(go.Bar(
        x=[float(probs[i]) * 100 for i in order], y=[CLASS_LABELS.get(names[i], names[i]) for i in order],
        orientation="h", marker_color=[STAGE_COLORS.get(names[i], "#15803d") for i in order],
        text=[f"{float(probs[i]):.0%}" for i in order], textposition="auto",
        textfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#ffffff", size=12)))
    fig.update_xaxes(range=[0, 100])
    return _layout(fig, title, height=230, legend=False, xtitle="Tingkat Keyakinan AI (%)")


def forecast_line(hist_x, hist_y, pred_x, pred_y, title, ytitle, color, actual_y=None):
    fig = go.Figure()
    line_col = "#0d9488" if color == "#38bdf8" else "#d97706"
    h_hover = [_idx_to_day_label(i) for i in hist_x]
    p_hover = [_idx_to_day_label(i) for i in pred_x]
    fig.add_trace(go.Scatter(
        x=hist_x, y=hist_y, mode="lines+markers", name="Data Terakhir (4 Hari)",
        text=h_hover,
        hovertemplate="%{text}<br>Riwayat: <b>%{y:.1f}</b><extra></extra>",
        line=dict(color=line_col, width=2.8)
    ))
    fig.add_trace(go.Scatter(
        x=pred_x, y=pred_y, mode="lines+markers", name="Prakiraan AI (4 Hari ke Depan)",
        text=p_hover,
        hovertemplate="%{text}<br>Prakiraan AI: <b>%{y:.1f}</b><extra></extra>",
        line=dict(color="#15803d", width=2.8, dash="dash"),
        marker=dict(symbol="diamond", size=7, color="#15803d")
    ))
    if actual_y is not None:
        a_hover = p_hover[:len(actual_y)]
        fig.add_trace(go.Scatter(
            x=pred_x[:len(actual_y)], y=actual_y, mode="lines", name="Data Asli (Pembanding)",
            text=a_hover,
            hovertemplate="%{text}<br>Data Asli: <b>%{y:.1f}</b><extra></extra>",
            line=dict(color="#5c6f64", width=2, dash="dot")
        ))
    if hist_x:
        fig.add_vline(x=hist_x[-1], line_dash="dot", line_color="#94a89b", annotation_text="Batas Hari Ini", annotation_font_color="#5c6f64")
    return _layout(fig, title, height=320, xtitle="Urutan Pengukuran (3x Sehari)", ytitle=ytitle)


def maturity_forecast(pred_x, pred_y, thresholds, last_x=None, last_y=None):
    fig = go.Figure()
    p_hover = [_idx_to_day_label(i) for i in pred_x]
    fig.add_hrect(y0=0, y1=thresholds[0], fillcolor="#0d9488", opacity=0.06, line_width=0,
                  annotation_text="Zona Masa Pertumbuhan", annotation_position="top left", annotation_font_color="#0d9488")
    fig.add_hrect(y0=thresholds[0], y1=thresholds[1], fillcolor="#d97706", opacity=0.06, line_width=0,
                  annotation_text="Zona Mendekati Panen", annotation_position="top left", annotation_font_color="#d97706")
    fig.add_hrect(y0=thresholds[1], y1=100, fillcolor="#15803d", opacity=0.09, line_width=0,
                  annotation_text="Zona Siap Panen", annotation_position="top left", annotation_font_color="#15803d")
    fig.add_trace(go.Scatter(
        x=pred_x, y=pred_y, mode="lines+markers", name="Prakiraan Kematangan",
        text=p_hover,
        hovertemplate="%{text}<br>Prakiraan Kematangan: <b>%{y:.1f}%</b><extra></extra>",
        line=dict(color="#15803d", width=3), marker=dict(size=8, color="#15803d")
    ))
    fig.update_yaxes(range=[0, 100])
    return _layout(fig, "Prakiraan Tingkat Kematangan Tanaman 4 Hari ke Depan", height=340, legend=False,
                   xtitle="Urutan Pengukuran (12 Pengukuran = 4 Hari ke Depan)", ytitle="Tingkat Kematangan (%)")


def confusion_fig(cm, names, title):
    labels = [CLASS_LABELS.get(n, n) for n in names]
    z = np.asarray(cm)
    fig = go.Figure(go.Heatmap(z=z.tolist(), x=labels, y=labels,
                               colorscale=[[0, "#ffffff"], [0.2, "#dcfce7"], [1, "#15803d"]],
                               showscale=False,
                               text=z.astype(int).tolist(), texttemplate="%{text} data",
                               textfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=13.5, color="#111c16")))
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, title, height=340, legend=False, xtitle="Tebakan AI (Prediksi)", ytitle="Kondisi Sebenarnya")


def history_maturity_curve(df):
    """Kurva Kematangan Tanaman Pakcoy dari Hari ke-1 hingga Masa Panen (Hari ke-30)."""
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=33, fillcolor="#0d9488", opacity=0.07, line_width=0,
                  annotation_text="Fase Awal (0–33%)", annotation_position="top left", annotation_font_color="#0d9488")
    fig.add_hrect(y0=33, y1=66, fillcolor="#0284c7", opacity=0.06, line_width=0,
                  annotation_text="Fase Vegetatif (34–66%)", annotation_position="top left", annotation_font_color="#0284c7")
    fig.add_hrect(y0=66, y1=84, fillcolor="#d97706", opacity=0.07, line_width=0,
                  annotation_text="Mendekati Panen (67–84%)", annotation_position="top left", annotation_font_color="#d97706")
    fig.add_hrect(y0=84, y1=100, fillcolor="#15803d", opacity=0.10, line_width=0,
                  annotation_text="Siap Panen (85–100%)", annotation_position="top left", annotation_font_color="#15803d")
    
    col_day = "Day" if "Day" in df.columns else ("Hari" if "Hari" in df.columns else df.columns[0])
    col_mat = "Ground Truth Maturity Level (%)" if "Ground Truth Maturity Level (%)" in df.columns else MATURITY_COL
    
    g = df.groupby(col_day)[col_mat].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=g[col_day], y=g[col_mat], mode="lines+markers",
        name="Rata-rata Kematangan (%)",
        line=dict(color="#15803d", width=3.2),
        marker=dict(size=7, color="#15803d"),
        hovertemplate="Hari ke-%{x}<br>Kematangan: <b>%{y:.1f}%</b><extra></extra>"
    ))
    fig.update_xaxes(range=[0, 31.5], dtick=2)
    fig.update_yaxes(range=[0, 105])
    fig.update_layout(margin=dict(l=16, r=28, t=50, b=18))
    return _layout(fig, "Kurva Pertumbuhan Menuju Panen Raya (Hari ke-1 s.d. 30)", height=370, legend=False,
                   xtitle="Umur Tanaman (Hari ke-)", ytitle="Tingkat Kematangan (%)")


def history_daily_15times(df):
    """Pola Fluktuasi Harian Sensor untuk 15 Kali Pengecekan per Hari (06:00 s.d. 20:00)."""
    times_15 = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
    if "Time" in df.columns and len(df) > 0:
        g = df.groupby("Time")[["Soil Moisture (%)", "Temperature (°C)"]].mean().reindex(times_15).dropna(how="all")
    else:
        g = pd.DataFrame(columns=["Soil Moisture (%)", "Temperature (°C)"])
    
    x_lbls = [str(t) for t in g.index]
    moist_vals = g["Soil Moisture (%)"].round(1).tolist() if len(g) else []
    temp_vals = g["Temperature (°C)"].round(1).tolist() if len(g) else []
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_lbls, y=moist_vals, name="Kelembapan Tanah (%)",
        marker_color="#15803d",
        text=[f"{v:.1f}%" for v in moist_vals], textposition="outside",
        hovertemplate="Pukul <b>%{x}</b><br>Kelembapan: <b>%{y:.1f}%</b><extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=x_lbls, y=temp_vals, name="Suhu Udara (°C)",
        marker_color="#d97706",
        text=[f"{v:.1f}°C" for v in temp_vals], textposition="outside",
        hovertemplate="Pukul <b>%{x}</b><br>Suhu Udara: <b>%{y:.1f}°C</b><extra></extra>"
    ))
    max_y = max(moist_vals + temp_vals + [75.0])
    fig.update_layout(
        barmode="group",
        height=390,
        margin=dict(l=16, r=16, t=55, b=65),
        legend=dict(
            orientation="h",
            y=-0.26,
            x=0.5,
            xanchor="center",
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#5c6f64")
        )
    )
    fig.update_yaxes(range=[0, max_y * 1.2])
    return _layout(fig, "Profil Sensor 15 Kali Pengecekan Harian (06:00 – 20:00)", height=390, legend=True,
                   xtitle="Jam Pengecekan Sensor (15× Sehari)", ytitle="Nilai Rata-rata Pengukuran")


def history_sensor_trend(df):
    """Tren Kelembapan Tanah dan Suhu Udara Berdasarkan Hari Pertumbuhan (Hari 1–30)."""
    col_day = "Day" if "Day" in df.columns else ("Hari" if "Hari" in df.columns else df.columns[0])
    g = df.groupby(col_day)[["Soil Moisture (%)", "Temperature (°C)"]].mean().reset_index()
    
    fig = go.Figure()
    fig.add_hrect(y0=55, y1=76, fillcolor="#15803d", opacity=0.08, line_width=0,
                  annotation_text="Rentang Kelembapan Optimal (55–76%)", annotation_position="top left", annotation_font_color="#15803d")
    fig.add_trace(go.Scatter(
        x=g[col_day], y=g["Soil Moisture (%)"], mode="lines+markers",
        name="Kelembapan Tanah (%)", line=dict(color="#15803d", width=2.8), marker=dict(size=6),
        hovertemplate="Hari ke-%{x}<br>Kelembapan: <b>%{y:.1f}%</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=g[col_day], y=g["Temperature (°C)"], mode="lines+markers",
        name="Suhu Udara (°C)", line=dict(color="#d97706", width=2.8), marker=dict(size=6),
        hovertemplate="Hari ke-%{x}<br>Suhu: <b>%{y:.1f}°C</b><extra></extra>"
    ))
    fig.update_xaxes(range=[0, 31.5], dtick=2)
    fig.update_layout(
        margin=dict(l=16, r=28, t=52, b=30),
        legend=dict(orientation="h", y=-0.24, x=0.5, xanchor="center")
    )
    return _layout(fig, "Tren Sensor Sepanjang Siklus Tanam (Hari 1–30)", legend=True,
                   xtitle="Umur Tanaman (Hari ke-)", ytitle="Nilai Sensor")

