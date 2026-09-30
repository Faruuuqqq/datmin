# TAHAP 2 FINAL — Data Understanding & Preprocessing Plan (terkunci 30 Sep 2026)

> Dataset: Utah FORGE Well 56-32, Pason 1 Hz, 2.506.360 baris × 22 kolom.
> Angka di bawah dari Colab 200k sampel acak (seed 42) + run notebook fathan (80k head-segment).
> Syarat tugas: ≥5 atribut numerik kontinu, beda skala, unlabeled — TERPENUHI (8 sensor).

## 2.1 Taksonomi sensor (8 dimodelkan + 2 dibuang)

| # | Sensor | Satuan | Domain | Status |
|---|---|---|---|---|
| 1 | Rate Of Penetration (ROP) | ft/hr | Pengeboran | Utama |
| 2 | Weight on Bit (WOB) | klbs | Mekanik | Utama |
| 3 | Rotary RPM | RPM | Rotasi | Utama |
| 4 | Standpipe Pressure (SPP) | psi | Hidrolik | Utama |
| 5 | Rotary Torque | kft-lb | Rotasi | Utama |
| 6 | Hook Load | klbs | Pengangkatan | Utama |
| 7 | Differential Pressure | psi | Hidrolik | Utama, KANDIDAT DROP (mean −692, skew −1.21) |
| 8 | Total Pump Output | GPM | Hidrolik | Utama |
| — | Pason Gas | % | — | DIBUANG (100% sentinel −999.25) |
| — | Gamma | API | — | DIBUANG (100% sentinel −999.25) |

## 2.2 Statistik deskriptif (sentinel dibuang; n ≈ 200k)

| Sensor | Mean | Std | Min | Median | Max | Skew | Range |
|---|---|---|---|---|---|---|---|
| ROP | 24.91 | 100.46 | 0 | 0 | 10,771.57 | **37.63** | 10,771.57 |
| WOB | 19.03 | 28.89 | 0 | 0 | 191.90 | 2.10 | 191.90 |
| RPM | 16.50 | 24.04 | 0 | 0.03 | 105.30 | 1.19 | 105.30 |
| SPP | 1,209.39 | 1,488.61 | 0 | 0 | 5,239.64 | 0.55 | 5,239.64 |
| Torque | 2.15 | 3.60 | 0 | 0 | 41.61 | 1.89 | 41.61 |
| Hookload | 93.30 | 60.91 | 0 | 65.50 | 376.70 | 0.72 | 376.70 |
| Diff Press | **−692.20** | 1,136.23 | −5,138.83 | −97.06 | 5,115.00 | −1.21 | 10,253.83 |
| Pump Out | 256.43 | 311.22 | 0 | 0 | 1,771.75 | 0.58 | 1,771.75 |

**Rasio skala: 258.9 : 1** (ROP vs Torque) → Euclidean collapse tanpa scaler. Median 5 sensor = 0 (dominan idle → Silhouette rentan inflated, lihat Tahap 3).

## 2.3 Sentinel & outlier

| Sensor | Sentinel −999.25 | Outlier IQR | Batas IQR |
|---|---|---|---|
| ROP | 2 (≈0%) | **8.65%** | −28.4 / 47.4 |
| WOB | 1 (≈0%) | 2.25% | −62.6 / 104.3 |
| RPM | 39 (0.02%) | 0.71% | −58.9 / 98.1 |
| SPP | 2,346 (1.17%) | 0.00% | −4,508 / 7,513 |
| Torque | 39 (0.02%) | 2.29% | −6.7 / 11.2 |
| Hookload | 2 (≈0%) | 0.26% | −112 / 291 |
| Diff Press | 2,346 (1.17%) | 0.68% | −3,951 / 2,583 |
| Pump Out | 2 (≈0%) | 0.02% | −990 / 1,651 |

Bacaan fisik: spike ROP = artefak kalkulasi (di-winsorize); spike Torque/WOB = stick-slip asli (direduksi RobustScaler, tidak dibuang).

## 2.4 Korelasi (Pearson) — kopel fisik rig

- SPP–Pump **0.925** (hidrolik), RPM–Torque **0.747** (rotasi), RPM–SPP 0.736, Hook–Pump 0.697.
- ROP–WOB **0.007** → hubungan nonlinier di granit; justifikasi regime discovery (bukan regresi).
- Visual: heatmap `fig1_correlation.png` + boxplot `fig2_boxplots.png` (output Kaggle — unduh ke `figures/`).

## 2.5 Preprocessing Plan (FINAL-LOCK, sudah di kode notebook fathan)

1. Sentinel → NaN; `dropna(subset=SENSORS)`; Pason Gas/Gamma dibuang.
2. **Winsorize ROP** di HI = Q3+1.5·IQR (≈47) — kode: cell 16/21/26.
3. **Diff Press default OFF** (7 sensor); run sensitivitas via `USE_DIFF_PRESS = True` untuk 8 sensor.
4. Dua jalur scaler: StandardScaler vs RobustScaler (median–IQR).
5. Dua representasi: point-based vs window-60 s/stride-30 s (mean/std/delta → 24 fitur).
6. Limitasi tercatat: sampel head-segment (8–10 Feb); EDA deskriptif cell 9/13 sudah diperbaiki agar buang sentinel dulu.
