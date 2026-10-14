# Repositori Proyek UTS Data Mining — Analisis Sensor Geotermal Well 56-32 & Audit Metodologi Deret Waktu

> **Proyek Ujian Tengah Semester (UTS) Data Mining — S1 Informatika**  
> **Topik:** *Multivariate Geothermal Drilling Sensor Clustering & Time-Series Methodology Audit*  
> **Studi Kasus:** Sensor Pason 1 Hz rig pemboran sumur panas bumi Utah FORGE Well 56-32 (2.506.360 rekaman baris × 22 kolom).

---

## 1. Status & Ringkasan Eksekutif

Repositori ini mengintegrasikan **dua lintasan arsitektur (Dual-Track Architecture)** untuk menjawab tantangan klasterisasi deret waktu sensor pemboran geotermal tanpa supervisi:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ARSITEKTUR DUAL-TRACK REPOSITORI                      │
├─────────────────────────────────────────┬───────────────────────────────────┤
│ Track 1: Baseline Eksplorasi Legacy    │ Track 2: Clean Pipeline v2        │
│ (`notebooks/00_`–`06_`, `src/`)         │ (`clean-pipeline-56-32/`, `07_`) │
├─────────────────────────────────────────┼───────────────────────────────────┤
│ • Eksplorasi awal & investigasi sensor  │ • Pipeline produksi bebas leakage │
│ • Perbandingan point vs sliding window  │ • Tumbling 60s non-overlapping    │
│ • StandardScaler vs RobustScaler global │ • Train-only scaler (chrono 70:30)│
│ • Prior k=4 & interpretasi kualitatif   │ • Embargo temporal >= 1 jam       │
│ • Menjadi objek audit metodologis       │ • Evaluasi Train/Test & NO-WINNER │
└─────────────────────────────────────────┴───────────────────────────────────┘
```

1. **Track 1 (Baseline Eksplorasi Legacy):** Rekaman jejak awal penelitian yang berfokus pada identifikasi "penyakit" data sensor (sentinel `-999.25`, skala jomplang 258.9:1, outlier ROP 8.65%, autokorelasi lag-1 ≈ 1.0) dan eksperimen perbandingan skenario standar.
2. **Track 2 (Clean Pipeline v2):** Refaktor metodologis penuh yang menerapkan protokol deret waktu ketat bebas kebocoran data (*leakage-free*). Seluruh keputusan pemodelan diisolasi pada partisi *Train*, dievaluasi secara independen pada partisi *Test* ter-embargo, serta mengadopsi prinsip evaluasi jujur berbasis integritas saintifik (*rejection option / NO-WINNER*).

---

## 2. Tabel Ringkasan Masalah & Solusi Metodologis

Hasil audit komprehensif terhadap arsitektur deret waktu lama menghasilkan transformasi sistematis pada pipeline baru:

| Dimensi | Pendekatan Baseline Legacy | Solusi Clean Pipeline v2 | Dampak Ilmiah |
|---|---|---|---|
| **Windowing & Leakage** | Sliding window 60s, stride 30s (tumpang-tindih **50%** antar window bersebelahan). | **Tumbling window 60s, stride 60s (0% overlap)**, dilengkapi *gap reset* pada selisih waktu > 1 detik. | Mencegah kebocoran informasi temporal antar-sampel; menjamin independensi unit analisis. |
| **Isolasi Penskalaan (Scaling)** | `fit_transform()` global pada seluruh dataset sebelum evaluasi. | **Train-Only Scaling**: Scaler (`StandardScaler`, `RobustScaler`, `MinMaxScaler`) hanya di-*fit* pada data Train (70%), Test (30%) murni di-*transform*. | Mencegah kebocoran distribusi masa depan (*look-ahead bias*) ke dalam proses pemodelan. |
| **Pemisahan Temporal** | Tidak ada partisi waktu formal; evaluasi dilakukan pada sampel campuran. | **Kronologis 70:30 dengan Embargo Temporal >= 3.600 detik (1 jam)** di antara Train dan Test. | Mengeliminasi korelasi residual autokorelasi tinggi pada batas partisi. |
| **Integritas Sampel** | `-999.25 → dropna()` langsung tanpa memperhatikan diskontinuitas waktu. | **Coverage Gating**: Minimal 54 dari 60 detik valid (≥90%) per kanal; segmen di-*reset* jika terjadi *gap*. | Menghasilkan **38.177 window valid** (26.723 Train, 60 Embargo, 11.394 Test) berkontrak 39 fitur. |
| **Distribusi Klaster** | *Cluster collapse* ekstrem pada `k=4`: C0 mendominasi **95,40%**, klaster minor hanya 0,71%. | **Evaluasi Multi-Seed (k=2..8)** pada K-Means & GMM; deteksi keruntuhan klaster (< 1% okupansi). | Transparansi penuh atas ketidakstabilan geometri data; menolak klaim klaster yang rapuh. |
| **Pengambilan Keputusan** | Memaksakan `k=4` berdasarkan asumsi awal 4 rezim operasional rig. | **Hak Eksplisit Status `NO-WINNER`** jika terjadi *collapse*, *negative silhouette*, atau *sharp test drop*. | Dari 42 pasangan primer, **38 dinyatakan NO-WINNER** dan 4 berstatus ELIGIBLE tanpa fabrikasi. |
| **Interpretasi Domain** | Centroid statistik langsung dilabeli nama rezim fisik pemboran tanpa driller log. | **Klaster dilabeli kode statistik murni (`C0..Ck`)**; batas inferensi diakui secara eksplisit. | Integritas penulisan ilmiah; klaim fisik hanya dibuka jika tersedia ground-truth log pemboran. |

---

## 3. Indeks Navigasi Repositori Lengkap

Repositori ditata secara modular agar mudah ditelusuri dari aspek kode eksekusi, data manifest, hingga naskah publikasi:

```
datmin/
├── clean-pipeline-56-32/       # Engine pipeline bersih Well 56-32 (v2)
│   ├── protocol.json           # Spesifikasi protokol kontrak terkunci
│   ├── scripts/                # Kode pipeline modular (Fase A, B, C, Contract)
│   ├── outputs/manifests/      # Manifest JSON reproduktifitas (Fase A, B, C)
│   ├── outputs/metrics/        # Ledger metrik evaluasi lengkap & Train EDA
│   └── models/scalers/         # Artefak model scaler Train-only tersimpan
│
├── audit/                      # Artefak perencanaan, audit & roadmap lanjutan
│   ├── clean-pipeline-56-32-plan-v1.md   # Rencana kerja & 5 strict rules 56-32
│   ├── plan-cross-well-16a-v1.md         # Roadmap transferabilitas OOD Well 16A
│   ├── h1-78b-negative-lock-v1.md        # Kunci negatif empiris sensor Well 78B
│   └── perbandingan-upstream-vs-audit.md # Analisis komparatif audit mendalam
│
├── notebooks/                  # Koleksi Jupyter Notebook eksperimen
│   ├── 07_clean_pipeline_walkthrough.ipynb # ⭐ Notebook utama walkthrough Fase A-C
│   ├── 00_cek_penyakit_colab.ipynb         # Eksplorasi penyakit data 1 Hz
│   ├── 05_preprocessing_proof.ipynb        # Pembuktian empiris efek penskalaan
│   ├── 06_final_clustering.ipynb           # Baseline clustering historis
│   └── ... (notebooks 01-04)
│
├── PERBANDINGAN_APPROACH_DAN_AUDIT_METODOLOGI.md # Dokumen pembanding metodologis
├── STATISTIK_DESKRIPTIF_DAN_EDA.md             # Dokumen statistik deskriptif Train-only
│
├── reports/                    # Laporan & luaran publikasi ilmiah
│   ├── 01-protokol-prisma/     # Protokol tinjauan literatur sistematis PRISMA
│   ├── 02-data-screening/      # Jejak seleksi & eligibility artikel ilmiah
│   ├── 03-sintesis/            # Gap analysis & sintesis hasil
│   └── 04-paper/               # Naskah Paper IEEE UTS
│       ├── draft_paper_ieee.md # Format naskah Markdown
│       ├── draft-paper-letx.tex# Format naskah LaTeX IEEEtran
│       ├── prisma.png          # Diagram alir PRISMA 2020 resmi
│       └── deklarasi_genai.md  # Formulir deklarasi penggunaan Gen-AI
│
└── figures/                    # Visualisasi visual & diagram alir (SVG, PNG, PDF)
```

### Rincian Modul & Berkas Utama

- **Notebook Utama (`notebooks/07_clean_pipeline_walkthrough.ipynb`)**:
  * Berfungsi sebagai *single walkthrough* interaktif untuk menjalankan dan memvisualisasikan seluruh tahapan pipeline bersih: Uji Kontrak, Fase A (Windowing), Fase B (Pemisahan Temporal & Penskalaan), hingga Fase C (Klasterisasi Grid & Pelaporan *Verdict Ledger*).
- **Pipeline Bersih (`clean-pipeline-56-32/`)**:
  * `scripts/prepare_windows.py`: Pipeline streaming chunked data mentah, sanitasi sentinel/SPP, tumbling 60s, ekstraksi 39 fitur statistik.
  * `scripts/split_scale.py`: Partisi kronologis 70:30, isolasi buffer embargo 3.600 detik, fitting scaler *Train-only*.
  * `scripts/cluster_evaluate.py`: Grid search K-Means dan GMM ($k=2..8$, 3 seed acak), evaluasi metrik internal ganda, deteksi *collapse*, serta penetapan vonis *NO-WINNER*.
  * `scripts/check_contract.py`: Rangkaian *assert-based contract checks* berbasis data sintetis untuk validasi logika sebelum pengolahan data riil.
  * `outputs/manifests/`: Rekam jejak biner & *hash audit* (`phase_a_manifest.json`, `phase_b_manifest.json`, `phase_c_manifest.json`).
  * `outputs/metrics/`: Berkas metrik komprehensif (`clustering_results_all.csv`, `verdict_ledger.csv`, `train_descriptive_stats.csv`, dll.).
- **Dokumen Metodologi**:
  * `PERBANDINGAN_APPROACH_DAN_AUDIT_METODOLOGI.md`: Analisis audit metodologis komparatif detail antara pendekatan legacy dan clean pipeline v2.
  * `STATISTIK_DESKRIPTIF_DAN_EDA.md`: Analisis statistik deskriptif 13 kanal sensor pada partisi Train bersih ($n=26.723$).
- **Audit & Riset Lanjutan (`audit/`)**:
  * `clean-pipeline-56-32-plan-v1.md`: Dokumen blueprint 5 aturan ketat integritas data.
  * `plan-cross-well-16a-v1.md`: Rencana pengujian transferabilitas *Out-of-Distribution (OOD)* ke sumur berarah Well 16A(78)-32.
  * `h1-78b-negative-lock-v1.md`: Dokumentasi vonis negatif *unsuitable holdout* Well 78B-32 akibat anomali perangkat keras lapangan (gas & gamma tidak valid).
- **Tinjauan Literatur & Paper IEEE**:
  * Penelusuran literatur PRISMA 2020: 740 artikel awal $\rightarrow$ 175 tersaring $\rightarrow$ 127 telaah abstrak $\rightarrow$ 70 dinilai penuh $\rightarrow$ **9 artikel inklusi utama** + 7 artikel cadangan.
  * Naskah lengkap IEEE format 5–8 halaman tersedia di `reports/04-paper/draft_paper_ieee.md` dan `reports/04-paper/draft-paper-letx.tex`.

---

## 4. Panduan Menjalankan (How to Run)

### A. Persyaratan Lingkungan (Environment)

Pastikan lingkungan kerja telah terpasang Python 3.10+ beserta pustaka pendukung:

```bash
pip install numpy pandas scikit-learn joblib matplotlib
```

*(Opsional: jika menggunakan `kagglehub` untuk unduhan langsung)*:
```bash
pip install kagglehub
```

### B. Menjalankan Uji Kontrak Sintetis (*Contract Test*)

Sebelum menjalankan pipeline pada data masif 357 MB, validasi kebenaran logika windowing, penskalaan, dan vonis keputusan menggunakan skrip kontrak sintetis:

```bash
cd clean-pipeline-56-32/scripts
python3 check_contract.py
```

*Output yang diharapkan:*
```text
PASS: Phase A, Phase B, and Phase C contract checks
```

### C. Menjalankan Notebook Walkthrough Utama

Jalankan Jupyter Notebook dan buka berkas panduan utama:

```bash
jupyter notebook notebooks/07_clean_pipeline_walkthrough.ipynb
```

Notebook akan secara otomatis:
1. Mendeteksi keberadaan berkas data mentah `56-32 1sec data 27029986.csv` (baik di direktori lokal `dataset/`, Kaggle Input, atau unduhan via `kagglehub`).
2. Menjalankan Fase A: Pembentukan 38.177 window tumbling 60 detik.
3. Menjalankan Fase B: Partisi Train (26.723), Embargo (60), dan Test (11.394) serta penskalaan data.
4. Menjalankan Fase C: Pelatihan grid K-Means & GMM serta ekspor *verdict ledger*.

### D. Mengunduh Dataset Mandiri via KaggleHub

Jika dataset mentah belum tersedia di folder lokal, gunakan potongan skrip Python berikut:

```python
import kagglehub
from kagglehub import KaggleDatasetAdapter

file_path = "56-32 1sec data 27029986.csv"
df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "faruqmahdison/utah-datmin",
    file_path,
)
print("Ukuran dataset:", df.shape)
```

### E. Membangun Diagram PRISMA

Untuk meregenerasi diagram alir metodologi literatur PRISMA 2020:

```bash
python3 src/generate_prisma.py
# Berkas luaran tersimpan pada: figures/prisma_flowchart_restart_v6.{png,pdf,svg}
```

---

## 5. Ringkasan Eksekusi & Artefak Akhir

| Fase | Masukan | Keluaran Utama | Status Integritas |
|---|---|---|---|
| **Fase A (Windowing)** | 2.506.360 baris mentah (1 Hz) | `phase_a_manifest.json`, 38.177 window tumbling (39 fitur) | Verified (`fit_rows: 38177`) |
| **Fase B (Split & Scale)** | 38.177 window valid | `phase_b_manifest.json`, Train: 26.723, Embargo: 60, Test: 11.394 | Verified (`fit_rows == 26723`) |
| **Fase C (Grid Clustering)** | Matriks Train & Test terpisah | `clustering_results_all.csv`, `verdict_ledger.csv` (126 run) | Verified (38 NO-WINNER, 4 ELIGIBLE) |
| **Paper Publikasi** | Hasil empiris & telaah pustaka | Draft IEEE LaTeX & Markdown, Deklarasi AI | Siap konversi / submit |

Dokumentasi audit ini menegaskan komitmen bahwa seluruh proses pengolahan data menjunjung tinggi keterbukaan sains, reproduksibilitas eksperimental, dan kejujuran metodologis.
