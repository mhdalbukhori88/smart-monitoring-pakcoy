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
        marker=dict(colors=[COND_COLORS[k] for k in counts.index], line=dict(color="#ffffff", width=2)),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        sort=False,
        direction="clockwise",
        hovertemplate="<b>%{label}</b><br>Jumlah: %{value:,} data (%{percent})<extra></extra>",
    ))
    fig = _layout(fig, "Proporsi Kondisi Kelembapan Tanah", height=360, legend=True)
    fig.update_layout(
        title=dict(text="Proporsi Kondisi Kelembapan Tanah", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0.5, xanchor="center",
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11.5, color="#2c3e35")),
        margin=dict(l=14, r=14, t=54, b=42),
    )
    return fig


def bar_stage(df):
    col = "Fase" if "Fase" in df.columns and any(k in df["Fase"].values for k in ["Fase Awal", "Fase Vegetatif"]) else "Ground Truth Criteria"
    if col not in df.columns or len(df) == 0:
        return go.Figure()
    counts = df[col].value_counts()
    matching = [k for k in CLASS_NAMES if k in counts.index]
    if matching:
        counts = counts.reindex(CLASS_NAMES).fillna(0)
        x_vals = [CLASS_LABELS.get(k, k) for k in counts.index]
        colors = [STAGE_COLORS.get(k, "#15803d") for k in counts.index]
    else:
        x_vals = [str(k) for k in counts.index]
        palette = ["#0d9488", "#15803d", "#d97706", "#0284c7", "#8b5cf6"]
        colors = [palette[i % len(palette)] for i in range(len(counts))]
    vals = [int(v) for v in counts.values]
    fig = go.Figure(go.Bar(
        x=x_vals, y=vals,
        marker=dict(color=colors, line=dict(width=0)),
        width=0.52,
        text=[f"{v:,}" for v in vals], textposition="outside",
        textfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11.5, color="#2c3e35"),
        hovertemplate="<b>%{x}</b><br>Jumlah: <b>%{y:,} pengukuran</b><extra></extra>",
    ))
    max_v = max(vals + [1])
    fig = _layout(fig, "Jumlah Data per Fase Pertumbuhan", height=360, legend=False, ytitle="Jumlah Pengukuran")
    fig.update_yaxes(range=[0, max_v * 1.18])
    fig.update_layout(
        title=dict(text="Jumlah Data per Fase Pertumbuhan", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=16, t=54, b=36),
    )
    return fig


def maturity_curve(df):
    """Maturity terhadap Umur Tanaman, diwarnai per tahap (rata-rata jika ada banyak siklus)."""
    col_age = "Day" if "Day" in df.columns else ("DAP" if "DAP" in df.columns else df.columns[0])
    fig = go.Figure()
    if "Ground Truth Criteria" in df.columns and MATURITY_COL in df.columns:
        g = df.groupby([col_age, "Ground Truth Criteria"])[MATURITY_COL].mean().reset_index()
        for k in CLASS_NAMES:
            d = g[g["Ground Truth Criteria"] == k]
            if len(d):
                fig.add_trace(go.Scatter(
                    x=d[col_age], y=d[MATURITY_COL], mode="lines+markers", name=CLASS_LABELS[k],
                    line=dict(color=STAGE_COLORS[k], width=3, shape="spline", smoothing=0.45),
                    marker=dict(size=6, line=dict(width=1.2, color="#ffffff")),
                    hovertemplate="Hari ke-%{x}<br>" + CLASS_LABELS[k] + ": <b>%{y:.1f}%</b><extra></extra>",
                ))
    if len(fig.data) == 0 and len(df) > 0 and MATURITY_COL in df.columns:
        g_all = df.groupby(col_age)[MATURITY_COL].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=g_all[col_age], y=g_all[MATURITY_COL], mode="lines+markers",
            name="Rata-rata Kematangan (%)",
            line=dict(color="#15803d", width=3, shape="spline", smoothing=0.45),
            marker=dict(size=6, line=dict(width=1.2, color="#ffffff")),
            hovertemplate="Hari ke-%{x}<br>Kematangan: <b>%{y:.1f}%</b><extra></extra>",
        ))
    fig = _layout(fig, "Rata-rata Kematangan Tanaman dari Hari ke-1 hingga Panen (Hari ke-30)", height=365,
                  xtitle="Umur Tanaman (Hari ke-)", ytitle="Tingkat Kematangan (%)")
    fig.update_yaxes(range=[0, 106], ticksuffix="%")
    fig.update_layout(
        title=dict(text="Rata-rata Kematangan Tanaman dari Hari ke-1 hingga Panen (Hari ke-30)", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=18, t=82, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0.0,
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11.5, color="#2c3e35")),
        hovermode="x unified",
    )
    return fig


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


def _day_ticks_from_indices(indices, max_ticks=8):
    """Bangun posisi tick dan label 'Hari ke-N' yang rapi dari daftar Time_Index."""
    if not indices:
        return [], []
    day_first = {}
    for idx in indices:
        try:
            d = (int(idx) - 1) // 3 + 1
        except Exception:
            continue
        if d not in day_first:
            day_first[d] = idx
    days = sorted(day_first.keys())
    if not days:
        return [], []
    step = max(1, (len(days) + max_ticks - 1) // max_ticks)
    chosen = days[::step]
    if days[-1] not in chosen:
        chosen.append(days[-1])
    return [day_first[d] for d in chosen], [f"Hari {d}" for d in chosen]


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
    tvals, ttext = _day_ticks_from_indices(x, max_ticks=7)
    fig = _layout(fig, title, height=height, xtitle="Umur Tanaman (Hari ke-)", ytitle=ytitle)
    fig.update_layout(
        title=dict(text=title, x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=16, t=78, b=46),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0.0,
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#2c3e35")),
    )
    if tvals:
        fig.update_xaxes(tickmode="array", tickvals=tvals, ticktext=ttext)
    return fig


def growth_curve(grow, thresholds):
    """Kurva maturity sejak awal tanam, dengan zona tahap."""
    x = grow.index.tolist()
    y = grow[MATURITY_COL].tolist()
    hover_txt = [_idx_to_day_label(i) for i in x]
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=thresholds[0], fillcolor="rgba(13, 148, 136, 0.045)", line_width=0)
    fig.add_hrect(y0=thresholds[0], y1=thresholds[1], fillcolor="rgba(217, 119, 6, 0.055)", line_width=0)
    fig.add_hrect(y0=thresholds[1], y1=100, fillcolor="rgba(21, 128, 61, 0.075)", line_width=0)
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name="Tingkat Kematangan",
        text=hover_txt,
        hovertemplate="%{text}<br>Kematangan: <b>%{y:.1f}%</b><extra></extra>",
        line=dict(color="#15803d", width=3, shape="spline", smoothing=0.45)
    ))
    if x:
        fig.add_trace(go.Scatter(
            x=[x[-1]], y=[y[-1]], mode="markers", name="Sekarang",
            text=[hover_txt[-1]],
            hovertemplate="%{text}<br>Sekarang: <b>%{y:.1f}%</b><extra></extra>",
            marker=dict(color="#15803d", size=9, line=dict(width=1.5, color="#ffffff"))
        ))
    fig.update_yaxes(range=[0, 104], ticksuffix="%")
    tvals, ttext = _day_ticks_from_indices(x, max_ticks=8)
    fig = _layout(fig, "Kurva Pertumbuhan & Kematangan Sejak Awal Tanam", height=300, legend=False,
                  xtitle="Umur Tanaman (Hari ke-)", ytitle="Tingkat Kematangan (%)")
    fig.update_layout(
        title=dict(text="Kurva Pertumbuhan & Kematangan Sejak Awal Tanam", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=16, t=54, b=46),
    )
    if tvals:
        fig.update_xaxes(tickmode="array", tickvals=tvals, ticktext=ttext)
    return fig


def gauge(value, title, thresholds=(66.5, 89.0)):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=float(value), number=dict(suffix="%", font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#111c16")),
        title=dict(text=title, font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14, color="#111c16", weight=600)),
        gauge=dict(axis=dict(range=[0, 100], tickfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#5c6f64")),
                   bar=dict(color="#15803d", thickness=0.26),
                   steps=[dict(range=[0, thresholds[0]], color="rgba(13, 148, 136, 0.12)"),
                          dict(range=[thresholds[0], thresholds[1]], color="rgba(217, 119, 6, 0.14)"),
                          dict(range=[thresholds[1], 100], color="rgba(21, 128, 61, 0.20)")])))
    fig.update_layout(template="plotly_white", height=290, margin=dict(l=20, r=20, t=58, b=12),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=13, color="#111c16"))
    return fig


def prob_bar(probs, names, title="Tingkat Keyakinan AI untuk Tiap Fase"):
    order = list(range(len(names)))
    fig = go.Figure(go.Bar(
        x=[float(probs[i]) * 100 for i in order], y=[CLASS_LABELS.get(names[i], names[i]) for i in order],
        orientation="h", marker_color=[STAGE_COLORS.get(names[i], "#15803d") for i in order],
        text=[f"{float(probs[i]):.0%}" for i in order], textposition="auto",
        textfont=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#ffffff", size=12),
        hovertemplate="<b>%{y}</b><br>Keyakinan AI: <b>%{x:.1f}%</b><extra></extra>",
    ))
    fig.update_xaxes(range=[0, 105], ticksuffix="%")
    fig = _layout(fig, title, height=290, legend=False, xtitle="Tingkat Keyakinan AI (%)")
    fig.update_layout(
        title=dict(text=title, x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=14, r=18, t=54, b=42),
    )
    return fig


def forecast_line(
    hist_x,
    hist_y,
    pred_x,
    pred_y,
    title,
    ytitle,
    color,
    actual_y=None,
    ideal_range=None,
    ideal_label=None,
    hist_hover=None,
    pred_hover=None,
    tickvals=None,
    ticktext=None,
    xtitle="Hari Pengamatan & Proyeksi",
    unit="",
    show_markers=True,
    height=370,
):
    fig = go.Figure()
    is_moisture = (color == "#38bdf8") or ("Kelembapan" in str(ytitle))
    hist_col = "#0284c7" if is_moisture else "#d97706"
    pred_col = "#15803d"
    actual_col = "#64748b"

    if ideal_range is None:
        ideal_range = (55.0, 76.0) if is_moisture else (22.0, 28.0)
    if ideal_label is None:
        ideal_label = "Zona Ideal (55–76%)" if is_moisture else "Zona Ideal (22–28°C)"
    if not unit:
        unit = "%" if is_moisture else "°C"

    h_hover = hist_hover if hist_hover is not None else [_idx_to_day_label(i) for i in hist_x]
    p_hover = pred_hover if pred_hover is not None else [_idx_to_day_label(i) for i in pred_x]

    # Area bayangan zona ideal (lembut di latar belakang)
    y0, y1 = float(ideal_range[0]), float(ideal_range[1])
    fig.add_hrect(
        y0=y0,
        y1=y1,
        fillcolor="rgba(21, 128, 61, 0.075)",
        line_width=0,
        layer="below",
    )
    fig.add_hline(y=y0, line_dash="dot", line_color="rgba(21, 128, 61, 0.25)", line_width=1)
    fig.add_hline(y=y1, line_dash="dot", line_color="rgba(21, 128, 61, 0.25)", line_width=1)
    # Posisi label zona ideal adaptif (menghindari garis data pada sisi kiri)
    y_mid = (y0 + y1) / 2.0
    first_y = float(hist_y[0]) if hist_y else y_mid
    if first_y >= y_mid:
        lbl_y, lbl_anchor, lbl_shift = y0, "bottom", 3
    else:
        lbl_y, lbl_anchor, lbl_shift = y1, "top", -3
    fig.add_annotation(
        x=0.01,
        xref="paper",
        xanchor="left",
        y=lbl_y,
        yref="y",
        yanchor=lbl_anchor,
        yshift=lbl_shift,
        text=ideal_label,
        showarrow=False,
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=10, color="#15803d"),
        bgcolor="rgba(240, 253, 244, 0.90)",
        borderpad=2,
    )

    trace_mode = "lines+markers" if show_markers else "lines"
    hist_marker = dict(size=6, symbol="circle", color=hist_col, line=dict(width=1.5, color="#ffffff"))
    pred_marker = dict(size=6.5, symbol="circle", color=pred_col, line=dict(width=1.5, color="#ffffff"))

    # Data Historis (garis solid halus)
    fig.add_trace(go.Scatter(
        x=hist_x,
        y=hist_y,
        mode=trace_mode,
        name="Historis (4 Hari)",
        customdata=h_hover,
        hovertemplate="<b>%{customdata}</b><br>Historis: <b>%{y:.1f}" + unit + "</b><extra></extra>",
        line=dict(color=hist_col, width=3, shape="spline", smoothing=0.55),
        marker=hist_marker if show_markers else None,
    ))

    # Garis sambungan halus antara titik terakhir historis & titik pertama prakiraan
    if hist_x and pred_x:
        fig.add_trace(go.Scatter(
            x=[hist_x[-1], pred_x[0]],
            y=[hist_y[-1], pred_y[0]],
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
            line=dict(color=pred_col, width=3, dash="dash"),
        ))

    # Prakiraan AI (garis putus-putus halus, tanpa penanda berlian)
    fig.add_trace(go.Scatter(
        x=pred_x,
        y=pred_y,
        mode=trace_mode,
        name="Prakiraan AI (H+1–H+4)",
        customdata=p_hover,
        hovertemplate="<b>%{customdata}</b><br>Prakiraan AI: <b>%{y:.1f}" + unit + "</b><extra></extra>",
        line=dict(color=pred_col, width=3, dash="dash", shape="spline", smoothing=0.55),
        marker=pred_marker if show_markers else None,
    ))

    # Garis pembanding data asli (opsional, dikontrol toggle yang default-nya mati)
    if actual_y is not None and len(actual_y) > 0:
        valid_pairs = [(px, ay, ph) for px, ay, ph in zip(pred_x, actual_y, p_hover) if ay is not None and not pd.isna(ay)]
        if valid_pairs:
            ax_vals = [p[0] for p in valid_pairs]
            ay_vals = [p[1] for p in valid_pairs]
            a_hover = [p[2] for p in valid_pairs]
            if hist_x:
                fig.add_trace(go.Scatter(
                    x=[hist_x[-1], ax_vals[0]],
                    y=[hist_y[-1], ay_vals[0]],
                    mode="lines",
                    showlegend=False,
                    hoverinfo="skip",
                    line=dict(color=actual_col, width=2, dash="dot"),
                ))
            fig.add_trace(go.Scatter(
                x=ax_vals,
                y=ay_vals,
                mode="lines",
                name="Data Asli Kebun",
                customdata=a_hover,
                hovertemplate="<b>%{customdata}</b><br>Data Asli: <b>%{y:.1f}" + unit + "</b><extra></extra>",
                line=dict(color=actual_col, width=2.2, dash="dot", shape="spline", smoothing=0.5),
            ))

    # Garis & label "Batas Hari Ini" dengan jarak aman agar tidak menimpa garis data
    if hist_x:
        fig.add_vline(
            x=hist_x[-1],
            line_dash="dot",
            line_color="#94a89b",
            line_width=1.5,
        )
        fig.add_annotation(
            x=hist_x[-1],
            xref="x",
            xanchor="left",
            xshift=7,
            y=0.98,
            yref="paper",
            yanchor="top",
            text="Batas Hari Ini",
            showarrow=False,
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=10.5, color="#475569"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#dce5de",
            borderwidth=1,
            borderpad=3,
        )

    # Hitung rentang Y dengan ruang lega di atas agar anotasi tidak bertumpuk garis
    all_vals = [v for v in (list(hist_y) + list(pred_y) + [y0, y1]) if v is not None and not pd.isna(v)]
    if actual_y is not None:
        all_vals += [v for v in actual_y if v is not None and not pd.isna(v)]
    if all_vals:
        vmin, vmax = min(all_vals), max(all_vals)
        span = max(vmax - vmin, 6.0 if not is_moisture else 12.0)
        y_low = max(0.0, vmin - span * 0.16) if is_moisture else vmin - span * 0.18
        y_high = min(100.0, vmax + span * 0.32) if is_moisture else vmax + span * 0.34
        fig.update_yaxes(range=[y_low, y_high])

    _layout(fig, title, height=height, legend=True, xtitle=xtitle, ytitle=ytitle)
    fig.update_layout(
        title=dict(
            text=title,
            x=0.0,
            y=0.98,
            xanchor="left",
            yanchor="top",
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600),
        ),
        margin=dict(l=16, r=18, t=84, b=54),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#2c3e35"),
            itemclick="toggleothers",
        ),
        hovermode="x unified",
    )
    if tickvals is not None and ticktext is not None:
        fig.update_xaxes(
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=0,
            title_standoff=12,
        )
    else:
        fig.update_xaxes(title_standoff=12)
    return fig


def maturity_forecast(
    pred_x,
    pred_y,
    thresholds,
    last_x=None,
    last_y=None,
    hist_x=None,
    hist_y=None,
    tickvals=None,
    ticktext=None,
    hist_hover=None,
    pred_hover=None,
    xtitle="Hari Pengamatan & Proyeksi (H+1 s.d. H+4)",
    show_markers=True,
    height=345,
):
    fig = go.Figure()
    t1, t2 = float(thresholds[0]), float(thresholds[1])
    p_hover = pred_hover if pred_hover is not None else [_idx_to_day_label(i) for i in pred_x]
    h_hover = hist_hover if hist_hover is not None else ([_idx_to_day_label(i) for i in hist_x] if hist_x else [])

    # Zona kematangan dengan warna lembut agar garis kurva tetap dominan & mudah dibaca
    fig.add_hrect(y0=0, y1=t1, fillcolor="rgba(13, 148, 136, 0.045)", line_width=0, layer="below")
    fig.add_hrect(y0=t1, y1=t2, fillcolor="rgba(217, 119, 6, 0.055)", line_width=0, layer="below")
    fig.add_hrect(y0=t2, y1=100, fillcolor="rgba(21, 128, 61, 0.075)", line_width=0, layer="below")

    fig.add_hline(y=t1, line_dash="dot", line_color="rgba(217, 119, 6, 0.35)", line_width=1)
    fig.add_hline(y=t2, line_dash="dot", line_color="rgba(21, 128, 61, 0.40)", line_width=1)

    zone_labels = [
        (t1 * 0.48, f"Masa Pertumbuhan (< {t1:.1f}%)", "#0f766e"),
        ((t1 + t2) / 2.0, f"Mendekati Panen ({t1:.1f}–{t2:.1f}%)", "#b45309"),
        (min(97.0, t2 + (100.0 - t2) * 0.52), f"Siap Panen (≥ {t2:.1f}%)", "#15803d"),
    ]
    for zy, ztxt, zcol in zone_labels:
        fig.add_annotation(
            x=0.99,
            xref="paper",
            xanchor="right",
            y=zy,
            yref="y",
            yanchor="middle",
            text=ztxt,
            showarrow=False,
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=10.5, color=zcol),
            bgcolor="rgba(255, 255, 255, 0.65)",
            borderpad=2,
        )

    trace_mode = "lines+markers" if show_markers else "lines"

    if hist_x and hist_y:
        fig.add_trace(go.Scatter(
            x=hist_x,
            y=hist_y,
            mode=trace_mode,
            name="Historis (4 Hari)",
            customdata=h_hover,
            hovertemplate="<b>%{customdata}</b><br>Kematangan Historis: <b>%{y:.1f}%</b><extra></extra>",
            line=dict(color="#0d9488", width=3, shape="spline", smoothing=0.5),
            marker=dict(size=6, symbol="circle", color="#0d9488", line=dict(width=1.5, color="#ffffff")) if show_markers else None,
        ))
        if pred_x:
            fig.add_trace(go.Scatter(
                x=[hist_x[-1], pred_x[0]],
                y=[hist_y[-1], pred_y[0]],
                mode="lines",
                showlegend=False,
                hoverinfo="skip",
                line=dict(color="#15803d", width=3, dash="dash"),
            ))
        fig.add_vline(
            x=hist_x[-1],
            line_dash="dot",
            line_color="#94a89b",
            line_width=1.5,
        )
        fig.add_annotation(
            x=hist_x[-1],
            xref="x",
            xanchor="left",
            xshift=7,
            y=0.98,
            yref="paper",
            yanchor="top",
            text="Batas Hari Ini",
            showarrow=False,
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=10.5, color="#475569"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#dce5de",
            borderwidth=1,
            borderpad=3,
        )

    fig.add_trace(go.Scatter(
        x=pred_x,
        y=pred_y,
        mode=trace_mode,
        name="Prakiraan Kematangan (H+1–H+4)",
        customdata=p_hover,
        hovertemplate="<b>%{customdata}</b><br>Prakiraan Kematangan: <b>%{y:.1f}%</b><extra></extra>",
        line=dict(color="#15803d", width=3.2, dash="dash" if (hist_x and hist_y) else "solid", shape="spline", smoothing=0.5),
        marker=dict(size=7, symbol="circle", color="#15803d", line=dict(width=1.5, color="#ffffff")) if show_markers else None,
    ))

    fig.update_yaxes(range=[0, 106], ticksuffix="%")
    _layout(
        fig,
        "Prakiraan Tingkat Kematangan Tanaman 4 Hari ke Depan",
        height=height,
        legend=bool(hist_x and hist_y),
        xtitle=xtitle,
        ytitle="Tingkat Kematangan (%)",
    )
    fig.update_layout(
        title=dict(
            text="Prakiraan Tingkat Kematangan Tanaman 4 Hari ke Depan",
            x=0.0,
            y=0.98,
            xanchor="left",
            yanchor="top",
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600),
        ),
        margin=dict(l=16, r=18, t=82 if (hist_x and hist_y) else 56, b=54),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11, color="#2c3e35"),
        ),
        hovermode="x unified",
    )
    if tickvals is not None and ticktext is not None:
        fig.update_xaxes(
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=0,
            title_standoff=12,
        )
    else:
        fig.update_xaxes(title_standoff=12)
    return fig


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
    zones = [
        (0, 33, "rgba(13, 148, 136, 0.045)", 16, "Fase Awal (0–33%)", "#0f766e"),
        (33, 66, "rgba(2, 132, 199, 0.045)", 50, "Fase Vegetatif (34–66%)", "#0369a1"),
        (66, 84, "rgba(217, 119, 6, 0.055)", 75, "Mendekati Panen (67–84%)", "#b45309"),
        (84, 100, "rgba(21, 128, 61, 0.075)", 93, "Siap Panen (85–100%)", "#15803d"),
    ]
    for y0, y1, fcol, zy, ztxt, zcol in zones:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=fcol, line_width=0, layer="below")
        fig.add_annotation(
            x=0.99, xref="paper", xanchor="right", y=zy, yref="y", yanchor="middle",
            text=ztxt, showarrow=False,
            font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=10.5, color=zcol),
            bgcolor="rgba(255,255,255,0.68)", borderpad=2,
        )

    col_day = "Day" if "Day" in df.columns else ("Hari" if "Hari" in df.columns else df.columns[0])
    col_mat = "Ground Truth Maturity Level (%)" if "Ground Truth Maturity Level (%)" in df.columns else MATURITY_COL

    g = df.groupby(col_day)[col_mat].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=g[col_day], y=g[col_mat], mode="lines+markers",
        name="Rata-rata Kematangan (%)",
        line=dict(color="#15803d", width=3.2, shape="spline", smoothing=0.45),
        marker=dict(size=6.5, color="#15803d", line=dict(width=1.4, color="#ffffff")),
        hovertemplate="<b>Hari ke-%{x}</b><br>Kematangan: <b>%{y:.1f}%</b><extra></extra>"
    ))
    fig.update_xaxes(range=[0.5, 31], dtick=2)
    fig.update_yaxes(range=[0, 106], ticksuffix="%")
    fig = _layout(fig, "Kurva Pertumbuhan Menuju Panen Raya (Hari ke-1 s.d. 30)", height=360, legend=False,
                  xtitle="Umur Tanaman (Hari ke-)", ytitle="Tingkat Kematangan (%)")
    fig.update_layout(
        title=dict(text="Kurva Pertumbuhan Menuju Panen Raya (Hari ke-1 s.d. 30)", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=18, t=54, b=46),
        hovermode="x unified",
    )
    return fig


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
        marker=dict(color="rgba(21, 128, 61, 0.78)", line=dict(width=0)),
        width=0.56,
        hovertemplate="Kelembapan Tanah: <b>%{y:.1f}%</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x_lbls, y=temp_vals, name="Suhu Udara (°C)",
        mode="lines+markers",
        line=dict(color="#d97706", width=3, shape="spline", smoothing=0.5),
        marker=dict(size=7, color="#d97706", line=dict(width=1.5, color="#ffffff")),
        hovertemplate="Suhu Udara: <b>%{y:.1f}°C</b><extra></extra>",
    ))
    max_y = max(moist_vals + temp_vals + [75.0])
    fig = _layout(fig, "Profil Sensor 15 Kali Pengecekan Harian (06:00 – 20:00)", height=370, legend=True,
                  xtitle="Jam Pengecekan Sensor (15× Sehari)", ytitle="Rata-rata Nilai Sensor")
    fig.update_yaxes(range=[0, max_y * 1.18])
    fig.update_layout(
        title=dict(text="Profil Sensor 15 Kali Pengecekan Harian (06:00 – 20:00)", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=18, t=82, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0.0,
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11.5, color="#2c3e35")),
        hovermode="x unified",
    )
    return fig


def history_sensor_trend(df):
    """Tren Kelembapan Tanah dan Suhu Udara Berdasarkan Hari Pertumbuhan (Hari 1–30)."""
    col_day = "Day" if "Day" in df.columns else ("Hari" if "Hari" in df.columns else df.columns[0])
    g = df.groupby(col_day)[["Soil Moisture (%)", "Temperature (°C)"]].mean().reset_index()

    fig = go.Figure()
    fig.add_hrect(y0=55, y1=76, fillcolor="rgba(21, 128, 61, 0.07)", line_width=0, layer="below")
    fig.add_annotation(
        x=0.99, xref="paper", xanchor="right", y=76, yref="y", yanchor="bottom", yshift=2,
        text="Zona Kelembapan Ideal (55–76%)", showarrow=False,
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=10, color="#15803d"),
        bgcolor="rgba(240,253,244,0.88)", borderpad=2,
    )
    fig.add_trace(go.Scatter(
        x=g[col_day], y=g["Soil Moisture (%)"], mode="lines+markers",
        name="Kelembapan Tanah (%)",
        line=dict(color="#15803d", width=2.8, shape="spline", smoothing=0.45),
        marker=dict(size=5.5, color="#15803d", line=dict(width=1.2, color="#ffffff")),
        hovertemplate="Kelembapan: <b>%{y:.1f}%</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=g[col_day], y=g["Temperature (°C)"], mode="lines+markers",
        name="Suhu Udara (°C)",
        line=dict(color="#d97706", width=2.8, shape="spline", smoothing=0.45),
        marker=dict(size=5.5, color="#d97706", line=dict(width=1.2, color="#ffffff")),
        hovertemplate="Suhu: <b>%{y:.1f}°C</b><extra></extra>"
    ))
    fig.update_xaxes(range=[0.5, 31], dtick=2)
    fig = _layout(fig, "Tren Sensor Sepanjang Siklus Tanam (Hari 1–30)", height=360, legend=True,
                  xtitle="Umur Tanaman (Hari ke-)", ytitle="Nilai Sensor")
    fig.update_layout(
        title=dict(text="Tren Sensor Sepanjang Siklus Tanam (Hari 1–30)", x=0.0, y=0.98, xanchor="left", yanchor="top",
                   font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=14.5, color="#111c16", weight=600)),
        margin=dict(l=16, r=18, t=82, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0.0,
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", size=11.5, color="#2c3e35")),
        hovermode="x unified",
    )
    return fig

