# Tabel Final 9 + Backup 7 — PRISMA Restart v6 (terkunci 30 Sep 2026)

> Sumber: `sought_list.csv` + Pass-2 Batch 1 (28 → 8) + Batch-2 conditional No.161 (+1). DOI aktif semua (klik untuk full-text OA).

## A. FINAL 9 (masuk sintesis + gap analysis + daftar pustaka IEEE)

| # | No | Paper (Judul — Tahun — Jurnal — DOI) | Dataset (n, frekuensi, sensor) | Preprocessing | Clustering / Metode | Evaluasi | Peran di paper kita / Gap → kontribusi |
|---|---|---|---|---|---|---|---|
| 1 | 61 | Feature-based time series clustering for efficient labelling of geothermal data — 2026 — Geothermics — [10.1016/j.geothermics.2026.103656](https://doi.org/10.1016/j.geothermics.2026.103656) | Wairakei binary plant: temp-difference/flow time series | Seleksi 13/1588 fitur self-supervised | 9 algos: k-Means/MeanShift/GMM/DBSCAN | SIL 0.66, CHI 1647, DBI 0.40 | Inti metode: satu-satunya dengan k-Means + SIL/DBI di geothermal. Gap: single-plant, tanpa studi scaler×window → kita 8-sensor + scaler×window |
| 2 | 77 | Research on an intelligent drilling parameter optimization method using sliding window segmentation — 2026 — PLOS ONE — [10.1371/journal.pone.0339324](https://doi.org/10.1371/journal.pone.0339324) | 7.231 sampel 4 sumur: WOB/RPM/torque/flow/ROP depth-series | RF imputation, fusi 3S/K-means/LOF, Savitzky-Golay, sliding window | (optimasi RF supervised) | RMSE turun semua param, akurasi ROP | Domain drilling terlengkap (5 sensor sama). Gap: supervised optimization → kita regime discovery label-free |
| 3 | 14 | Unsupervised deep learning framework for early detection of wellbore trajectory deviation — 2026 — Front. Artif. Intell. — [10.3389/frai.2026.1942787](https://doi.org/10.3389/frai.2026.1942787) | 1 sumur, 12 log depth-series (GR/resistivity/sonic/density/porositas) | Interpolasi gap, normalisasi, window tetap len-50 | LSTM autoencoder GNN unsupervised | Recon err, P/R/F1/AUC | Gap: depth-series + tanpa banding scaler → kita sensor permukaan 1 Hz + studi scaler |
| 4 | 60 | STADe: unsupervised time-windows anomaly detection in oil & gas ICPS — 2025 — Int. J. Crit. Infrastruct. Prot. — [10.1016/j.ijcip.2025.100762](https://doi.org/10.1016/j.ijcip.2025.100762) | Wellhead ICPS packet inter-arrival traces | Sliding time-window + fitur periodisitas | STADe vs KNN/IF/LOF | F1 0.97/0.92/0.80, zero FP | Pembanding unsupervised vs baseline. Gap: data paket jaringan, bukan sensor fisik rig → kita sensor fisik |
| 5 | 79 | Anomaly Detection in Geothermal Steam Production Time Series Using SSA — 2025 — Eng. Proc. — [10.3390/engproc2025107024](https://doi.org/10.3390/engproc2025107024) | 9 sumur geothermal, steam 5-menit 14 tahun | Butterworth low-pass denoising, agregasi NMS | SSA anomaly | F1/ROC/PR + tuning threshold | Domain geothermal ke-2. Gap: univariat steam → kita multivariat 8-sensor |
| 6 | 131 | Oil and gas flow anomaly detection on offshore naturally flowing wells (3W Petrobras) — 2024 — Geoenergy Sci. Eng. — [10.1016/j.geoen.2024.213240](https://doi.org/10.1016/j.geoen.2024.213240) | 21 sumur offshore 2012–2018, flow multivariat | ffill missing, standardise, downsample 1 mnt, window-30, SMOTE | DNN anomaly (supervised) | F1 0.97 | Benchmark industri standar (3W). Gap: butuh label → kita unsupervised |
| 7 | 80 | ML workflow for classifying production profiles in unconventional reservoirs — 2026 — Energy Explor. Exploit. — [10.1177/01445987261433779](https://doi.org/10.1177/01445987261433779) | 189 sumur Permian + completion/geologi | Completion-norm, MRMR/VIF/RFE, MDS | RF (segmen via elbow + CH k=2) | Elbow, Calinski-Harabasz, acc 97.5% | Satu-satunya dengan elbow (wajib `tugas.txt`). Gap: fitur statis + supervised → kita temporal window |
| 8 | 12 | Tool condition monitoring by anomaly segmentation of time-frequency images using AE in small hole drilling — 2023 — J. Adv. Mech. Des. Syst. — [10.1299/jamdsm.2023jamdsm0034](https://doi.org/10.1299/jamdsm.2023jamdsm0034) | AE peck drilling SKD61 (±3.869 lubang) | CWT time-frequency images, deep features | DDM MVG vs CAE segmentation | Anomaly maps/scores | Domain drilling ke-3. Gap: single-sensor lab → kita multivariat lapangan |

| 9 | 161 | Clustering analysis for predictive maintenance of oil wells in Kazakhstan — 2026 — SOCAR Proceedings (IF 2.4) — [10.5510/OGP20260101153](https://doi.org/10.5510/OGP20260101153) | >3 jt entri 2 thn harian oil/liquid/water-cut, operator Kazakhstan | normalization, outlier handling, correlation analysis | K-means unsupervised | Elbow K=10 + stabilitas temporal 70% | Jangkar k-Means ke-2 + Elbow. Gap: agregat harian, tanpa scaler×window → kita sensor 1 Hz + scaler×window. Catatan: redirect doi.org inkonsisten, terverifikasi repositori Satbayev + Scopus 105034863083 |

## B. BACKUP 7 (eligible, standby — diambil jika reviewer/dosen minta tambah, tanpa screening ulang)

| # | No | Paper (Judul — Tahun — Jurnal — DOI) | Kenapa backup (bukan final) |
|---|---|---|---|
| 1 | 7 | External factors driving surface temperature changes above geothermal systems — 2024 — Front. Earth Sci. — [10.3389/feart.2024.1372621](https://doi.org/10.3389/feart.2024.1372621) | Geothermal tapi supervised + tanpa clustering → kalah dari No.79 |
| 2 | 54 | Toward basin-agnostic well log imputation and anomaly detection (TimeGPT foundation model) — 2026 — Energy Geosci. — [10.1016/j.engeos.2026.100536](https://doi.org/10.1016/j.engeos.2026.100536) | Foundation model, jauh dari K-Means → kalah dari No.14 |
| 3 | 57 | Anomaly detection with domain specific shapelet learning for sucker rod pump — 2025 — Sci. Rep. — [10.1038/s41598-025-11945-4](https://doi.org/10.1038/s41598-025-11945-4) | Bagus (shapelet one-class) tapi pompa tunggal → kalah dari No.60 |
| 4 | 67 | Data-Driven Time-Series Modeling for reservoir development indicators — 2025 — Energies — [10.3390/en18215753](https://doi.org/10.3390/en18215753) | Produksi harian agregat + tanpa clustering → kalah dari No.80 |
| 5 | 74 | Anomaly Detection in Borehole Strain Data with CNN and Frequency-Aware VAE — 2025 — JACIII — [10.20965/jaciii.2025.p1390](https://doi.org/10.20965/jaciii.2025.p1390) | Strain seismik + VAE, jauh dari rig → kalah dari No.14 |
| 6 | 143 | Reference station-based transfer learning for earthquake anomaly extraction from borehole strain — 2026 — Big Earth Data — [10.1080/20964471.2025.2581423](https://doi.org/10.1080/20964471.2025.2581423) | Gempa (bukan operasi rig) → kalah dari No.74 sekalipun |
| 7 | 156 | Vibration signal processing and fault diagnosis for high-pressure quintuplex pumps — 2026 — Sensors — [10.3390/s26154917](https://doi.org/10.3390/s26154917) | Pompa drilling relevan tapi supervised diagnosis → kalah dari No.12 |

## C. Referensi pendukung (di luar hitungan 9 — fondasi Bab II, bukan hasil PRISMA)

| # | Referensi | Fungsi di paper |
|---|---|---|
| S1 | Ben Aoun & Madarász (2022), Energies, [10.3390/en15124288](https://doi.org/10.3390/en15124288) — ROP Utah FORGE same-site | Background domain Bab I (tidak lolos query 4-blok karena supervised tanpa istilah clustering di abstrak — dicatat transparan) |
| S2 | Lloyd (1982) / MacQueen (1967) k-Means | Rumus algoritma Bab II |
| S3 | Rousseeuw (1987) Silhouette — [10.1016/0377-0427(87)90125-7](https://doi.org/10.1016/0377-0427(87)90125-7) | Rumus evaluasi Bab II |
| S4 | Davies & Bouldin (1979) DBI — [10.1109/TPAMI.1979.4766909](https://doi.org/10.1109/TPAMI.1979.4766909) | Rumus evaluasi Bab II |
| S5 | Keogh & Lin (2005) subsequence clustering — [10.1007/s10115-004-0172-7](https://doi.org/10.1007/s10115-004-0172-7) | Justifikasi sliding-window Bab II |
| S6 | Aghabozorgi et al. (2015) time-series clustering review — [10.1016/j.is.2015.04.007](https://doi.org/10.1016/j.is.2015.04.007) | Taksonomi metode Bab II |

## D. Cara pakai tabel ini

- Final 9 → sintesis Bab I (PRISMA + gap), metodologi Bab II (acuan scaler/window/evaluasi), daftar pustaka IEEE (9 entri DOI §A).
- Backup 7 → jangan dikutip kecuali diminta; status "eligible standby" di `screening_work.csv` (Reason = backup-sufficiency).
- Pendukung S1–S6 → dikutip di Bab I/II sebagai fondasi, label eksplisit "supporting, outside PRISMA count".
