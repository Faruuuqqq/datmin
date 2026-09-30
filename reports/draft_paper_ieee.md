# DRAFT PAPER IEEE — Impact of Feature Scaling and Temporal Window Aggregation on Multivariate Geothermal Drilling Sensor Clustering Using K-Means

> Status: DRAF 30 Sep 2026 untuk template IEEE dua kolom (5–8 hlm). Angka bertanda [TODO-RUN] diisi setelah `notebooks/04_clustering.ipynb` dieksekusi. Semua angka lain RIIL (Colab 200k + PRISMA terkunci). Konversi ke .doc via template https://www.ieee.org/conferences/publishing/templates.

---

## Title

**Impact of Feature Scaling and Temporal Window Aggregation on Multivariate Geothermal Drilling Sensor Clustering Using K-Means**

## Abstract

*Unsupervised monitoring of geothermal drilling rigs requires clustering high-frequency multivariate sensor streams without labels. The Utah FORGE Well 56-32 dataset (2,506,360 records at 1 Hz, 8 sensors) exhibits three technical diseases: scale disparity (range ratio 258.9:1), temporal dependency (autocorrelation ≈ 1.0 at lag-1), and instrument noise (sentinel −999.25, 8.65% IQR outliers in ROP). A PRISMA-guided review (740 → 175 → 127 → 70 → 9 included studies) shows prior work either needs labels, uses single sensors, or ignores scaler–window interaction. We compare StandardScaler vs RobustScaler × point-based vs 60-s sliding-window (mean/std/delta) representations under K-Means (k = 2–8), evaluated by Silhouette coefficient and Davies–Bouldin index with elbow selection. [TODO-RUN: 1–2 kalimat hasil — skenario terbaik + Sil/DBI + pemetaan 4 rezim rig.]*

**Keywords:** geothermal drilling; multivariate time series; K-means clustering; feature scaling; sliding window; Silhouette; Davies-Bouldin; Utah FORGE.

---

## I. Introduction

### A. Operational Problem

Geothermal drilling in hard crystalline granite (Utah FORGE) costs tens of thousands of dollars per day. Manual rig-state logging lags, is subjective, and is often discontinuous. Three data diseases must be solved before clustering (`dataset/tugas.txt`):

1. **Scale disparity** — Standpipe Pressure spans thousands of psi while Rotary Torque spans tens of kft-lb (measured range ratio **258.9:1**, ROP skewness 37.63). Euclidean distance collapses without scaling.
2. **Temporal dependency** (bonus) — 1-Hz autocorrelation ≈ 1.0 at lag-1 (SPP 1.000, RPM 0.999, ROP 0.988); point-based clustering ignores it.
3. **Noise & outliers** (bonus) — Pason sentinel −999.25 (1.17% SPP/Diff Press), ROP IQR outliers 8.65% (max 10,771 ft/hr spike), torque stick-slip 2.29%.

### B. Literature Selection (PRISMA 2020)

Query terkunci (Scopus, 30 Sep 2026), 4 blok — domain + data + metode + preprocessing:

```text
TITLE-ABS-KEY((geothermal OR drill* OR wellbore* OR borehole* OR rig OR "rate of penetration"
OR "weight on bit" OR "rig state*" OR petro* OR "oil and gas") AND ("time series" OR "time-series"
OR temporal OR multivariate OR sensor* OR "sensor data" OR "sensor signal*" OR "high-frequency"
OR unlabeled) AND (clust* OR "k-means" OR "k means" OR "fuzzy c-means" OR DBSCAN OR GMM
OR "gaussian mixture" OR "k-shape*" OR "pattern recognition" OR "anomaly detection")
AND (normali* OR scal* OR preprocess* OR "feature extraction" OR "feature engineering"
OR "sliding window*" OR outlier* OR denoising))
```

Flow: **740 raw → 175 filtered** (OA + journal + English + article) **→ 48 older-than-2021 → 127 title/abstract → 57 excluded (E1 21/E2 20/E3 16) → 70 sought (Batch-1 28 + Batch-2 42) → Batch-1: 4 not retrieved + 16 excluded + 8 included → Batch-2 conditional +1 → 9 included** (syarat ≥ 8 TERLAMPUI). Screening manual tanpa automation (semua keputusan manusia, jejak di `screening_work.csv`).

### C. Gap Analysis (ringkas — penuh di `tabel_final_backup.md`)

| Studi | Metode + Preprocessing | Gap → kontribusi kita |
|---|---|---|
| [1] Geothermal clustering (9 algos, SIL 0.66/DBI 0.40) | k-Means/GMM/DBSCAN + seleksi fitur | Single-plant, tanpa studi scaler×window → kita 8-sensor + scaler×window |
| [2] Drilling optimization + sliding window | RF + imputation + Savitzky-Golay + window | Supervised → kita label-free regime discovery |
| [3] Wellbore unsupervised autoencoder | Interpolasi + normalisasi + window-50 | Depth-series, tanpa banding scaler → kita permukaan 1 Hz + studi scaler |
| [4] STADe sliding-window vs KNN/IF/LOF | Window + fitur periodisitas | Data paket jaringan → kita sensor fisik rig |
| [5] Geothermal steam SSA | Butterworth denoise | Univariat → kita multivariat |
| [6] 3W Petrobras DNN (F1 0.97) | ffill + standardise + window-30 | Butuh label → kita unsupervised |
| [7] Permian profiles (elbow + CH) | Completion-norm + MRMR/RFE | Fitur statis → kita temporal |
| [8] Drilling AE segmentation | CWT time-frequency | Single-sensor lab → kita lapangan multivariat |
| [9] Kazakhstan oil-well K-Means (Elbow K=10) | Normalization + outlier + korelasi | Agregat harian → kita 1 Hz + scaler×window |

### D. Contributions

1. Komparasi **StandardScaler vs RobustScaler** pada 8 sensor berskala ekstrem.
2. Agregasi **sliding-window 60 s/30 s (mean/std/delta)** vs point-based untuk dependensi temporal.
3. **Regime discovery** 4 rezim rig (drilling, circulation, tripping/connection, idle) tanpa label, divalidasi Silhouette + DBI + elbow.

---

## II. Methodology

### A. Dataset

Utah FORGE Well 56-32, Pason 1 Hz, 2.506.360 baris × 22 kolom → 8 sensor utama: ROP (ft/hr), WOB (klbs), RPM, SPP (psi), Torque (kft-lb), Hookload (klbs), Diff Press (psi), Pump Out (GPM). Median ROP/WOB/RPM/SPP/Torque = 0 (dominan idle). Diff Press bermasalah (mean −692, skew −1.21) → kandidat drop (7-sensor sensitivity run). Korelasi kunci: SPP–Pump 0.925 (hidrolik), RPM–Torque 0.747 (rotasi), ROP–WOB 0.007 (nonlinier granit — butuh rezim, bukan regresi).

### B. Preprocessing Pipeline

1. Sentinel → NaN (`-999.25`), drop baris invalid; pisahkan Diff Press.
2. Winsorize ROP pada batas atas IQR (47.4) — spike kalkulasi dipertahankan bentuknya, diredam dampaknya.
3. Dua jalur: **StandardScaler** (z-score, sensitif pencilan) vs **RobustScaler** (median–IQR).
4. Dua representasi: **point-based** vs **window-60 s stride-30 s** (mean/std/delta per sensor → 24 fitur).

### C. K-Means Formulation

Minimasi $J = \sum_{j=1}^{k}\sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2$ (Euclidean; Lloyd [S2]). Grid k = 2–8, n_init = 10, seed 42, subsampel 20k untuk metrik. Empat skenario: point-standard, point-robust, window60-standard, window60-robust (`notebooks/04_clustering.ipynb`).

### D. Cluster Evaluation

Elbow inertia untuk k; **Silhouette** $s(i)$ [S3] (maksimum) dan **Davies–Bouldin index** [S4] (minimum) sebagai validasi internal. Literatur [1] melaporkan SIL 0.66/DBI 0.40 sebagai pembanding.

---

## III. Results

### A. Data Understanding (RIIL — Colab 200k, seed 42)

- Deskriptif: ROP mean 24.91/std 100.46/max 10,771; SPP mean 1,209/max 5,239; Torque mean 2.15/max 41.6.
- Sentinel & outlier: §I-A. Heatmap korelasi + boxplot (lampiran gambar).
- Keputusan: Diff Press dipisahkan; ROP di-winsorize; RobustScaler hipotesis unggul (menunggu §III-B).

### B. Clustering Experiments ([TODO-RUN] — rancangan terkunci di `04_clustering.ipynb`)

- Tabel: inertia/Silhouette/DBI per (skenario × k) + kurva elbow.
- Klaim yang diuji: window60-robust k=4 optimal; centroid → 4 rezim fisik; PCA-2D visual.
- [TODO-RUN: isi angka + 3 gambar: elbow/silhouette, PCA clusters, tabel centroid.]

---

## IV. Conclusion and Future Work

[TODO: 1 paragraf kesimpulan setelah §III-B terisi + saran: online/streaming clustering, GMM/DBSCAN comparison, Diff Press reintegration.]

---

## References (IEEE)

[1] Feature-based time series clustering for efficient labelling of geothermal data, *Geothermics*, 2026. DOI: 10.1016/j.geothermics.2026.103656.\
[2] Research on an intelligent drilling parameter optimization method using sliding window segmentation, *PLOS ONE*, 2026. DOI: 10.1371/journal.pone.0339324.\
[3] Unsupervised deep learning framework for early detection of wellbore trajectory deviation, *Front. Artif. Intell.*, 2026. DOI: 10.3389/frai.2026.1942787.\
[4] STADe: unsupervised time-windows anomaly detection in oil & gas ICPS, *Int. J. Crit. Infrastruct. Prot.*, 2025. DOI: 10.1016/j.ijcip.2025.100762.\
[5] Anomaly Detection in Geothermal Steam Production Time Series Using SSA, *Eng. Proc.*, 2025. DOI: 10.3390/engproc2025107024.\
[6] Oil and gas flow anomaly detection on offshore naturally flowing wells, *Geoenergy Sci. Eng.*, 2024. DOI: 10.1016/j.geoen.2024.213240.\
[7] ML workflow for classifying production profiles in unconventional reservoirs, *Energy Explor. Exploit.*, 2026. DOI: 10.1177/01445987261433779.\
[8] Tool condition monitoring by anomaly segmentation using AE in small hole drilling, *J. Adv. Mech. Des. Syst.*, 2023. DOI: 10.1299/jamdsm.2023jamdsm0034.\
[9] Clustering analysis for predictive maintenance of oil wells in Kazakhstan, *SOCAR Proc.*, 2026. DOI: 10.5510/OGP20260101153.\
[S1] M. A. Ben Aoun and T. Madarász, ROP prediction Utah FORGE, *Energies*, 2022. DOI: 10.3390/en15124288. (Background, outside PRISMA count.)\
[S2] S. Lloyd, Least squares quantization in PCM, *IEEE Trans. Inf. Theory*, 1982.\
[S3] P. J. Rousseeuw, Silhouettes, *J. Comput. Appl. Math.*, 1987. DOI: 10.1016/0377-0427(87)90125-7.\
[S4] D. L. Davies and D. W. Bouldin, A cluster separation measure, *IEEE TPAMI*, 1979. DOI: 10.1109/TPAMI.1979.4766909.\
[S5] E. Keogh and J. Lin, Clustering of time-series subsequences is meaningless, *Knowl. Inf. Syst.*, 2005. DOI: 10.1007/s10115-004-0172-7.\
[S6] S. Aghabozorgi et al., Time-series clustering — a decade review, *Inf. Syst.*, 2015. DOI: 10.1016/j.is.2015.04.007.

---

## Lampiran wajib (cek `tugas.txt:51-54`)

- [ ] Konversi file ini ke .doc template IEEE dua kolom.
- [ ] Tautan repo kode + dataset Kaggle (`faruqmahdison/utah-datmin`) + diagram PRISMA (`prisma.restart.v6.md:§4`).
- [ ] `deklarasi_genai.md` + 7 CSV/MD jejak (`screening-175paper.csv`, `screening_work.csv`, `sought_list.csv`, `screening_127.csv`, `eligibility_16.csv`, `tabel_final_backup.md`).
- [ ] [TODO-RUN] §III-B + Abstrak + §IV setelah eksekusi notebook.
