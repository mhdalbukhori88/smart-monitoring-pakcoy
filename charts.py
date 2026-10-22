"""Pembuat grafik Plotly untuk aplikasi Smart Farming Pakcoy."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils import CLASS_NAMES, CLASS_LABELS, MATURITY_COL

# Warna tema DESIGN.md
STAGE_COLORS = {
    "masa_pertumbuhan": "#533afd",  # Primary Indigo
    "mendekati_panen": "#9b6829",   # Lemon / Amber
    "siap_panen": "#00875a"         # Soft Green
}
COND_COLORS = {
    "Optimal": "#00875a",           # Soft Green
    "Dry": "#ea2261",               # Ruby
    "Wet": "#665efd"                # Primary Soft Indigo
}
GRID = "#eef2f6"
BORDER = "#e3e8ee"


def _layout(fig, title=None, height=340, legend=True, xtitle=None, ytitle=None):
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.02, font=dict(family="Inter, sans-serif", size=15, color="#0d253d", weight=600)) if title else None,
        height=height,
        margin=dict(l=14, r=14, t=52 if title else 18, b=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#273951"),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.22, font=dict(family="Inter, sans-serif", size=11, color="#64748d")),
        hovermode="closest",
    )
    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor=BORDER,
        linecolor=BORDER,
        tickfont=dict(family="Inter, sans-serif", size=11, color="#64748d"),
        title=dict(text=xtitle, font=dict(family="Inter, sans-serif", size=12, color="#273951")) if xtitle else None
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor=BORDER,
        linecolor=BORDER,
        tickfont=dict(family="Inter, sans-serif", size=11, color="#64748d"),
        title=dict(text=ytitle, font=dict(family="Inter, sans-serif", size=12, color="#273951")) if ytitle else None
    )
    return fig


def donut_condition(df):
    counts = df["Soil Condition"].value_counts().reindex(["Optimal", "Dry", "Wet"]).fillna(0)
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(), values=counts.values.tolist(), hole=0.62,
        marker=dict(colors=[COND_COLORS[k] for k in counts.index]), textinfo="percent+label", sort=False))
    return _layout(fig, "Distribusi Kondisi Tanah", height=360, legend=False)


def bar_stage(df):
    counts = df["Ground Truth Criteria"].value_counts().reindex(CLASS_NAMES).fillna(0)
    fig = go.Figure(go.Bar(
        x=[CLASS_LABELS[k] for k in counts.index], y=counts.values.tolist(),
        marker_color=[STAGE_COLORS[k] for k in counts.index],
        text=[int(v) for v in counts.values], textposition="outside"))
    return _layout(fig, "Distribusi Tahap Pertumbuhan", height=360, legend=False, ytitle="Jumlah data")


def maturity_curve(df):
    """Maturity terhadap DAP, diwarnai per tahap (rata-rata jika ada banyak siklus)."""
    g = df.groupby(["DAP", "Ground Truth Criteria"])[MATURITY_COL].mean().reset_index()
    fig = go.Figure()
    for k in CLASS_NAMES:
        d = g[g["Ground Truth Criteria"] == k]
        if len(d):
            fig.add_trace(go.Scatter(x=d["DAP"], y=d[MATURITY_COL], mode="lines+markers", name=CLASS_LABELS[k],
                                     line=dict(color=STAGE_COLORS[k], width=3), marker=dict(size=6)))
    return _layout(fig, "Tingkat Kematangan Pakcoy terhadap Hari Setelah Tanam (DAP)", height=380,
                   xtitle="DAP (hari)", ytitle="Maturity (%)")


def hist_moisture(df, dry, wet):
    fig = go.Figure(go.Histogram(x=df["Soil Moisture (%)"], nbinsx=30, marker_color="#533afd"))
    fig.add_vline(x=dry, line_dash="dash", line_color="#ea2261", annotation_text="Batas Kering", annotation_font_color="#ea2261")
    fig.add_vline(x=wet, line_dash="dash", line_color="#00875a", annotation_text="Batas Basah", annotation_font_color="#00875a")
    return _layout(fig, "Distribusi Kelembapan Tanah", legend=False, xtitle="Kelembapan (%)", ytitle="Jumlah")


def scatter_moist_temp(df, max_points=1500):
    d = df if len(df) <= max_points else df.sample(max_points, random_state=0)
    fig = go.Figure()
    for k in ["Wet", "Optimal", "Dry"]:
        s = d[d["Soil Condition"] == k]
        if len(s):
            fig.add_trace(go.Scatter(x=s["Soil Moisture (%)"], y=s["Temperature (°C)"], mode="markers", name=k,
                                     marker=dict(color=COND_COLORS[k], size=6, opacity=0.8)))
    return _layout(fig, "Kelembapan vs Suhu", xtitle="Kelembapan (%)", ytitle="Suhu (°C)")


def box_temp_stage(df):
    fig = go.Figure()
    for k in CLASS_NAMES:
        s = df[df["Ground Truth Criteria"] == k]
        if len(s):
            fig.add_trace(go.Box(y=s["Temperature (°C)"], name=CLASS_LABELS[k], marker_color=STAGE_COLORS[k], boxmean=True))
    return _layout(fig, "Suhu per Tahap Pertumbuhan", legend=False, ytitle="Suhu (°C)")


def live_line(hist, col, title, color, ytitle, dry=None, wet=None, trend=None, height=300):
    """Garis sensor yang bergerak. hist: dataframe ber-indeks Time_Index. trend: prediksi regresi (opsional)."""
    x = hist.index.tolist()
    y = hist[col].tolist()
    line_col = "#533afd" if "Moisture" in col or color == "#38bdf8" else "#9b6829"
    fill_col = "rgba(83, 58, 253, 0.06)" if line_col == "#533afd" else "rgba(155, 104, 41, 0.06)"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Sensor", line=dict(color=line_col, width=3),
                             fill="tozeroy", fillcolor=fill_col))
    if x:
        fig.add_trace(go.Scatter(x=[x[-1]], y=[y[-1]], mode="markers", name="Terbaru", marker=dict(color=line_col, size=10)))
    if trend is not None and len(trend) and x:
        tx = [x[-1] + i for i in range(1, len(trend) + 1)]
        fig.add_trace(go.Scatter(x=tx, y=list(trend), mode="lines", name="Tren (regresi)",
                                 line=dict(color="#ea2261", width=2, dash="dash")))
    if dry is not None:
        fig.add_hline(y=dry, line_dash="dot", line_color="#ea2261", annotation_text="Batas Kering", annotation_position="top left",
                      annotation_font_color="#ea2261")
    if wet is not None:
        fig.add_hline(y=wet, line_dash="dot", line_color="#00875a", annotation_text="Batas Basah", annotation_position="top left",
                      annotation_font_color="#00875a")
    return _layout(fig, title, height=height, xtitle="Pembacaan ke-", ytitle=ytitle)


def growth_curve(grow, thresholds):
    """Kurva maturity sejak awal tanam, dengan zona tahap."""
    x = grow.index.tolist()
    y = grow[MATURITY_COL].tolist()
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=thresholds[0], fillcolor="#533afd", opacity=0.06, line_width=0)
    fig.add_hrect(y0=thresholds[0], y1=thresholds[1], fillcolor="#9b6829", opacity=0.06, line_width=0)
    fig.add_hrect(y0=thresholds[1], y1=100, fillcolor="#00875a", opacity=0.08, line_width=0)
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Maturity", line=dict(color="#00875a", width=3)))
    if x:
        fig.add_trace(go.Scatter(x=[x[-1]], y=[y[-1]], mode="markers", name="Sekarang", marker=dict(color="#00875a", size=10)))
    fig.update_yaxes(range=[0, 100])
    return _layout(fig, "Perkembangan maturity sejak awal tanam", height=300, legend=False,
                   xtitle="Pembacaan ke-", ytitle="Maturity (%)")


def gauge(value, title, thresholds=(66.5, 89.0)):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=float(value), number=dict(suffix="%", font=dict(family="Inter, sans-serif", color="#0d253d")),
        title=dict(text=title, font=dict(family="Inter, sans-serif", size=14, color="#0d253d")),
        gauge=dict(axis=dict(range=[0, 100], tickfont=dict(family="Inter, sans-serif", color="#64748d")),
                   bar=dict(color="#533afd", thickness=0.25),
                   steps=[dict(range=[0, thresholds[0]], color="rgba(83, 58, 253, 0.15)"),
                          dict(range=[thresholds[0], thresholds[1]], color="rgba(155, 104, 41, 0.20)"),
                          dict(range=[thresholds[1], 100], color="rgba(0, 135, 90, 0.25)")])))
    fig.update_layout(template="plotly_white", height=280, margin=dict(l=20, r=20, t=60, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", size=13, color="#0d253d"))
    return fig


def prob_bar(probs, names, title="Probabilitas tiap kelas"):
    order = list(range(len(names)))
    fig = go.Figure(go.Bar(
        x=[float(probs[i]) * 100 for i in order], y=[CLASS_LABELS.get(names[i], names[i]) for i in order],
        orientation="h", marker_color=[STAGE_COLORS.get(names[i], "#533afd") for i in order],
        text=[f"{float(probs[i]):.0%}" for i in order], textposition="auto",
        textfont=dict(family="Inter, sans-serif", color="#ffffff", size=12)))
    fig.update_xaxes(range=[0, 100])
    return _layout(fig, title, height=230, legend=False, xtitle="Probabilitas (%)")


def forecast_line(hist_x, hist_y, pred_x, pred_y, title, ytitle, color, actual_y=None):
    fig = go.Figure()
    line_col = "#533afd" if color == "#38bdf8" else "#9b6829"
    fig.add_trace(go.Scatter(x=hist_x, y=hist_y, mode="lines+markers", name="Riwayat", line=dict(color=line_col, width=3)))
    fig.add_trace(go.Scatter(x=pred_x, y=pred_y, mode="lines+markers", name="Prediksi LSTM",
                             line=dict(color="#665efd", width=3, dash="dash"), marker=dict(symbol="diamond", size=8, color="#665efd")))
    if actual_y is not None:
        fig.add_trace(go.Scatter(x=pred_x[:len(actual_y)], y=actual_y, mode="lines", name="Sebenarnya (data)",
                                 line=dict(color="#64748d", width=2, dash="dot")))
    if hist_x:
        fig.add_vline(x=hist_x[-1], line_dash="dot", line_color="#a8c3de", annotation_text="sekarang", annotation_font_color="#64748d")
    return _layout(fig, title, height=320, xtitle="Pembacaan ke-", ytitle=ytitle)


def maturity_forecast(pred_x, pred_y, thresholds, last_x=None, last_y=None):
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=thresholds[0], fillcolor="#533afd", opacity=0.06, line_width=0,
                  annotation_text="Masa Pertumbuhan", annotation_position="top left", annotation_font_color="#533afd")
    fig.add_hrect(y0=thresholds[0], y1=thresholds[1], fillcolor="#9b6829", opacity=0.06, line_width=0,
                  annotation_text="Mendekati Panen", annotation_position="top left", annotation_font_color="#9b6829")
    fig.add_hrect(y0=thresholds[1], y1=100, fillcolor="#00875a", opacity=0.08, line_width=0,
                  annotation_text="Siap Panen", annotation_position="top left", annotation_font_color="#00875a")
    fig.add_trace(go.Scatter(x=pred_x, y=pred_y, mode="lines+markers", name="Maturity prediksi",
                             line=dict(color="#00875a", width=3), marker=dict(size=8, color="#00875a")))
    fig.update_yaxes(range=[0, 100])
    return _layout(fig, "Prediksi maturity 4 hari ke depan", height=340, legend=False,
                   xtitle="Pembacaan ke-", ytitle="Maturity (%)")


def confusion_fig(cm, names, title):
    labels = [CLASS_LABELS.get(n, n) for n in names]
    z = np.asarray(cm)
    fig = go.Figure(go.Heatmap(z=z.tolist(), x=labels, y=labels,
                               colorscale=[[0, "#ffffff"], [0.2, "#f0f1fe"], [1, "#533afd"]],
                               showscale=False,
                               text=z.astype(int).tolist(), texttemplate="%{text}",
                               textfont=dict(family="Inter, sans-serif", size=14, color="#0d253d")))
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, title, height=340, legend=False, xtitle="Prediksi", ytitle="Sebenarnya")
