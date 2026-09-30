# TAHAP 3 FINAL — Time-Series Clustering Design & Evaluation (terkunci 30 Sep 2026)

> Desain terkunci di notebook fathan (cell 24–34). Angka di bawah RIIL dari run Kaggle awal
> (60k sampel, seed 42). Kode sudah diperbaiki (winsorize + Diff Press OFF) → WAJIB re-run sebelum submit.

## 3.1 Desain eksperimen (FINAL)

- 4 skenario: {point, window-60 s/stride-30 s} × {StandardScaler, RobustScaler}.
- Window: mean/std/delta per sensor → 24 fitur (Keogh & Lin 2005 [S5]).
- K-Means k = 2–8, n_init = 10, seed 42, subsampel 20k untuk metrik.
- Seleksi: Elbow inertia + Silhouette (maks) + DBI (min); tanpa label.

## 3.2 Hasil scaler demo k=4 (RIIL, cell 16)

| Skenario | Silhouette (↑) | DBI (↓) |
|---|---|---|
| Unscaled | 0.8973 | 0.2765 |
| StandardScaler | 0.6272 | 0.6253 |
| RobustScaler | **0.9658** | **0.2456** |

→ Robust menang telak; unscaled menipu (tinggi karena massa nol). Klaim paper: JANGAN pakai unscaled.

## 3.3 Hasil window vs point k=4 (RIIL, cell 21 — dilaporkan JUJUR)

- Point-based Silhouette: **0.9215** vs Window-60 s: **0.8486** → point menang di run awal.
- Interpretasi: window diuji pada 999 window dari head-segment idle; belum bukti window kalah — butuh re-run full-range + banding DBI (`table3_temporal_compare.csv` + `table4_elbow_metrics.csv` di output Kaggle).

## 3.4 Hasil elbow k=2–8 Silhouette (RIIL, cell 28)

| k | point-robust | point-standard | window60-robust | window60-standard |
|---|---|---|---|---|
| 2 | 0.9523 | 0.7177 | 0.9404 | 0.7100 |
| 3 | 0.9314 | 0.6191 | 0.9451 | 0.7066 |
| 4 | 0.9145 | 0.6506 | 0.9456 | 0.6965 |
| 5 | 0.9176 | 0.6916 | 0.9333 | 0.6978 |
| 6 | 0.9291 | 0.6962 | 0.9364 | 0.6936 |
| 7 | 0.9306 | 0.6952 | 0.9239 | 0.5488 |
| 8 | 0.9301 | 0.7146 | 0.9182 | 0.5461 |

- Robust stabil ≥0.91 di semua k; standard jatuh di k≥7 (window60-standard 0.54).
- BEST_K = 4 dipilih BERBASIS DOMAIN (4 rezim Coley [195]), bukan puncak elbow (datar) — tulis eksplisit di paper.
- Tabel DBI lengkap: unduh `table4_elbow_metrics.csv` dari output Kaggle.

## 3.5 Centroid & pemetaan rezim (RIIL sebagian, cell 32 — FLAG VERIFIKASI)

- Cluster 0: ROP 109 / WOB 51 / RPM −3.3 / SPP 0.39 → **TIDAK FISIK** (bor tanpa pompa; RPM negatif).
- Cluster 1–3: mendekati nol (idle split).
- Status: JANGAN masuk paper sebelum re-run pasca-winsorize; kemungkinan artefak sampel head + ROP tak ter-clip.share per klaster di `table6_cluster_share.csv`; visual PCA `fig6_pca_clusters.png`.

## 3.6 Limitasi jujur (masuk paper §III/§IV)

1. Silhouette 0.9+ terinflasi massa nol (median 5 sensor = 0) → andalkan DBI + fisika centroid.
2. Sampel head-segment (Feb, dangkal) belum mewakili 2.5M baris sebulan penuh.
3. Centroid run awal belum layak tafsir fisik → re-run wajib setelah perbaikan kode.

## 3.7 To-run sebelum submit (checklist)

- [ ] Re-run notebook fathan penuh di Kaggle pasca-perbaikan (winsorize + Diff Press OFF + sentinel-fix).
- [ ] Unduh `/kaggle/output/` → `table0–table6`, `fig1–fig6` ke `figures/`.
- [ ] Isi angka DBI + centroid baru ke draft paper §III-B; putuskan BEST_K final dari Fig 5.
- [ ] Opsional: run sensitivitas `USE_DIFF_PRESS = True` (8 sensor) sebagai pembanding satu tabel.
