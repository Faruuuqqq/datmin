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

| Skenario | Silhouette (↑) | DBI (↓) |
|---|---|---|
| Unscaled | 0.9066 | 0.3092 |
| StandardScaler | 0.6592 | 0.6278 |
| RobustScaler | **0.9836** | **0.2103** |

→ RobustScaler menang telak pada Silhouette (0.9836) dan DBI (0.2103); unscaled memberikan ilusi Silhouette tinggi karena jarak didominasi mutlak oleh magnitudo SPP ribuan psi (*Euclidean collapse*). Klaim paper: JANGAN pakai unscaled.

## 3.3 Hasil window vs point k=4 (RIIL, `table3_temporal_compare.csv` — dilaporkan JUJUR)

- Point-based: Silhouette **0.9304**, DBI **0.3738**.
- Window-60 s: Silhouette **0.8570**, DBI **0.6231**.
- Interpretasi: Representasi titik memiliki Silhouette lebih tinggi karena massa titik idle yang sangat rapat di kedalaman awal sumur. Namun, representasi jendela 60 detik menangkap dinamika temporal kecepatan, getaran, dan tren, mengompresi data 60x lipat, serta mengeliminasi efek *chattering* (loncatan label liar tiap detik).

## 3.4 Hasil elbow k=2–8 Silhouette & DBI (RIIL, `table4_elbow_metrics.csv`)

| k | point-robust (Sil / DBI) | point-standard (Sil / DBI) | window60-robust (Sil / DBI) | window60-standard (Sil / DBI) |
|---|---|---|---|---|
| 2 | 0.9537 / 0.0979 | 0.7814 / 0.8290 | 0.9464 / 0.1507 | 0.7403 / 1.6054 |
| 3 | 0.9352 / 0.1266 | 0.7791 / 0.9402 | 0.9502 / 0.2185 | 0.7366 / 1.3969 |
| 4 | 0.9263 / 0.3358 | 0.7889 / 0.6625 | 0.9377 / 0.5186 | 0.7247 / 1.6903 |
| 5 | 0.9272 / 0.3848 | 0.8065 / 0.6258 | 0.9385 / 0.4936 | 0.7152 / 1.4842 |
| 6 | 0.9396 / 0.3923 | 0.7890 / 0.6084 | 0.9207 / 0.5809 | 0.7203 / 1.5671 |
| 7 | 0.9578 / 0.2685 | 0.7907 / 0.5528 | 0.9242 / 0.5517 | 0.7364 / 1.2927 |
| 8 | 0.9579 / 0.3048 | 0.7948 / 0.5965 | 0.9174 / 0.5254 | 0.7370 / 1.2349 |

- RobustScaler konsisten stabil $\geq 0.91$ di semua $k$; StandardScaler mengalami degradasi separasi pada DBI ($> 1.2$ pada window-standard).
- Kurva penurunan inersia (Elbow) melandai bertahap tanpa patahan tajam (*elbow datar*).
- **BEST_K = 4** dipilih **BERBASIS DOMAIN** (4 rezim operasional rig Coley 2019), bukan semata puncak kurva matematika — ditulis eksplisit di paper.

## 3.5 Centroid & pemetaan rezim fisik (RIIL PASCA-PERBAIKAN, `table5_centroids.csv`)

| Klaster | ROP (ft/hr) | WOB (klbs) | RPM | SPP (psi) | Torque (kft-lb) | Pump (GPM) | Share (%) | Interpretasi Fisik Rig (Coley 2019) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.04 | 0.05 | 0.10 | 25.70 | 0.02 | 20.35 | 90.95% | **Idle / Standby / Tripping** (mesin istirahat) |
| 1 | 13.89 | 0.40 | 58.90 | 849.25 | 2.90 | 583.62 | 6.35% | **Active Rotary Drilling** (bor aktif memotong batuan) |
| 2 | 1.87 | 0.86 | 21.22 | 318.83 | 1.11 | 235.23 | 1.30% | **Circulation & Low-Speed Transition** |
| 3 | 0.00 | 0.00 | 0.03 | 4853.26 | 0.00 | 0.00 | 1.40% | **High-Pressure Wellbore Test / Shut-In** |

- **Status:** **LOLOS UJI FISIKA 100%**.
- Masalah RPM negatif (-3.3) dan bor tanpa pompa pada run awal tuntas teratasi: terbukti bersumber dari kekeliruan *slicing* indeks kolom fitur pada cell 32, yang telah diperbaiki.
- Centroid dan share tersimpan di `table5_centroids.csv` dan `table6_cluster_share.csv`; visual PCA tersimpan di `fig6_pca_clusters.png`.

## 3.6 Limitasi jujur (masuk paper §III/§IV)

1. Silhouette 0.9+ terinflasi massa nol (median sensor = 0) pada kedalaman dangkal → dipandu oleh DBI + validasi fisika centroid.
2. Sampel 60k mencerminkan segmen awal sumur; untuk penelitian masa depan direkomendasikan sampling berimbang sepanjang interval kedalaman total 2,5 juta baris sumur.

## 3.7 Checklist Status

- [x] Audit desain 4 skenario × k=2–8, seed 42, subsampel 20k.
- [x] Perbaikan kode (winsorize ROP, Diff Press OFF, perbaikan indexing centroid cell 32).
- [x] Eksekusi pipeline penuh lokal (`src/run_clustering_eval.py`) & sinkronisasi notebook Kaggle.
- [x] Seluruh file output (`table0`–`table6` dan `fig1`–`fig6`) tersedia di `figures/`.
- [x] Seluruh penanda `[TODO-RERUN]` pada draft paper (`draft_paper_ieee.md` dan `draft-paper.tex`) digantikan dengan angka final dan pembahasan centroid fisik.
