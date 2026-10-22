# Smart Farming Pakcoy (LSTM + CNN + Streamlit)

Website monitoring pertumbuhan pakcoy: dashboard dengan grafik realtime yang bergerak, eksplorasi data, monitoring sensor
(simulasi IoT + pompa otomatis), LSTM (klasifikasi tahap + prediksi 4 hari), CNN (scan foto), dan scan gabungan.

## Struktur
```
app.py            halaman Streamlit (jalankan file ini)
utils.py          fungsi data, prediksi, analisis foto, laporan
charts.py         grafik Plotly
ui.py             tampilan (CSS, kartu, banner)
check_setup.py    pemeriksaan kesiapan project
data/             data_training.csv (30 siklus simulasi), data_asli.csv (data asli 40 hari)
models/           hasil training dari Colab (5 file, lihat di bawah)
notebooks/        01_lstm_pakcoy.ipynb, 02_cnn_pakcoy.ipynb (dijalankan di Google Colab)
.streamlit/       tema gelap
```

## 1. Training di Google Colab
Letakkan di Google Drive folder `MyDrive/pakcoy-project/data/`:
`dataset_pakcoy_monitoring_40hari.xlsx` dan `dataset_gambar_pakcoy_monitoring.zip`.
1. Buka `notebooks/01_lstm_pakcoy.ipynb` di Colab, Runtime > Run all. Catat versi TensorFlow yang tercetak.
2. Buka `notebooks/02_cnn_pakcoy.ipynb`, Runtime > Change runtime type > T4 GPU, lalu Run all.
3. Unduh dari `MyDrive/pakcoy-project/models/` lima file ini, taruh di folder `models/` project:
   `model_lstm_klasifikasi.keras`, `model_lstm_forecast.keras`, `config_lstm.json`, `model_cnn.keras`, `config_cnn.json`.

## 2. Jalankan di komputer
```
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python check_setup.py              # semua harus OK / hanya peringatan
streamlit run app.py
```
Jika model gagal dimuat: ubah `tensorflow-cpu` di `requirements.txt` menjadi `tensorflow-cpu==VERSI_COLAB`.

## 3. Deploy gratis di Streamlit Community Cloud
1. Pastikan folder `models/` berisi 5 file hasil Colab (tiap file harus di bawah 100 MB).
2. `git init`, `git add .`, `git commit -m "Smart Farming Pakcoy"`, buat repo di GitHub, lalu `git push`.
3. Buka share.streamlit.io, login GitHub, Create app, pilih repo, branch `main`, file `app.py`.
4. Advanced settings: pilih Python 3.11 atau 3.12. Klik Deploy (build pertama beberapa menit).
5. Buka URL aplikasi dan periksa setiap menu. Chip di sidebar harus hijau untuk LSTM klasifikasi, LSTM prediksi, dan CNN.

## Masalah umum
| Gejala | Penyebab / solusi |
|---|---|
| Chip model di sidebar abu-abu | File model belum ada di `models/`, atau klik "Muat ulang model" setelah menambahkannya |
| Error saat memuat model | Versi TensorFlow berbeda dengan Colab: pasang versi yang sama |
| Build deploy gagal / kehabisan memori | Pakai `tensorflow-cpu`, Python 3.11/3.12, dan jangan commit file yang tidak perlu |
| Aplikasi "tidur" di Streamlit Cloud | Normal pada paket gratis; buka lagi untuk membangunkan |
| Dataset unggahan ditolak | Kolom wajib: Day, DAP, Time, Soil Moisture (%), Temperature (°C), Soil Condition, Ground Truth Maturity Level (%), Ground Truth Criteria |

## Catatan jujur untuk laporan
- Monitoring realtime adalah demo (data diputar ulang). Sensor sungguhan butuh perangkat keras (mis. ESP32).
- Data latih LSTM sebagian simulasi (augmentasi); laporkan juga hasil pada data asli.
- Jumlah gambar uji CNN kecil, jadi akurasinya kasar. Foto dan sensor belum tentu dari tanaman yang sama.
- Ukuran daun dalam cm hanya akurat jika foto memuat benda pembanding (isi skala foto).
