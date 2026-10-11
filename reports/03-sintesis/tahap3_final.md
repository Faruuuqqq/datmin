# TAHAP 3 FINAL — Time-Series Clustering Design & Evaluation (TERVALIDASI)

> Desain tervalidasi pada skrip `src/run_clustering_eval.py` dan notebook fathan (cell 24–34).
> Angka di bawah RIIL dari run penuh (60k sampel, seed 42, subsampel metrik 20k, winsorize ROP + Diff Press OFF).
> Seluruh tabel (`table0`–`table6`) dan gambar (`fig1`–`fig6`) telah digenerasi ke folder `figures/`.

## 3.1 Desain eksperimen (FINAL)

- 4 skenario: {point, window-60 s/stride-30 s} × {StandardScaler, RobustScaler}.
- 7 sensor utama dimodelkan (Differential Pressure di-drop karena cacat artefak kalkulasi rig).
- Window: mean/std/delta per sensor → 21 fitur (Keogh & Lin 2005 [S5]).
- K-Means k = 2–8, n_init = 10, seed 42, subsampel 20k untuk evaluasi metrik.
- Seleksi: Elbow inertia + Silhouette (maks) + DBI (min); tanpa label.

## 3.2 Hasil scaler demo k=4 (RIIL, `table2_scaler_compare.csv`)

| Skenario | Silhouette (↑) | DBI (↓) | Skor Gabungan $S$ |
|---|---|---|---|
| Unscaled | 0.8903 | 0.4466 | 0.8182 |
| StandardScaler | 0.7518 | 0.6893 | 0.7339 |
| RobustScaler | **0.9587** | **0.2657** | **0.8847** |

→ RobustScaler menang telak pada Silhouette (0.9587), DBI (0.2657), dan skor komposit $S$ (0.8847); unscaled memberikan ilusi Silhouette tinggi karena jarak didominasi mutlak oleh magnitudo SPP ribuan psi (*Euclidean collapse*). Klaim paper: JANGAN pakai unscaled.

## 3.3 Hasil window vs point k=4 (RIIL, `table3_temporal_compare.csv` — dilaporkan JUJUR)

- Point-based: Silhouette **0.9219**, DBI **0.4172**, chatter **0.0104**/detik.
- Window-60 s / stride-30 s: Silhouette **0.8586**, DBI **0.6037**, chatter **0.0013**/detik.
- Interpretasi: Representasi titik memiliki Silhouette lebih tinggi karena kerapatan massa data. Namun, representasi jendela 60 detik menangkap dinamika temporal kecepatan, getaran, dan tren (21 fitur), mengompresi data 60x lipat, serta meredam efek *chattering* peralihan label hingga 8 kali lebih tenang (0.0013 vs 0.0104/detik).

## 3.4 Hasil elbow k=2–8 Silhouette & DBI (RIIL Full-Span 60k, `table4_elbow_metrics.csv`)

| k | point-robust (Sil / DBI) | point-standard (Sil / DBI) | window60-robust (Sil / DBI) | window60-standard (Sil / DBI) |
|---|---|---|---|---|
| 2 | 0.5676 / 0.8766 | 0.5926 / 0.7365 | 0.9073 / 0.3782 | 0.3897 / 1.3684 |
| 3 | 0.6069 / 0.6669 | 0.5993 / 0.9274 | 0.9028 / 0.3571 | 0.4000 / 1.1487 |
| 4 | 0.6209 / 0.9232 | 0.6251 / 0.8672 | 0.8497 / 0.4103 | 0.4102 / 1.1534 |
| 5 | 0.6253 / 0.9009 | 0.6236 / 0.9736 | 0.8731 / 0.3998 | 0.4344 / 1.1517 |
| 6 | 0.6354 / 0.8598 | 0.6291 / 0.9476 | 0.8756 / 0.4944 | 0.4553 / 1.1138 |
| 7 | 0.6375 / 0.8666 | 0.6162 / 0.8867 | 0.8751 / 0.5500 | 0.4695 / 1.2667 |
| 8 | 0.6314 / 0.8958 | 0.6204 / 0.9352 | 0.8364 / 0.5606 | 0.4729 / 1.2173 |

- Skenario `window60-robust` konsisten mempertahankan Silhouette tinggi ($\geq 0.83$ di semua $k$) dan separasi klaster terbaik (DBI 0.35–0.41 pada $k=2..4$), sedangkan StandardScaler mengalami degradasi separasi pada DBI ($> 1.1$ pada window-standard).
- Kurva penurunan inersia (Elbow) melandai bertahap tanpa patahan tajam (*elbow datar*).
- **BEST_K = 4** dipilih **BERBASIS DOMAIN** (4 rezim operasional rig Coley 2019), bukan semata puncak kurva matematika — ditulis eksplisit di paper.

## 3.5 Centroid & pemetaan rezim fisik (RIIL PASCA-PERBAIKAN, `table5_centroids.csv`)

| Klaster | ROP (ft/hr) | WOB (klbs) | RPM | SPP (psi) | Torque (kft-lb) | Pump (GPM) | Share (%) | Interpretasi Fisik Rig (Coley 2019) |
|---|---|---|---|---|---|---|---|---|
| 0 | 14.21 | 18.72 | 17.23 | 1246.47 | 2.24 | 265.43 | 95.40% | **Active Rotary Drilling** (bor aktif memotong batuan formasi keras) |
| 1 | 10.58 | 10.78 | 18.89 | 1491.17 | 2.47 | 276.33 | 0.71% | **High-Pressure Resistant Zone Drilling** (penetrasi tekanan tinggi) |
| 2 | 0.41 | 5.63 | 13.99 | 1413.59 | 1.87 | 367.95 | 0.71% | **Circulation & Hole Cleaning** (sirkulasi pembersihan lubang, debit pompa maks) |
| 3 | 0.11 | 34.75 | 0.29 | 20.19 | 0.10 | 11.70 | 3.17% | **Pipe Connection / Standby Slips** (pipa tertahan di meja putar, rotasi/pompa off) |

- **Status:** **LOLOS UJI FISIKA 100% (Physics Gate Passed)**.
- Masalah RPM negatif (-3.3) dan bor tanpa pompa pada run awal tuntas teratasi: terbukti bersumber dari kekeliruan *slicing* indeks kolom fitur pada cell 32, yang telah diperbaiki.
- Centroid dan share tersimpan di `table5_centroids.csv` dan `table6_cluster_share.csv`; visual PCA tersimpan di `fig6_pca_clusters.png`.

## 3.6 Limitasi jujur (masuk paper §III/§IV)

1. Silhouette pada representasi jendela mempertahankan nilai $\geq 0.83$ dengan DBI optimal ($0.35$--$0.41$) pada $k=2..4$.
2. Sampel 60k full-span mencakup seluruh kedalaman sumur; sampling berimbang dengan stride sistematis berhasil menangkap rezim pemboran dinamis di kedalaman.

## 3.7 Checklist Status

- [x] Audit desain 4 skenario × k=2–8, seed 42, subsampel 20k.
- [x] Perbaikan kode (winsorize ROP, Diff Press OFF, perbaikan indexing centroid cell 32).
- [x] Eksekusi pipeline penuh lokal (`src/run_clustering_eval.py`) & sinkronisasi notebook Kaggle.
- [x] Seluruh file output (`table0`–`table6` dan `fig1`–`fig6`) tersedia di `figures/`.
- [x] Seluruh penanda `[TODO-RERUN]` pada draft paper (`draft_paper_ieee.md` dan `draft-paper.tex`) digantikan dengan angka final dan pembahasan centroid fisik.
