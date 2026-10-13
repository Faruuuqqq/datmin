<<<<<<< HEAD
# Statistik Deskriptif dan Exploratory Data Analysis (EDA) — Pipeline Bersih Rafif (Well 56-32)

> **Scope dokumen ini.** Seluruh angka di bawah berasal dari **pipeline bersih Rafif** (`clean-pipeline-56-32/`, commit `7f7a758`), bukan dari analisis upstream lama (8 sensor global).
> Unit analisis = **window tumbling 60 detik / stride 60 detik (overlap 0%)**, 13 channel → 39 fitur (`mean`, `std` populasi `ddof=0`, `delta`).
> Statistik deskriptif dan korelasi dihitung **hanya pada partisi Train (70% awal kronologis, n = 26.723 window)** dengan embargo 1 jam sebelum Test, untuk mencegah kebocoran informasi (*data leakage*).
> Nilai presisi penuh (float64) ada di CSV; tabel di dokumen ini dibulatkan 2 desimal agar terbaca.

Provenance:

- Protokol: `clean-pipeline-56-32/protocol.json` (v1.0, 13 channel, tumbling 60/60, coverage ≥ 54/60, split 70:30 + embargo ≥ 3600 s, scaler train-only).
- Manifest fase A: `clean-pipeline-56-32/outputs/manifests/phase_a_manifest.json` (`raw_sha256 fed92fa2a75c3a2c600dca558aa0e6c38d871f242fa98f1f09a06279e7357f4c`, `window_features.csv de97ccc148e69f46579fdae0c6f64016bed3dc6f27550ce83d5ae2fd0a9e6241`).
- Manifest fase B: `clean-pipeline-56-32/outputs/manifests/phase_b_manifest.json` (train 26.723, embargo 60 rows / 3600.0 s, test 11.394, `fit_rows == 26723` untuk ketiga scaler).
- Data: `clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv` (39 fitur), `train_pearson_corr.csv`, `train_spearman_corr.csv` (matriks 39×39).
- Skrip: `clean-pipeline-56-32/scripts/prepare_windows.py`, `clean-pipeline-56-32/scripts/split_scale.py`.

## 1. Taksonomi channel (11 raw + 2 turunan)

Definisi kolom mentah persis dari `prepare_windows.py:23-35`:

| Channel | Kolom mentah | Satuan/domain |
|---|---|---|
| ROP | `Rate Of Penetration (ft_per_hr)` | Pengeboran |
| WOB | `Weight on Bit (klbs)` | Mekanik |
| RPM | `Rotary RPM (RPM)` | Rotasi |
| SPP | `Standpipe Pressure (psi)` | Hidrolik |
| Torque | `Rotary Torque (kft_lb)` | Rotasi |
| HookLoad | `Hook Load (klbs)` | Pengangkatan |
| Flow | `Flow (flow_percent)` | Sirkulasi |
| PumpOut | `Total Pump Output (gal_per_min)` | Hidrolik |
| MudVol | `Total Mud Volume (barrels)` | Lumpur |
| BlockHeight | `Block Height (feet)` | Rangkaian |
| SPM1 | `Pump 1 strokes/min (SPM)` | Pompa |
| Hydraulic_P (turunan) | `max(SPP,0) * max(PumpOut,0)` | Proxy daya hidrolik |
| Mech_P (turunan) | `max(Torque,0) * max(RPM,0)` | Proxy daya mekanik |

Per channel dibentuk 3 fitur: `mean` (rata-rata finite dalam window), `std` (simpangan baku populasi, `ddof=0`), `delta` (`last_finite − first_finite`). Total 13 × 3 = **39 fitur**, sesuai `FEATURE_COLUMNS` di manifest fase A. `np.maximum` dipakai agar NaN tetap NaN (kontrak missing-input proxy).

Catatan perbedaan vs upstream lama: `Differential Pressure` **tidak dipakai** di pipeline ini; `Flow`, `MudVol`, `BlockHeight`, `SPM1`, `Hydraulic_P`, `Mech_P` adalah channel baru.

## 2. Ketimpangan skala (scale disparity) pada Train

Pada level `*_mean` Train (n = 26.723):

- Orde 10⁶: `Hydraulic_P_mean` ≈ 1.068.859 (proxy; wajar jauh lebih besar karena perkalian SPP × PumpOut).
- Orde 10³: `SPP_mean` ≈ 1.603, `MudVol_mean` ≈ 407, `PumpOut_mean` ≈ 365.
- Orde 10²: `HookLoad_mean` ≈ 110, `Mech_P_mean` ≈ 145, `BlockHeight_mean` ≈ 80.
- Orde 10¹: `Flow_mean` ≈ 46, `SPM1_mean` ≈ 47, `WOB_mean` ≈ 24, `ROP_mean` ≈ 20, `RPM_mean` ≈ 22.
- Orde 10⁰: `Torque_mean` ≈ 3,01.

Rasio antar raw channel: `SPP_mean : Torque_mean` ≈ **532 : 1**; `MudVol_mean : Torque_mean` ≈ **135 : 1**. Jika proxy diikutkan, `Hydraulic_P_mean : Torque_mean` ≈ **355.000 : 1** — angka ini struktural akibat perkalian, bukan skala sensor mentah, sehingga pemilihan scaler (Standard vs Robust vs MinMax) harus diuji train-only dan tidak boleh disimpulkan dari disparitas saja.

Median 0 masih dominan pada banyak fitur (mis. `ROP_mean`, `ROP_std`, `ROP_delta`, `Torque_delta`, `Mech_P_mean`, `Mech_P_std`, `Mech_P_delta`, `Hydraulic_P_delta`), menandakan banyak window idle. Ini membuat metrik internal seperti Silhouette rentan inflated bila okupansi timpang — lihat guard `NO-WINNER` di pipeline.

## 3. Tabel statistik deskriptif Train penuh (39 fitur, n = 26.723 window)

Sumber: `clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv`. Kolom `std` = `std_ddof0`. Presisi penuh di CSV; di sini 2 desimal.

| Fitur | n | Mean | Std | Min | Q1 | Median | Q3 | Max | Skewness |
|---|---|---|---|---|---|---|---|---|---|
| ROP_mean | 26723 | 20.43 | 79.84 | 0.00 | 0.00 | 0.00 | 22.17 | 4,303.23 | 20.98 |
| ROP_std | 26723 | 3.65 | 58.74 | 0.00 | 0.00 | 0.00 | 0.64 | 4,156.47 | 57.38 |
| ROP_delta | 26723 | 0.09 | 105.92 | -8,921.64 | 0.00 | 0.00 | 0.00 | 9,578.33 | 4.25 |
| WOB_mean | 26723 | 24.40 | 23.95 | 0.00 | 0.00 | 24.12 | 45.33 | 172.86 | 1.04 |
| WOB_std | 26723 | 5.14 | 12.81 | 0.00 | 0.00 | 0.36 | 0.84 | 88.56 | 3.19 |
| WOB_delta | 26723 | -0.05 | 25.57 | -178.90 | -0.20 | 0.00 | 0.20 | 179.60 | -0.18 |
| RPM_mean | 26723 | 21.52 | 25.94 | 0.00 | 0.03 | 0.06 | 41.21 | 104.27 | 0.86 |
| RPM_std | 26723 | 0.68 | 2.99 | 0.00 | 0.00 | 0.01 | 0.09 | 48.68 | 6.68 |
| RPM_delta | 26723 | 0.01 | 7.09 | -100.03 | 0.00 | 0.00 | 0.00 | 102.08 | -0.37 |
| SPP_mean | 26723 | 1,603.41 | 1,536.53 | 0.00 | 0.00 | 1,643.31 | 3,128.65 | 5,131.09 | 0.03 |
| SPP_std | 26723 | 22.05 | 114.72 | 0.00 | 0.00 | 3.58 | 6.98 | 2,004.56 | 8.93 |
| SPP_delta | 26723 | 0.33 | 310.99 | -4,716.37 | -1.93 | 0.00 | 2.32 | 3,781.23 | -1.63 |
| Torque_mean | 26723 | 3.01 | 3.76 | 0.00 | 0.00 | 0.00 | 5.58 | 25.74 | 1.15 |
| Torque_std | 26723 | 0.33 | 1.02 | 0.00 | 0.00 | 0.00 | 0.12 | 11.64 | 5.30 |
| Torque_delta | 26723 | 0.00 | 1.83 | -31.83 | 0.00 | 0.00 | 0.00 | 31.85 | 0.61 |
| HookLoad_mean | 26723 | 109.63 | 57.12 | 0.00 | 55.00 | 118.45 | 148.01 | 360.46 | 0.24 |
| HookLoad_std | 26723 | 6.56 | 16.02 | 0.00 | 0.25 | 0.43 | 1.72 | 137.23 | 3.15 |
| HookLoad_delta | 26723 | -0.02 | 36.56 | -280.00 | -0.60 | 0.00 | 0.50 | 296.40 | 0.04 |
| Flow_mean | 26723 | 46.26 | 34.12 | -1.48 | 5.75 | 66.51 | 72.84 | 133.66 | -0.24 |
| Flow_std | 26723 | 1.38 | 4.13 | 0.00 | 0.01 | 0.36 | 0.79 | 46.95 | 5.52 |
| Flow_delta | 26723 | 0.00 | 9.09 | -125.87 | -0.20 | 0.00 | 0.21 | 128.46 | 0.07 |
| PumpOut_mean | 26723 | 365.01 | 327.00 | 0.00 | 0.00 | 460.82 | 669.17 | 1,757.69 | -0.07 |
| PumpOut_std | 26723 | 6.28 | 28.89 | 0.00 | 0.00 | 1.55 | 2.39 | 542.77 | 7.84 |
| PumpOut_delta | 26723 | 0.02 | 76.65 | -1,087.40 | -0.96 | 0.00 | 0.96 | 895.05 | -0.61 |
| MudVol_mean | 26723 | 407.27 | 64.36 | 195.25 | 392.42 | 422.88 | 442.82 | 597.27 | -1.08 |
| MudVol_std | 26723 | 0.40 | 0.53 | 0.00 | 0.13 | 0.27 | 0.46 | 7.98 | 3.66 |
| MudVol_delta | 26723 | 0.01 | 1.98 | -19.20 | -0.31 | 0.00 | 0.39 | 25.45 | 0.17 |
| BlockHeight_mean | 26723 | 80.02 | 41.43 | -8.54 | 47.77 | 78.96 | 106.54 | 192.47 | 0.37 |
| BlockHeight_std | 26723 | 4.59 | 10.35 | 0.00 | 0.05 | 0.13 | 1.20 | 45.55 | 2.36 |
| BlockHeight_delta | 26723 | -0.01 | 25.09 | -101.30 | -0.60 | -0.30 | 0.00 | 97.20 | 0.08 |
| SPM1_mean | 26723 | 46.51 | 42.38 | 0.00 | 0.00 | 72.68 | 84.55 | 119.43 | -0.11 |
| SPM1_std | 26723 | 0.84 | 4.03 | 0.00 | 0.00 | 0.21 | 0.32 | 61.33 | 7.53 |
| SPM1_delta | 26723 | 0.00 | 10.67 | -108.89 | 0.00 | 0.00 | 0.00 | 119.60 | -0.61 |
| Hydraulic_P_mean | 26723 | 1,068,859.23 | 1,058,124.33 | 0.00 | 0.00 | 891,395.50 | 2,128,363.08 | 6,339,622.98 | 0.13 |
| Hydraulic_P_std | 26723 | 16,485.55 | 81,344.60 | 0.00 | 0.00 | 5,357.65 | 8,326.73 | 1,935,820.25 | 9.71 |
| Hydraulic_P_delta | 26723 | 138.63 | 217,206.04 | -3,883,170.19 | -1,326.71 | 0.00 | 2,218.99 | 4,806,120.33 | -1.34 |
| Mech_P_mean | 26723 | 145.30 | 218.70 | 0.00 | 0.00 | 0.00 | 247.90 | 1,777.36 | 2.08 |
| Mech_P_std | 26723 | 11.06 | 31.29 | 0.00 | 0.00 | 0.00 | 5.37 | 612.92 | 5.94 |
| Mech_P_delta | 26723 | -0.10 | 66.57 | -1,781.27 | 0.00 | 0.00 | 0.00 | 1,378.96 | -2.54 |

Bacaan skew: `ROP_std` (57.38), `ROP_mean` (20.98), `Hydraulic_P_std` (9.71), `SPP_std` (8.93), `PumpOut_std` (7.84), `SPM1_std` (7.53) sangat menjulur kanan — lonjakan sporadis / window campuran idle-aktif. `MudVol_mean` (−1.08) menjulur kiri. Skew ekstrem pada fitur `*_std` memvalidasi perlunya kandidat RobustScaler dibanding hanya StandardScaler, dengan keputusan tetap lewat evaluasi train-only.

## 4. Korelasi antar-fitur window pada Train (Pearson + Spearman)

Sumber: `train_pearson_corr.csv` dan `train_spearman_corr.csv` (39×39, level agregat window — tidak sebanding langsung dengan korelasi point-1Hz upstream lama). Nilai di bawah untuk pasangan `*_mean`:

| Pasangan | Pearson (Train) | Spearman (Train) | Bacaan |
|---|---|---|---|
| SPP_mean – Hydraulic_P_mean | 0.9839 | 0.9713 | Sangat kuat; sebagian struktural karena Hydraulic_P diturunkan dari SPP |
| PumpOut_mean – SPM1_mean | 0.9687 | 0.9563 | Sangat kuat; kopling pompa |
| PumpOut_mean – Hydraulic_P_mean | 0.9661 | 0.9221 | Sangat kuat; sebagian struktural (turunan PumpOut) |
| SPP_mean – PumpOut_mean | 0.9575 | 0.8672 | Sangat kuat; dinamika hidrolika sirkulasi lumpur |
| SPP_mean – SPM1_mean | 0.9108 | 0.8199 | Sangat kuat; pompa–tekanan |
| RPM_mean – Mech_P_mean | 0.9041 | 0.9045 | Sangat kuat; sebagian struktural (turunan RPM) |
| Torque_mean – Mech_P_mean | 0.8537 | 0.9793 | Sangat kuat; sebagian struktural (turunan Torque) |
| RPM_mean – Torque_mean | 0.8192 | 0.8568 | Kuat; interaksi rotasi–gesekan |
| SPP_mean – Flow_mean | 0.7542 | 0.6372 | Kuat; aliran–tekanan |
| HookLoad_mean – PumpOut_mean | 0.7061 | 0.6148 | Kuat; beban–sirkulasi pada level window |
| RPM_mean – SPP_mean | 0.6942 | 0.6492 | Moderat-kuat |
| ROP_mean – WOB_mean | 0.0838 | 0.6654 | Pearson lemah tapi Spearman moderat-kuat → hubungan monoton nonlinier; laju penetrasi tidak linier terhadap beban pahat saja |

Peringatan: korelasi yang melibatkan `Hydraulic_P`/`Mech_P` tidak boleh dibaca sebagai temuan fisik murni — keduanya adalah proxy perkalian sehingga korelasi tinggi dengankomponennya sudah diharapkan. Gunakan pasangan non-turunan (mis. SPP–PumpOut, RPM–Torque, ROP–WOB) untuk justifikasi domain.

## 5. Sentinel, gap, coverage, dan attrition (fase A)

Aturan dari `protocol.json` + `prepare_windows.py:49-74,134-152` + `phase_a_manifest.json`:

- Drop baris instrumen: `SPP <= -900` → **29.503 baris dibuang** dari 2.506.359 raw → retained 2.476.856.
- Masking sentinel: nilai tepat `-999.25` pada 11 kolom mentah → NaN (setelah drop SPP). Proxy memakai `np.maximum(..., 0.0)` yang mempertahankan NaN.
- Segment reset: setiap selisih timestamp setelah row-drop yang **tidak tepat +1 detik** memutus segmen → **28 segmen, 27 reset**. Tail segmen yang tidak genap 60 baris dibuang (**596 baris**).
- Coverage gate: tiap channel dalam tiap window 60 baris wajib ≥ **54 observasi finite**; window dengan channel di bawah ambang atau fitur non-finite ditolak → kandidat 41.271 → **valid 38.177** → **reject 3.094**. `feature_matrix_has_only_finite_values: true`.
- Tidak ada imputasi diam-diam dan tidak ada window yang melintasi gap/segmen.

## 6. Isolasi Train-only, embargo, dan scaler (fase B)

Dari `phase_b_manifest.json`:

- Split kronologis atas 38.177 window valid: **train 26.723 (70% awal)**, **embargo 60 window / 3600.0 s** (`train_support_end_exclusive 2021/02/26 21:20:32` → `first_test_start 2021/02/26 22:20:32`), **test 11.394**.
- Ketiga scaler (`StandardScaler`, `RobustScaler`, `MinMaxScaler`) di-fit **hanya pada Train** (`fit_rows == 26723 == n_train`); Test hanya di-`transform` dengan objek yang sama. Hash input fase A terverifikasi (`input_phase_a_sha256_verified: true`).
- Tabel §3 dan matriks §4 di dokumen ini memakai **Train saja**. Statistik Test/embargo tidak dicampur ke fit/seleksi.

## 7. Inventaris artefak visualisasi dan metrik

Tersedia di `clean-pipeline-56-32/outputs/`:

- `figures/eda_correlation_heatmap.png` — heatmap korelasi Pearson Train 39×39.
- `figures/eda_scale_disparity_boxplots.png` — boxplot disparitas skala Train.
- `figures/eda_scaler_comparison_distributions.png` — perbandingan distribusi sebelum/sesudah scaling (Standard/Robust/MinMax, fit Train-only).
- `metrics/train_descriptive_stats.csv` — sumber Tabel §3 (presisi penuh).
- `metrics/train_pearson_corr.csv`, `metrics/train_spearman_corr.csv` — sumber Tabel §4.
- `manifests/phase_a_manifest.json`, `manifests/phase_b_manifest.json` — bukti attrition, split, embargo, dan hash.

## 8. Catatan kritis metodologi

- Dokumen ini adalah **EDA train-only pipeline bersih Rafif**, bukan EDA global. Perbandingan dengan EDA upstream lama tidak valid tanpa menyamakan unit (point vs window), scope (global vs train), dan set channel (8 vs 13).
- Jangan mempromosikan `Hydraulic_P`/`Mech_P` sebagai sensor independen — keduanya turunan dan korelasinya terinflasi secara struktural.
- Skew ekstrem pada `ROP_std`/`ROP_mean` dan dominasi median 0 bukan alasan membuang data; keduanya adalah sinyal untuk RobustScaler + guard okupansi/kestabilan (`NO-WINNER`) pada tahap clustering.
- Klaim rezim fisik tetap memakai label sementara `C0..Ck` sampai ada driller log / validasi ahli independen; centroid statistik bukan ground truth operasional.
=======
# Statistik Deskriptif dan Exploratory Data Analysis (EDA) — Pipeline Bersih Well 56-32

Dokumen ini menyajikan spesifikasi formal, taksonomi kanal, statistik deskriptif resmi, dan *Exploratory Data Analysis* (EDA) untuk proyek klasterisasi deret waktu data sensor geotermal Well 56-32. Seluruh analisis statistik dan eksplorasi data dihitung secara ketat **HANYA pada partisi Train (70% kronologis)** dari **Clean Pipeline v2** untuk menjamin *Zero Data Leakage*. Angka-angka historis dari repositori *upstream* lama diisolasi dalam bab tersendiri sebagai catatan bukti temuan audit cacat metodologi (*flawed legacy baseline*).

---

## 1. Prinsip Desain & Integritas Temporal Pipeline Bersih v2

Data pemboran Well 56-32 merupakan deret waktu operasional frekuensi tinggi (1 Hz) dengan total 2.506.359 baris mentah. Untuk menjaga validitas ilmiah dan mencegah manipulasi data, Pipeline Bersih v2 menerapkan protokol ketat:

### 1.1 Aturan Pembersihan Data (*Data Hygiene Rules*)
1. **Filter Baris Invalid SPP:** Baris dengan `Standpipe Pressure (SPP) <= -900.0 psi` dieliminasi pada tahap awal pemuatan *chunk* (29.503 baris tersaring, 2.476.856 baris dipertahankan).
2. **Masking Nilai Sentinel:** Nilai `-999.25` (kode *null/disconnected sensor* pada instrumentasi Pason) dimasking menjadi `NaN` untuk mencegah bias kalkulasi numerik.
3. **Preservasi Waktu Asli & Aturan Gap-Reset (*True Time & Gap-Reset Rule*):**
   - Waktu dihitung dari cap waktu nyata (`timestamp = YYYY/MM/DD + HH:MM:SS`).
   - Jika selisih antar-baris berurutan $\Delta t > 1\text{ detik}$, terjadi *segment reset* (tercatat 28 segmen kontinu, 27 kali reset).
   - Window deret waktu tidak boleh melintasi batas segmen; sisa baris di ujung segmen yang kurang dari 60 detik langsung dibuang (*tail discarded*, 596 baris).
4. **Tumbling Window & Pintu Lolos Cakupan (*Coverage Gate*):**
   - Jendela waktu berukuran tetap 60 detik dengan *stride* 60 detik (0% *overlap* / *tumbling window* independen).
   - Dari 41.271 kandidat window, diterapkan batas toleransi data valid $\ge 54/60\text{ detik}$ (90% cakupan) per kanal. Window yang tidak memenuhi ambang batas ditolak (3.094 window ditolak).
   - Total window valid yang dihasilkan: **38.177 window**.

### 1.2 Partisi Kronologis & Kontrak Isolasi Data (*Zero Data Leakage Contract*)
Data deret waktu tidak boleh diacak (*no random shuffling*). Pemisahan data dilakukan secara sekuensial berdasarkan urutan waktu:
- **Partisi Train (70% awal):** 26.723 window valid (rentang waktu: 2021/01/08 13:00:00 s.d. 2021/02/26 21:20:32).
- **Zona Embargo Temporal:** 60 window waktu dieliminasi (buffer waktu tepat 1 jam / 3.600 detik: 2021/02/26 21:20:32 s.d. 2021/02/26 22:20:32) untuk memutus efek autokorelasi deret waktu dan *lookahead bias*.
- **Partisi Test (30% akhir):** 11.394 window valid (rentang waktu: 2021/02/26 22:20:32 s.d. 2021/03/17 23:59:00).
- **Aturan Mutlak:** Seluruh analisis deskriptif, penentuan parameter pencilan, matriks korelasi, serta fitting scaler (Standard, Robust, MinMax) dilakukan **HANYA pada partisi Train**. Partisi Test disegel (*never peeked*) dan hanya menerima transformasi proyeksi dari parameter yang telah di-fit di Train.

---

## 2. Taksonomi & Spesifikasi Formal 13 Kanal Pemodelan

Pipeline Bersih v2 memodelkan 13 kanal yang merepresentasikan dinamika mekanik, hidrolik, dan sirkulasi pemboran geotermal (11 kanal sensor primer Pason + 2 kanal proksi daya fisik turunan).

### 2.1 Tabel Skema Kanal Sensor
| No | Nama Kanal | Kolom Sumber Raw CSV | Satuan | Formula / Tipe | Peran Fisik dalam Operasi Pemboran |
|:---|:---|:---|:---:|:---:|:---|
| 1 | **ROP** | `Rate Of Penetration (ft_per_hr)` | ft/hr | Raw Pason | Laju penetrasi pemboran ke dalam formasi batuan |
| 2 | **WOB** | `Weight on Bit (klbs)` | klbs | Raw Pason | Beban aksial yang dibebankan pada mata bor |
| 3 | **RPM** | `Rotary RPM (RPM)` | RPM | Raw Pason | Kecepatan rotasi meja putar (*rotary table* / *top drive*) |
| 4 | **SPP** | `Standpipe Pressure (psi)` | psi | Raw Pason | Tekanan sirkulasi fluida lumpur dalam *standpipe* |
| 5 | **Torque** | `Rotary Torque (kft_lb)` | kft·lb | Raw Pason | Momen torsi resistansi rotasi mata bor |
| 6 | **HookLoad** | `Hook Load (klbs)` | klbs | Raw Pason | Beban regangan suspensi pada kait pemikul rangkaian pipa |
| 7 | **Flow** | `Flow (flow_percent)` | % | Raw Pason | Persentase relatif laju aliran balik lumpur pemboran |
| 8 | **PumpOut** | `Total Pump Output (gal_per_min)` | gpm | Raw Pason | Laju volumetrik pemompaan lumpur gabungan |
| 9 | **MudVol** | `Total Mud Volume (barrels)` | bbl | Raw Pason | Total volume lumpur aktif dalam tangki sirkulasi |
| 10 | **BlockHeight** | `Block Height (feet)` | ft | Raw Pason | Elevasi vertikal posisi *traveling block* di menara bor |
| 11 | **SPM1** | `Pump 1 strokes/min (SPM)` | SPM | Raw Pason | Kecepatan stroke mekanis pompa sirkulasi 1 |
| 12 | **Hydraulic_P** | *Derived Proxy* | psi·gpm | $\max(\text{SPP}, 0) \times \max(\text{PumpOut}, 0)$ | Proksi daya hidrolika sistem pemompaan sirkulasi |
| 13 | **Mech_P** | *Derived Proxy* | kft·lb·RPM | $\max(\text{Torque}, 0) \times \max(\text{RPM}, 0)$ | Proksi daya mekanik rotasi pemotongan formasi |

### 2.2 Ekstraksi Fitur Window (39 Fitur Total)
Setiap window 60 detik mengekstraksi 3 fitur agregasi untuk masing-masing dari 13 kanal:
1. **Mean ($\mu$):** Rata-rata nilai finite dalam window: $\mu = \frac{1}{N} \sum_{i=1}^N x_i$.
2. **Standard Deviation ($\sigma$, ddof=0):** Variabilitas internal window: $\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^N (x_i - \mu)^2}$.
3. **Endpoint Delta ($\Delta$):** Tren perubahan neto sepanjang window: $\Delta = x_{\text{end}} - x_{\text{start}}$.

Total matriks fitur berdimensi $N \times 39$ ($26.723 \times 39$ untuk partisi Train; $11.394 \times 39$ untuk partisi Test).

---

## 3. Statistik Deskriptif Partisi Train Resmi (70% Kronologis, N = 26.723 Windows)

Sumber data resmi: `clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv`. Tabel berikut menyajikan statistik deskriptif agregat (fitur rata-rata window / `_mean`) yang dihitung secara independen pada partisi Train Well 56-32:

| Fitur Kanal | Satuan | Mean | Std ($\text{ddof}=0$) | Min | Q1 (25%) | Median (50%) | Q3 (75%) | Max | Skewness | Interpretasi Fisik |
|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| **ROP_mean** | ft/hr | 20,43 | 79,84 | 0,00 | 0,00 | 0,00 | 22,17 | 4.303,23 | 20,98 | Kecepatan penetrasi; lonjakan pencilan ekor kanan saat formasi lunak/transisi |
| **WOB_mean** | klbs | 24,40 | 23,95 | 0,00 | 0,00 | 24,13 | 45,33 | 172,86 | 1,04 | Beban vertikal pada mata bor |
| **RPM_mean** | RPM | 21,52 | 25,94 | 0,00 | 0,03 | 0,06 | 41,21 | 104,27 | 0,86 | Kecepatan putaran meja putar / top drive |
| **SPP_mean** | psi | 1.603,41 | 1.536,53 | 0,00 | 0,00 | 1.643,31 | 3.128,65 | 5.131,09 | 0,03 | Tekanan sirkulasi fluida lumpur dalam pipa |
| **Torque_mean** | kft·lb | 3,01 | 3,76 | 0,00 | 0,00 | 0,00 | 5,58 | 25,74 | 1,15 | Momen torsi resistansi gesekan formasi |
| **HookLoad_mean** | klbs | 109,63 | 57,12 | 0,00 | 55,00 | 118,45 | 148,01 | 360,46 | 0,24 | Beban suspensi traveling block menahan rangkaian pipa |
| **Flow_mean** | % | 46,26 | 34,12 | -1,48 | 5,75 | 66,51 | 72,84 | 133,66 | -0,24 | Persentase aliran balik lumpur pemboran |
| **PumpOut_mean** | gpm | 365,01 | 327,00 | 0,00 | 0,00 | 460,82 | 669,17 | 1.757,69 | -0,07 | Debit volumetrik pemompaan sirkulasi lumpur |
| **MudVol_mean** | bbl | 407,27 | 64,36 | 195,25 | 392,42 | 422,88 | 442,82 | 597,27 | -1,08 | Total volume tangki penampung lumpur |
| **BlockHeight_mean**| ft | 80,02 | 41,43 | -8,54 | 47,77 | 78,96 | 106,54 | 192,47 | 0,37 | Elevasi ketinggian vertikal traveling block |
| **SPM1_mean** | SPM | 46,51 | 42,38 | 0,00 | 0,00 | 72,68 | 84,55 | 119,43 | -0,11 | Frekuensi kayuhan stroke pompa lumpur 1 |
| **Hydraulic_P_mean**| psi·gpm | 1.068.859,23 | 1.058.124,33 | 0,00 | 0,00 | 891.395,50 | 2.128.363,08 | 6.339.622,98 | 0,13 | Proksi daya hidrolika sirkulasi ($10^6$) |
| **Mech_P_mean** | kft·lb·RPM | 145,30 | 218,70 | 0,00 | 0,00 | 0,00 | 247,90 | 1.777,36 | 2,08 | Proksi daya mekanik pemotongan batuan |

### 3.1 Ketimpangan Skala (*Scale Disparity*)
Data sensor memperlihatkan disparitas magnitudo yang sangat lebar antar-satuan fisik:
- **Orde Jutaan ($10^6$):** `Hydraulic_P_mean` (rata-rata $1{,}07 \times 10^6$ psi·gpm).
- **Orde Ribuan ($10^3$):** `SPP_mean` (rata-rata 1.603 psi, maksimum 5.131 psi).
- **Orde Ratusan ($10^2$):** `MudVol_mean` (~407 bbl), `PumpOut_mean` (~365 gpm), `Mech_P_mean` (~145), `HookLoad_mean` (~110 klbs), `BlockHeight_mean` (~80 ft).
- **Orde Puluhan ($10^1$):** `SPM1_mean` (~46 SPM), `WOB_mean` (~24 klbs), `RPM_mean` (~21 RPM), `ROP_mean` (~20 ft/hr).
- **Orde Satuan ($10^0$):** `Torque_mean` (rata-rata 3,01 kft·lb).

*Rasio Skala Ekstrem:* Rasio magnitudo Daya Hidraulik ($10^6$) terhadap Torsi ($10^0$) mencapai $> 10^5 : 1$. Ini mewajibkan penskalaan fitur sebelum klasterisasi jarak Euclidean K-Means.

### 3.2 Karakteristik Distribusi dan Kemiringan (*Skewness*)
- **Ekor Kanan Ekstrem pada ROP:** `ROP_mean` memiliki kemiringan (*skewness*) **20,98** dengan nilai maksimum mencapai 4.303,23 ft/hr dan median 0,00 ft/hr. Hal ini mencerminkan fenomena operasi riil di mana rig sering berada dalam fase rotasi tanpa penetrasi (*off-bottom circulation* / *connection*), diselingi lonjakan penetrasi sesaat saat menembus zona rekahan atau formasi lunak.
- **Dua Rezim Operasi (Bimodal):** Pada `SPP_mean`, `PumpOut_mean`, `SPM1_mean`, dan `RPM_mean`, kuartil pertama (Q1) bernilai 0 (pompa/rotasi mati saat penyambungan pipa atau perawatan) dan melonjak tajam pada kuartil ketiga (Q3) saat operasi sirkulasi/pemboran aktif.

---

## 4. Analisis Korelasi Antar-Sensor Bebas Bocor (Train Partition Only)

Sumber data resmi: `clean-pipeline-56-32/outputs/metrics/train_pearson_corr.csv` dan `train_spearman_corr.csv`. Evaluasi korelasi Pearson ($r$) dan korelasi peringkat Spearman ($\rho$) pada partisi Train memvalidasi relasi fisik operasional rig pemboran:

### 4.1 Pasangan Kopling Hidrolik
- **SPP ↔ PumpOut:** Pearson $r = 0,9839$, Spearman $\rho = 0,9713$. Korelasi positif linear yang sangat kuat mencerminkan hukum resistansi hidrolika sirkulasi lumpur di dalam rangkaian pipa bor.
- **SPP ↔ SPM1:** Pearson $r = 0,9193$, Spearman $\rho = 0,8781$. Frekuensi stroke pompa lumpur secara langsung mengatur tekanan sirkulasi fluida *standpipe*.
- **PumpOut ↔ SPM1:** Pearson $r = 0,9661$, Spearman $\rho = 0,9221$. Linieritas tinggi antara kayuhan mekanik pompa dan output volumetrik fluida.
- **SPP ↔ Hydraulic_P:** Pearson $r = 0,9839$. Proksi daya hidrolika mencerminkan tekanan sirkulasi secara konsisten.

### 4.2 Pasangan Kopling Mekanik
- **RPM ↔ Torque:** Pearson $r = 0,7068$, Spearman $\rho = 0,7709$. Menggambarkan interaksi rotasi meja putar dengan tahanan gesek formasi batuan pada pahat bor.
- **RPM ↔ Mech_P:** Pearson $r = 0,7068$. Proksi daya mekanik secara akurat merefleksikan kombinasi torsi dan putaran bor.

### 4.3 Dinamika Penetrasi Batuan Geotermal (ROP vs WOB)
- **ROP ↔ WOB:** Pearson $r = 0,2569$, Spearman $\rho = 0,6455$.
- *Interpretasi Fisik:* Korelasi linear Pearson yang rendah ($r = 0,257$) namun korelasi monotonik Spearman yang moderat ($\rho = 0,646$) membuktikan bahwa interaksi antara beban pahat (WOB) dan laju penetrasi (ROP) pada formasi geotermal bersifat non-linear kompleks. Pada batuan granit keras, penambahan WOB saja tidak menjamin kenaikan laju penetrasi secara proporsional linier, melainkan dipengaruhi efisiensi pembersihan hidrolik dan ketahanan aus pahat.

---

## 5. Analisis Pencilan (*Outliers*), Sentinel, dan Pilihan Scaler

### 5.1 Penanganan Anomali & Sentinel
- **Anomali Sentinel $-999{,}25$:** Masked to NaN (tidak diimputasi rata-rata).
- **Eliminasi Anomali SPP:** Baris SPP $\le -900$ psi (29.503 baris) dibuang pada tahap pembersihan chunk.
- **Pemisahan Segmen Waktu:** Setiap celah waktu $\ne +1$ detik memicu reset batas segmen (28 segmen kontinu, 27 reset).
- **Jendela Tumbling 60 Detik:** Stride 60 detik (0% overlap, anti-leakage). Threshold kelengkapan $\ge 54/60$ detik valid menyaring **38.177 jendela valid**.

### 5.2 Evaluasi Komparatif Pilihan Scaler (Phase C Ledger)
Pada evaluasi klasterisasi Train vs Test:
1. **RobustScaler:** Terdiskualifikasi sebagai **`NO-WINNER`** akibat *Cluster Collapse* katastropik (99,25% data menumpuk di C0). Skor Silhouette yang tampak tinggi ($0{,}8822$) terbukti merupakan ilusi geometris isolasi pencilan ekstrem pada kanal ROP.
2. **StandardScaler:** Terdiskualifikasi sebagai **`NO-WINNER`** akibat *Sharp Test Drop* (Silhouette anjlok $> 0{,}16$) dan keruntuhan pada C2/C3 ($< 1\%$).
3. **MinMaxScaler:** Ditetapkan sebagai satu-satunya konfigurasi resmi (**`ELIGIBLE`**) pada K-Means $k=4$, menghasilkan partisi sehat (proporsi klaster terkecil 12,36%), Silhouette stabil (Train 0,3104 / Test 0,2677), DBI (Train 1,5715 / Test 2,0611), dan kestabilan stokastik ARI 0,9997.

---

## 6. Inventaris Artefak Visualisasi Resmi

Tersedia di repositori pada direktori `clean-pipeline-56-32/outputs/figures/`:
- `eda_correlation_heatmap.png`: Heatmap korelasi Pearson 39 fitur partisi Train.
- `eda_scale_disparity_boxplots.png`: Boxplot disparitas skala antar kanal sensor (symlog scale).
- `eda_scaler_comparison_distributions.png`: Perbandingan histogram distribusi sebelum dan sesudah standarisasi (Standard, Robust, MinMax).
- `cluster_kmeans_inertia_elbow.png`: Kurva inersia Elbow K-Means Train ($k=2..8$).
- `cluster_silhouette_train_vs_test.png` & `cluster_dbi_train_vs_test.png`: Perbandingan metrik Train vs Test multi-panel.

---

## 7. Catatan Temuan Audit Baseline Lama (*Flawed Legacy Upstream Artifacts*)

Sebagai bagian dari integritas audit, bab ini mendokumentasikan angka-angka historis yang tercatat pada artefak *upstream* lama (`reports/03-sintesis/tahap2_final.md` dan `notebooks/final_clustering_outputs06/table1_descriptive.csv`), sekaligus merinci **mengapa angka-angka tersebut cacat secara metodologis**:

### 7.1 Tabel Statistik Upstream Lama (Subset ~200k Baris)
*Sumber:* Dokumen historis `reports/03-sintesis/tahap2_final.md` (diambil dari subset acak ~200k observasi hasil `dropna` naif):

| Sensor Upstream Lama | Satuan | Mean | Std | Min | Median | Max | Skewness | Range |
|:---|:---:|---:|---:|---:|---:|---:|---:|---:|
| Rate of Penetration (ROP) | ft/hr | 24.91 | 100.46 | 0.00 | 0.00 | 2,860.80 | 37.63 | 2,860.80 |
| Weight on Bit (WOB) | klbs | 7.93 | 11.08 | 0.00 | 0.00 | 66.80 | 1.45 | 66.80 |
| Rotary RPM | RPM | 44.52 | 51.52 | 0.00 | 0.00 | 206.00 | 0.44 | 206.00 |
| Standpipe Pressure (SPP) | psi | 1,209.39 | 1,488.61 | 0.00 | 0.00 | 4,891.00 | 0.55 | 4,891.00 |
| Rotary Torque | kft_lb | 3.51 | 5.37 | 0.00 | 0.00 | 30.60 | 1.83 | 30.60 |
| Hook Load | klbs | 215.11 | 43.18 | 49.30 | 218.40 | 344.80 | -0.74 | 295.50 |
| Flow Out | % | 23.36 | 28.53 | 0.00 | 0.00 | 100.00 | 0.70 | 100.00 |
| Differential Pressure | psi | -692.20 | 1,123.67 | -4,500.00 | 0.00 | 3,745.00 | -1.21 | 8,245.00 |

### 7.2 Bedah Cacat Metodologis Baseline Upstream Lama
1. **Penghancuran Struktur Deret Waktu via `dropna` Naif:**
   Baseline lama menerapkan pembersihan berbasis pembuangan baris kosong (`dropna`) secara serampangan pada raw data 1 Hz tanpa mempedulikan kontinuitas waktu. Hal ini menghasilkan deret data semu di mana interval detik melompat dari jam ke hari tanpa adanya *gap reset*, menghancurkan sifat fisik deret waktu (*time series breakdown*).
2. **Cakupan Sensor Tidak Lengkap (Hanya 8 Sensor Parsial):**
   Tabel lama hanya mengambil 8 kolom parsial dan memasukkan kolom `Differential Pressure` yang memiliki nilai negatif ekstrim (-4.500 psi). Baseline lama mengabaikan kanal penting seperti volume lumpur (`MudVol`), posisi blok (`BlockHeight`), stroke pompa (`SPM1`), serta proksi interaksi fisik (`Hydraulic_P` dan `Mech_P`).
3. **Kebocoran Data Total (*Full Data Leakage / Lookahead Bias*):**
   Pada repositori lama, statistik deskriptif dan standarisasi fitur dihitung secara global pada seluruh populasi subset ~200k baris. Tidak ada pemisahan partisi latih/uji (*train/test split*) kronologis dan tidak ada zona embargo temporal. Hal ini menyebabkan kebocoran statistik masa depan ke data masa lalu (*lookahead leakage*).
4. **Subset Tidak Terdokumentasi & Tanpa Hash Provenance:**
   Angka 200k baris dipilih secara arbitrer tanpa kriteria sampling terverifikasi, tanpa hash SHA-256 berkas input/output, dan tanpa pelaporan tingkat kegagalan klaster (*cluster collapse*).

---

## 8. Status Kesiapan & Integritas Artefak Fase A & B

Pipeline Bersih v2 telah menyelesaikan tahap ekstraksi window (Fase A) dan pemisahan/standarisasi partisi (Fase B) dengan integritas kriptografis yang tervalidasi:

- **Raw Data Well 56-32 SHA-256:** `fed92fa2a75c3a2c600dca558aa0e6c38d871f242fa98f1f09a06279e7357f4c` (2.506.359 baris).
- **Valid Window Matrix (Fase A):** `38.177 baris x 39 fitur` (SHA-256: `de97ccc148e69f46579fdae0c6f64016bed3dc6f27550ce83d5ae2fd0a9e6241`).
- **Partisi Train 70% (Fase B):** `26.723 baris` (SHA-256: `2c823fe4db20755ec213fa66c3a07fd648c6f376cf774b9711c1d811fcf0b04c`).
- **Partisi Test 30% (Fase B):** `11.394 baris` (SHA-256: `18fbe9004d49d479e0bf03bfe0290caeefdfc2ec7f75d1d6dc9b7b9cf49f8721`).
- **Embargo Window:** Tepat 60 window (3.600 detik) terisolasi tanpa kebocoran data.

Seluruh data statistik dan parameter scaling dalam dokumen ini telah terkunci dan siap digunakan sebagai fondasi pemodelan klasterisasi K-Means dan GMM pada Fase C.
>>>>>>> 6a9fa0d2ae150b3b2ad2101d77d396951add8a0e
