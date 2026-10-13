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
