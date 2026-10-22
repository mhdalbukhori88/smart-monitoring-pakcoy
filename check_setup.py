"""Pemeriksaan kesiapan project. Jalankan:  python check_setup.py
Mengecek paket, file data/model, kecocokan versi TensorFlow, dan uji prediksi singkat."""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).parent
fails, warns = 0, 0


def out(status, msg):
    global fails, warns
    if status == "FAIL":
        fails += 1
    if status == "WARN":
        warns += 1
    print(f"[{status}] {msg}")


print(f"Python {sys.version.split()[0]}")
if sys.version_info[:2] not in [(3, 10), (3, 11), (3, 12)]:
    out("WARN", "Python yang paling aman untuk TensorFlow adalah 3.11 atau 3.12.")

# 1) paket
mods = {}
for name, pip in [("streamlit", "streamlit"), ("pandas", "pandas"), ("numpy", "numpy"), ("PIL", "pillow"),
                  ("plotly", "plotly"), ("openpyxl", "openpyxl"), ("tensorflow", "tensorflow-cpu")]:
    try:
        mods[name] = importlib.import_module(name)
        out("OK", f"{name} {getattr(mods[name], '__version__', '')}")
    except Exception as e:
        out("FAIL", f"{name} belum terpasang ({e.__class__.__name__}). Jalankan: pip install {pip}")

# 2) file
for f in ["app.py", "utils.py", "ui.py", "charts.py", "data/data_training.csv", "data/data_asli.csv"]:
    out("OK" if (ROOT / f).exists() else "FAIL", f"file {f}")
model_files = ["model_lstm_klasifikasi.keras", "model_lstm_forecast.keras", "config_lstm.json",
               "model_cnn.keras", "config_cnn.json"]
for f in model_files:
    p = ROOT / "models" / f
    if p.exists():
        out("OK", f"models/{f} ({p.stat().st_size / 1e6:.1f} MB)")
    else:
        out("WARN", f"models/{f} belum ada. Latih di Colab lalu taruh di folder models/.")

sys.path.insert(0, str(ROOT))
try:
    import utils
    out("OK", "utils.py dapat diimpor")
except Exception as e:
    out("FAIL", f"utils.py gagal diimpor: {e}")
    utils = None

# 3) versi TensorFlow vs yang dipakai saat training
if "tensorflow" in mods and utils:
    for cfgname in ["config_lstm.json", "config_cnn.json"]:
        p = ROOT / "models" / cfgname
        if p.exists():
            ver = utils.load_json(p).get("tf_version")
            if ver and ver != mods["tensorflow"].__version__:
                out("WARN", f"{cfgname}: dilatih dengan TensorFlow {ver}, terpasang {mods['tensorflow'].__version__}. "
                            f"Jika model gagal dimuat, pasang tensorflow-cpu=={ver}.")

# 4) uji prediksi singkat
if "tensorflow" in mods and utils:
    import numpy as np
    from tensorflow import keras
    tests = [("model_lstm_klasifikasi.keras", (1, 6, 5)), ("model_lstm_forecast.keras", (1, 12, 5)),
             ("model_cnn.keras", (1, 224, 224, 3))]
    for fname, shape in tests:
        p = ROOT / "models" / fname
        if not p.exists():
            continue
        try:
            model = keras.models.load_model(p, compile=False)
            y = np.asarray(model(np.random.rand(*shape).astype("float32") * (255 if len(shape) == 4 else 1),
                                 training=False))
            out("OK", f"{fname}: dimuat, keluaran berbentuk {y.shape}")
        except Exception as e:
            out("FAIL", f"{fname}: gagal dimuat/dijalankan: {e}")

# 5) data
if "pandas" in mods and utils:
    import pandas as pd
    d = pd.read_csv(ROOT / "data" / "data_training.csv")
    missing = [c for c in utils.REQUIRED_COLS if c not in d.columns]
    out("OK" if not missing else "FAIL", f"data_training.csv: {len(d):,} baris, kolom wajib {'lengkap' if not missing else 'kurang: ' + str(missing)}")

print()
if fails:
    print(f"HASIL: {fails} masalah harus diperbaiki, {warns} peringatan.")
    sys.exit(1)
print(f"HASIL: siap dijalankan ({warns} peringatan)." + ("  Latih/pasang model agar semua menu aktif." if warns else ""))
