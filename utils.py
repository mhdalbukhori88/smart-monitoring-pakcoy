"""Fungsi pendukung aplikasi monitoring pakcoy (tanpa TensorFlow/Streamlit)."""
import json
from datetime import datetime

import numpy as np
import pandas as pd
from PIL import Image

CLASS_NAMES = ["masa_pertumbuhan", "mendekati_panen", "siap_panen"]
CNN_CLASS_NAMES = ["bukan_pakcoy", "masa_pertumbuhan", "mendekati_panen", "siap_panen"]
CLASS_LABELS = {
    "bukan_pakcoy": "Bukan Pakcoy",
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
    "bukan_pakcoy": {
        "ciri": "Objek bukan merupakan tanaman pakcoy (bisa berupa pot/tanah kosong, gulma/tanaman lain, atau benda sehari-hari).",
        "saran": "Unggah foto daun tanaman pakcoy yang jelas dan fokus dari sudut atas agar dapat dianalisis.",
    },
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
            "Tingkat Kematangan (%)": round(mat, 1),
            "Tahap": CLASS_LABELS[CLASS_NAMES[sid]],
        })
    df_res = pd.DataFrame(rows)
    df_res["Maturity (%)"] = df_res["Tingkat Kematangan (%)"]
    return df_res


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
    """Segmentasi warna hijau sederhana (HSV) untuk memperkirakan tutupan, kerapatan rimbun, dan dimensi fisik daun (cm).
    Secara otomatis mengestimasi ukuran dalam cm berdasarkan standar foto HP, atau kalibrasi presisi dari skala."""
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
        "area_cm2": 0.0, "width_cm": 0.0, "height_cm": 0.0, "is_estimated_cm": True,
    }
    if mask.any():
        result["yellow_pct"] = float((h[mask] < 48).mean() * 100.0)      # hijau kekuningan
        result["greenness"] = float(s[mask].mean() / 255.0 * 100.0)      # kepekatan warna hijau
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

        # Konversi ke centimeter (cm & cm²) yang ramah bagi orang awam
        is_manual_scale = bool(px_per_cm and px_per_cm > 0)
        effective_px_per_cm = float(px_per_cm) if is_manual_scale else max(1.0, float(max(ow, oh)) / 50.0)
        result["width_cm"] = float(result["bbox_w_px"] / effective_px_per_cm)
        result["height_cm"] = float(result["bbox_h_px"] / effective_px_per_cm)
        result["area_cm2"] = float(mask.sum() / (scale ** 2) / (effective_px_per_cm ** 2))
        result["is_estimated_cm"] = not is_manual_scale

    arr = np.asarray(small).astype(np.float32)
    arr[~mask] *= 0.3
    result["overlay"] = Image.fromarray(arr.astype(np.uint8))
    return result


def readiness_index(probs, names):
    """Indeks kesiapan panen 0-100 dari probabilitas CNN: siap_panen = 1, mendekati_panen = 0,5.
    Jika objek dideteksi bukan pakcoy, indeks = 0."""
    w = {"bukan_pakcoy": 0.0, "masa_pertumbuhan": 0.0, "mendekati_panen": 0.5, "siap_panen": 1.0}
    top_idx = int(np.argmax(probs))
    if names[top_idx] == "bukan_pakcoy":
        return 0.0
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
        tahap_str = CLASS_LABELS.get(cnn[0], cnn[0])
        L += ["## Analisis foto (CNN)", f"- Tahap: {tahap_str} (keyakinan {cnn[1]:.0%})"]
    if green:
        w_raw = green.get('width_cm')
        h_raw = green.get('height_cm')
        a_raw = green.get('area_cm2')
        try:
            w_val = float(w_raw) if w_raw is not None else 0.0
        except (ValueError, TypeError):
            w_val = 0.0
        try:
            h_val = float(h_raw) if h_raw is not None else 0.0
        except (ValueError, TypeError):
            h_val = 0.0
        try:
            a_val = float(a_raw) if a_raw is not None else 0.0
        except (ValueError, TypeError):
            a_val = 0.0

        est_txt = " (estimasi)" if green.get("is_estimated_cm") else ""
        bentang_txt = f"{w_val:.1f} × {h_val:.1f} cm{est_txt}" if (w_val > 0 and h_val > 0) else "Belum terkalibrasi"
        luas_txt = f"{a_val:.0f} cm²{est_txt}" if a_val > 0 else "Belum terkalibrasi"
        cov = float(green.get('coverage_pct') or 0.0)
        comp = float(green.get('compactness') or 0.0)
        yel = float(green.get('yellow_pct') or 0.0)
        grn = float(green.get('greenness') or 0.0)

        L += [f"- Tutupan daun pada foto: {cov:.1f}%",
              f"- Kerapatan rumpun daun: {comp:.0%}",
              f"- Tingkat daun menguning: {yel:.1f}%",
              f"- Kepekatan warna hijau: {grn:.0f}%",
              f"- Bentang rumpun daun (lebar × panjang): {bentang_txt}",
              f"- Perkiraan luas area daun: {luas_txt}"]
    if cnn or green:
        L.append("")
    if lstm:
        tahap_lstm = CLASS_LABELS.get(lstm[0], lstm[0])
        L += ["## Analisis sensor (LSTM)", f"- Tahap: {tahap_lstm} (keyakinan {lstm[1]:.0%})", ""]
    final = (cnn or lstm or [None])[0]
    if final and final in STAGE_INFO and final != "bukan_pakcoy":
        L += ["## Ciri dan saran umum", f"- Ciri: {STAGE_INFO[final]['ciri']}", f"- Saran: {STAGE_INFO[final]['saran']}", ""]
    elif final == "bukan_pakcoy":
        L += ["## Catatan Objek", "- Objek pada foto bukan merupakan tanaman pakcoy.", ""]
    if table is not None:
        mat_val = table["Tingkat Kematangan (%)"].iloc[-1] if "Tingkat Kematangan (%)" in table.columns else table["Maturity (%)"].iloc[-1]
        L += ["## Prediksi 4 hari ke depan",
              f"- Tahap akhir: {table['Tahap'].iloc[-1]} (tingkat kematangan tanaman sekitar {mat_val:.0f}%)", "",
              table.to_markdown(index=False) if hasattr(table, "to_markdown") and _has_tabulate() else table.to_string(index=False), ""]
    L += ["---", "Catatan: data sensor berbasis siklus perkembangan tanaman pakcoy; foto dan sensor dianalisis secara komprehensif. "
          "Gunakan laporan ini sebagai pendukung keputusan, bukan pengganti pengamatan langsung."]
    return "\n".join(L)


def _has_tabulate():
    try:
        import tabulate  # noqa: F401
        return True
    except Exception:
        return False
