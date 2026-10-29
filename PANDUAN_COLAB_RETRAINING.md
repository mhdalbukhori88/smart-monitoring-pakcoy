# Panduan Training Ulang Model di Google Colab (LSTM & CNN 4-Kelas)
**Proyek:** Smart Farming Pakcoy  
**Tanggal:** 28 Oktober 2026  
**Status:** Siap Dijalankan di Google Colab

---

## 1. Ringkasan Pembaruan Dataset & Arsitektur

Untuk menuntaskan masalah deteksi salah pada objek non-pakcoy (sepatu, cangkir, manusia, pot kosong, gulma/tanaman lain), sistem telah diperbarui:

1. **Dataset Citra 4 Kelas (`dataset_gambar_pakcoy_4kelas.zip`)**:
   - `bukan_pakcoy` (kelas negatif baru: berisi foto gulma/rumput liar, pot/tanah, tanaman lain, serta benda sehari-hari: laptop, cangkir, sepatu, ruangan, manusia).
   - `masa_pertumbuhan`
   - `mendekati_panen`
   - `siap_panen`
   *File zip telah otomatis dibuat dan tersedia di:*
   - `/home/bukhori/Downloads/dataset_gambar_pakcoy_4kelas.zip`
   - `data/dataset_gambar_pakcoy_4kelas.zip`

2. **Notebook `02_cnn_pakcoy.ipynb`**:
   - Diperbarui menjadi **4 neuron output (`Dense(4, activation='softmax')`)**.
   - Dilengkapi *dynamic class weight* dan metrik evaluasi confusion matrix 4 kelas.

3. **Notebook `01_lstm_pakcoy.ipynb`**:
   - Diperbarui dengan dukungan otomatis membaca Excel `dataset_pakcoy_monitoring_40hari.xlsx` maupun CSV alternatif `data_training.csv`.

4. **Proteksi Aplikasi (`app.py`, `utils.py`, `charts.py`)**:
   - **Green Gatekeeper**: Menolak foto secara langsung jika tutupan hijau $< 4\%$.
   - **Pemutus Pipeline**: Jika foto terdeteksi `bukan_pakcoy`, sistem **langsung menghentikan** eksekusi prediksi sensor LSTM 4 hari ke depan pada menu *Scan Gabungan*.

---

## 2. Struktur Folder di Google Drive

Pastikan struktur folder di Google Drive Anda adalah:

```text
Google Drive
└── MyDrive/
    └── pakcoy-project/
        ├── data/
        │   ├── dataset_gambar_pakcoy_4kelas.zip     <-- Upload dari Downloads / folder data
        │   └── dataset_pakcoy_monitoring_40hari.xlsx <-- Upload dari Downloads / folder data
        └── models/                                  <-- Folder kosong (akan diisi otomatis oleh Colab)
```

> **Tips:** Jika folder `pakcoy-project/data/` dan `pakcoy-project/models/` belum ada di Drive Anda, buatlah folder tersebut di Google Drive.

---

## 3. Langkah Training Model CNN (02_cnn_pakcoy.ipynb)

1. Buka [Google Colab](https://colab.research.google.com/).
2. Klik tab **Upload**, lalu pilih file notebook:
   `notebooks/02_cnn_pakcoy.ipynb` dari laptop Anda.
3. **Wajib Aktifkan GPU**:
   - Masuk ke menu: **Runtime** > **Change runtime type** (Ubah jenis runtime).
   - Pilih Hardware accelerator: **T4 GPU**.
   - Klik **Save**.
4. Jalankan seluruh sel:
   - Pilih menu **Runtime** > **Run all** (Jalankan semua).
   - Saat muncul dialog otorisasi Google Drive, klik **Connect to Google Drive** dan izinkan akses.
5. Tunggu proses training selesai (~3-5 menit dengan T4 GPU).
6. File yang dihasilkan di folder `MyDrive/pakcoy-project/models/`:
   - `model_cnn.keras`
   - `config_cnn.json`

---

## 4. Langkah Training Model LSTM (01_lstm_pakcoy.ipynb)

1. Di Google Colab, klik **File** > **Upload notebook**.
2. Pilih file notebook:
   `notebooks/01_lstm_pakcoy.ipynb` dari laptop Anda.
3. Runtime CPU standar sudah cukup cepat (atau bisa gunakan GPU T4 yang sama).
4. Jalankan seluruh sel: **Runtime** > **Run all**.
5. Tunggu proses training selesai (~2 menit).
6. File yang dihasilkan di folder `MyDrive/pakcoy-project/models/`:
   - `model_lstm_klasifikasi.keras`
   - `model_lstm_forecast.keras`
   - `config_lstm.json`

---

## 5. Memindahkan Model Hasil Training ke Komputer Lokal

Setelah kedua notebook selesai dijalankan:

1. Buka Google Drive Anda pada folder `MyDrive/pakcoy-project/models/`.
2. Unduh 5 file berikut:
   - `model_cnn.keras`
   - `config_cnn.json`
   - `model_lstm_klasifikasi.keras`
   - `model_lstm_forecast.keras`
   - `config_lstm.json`
3. Salin/pindahkan kelima file tersebut ke dalam folder:
   `/home/bukhori/Music/smart-monitoring-pakcoy/models/`
   *(Menimpa file model lama).*

---

## 6. Uji Coba pada Aplikasi Lokal

Setelah file model baru disalin ke folder `models/`:

1. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
2. Buka menu **Model CNN** atau **Scan Gabungan**:
   - Unggah foto pakcoy asli $\rightarrow$ sistem mengenali tahap pakcoy secara akurat (*Masa Pertumbuhan*, *Mendekati Panen*, atau *Siap Panen*).
   - Unggah foto sepatu, cangkir, wajah, pot kosong, atau kendaraan $\rightarrow$ sistem menampilkan label merah: **Bukan Pakcoy** dan menghentikan prediksi pertumbuhan tanaman!
