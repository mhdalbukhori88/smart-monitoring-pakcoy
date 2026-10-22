"""Fungsi pendukung aplikasi monitoring pakcoy (tanpa TensorFlow/Streamlit)."""
import json
from datetime import datetime

import numpy as np
import pandas as pd
from PIL import Image

CLASS_NAMES = ["masa_pertumbuhan", "mendekati_panen", "siap_panen"]
CLASS_LABELS = {
    "masa_pertumbuhan": "Masa Pertumbuhan",
    "mendekati_panen": "Mendekati Panen",
    "siap_panen": "Siap Panen",
}
JAM_MAP = {"08:00": 0, "12:00": 1, "16:00": 2}
JAM_LIST = ["08:00", "12:00", "16:00"]
SENSOR_COLS = ["Soil Moisture (%)", "Temperature (°C)"]
MATURITY_COL = "Ground Truth Maturity Level (%)"
REQUIRED_COLS = ["Day", "DAP", "Time", "Soil Moisture (%)", "Temperature (°C)",
                 "Soil Condition", MATURITY_COL, "Ground Truth Criteria"]

DRY_LIMIT = 55.0   # batas kering (%), sama dengan aturan label Dry di Data_Training
WET_LIMIT = 76.0   # batas basah (%)

# Informasi umum agronomi pakcoy (bukan hasil model).
STAGE_INFO = {
    "masa_pertumbuhan": {
        "ciri": "Bibit sampai fase vegetatif: daun masih kecil hingga mulai melebar, tanaman belum membentuk roset yang padat.",
        "saran": "Jaga kelembapan tanah tetap stabil, siram teratur, dan pantau hama pada daun muda.",
    },
    "mendekati_panen": {
        "ciri": "Daun makin lebar, roset mulai padat, tangkai daun menebal, dan warna daun semakin hijau pekat.",
        "saran": "Pertahankan penyiraman, kurangi gangguan pada tanaman, dan siapkan jadwal panen.",
    },
    "siap_panen": {
        "ciri": "Daun lebar dan penuh, tangkai tebal, tanaman rimbun. Pakcoy umumnya dipanen sekitar 30-40 hari setelah tanam.",
        "saran": "Segera panen agar kualitas tidak menurun (daun menguning atau tanaman berbunga jika terlambat).",
    },
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ data
def stage_key(text):
    """Petakan teks tahap (nama folder atau label Excel asli) ke salah satu CLASS_NAMES."""
    t = str(text).strip().lower()
    if t in CLASS_NAMES:
        return t
    if "harvest ready" in t or "siap" in t:
        return "siap_panen"
    if "pre-harvest" in t or "mendekati" in t:
        return "mendekati_panen"
    if "initial" in t or "vegetative" in t or "pertumbuhan" in t:
        return "masa_pertumbuhan"
    return None


def normalize_dataset(df):
    """Rapikan dataset Excel unggahan agar sesuai format aplikasi.
    Menerima format asli (4 tahap bahasa Inggris) maupun format baru (3 nama folder)."""
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError("Kolom wajib tidak ditemukan: " + ", ".join(missing))
    out = df.copy()
    out["Time"] = out["Time"].astype(str).str.slice(0, 5)
    out["Ground Truth Criteria"] = out["Ground Truth Criteria"].map(stage_key)
    if out["Ground Truth Criteria"].isna().any():
        raise ValueError("Ada nilai 'Ground Truth Criteria' yang tidak dikenali "
                         "(harus Initial/Vegetative/Pre-Harvest/Harvest Ready atau nama folder kelas).")
    if "Cycle_ID" not in out.columns:
        out["Cycle_ID"] = 0
    out = out.sort_values(["Cycle_ID", "Day", "Time"]).reset_index(drop=True)
    if "Time_Index" not in out.columns:
        out["Time_Index"] = out.groupby("Cycle_ID").cumcount() + 1
    out["Stage_ID"] = out["Ground Truth Criteria"].map({k: i for i, k in enumerate(CLASS_NAMES)})
    out["Condition_ID"] = out["Soil Condition"].map({"Wet": 0, "Optimal": 1, "Dry": 2})
    if "Split" not in out.columns:
        out["Split"] = "upload"
    return out


def make_features(df, cfg):
    """Ubah dataframe pembacaan sensor menjadi array fitur (n, 5):
    kelembapan & suhu (skala 0-1, memakai min/max dari data latih) + one-hot jam."""
    mins = np.array(cfg["mins"], dtype="float32")
    maxs = np.array(cfg["maxs"], dtype="float32")
    sensor = (df[SENSOR_COLS].values.astype("float32") - mins) / (maxs - mins)
    jam_idx = df["Time"].astype(str).map(JAM_MAP)
    if jam_idx.isna().any():
        raise ValueError("Kolom Time harus berisi 08:00, 12:00, atau 16:00.")
    jam = np.eye(3, dtype="float32")[jam_idx.values.astype(int)]
    return np.hstack([sensor, jam])


def stage_from_maturity(maturity, thresholds):
    """thresholds = [batas masa->mendekati, batas mendekati->siap] (persen)."""
    if maturity < thresholds[0]:
        return 0
    if maturity < thresholds[1]:
        return 1
    return 2


def forecast_table(pred, cfg, last_jam_idx):
    """pred: array (12, 3) skala 0-1 [kelembapan, suhu, maturity/100]."""
    mins, maxs = cfg["mins"], cfg["maxs"]
    rows = []
    for j in range(pred.shape[0]):
        pos = last_jam_idx + 1 + j
        jam = JAM_LIST[pos % 3]
        offset = pos // 3
        moist = float(pred[j, 0] * (maxs[0] - mins[0]) + mins[0])
        temp = float(pred[j, 1] * (maxs[1] - mins[1]) + mins[1])
        mat = float(np.clip(pred[j, 2] * 100.0, 0, 100))
        sid = stage_from_maturity(mat, cfg["maturity_thresholds"])
        rows.append({
            "Langkah": j + 1,
            "Hari": "Hari ini" if offset == 0 else f"Hari +{offset}",
            "Jam": jam,
            "Kelembapan (%)": round(moist, 1),
            "Suhu (°C)": round(temp, 1),
            "Maturity (%)": round(mat, 1),
            "Tahap": CLASS_LABELS[CLASS_NAMES[sid]],
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ logika monitoring
def linear_trend(values, horizon=5):
    """Regresi linear sederhana pada pembacaan terakhir -> (kemiringan per pembacaan, prediksi ke depan)."""
    y = np.asarray(values, dtype=float)
    if len(y) < 3:
        last = y[-1] if len(y) else np.nan
        return 0.0, np.full(horizon, last)
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    future = intercept + slope * np.arange(len(y), len(y) + horizon)
    return float(slope), future


def pump_decision(moisture, was_on, dry=DRY_LIMIT, wet=WET_LIMIT, margin=5.0):
    """Otomatisasi pompa dengan histeresis. Mengembalikan (pompa_nyala, status)."""
    if moisture < dry:
        return True, "dry"
    if was_on and moisture < dry + margin:
        return True, "recovering"
    if moisture >= wet:
        return False, "wet"
    return False, "ok"


# ------------------------------------------------------------------ analisis foto
def green_analysis(img, px_per_cm=0.0, max_side=640):
    """Segmentasi warna hijau sederhana (HSV) untuk memperkirakan tutupan, kepadatan, dan ukuran kanopi.
    Ukuran dalam cm hanya akurat jika px_per_cm (skala foto) diisi dari benda pembanding."""
    img = img.convert("RGB")
    ow, oh = img.size
    scale = min(1.0, max_side / max(ow, oh))
    small = img.resize((max(1, int(ow * scale)), max(1, int(oh * scale))))
    hsv = np.asarray(small.convert("HSV")).astype(np.int16)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = (h >= 30) & (h <= 120) & (s >= 50) & (v >= 40)

    result = {
        "coverage_pct": float(mask.mean() * 100.0),
        "bbox_w_px": 0, "bbox_h_px": 0, "compactness": 0.0, "aspect": 0.0,
        "yellow_pct": 0.0, "greenness": 0.0, "brightness": 0.0,
        "area_cm2": None, "width_cm": None, "height_cm": None,
    }
    if mask.any():
        result["yellow_pct"] = float((h[mask] < 48).mean() * 100.0)      # hijau kekuningan
        result["greenness"] = float(s[mask].mean() / 255.0 * 100.0)      # kejenuhan warna daun
        result["brightness"] = float(v[mask].mean() / 255.0 * 100.0)
    rows = np.where(mask.mean(axis=1) > 0.01)[0]
    cols = np.where(mask.mean(axis=0) > 0.01)[0]
    if len(rows) and len(cols):
        bw = int(cols.max() - cols.min() + 1)
        bh = int(rows.max() - rows.min() + 1)
        result["bbox_w_px"] = int(round(bw / scale))
        result["bbox_h_px"] = int(round(bh / scale))
        result["compactness"] = float(mask.sum() / max(1, bw * bh))
        result["aspect"] = float(bw / max(1, bh))
        if px_per_cm and px_per_cm > 0:
            result["width_cm"] = result["bbox_w_px"] / px_per_cm
            result["height_cm"] = result["bbox_h_px"] / px_per_cm
            result["area_cm2"] = float(mask.sum() / (scale ** 2) / (px_per_cm ** 2))

    arr = np.asarray(small).astype(np.float32)
    arr[~mask] *= 0.3
    result["overlay"] = Image.fromarray(arr.astype(np.uint8))
    return result


def readiness_index(probs, names):
    """Indeks kesiapan panen 0-100 dari probabilitas CNN: siap_panen = 1, mendekati_panen = 0,5."""
    w = {"masa_pertumbuhan": 0.0, "mendekati_panen": 0.5, "siap_panen": 1.0}
    return float(sum(p * w.get(n, 0.0) for p, n in zip(probs, names)) * 100.0)


# ------------------------------------------------------------------ laporan
def build_report(cnn=None, lstm=None, green=None, table=None, sensor=None):
    """Susun laporan perkembangan (Markdown) untuk diunduh."""
    L = ["# Laporan Perkembangan Pakcoy", f"Dibuat: {datetime.now():%d-%m-%Y %H:%M}", ""]
    if sensor is not None:
        L += ["## Pembacaan sensor terakhir",
              f"- Hari {int(sensor['Day'])}, jam {sensor['Time']}",
              f"- Kelembapan tanah: {sensor['Soil Moisture (%)']:.0f}%",
              f"- Suhu: {sensor['Temperature (°C)']:.1f} °C", ""]
    if cnn:
        L += ["## Analisis foto (CNN)", f"- Tahap: {CLASS_LABELS[cnn[0]]} (keyakinan {cnn[1]:.0%})"]
    if green:
        L += [f"- Tutupan hijau pada foto: {green['coverage_pct']:.1f}%",
              f"- Kepadatan dalam kotak kanopi: {green['compactness']:.0%}",
              f"- Hijau kekuningan: {green['yellow_pct']:.1f}%"]
        if green.get("area_cm2") is not None:
            L += [f"- Perkiraan luas daun: {green['area_cm2']:.0f} cm2",
                  f"- Perkiraan lebar x tinggi: {green['width_cm']:.1f} x {green['height_cm']:.1f} cm"]
    if cnn or green:
        L.append("")
    if lstm:
        L += ["## Analisis sensor (LSTM)", f"- Tahap: {CLASS_LABELS[lstm[0]]} (keyakinan {lstm[1]:.0%})", ""]
    final = (cnn or lstm or [None])[0]
    if final:
        L += ["## Ciri dan saran umum", f"- Ciri: {STAGE_INFO[final]['ciri']}", f"- Saran: {STAGE_INFO[final]['saran']}", ""]
    if table is not None:
        L += ["## Prediksi 4 hari ke depan",
              f"- Tahap akhir: {table['Tahap'].iloc[-1]} (maturity sekitar {table['Maturity (%)'].iloc[-1]:.0f}%)", "",
              table.to_markdown(index=False) if hasattr(table, "to_markdown") and _has_tabulate() else table.to_string(index=False), ""]
    L += ["---", "Catatan: data pelatihan LSTM sebagian simulasi; foto dan sensor belum tentu dari tanaman yang sama. "
          "Gunakan laporan ini sebagai pendukung keputusan, bukan pengganti pengamatan langsung."]
    return "\n".join(L)


def _has_tabulate():
    try:
        import tabulate  # noqa: F401
        return True
    except Exception:
        return False
