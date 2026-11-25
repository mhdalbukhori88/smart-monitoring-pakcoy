# Smart Farming Pakcoy (LSTM + CNN + Streamlit)

Sistem monitoring, analitik, dan pendukung keputusan budidaya tanaman pakcoy (*Brassica rapa* subsp. *chinensis*) berbasis web menggunakan **Streamlit**, **LSTM** (klasifikasi fase & prakiraan 4 hari ke depan), **CNN MobileNetV2** (analisis citra daun), dan **Asisten Kebun AI** (Google Gemini).

- **Demo Aplikasi:** https://smart-monitoring-pakcoy.streamlit.app/
- **Dokumentasi Teknis & Evaluasi Jurnal:** [docs/CATATAN_JURNAL.md](docs/CATATAN_JURNAL.md)

---

## Fitur Utama

1. **Dashboard Utama** — Pemilihan siklus budidaya (Siklus 1–30, Semua Siklus, atau Dataset Unggahan Excel), 6 kartu KPI dinamis yang sinkron dengan data terpilih, grafik distribusi kondisi kelembapan tanah & fase pertumbuhan, kurva kematangan, tabel sensor lengkap, serta **Konsol Live Telemetry** dengan klasifikasi fase LSTM dan kontrol pompa air otomatis berbasis **histeresis** (`<55%` nyala, `55–60%` pemulihan, `≥76%` mati) maupun manual.
2. **Prakiraan 4 Hari (LSTM)** — Panel kontrol ringkas (siklus, slider titik awal, preset fase Hari ke-7/17/25), 4 kartu ringkasan KPI (`H+4`), serta 4 tab terstruktur: **Ringkasan** (visual tanaman + 4 kartu harian + expander estimasi daun/tajuk), **Grafik Tren** (mode Rata-rata Harian & Per Sesi, area zona ideal, toggle pembanding data asli), **Tabel Data** (ringkasan harian, rincian per waktu ukur, unduh CSV), dan **Rekomendasi Antisipasi**.
3. **Analisis Tanaman (CNN)** — Klasifikasi 4 kelas citra (`bukan_pakcoy`, `masa_pertumbuhan`, `mendekati_panen`, `siap_panen`) berbasis **MobileNetV2**, pra-validasi citra daun HSV transparan, skor kesiapan panen (`0–100%`), estimasi morfologi daun & proksi klorofil visual (HSV) dengan opsi kalibrasi skala manual (`px/cm`), narasi saran perawatan, serta tab evaluasi & confusion matrix model CNN.
4. **History Perkembangan** — Eksplorasi riwayat pertumbuhan resolusi tinggi `15×/hari` (`06:00–20:00`, `1.400` catatan mencakup Siklus 1–3 penuh dan awal Siklus 4), filter interaktif dinamis, unduh CSV, peninjauan dataset asli mentah (`1.140` baris), dan panduan agronomi siklus 30 hari.
5. **Asisten Kebun AI** — Chat konsultasi agronomi pakcoy dan panduan aplikasi berbasis Google Gemini (`google-genai`, default `gemini-2.5-flash` dengan cadangan `gemini-2.5-flash-lite`).
6. **Impor Excel, Muat Ulang Model & Manajemen Akun** — Validasi unggahan `.xlsx` ter-cache di sidebar, muat ulang model AI dengan indikator status, serta autentikasi lokal SQLite (`PBKDF2-HMAC-SHA256`, 100.000 iterasi, dukungan `st.secrets`, dan rate limiting login).

---

## Struktur Folder

```text
smart-monitoring-pakcoy/
├── app.py                        # Aplikasi utama Streamlit (5 halaman & navigasi sidebar)
├── ui.py                         # Sistem desain hijau botani (CSS, kartu KPI, konsol live, komponen prakiraan)
├── charts.py                     # Grafik interaktif Plotly
├── utils.py                      # Preprocessing LSTM, validasi Excel, pompa histeresis, analisis HSV
├── auth.py                       # Otentikasi pengguna (SQLite + PBKDF2-SHA256 + rate limiting)
├── ai_assistant.py               # Integrasi Asisten Kebun AI (Google Gemini SDK)
├── check_setup.py                # Skrip verifikasi paket, dataset, dan smoke test model AI
├── requirements.txt              # Dependensi Python
├── .streamlit/
│   ├── config.toml               # Tema terang (Botanical Green) & batas upload 10 MB
│   └── secrets.toml.example      # Contoh konfigurasi GEMINI_API_KEY & ADMIN_PASSWORD
├── assets/
│   ├── logo_pakcoy.png           # Logo aplikasi
│   └── pakcoy_stages/            # Foto referensi tiap fase pertumbuhan pakcoy
├── data/
│   ├── data_training_30hari.csv  # 30 siklus budidaya 30 hari (2.700 baris, 3x/hari, pola diurnal terjaga)
│   ├── data_asli_30hari.csv      # 1 siklus data lapangan 30 hari (90 baris, 3x/hari)
│   ├── history_perkembangan_pakcoy_1400.csv  # 1.400 catatan resolusi tinggi (15x/hari, Siklus 1–4)
│   └── dataset_asli_mentah.csv   # 1.140 baris data mentah sumber (sebelum pembersihan 30 hari)
├── dataset asli/
│   └── new Dataset_Pakcoy.xlsx   # Workbook Excel mentah sumber
├── models/
│   ├── model_lstm_klasifikasi.keras  # Model LSTM klasifikasi 3 fase (31.491 parameter)
│   ├── model_lstm_forecast.keras     # Model LSTM prakiraan 4 hari (75.204 parameter)
│   ├── config_lstm.json              # Parameter normalisasi & metrik evaluasi lengkap LSTM
│   ├── model_cnn.keras               # Model CNN MobileNetV2 4 kelas (2.263.108 parameter)
│   ├── config_cnn.json               # Konfigurasi & metrik evaluasi CNN
│   └── backup_40hari/                # Cadangan model LSTM versi 40 hari sebelumnya
├── notebooks/
│   ├── 01_lstm_pakcoy.ipynb      # Notebook pelatihan & evaluasi LSTM (Google Colab)
│   └── 02_cnn_pakcoy.ipynb       # Notebook pelatihan & evaluasi CNN MobileNetV2 (Google Colab)
└── docs/
    └── CATATAN_JURNAL.md         # Dokumentasi teknis, metrik reproduktif, & keterbatasan untuk jurnal
```

---

## Cara Instalasi

Disarankan menggunakan **Python 3.11 atau 3.12** (sesuai kompatibilitas `tensorflow-cpu==2.21.0`).

```bash
# 1. Kloning repositori
git clone https://github.com/mhdalbukhori88/smart-monitoring-pakcoy.git
cd smart-monitoring-pakcoy

# 2. Buat & aktifkan virtual environment
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Pasang dependensi
pip install --upgrade pip
pip install -r requirements.txt

# 4. (Opsional) Konfigurasi Secrets untuk Asisten Kebun AI & Admin
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml lalu isi GEMINI_API_KEY dan ADMIN_PASSWORD
```

---

## Cara Menjalankan

```bash
# Verifikasi kesiapan paket, dataset, dan model (target: 0 masalah)
python check_setup.py

# Jalankan aplikasi Streamlit secara lokal
streamlit run app.py
```

Aplikasi dapat diakses di `http://localhost:8501`.
- Jika `ADMIN_PASSWORD` belum diset pada `.streamlit/secrets.toml` atau environment variable, akun demo lokal `admin` / `admin123` akan dibuat otomatis (sangat disarankan mengatur `ADMIN_PASSWORD` di **App Settings → Secrets** saat deploy ke Streamlit Cloud).

---

## Ringkasan Evaluasi Model Aktual

| Model | Set Evaluasi | Metrik Utama |
| :--- | :--- | :--- |
| **LSTM Klasifikasi** (`W=6`) | Uji Simulasi 30 Hari (`n=425`) | Akurasi **84,71%**, Macro-F1 **79,43%** |
| **LSTM Klasifikasi** (`W=6`) | Data Asli 30 Hari (`n=85`) | Akurasi **72,94%**, Macro-F1 **61,22%** |
| **LSTM Forecast 4 Hari** (`W=12 → H=12`) | Uji Simulasi 30 Hari (`n=335`) | Kelembapan MAE **1,63%** ($R^2$ **0,890**), Suhu MAE **0,75°C** ($R^2$ **0,786**), Kematangan MAE **2,07%** ($R^2$ **0,987**) |
| **LSTM Forecast 4 Hari** (`W=12 → H=12`) | Data Asli 30 Hari (`n=67`) | Kelembapan MAE **0,66%** ($R^2$ **0,982**), Suhu MAE **0,13°C** ($R^2$ **0,992**), Kematangan MAE **12,01%** ($R^2$ **0,680**) |
| **CNN MobileNetV2** (`224×224`) | Citra Uji (`n=26`) | Akurasi **88,46%** (`23/26`), Macro-F1 **87,94%** |

Detail lengkap hyperparameter, confusion matrix, pembanding baseline, dan keterbatasan ilmiah tersedia di [docs/CATATAN_JURNAL.md](docs/CATATAN_JURNAL.md).

---

## Deploy di Streamlit Community Cloud

1. Pastikan folder `models/` berisi 5 file model aktif (`model_lstm_klasifikasi.keras`, `model_lstm_forecast.keras`, `config_lstm.json`, `model_cnn.keras`, `config_cnn.json`).
2. Buka [share.streamlit.io](https://share.streamlit.io), pilih repositori & branch target, set main file `app.py`, dan pilih **Python 3.11 / 3.12** di *Advanced settings*.
3. Tambahkan `GEMINI_API_KEY` dan `ADMIN_PASSWORD` di menu **App Settings → Secrets**.
