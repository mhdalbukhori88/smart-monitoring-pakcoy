# Analisis Masalah Model CNN & LSTM Serta Rencana Perbaikan
**Proyek:** Smart Farming Pakcoy (Monitoring, CNN, LSTM)  
**Tanggal:** 28 Oktober 2026  
**Status:** Tersimpan untuk kelanjutan pekerjaan  

---

## 1. Ringkasan Permasalahan
Saat pengguna mengunggah foto pakcoy asli, model CNN dan LSTM berhasil mengklasifikasikan tahap pertumbuhan dan memprediksi kondisi 4 hari ke depan. Namun, saat mengunggah foto objek lain (bukan pakcoy, misalnya: sepatu, cangkir, kendaraan, wajah manusia, perabot):
1. **Model CNN tetap mendeteksi objek tersebut sebagai tanaman pakcoy** (bahkan sering kali dengan keyakinan tinggi pada salah satu tahap: *Masa Pertumbuhan*, *Mendekati Panen*, atau *Siap Panen*).
2. **Model LSTM ikut-ikutan menghasilkan prediksi 4 hari ke depan** dan sistem menyimpulkan bahwa tanaman pada foto berada dalam kondisi tertentu, padahal objeknya sama sekali bukan tanaman pakcoy.

---

## 2. Temuan Akar Masalah (Root Cause Analysis)

### A. Akar Masalah Model CNN (Klasifikasi Foto)
1. **Asumsi Dunia Tertutup (*Closed-Set Classification*) & Softmax Forcing**:
   - Di notebook training `notebooks/02_cnn_pakcoy.ipynb`, model hanya didefinisikan dengan 3 kelas:
     ```python
     CLASS_NAMES = ['masa_pertumbuhan', 'mendekati_panen', 'siap_panen']
     ```
   - Lapisan output terakhir model menggunakan aktivasi Softmax 3 neuron:
     ```python
     out = layers.Dense(3, activation='softmax')(x)
     ```
   - Karakteristik matematis fungsi Softmax:
     $$\sum_{i=1}^{3} P(\text{kelas}_i) = 1.0 \quad (100\%)$$
   - Softmax **memaksa** total probabilitas ketiga kelas berjumlah 100%. Model tidak memiliki jalan keluar (*escape class*) untuk menyatakan "Objek Tidak Dikenal" atau "Bukan Pakcoy".
   - Akibatnya, fungsi `p.argmax()` di `app.py` baris 559 **selalu memilih salah satu dari 3 kelas tersebut**, apa pun gambar yang diunggah.

2. **Ketiadaan Dataset Kelas Negatif (*Non-Pakcoy Class*)**:
   - Dataset gambar (`dataset_gambar_pakcoy_bersih.zip` di `~/Downloads/`) hanya memiliki 3 folder kelas pakcoy.
   - Tidak pernah ada sampel citra negatif (tanah kosong, pot kosong, gulma/rumput liar, objek sehari-hari, tangan manusia) yang dilatihkan ke model.

3. ***Deep Learning Overconfidence* pada Out-of-Distribution (OOD)**:
   - Feature extractor MobileNetV2 mengekstraksi tekstur, kontras, dan tepian visual dari objek sembarang.
   - Karena bobot dense layer hanya memetakan ke 3 kelas pakcoy, proyeksi fitur objek sembarang sering kali memicu aktivasi tinggi pada salah satu kelas (keyakinan palsu > 80%).

---

### B. Akar Masalah Model LSTM & Fitur "Scan Gabungan"
1. **LSTM Tidak Pernah Membaca Foto**:
   - Model LSTM (`model_lstm_klasifikasi.keras` dan `model_lstm_forecast.keras`) murni berbasis data sensor numerik tabular:
     `Soil Moisture (%)`, `Temperature (°C)`, dan *one-hot* jam (`08:00`, `12:00`, `16:00`).
2. **Kelemahan Alur Eksekusi di `app.py` (`page_scan`)**:
   - Pada menu **Scan Gabungan** (`app.py` baris 636–684), upload foto disandingkan langsung dengan pembacaan sensor CSV default:
     ```python
     # 1) Foto diproses oleh CNN
     cnn, g = photo_panel(m, img, "scan")
     
     # 2) Sensor diproses oleh LSTM tanpa validasi foto
     if lstm_ready(m, "clf"):
         pc = predict_stage(m, df.iloc[step - wc: step])
         ...
     if lstm_ready(m, "fc"):
         table = predict_forecast(m, df.iloc[step - w_in: step])
     ```
   - Ketika CNN salah mengidentifikasi objek asing sebagai pakcoy, alur kode langsung mengeksekusi LSTM pada data sensor default, lalu menampilkan grafik prediksi 4 hari ke depan untuk objek tersebut.

---

### C. Ketiadaan Gerbang Filter (*Gatekeeper*) pada Input Citra
- Di `utils.py`, fungsi `green_analysis()` telah menghitung segmentasi warna hijau daun (`coverage_pct`), namun nilai ini hanya ditampilkan sebagai kartu statistik kanopi, **tidak digunakan untuk menyaring/menolak foto non-tanaman**.

---

### D. Akar Masalah Persepsi "Hasil Prediksi LSTM Tidak Berubah-ubah"
1. **Distribusi Tahap pada Siklus 40 Hari**:
   - Dalam 1 siklus budidaya 40 hari (120 pembacaan sensor: jam 08:00, 12:00, 16:00):
     - **Masa Pertumbuhan (Vegetatif):** Pembacaan 1 s.d. 65 (Hari ke-10 s.d. 28 DAP) $\rightarrow$ **mencakup >54% panjang siklus!**
     - **Mendekati Panen:** Pembacaan 66 s.d. 85 (Hari ke-29 s.d. 38 DAP).
     - **Siap Panen:** Pembacaan 86 s.d. 120 (Hari ke-39 s.d. 49 DAP).
2. **Nilai Default Slider Berada di Tengah Fase Pertumbuhan**:
   - Slider pembacaan di aplikasi sebelumnya bermula pada default nilai `60`.
   - Ketika pengguna menggeser slider ke kiri (misal: 10, 20, 30, 45, 55, 60), seluruh rentang data tersebut memang murni berada pada *Masa Pertumbuhan*.
   - Akibatnya model LSTM secara konsisten memprediksi *Masa Pertumbuhan (97%–100%)* dan label sebenarnya juga *Masa Pertumbuhan*. Pengguna yang belum memahami struktur waktu mengira sistem mengalami *stuck* atau error tidak memperbarui hasil.
3. **Solusi yang Diterapkan pada Aplikasi**:
   - Menambahkan **Pintasan Uji Cepat Tiap Tahap (1-Click Presets)**:
     - `🌱 Uji: Masa Pertumbuhan (Baca ke-25 / DAP 18)`
     - `🌿 Uji: Mendekati Panen (Baca ke-75 / DAP 34)`
     - `🥬 Uji: Siap Panen (Baca ke-100 / DAP 43)`
   - Menambahkan **Status Bar Kontekstual**: menampilkan `📅 Hari ke-X (DAP Y) • ⏰ Jam HH:MM • 📍 Pembacaan ke-Z` serta badge status fase data asli secara jelas.
   - Menyediakan **Template Simulasi Input Manual**: tombol template kondisi tanah lembap (70%), sedang (55%), dan siap panen (48%) agar pengujian manual langsung menghasilkan prediksi yang berbeda tanpa perlu menebak-nebak angka sensor.
   - Memperkaya tabel sensor dengan kolom `Hari ke-`, `DAP`, `Jam`, `Kelembapan (%)`, `Suhu (°C)`, dan `Kondisi Tanah`.

---

## 3. Rencana Solusi & Perbaikan

### Solusi 1: Perbaikan Cepat pada Kode Aplikasi (Langsung Efektif)
Dapat diterapkan langsung pada `app.py` dan `utils.py` tanpa perlu menunggu training ulang model:
1. **Green Vegetation Gatekeeper**:
   - Cek nilai tutupan warna daun (`coverage_pct`). Jika di bawah ambang batas (misal $< 6\%$), tolak gambar secara langsung:
     *"Objek tidak dikenali sebagai tanaman (tidak ditemukan dedaunan hijau)"*.
2. **Confidence & Entropy Thresholding**:
   - Jika nilai probabilitas tertinggi CNN $< 70\%$ atau jika skor probabilitas ketiga kelas terbagi rata (entropi tinggi), tolak dengan status:
     *"Objek tidak dapat dipastikan sebagai tanaman pakcoy"*.
3. **Pemutusan Pipeline pada Scan Gabungan**:
   - Jika foto tidak lolos validasi, **hentikan eksekusi LSTM**. Jangan tampilkan prediksi 4 hari ke depan untuk objek non-pakcoy.

### Solusi 2: Perbaikan Arsitektur & Dataset Model (Training Ulang di Google Colab)
1. **Tambahkan Kelas ke-4: `bukan_pakcoy`**:
   - Struktur dataset diperluas menjadi 4 folder:
     - `masa_pertumbuhan`
     - `mendekati_panen`
     - `siap_panen`
     - `bukan_pakcoy` (berisi 50–100 foto acak: pot kosong, tanah kosong, tanaman lain/rumput liar, objek ruangan/sehari-hari).
2. **Update Arsitektur `02_cnn_pakcoy.ipynb`**:
   - Ubah output layer menjadi `layers.Dense(4, activation='softmax')(x)`.
   - Update `CLASS_NAMES` menjadi 4 kelas.
   - Latih ulang di Google Colab, lalu simpan `model_cnn.keras` dan `config_cnn.json` yang baru.

---

## 4. Lokasi File & Dataset Terkait di Komputer
- **Dataset Gambar Asli**: `/home/bukhori/Downloads/dataset_gambar_pakcoy_bersih.zip`
- **Dataset Sensor Asli**: `/home/bukhori/Downloads/dataset_pakcoy_monitoring_40hari.xlsx`
- **Data CSV Bawaan**: `data/data_asli.csv` dan `data/data_training.csv`
- **Model CNN Saat Ini**: `models/model_cnn.keras` dan `models/config_cnn.json`
- **Notebook Training**: `notebooks/01_lstm_pakcoy.ipynb` dan `notebooks/02_cnn_pakcoy.ipynb`
- **Kode Aplikasi Utama**: `app.py`, `utils.py`, `ui.py`
