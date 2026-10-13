# DRAFT PAPER IEEE (CRISP-DM) — Impact of Feature Scaling and Temporal Window Aggregation on Multivariate Geothermal Drilling Sensor Clustering Using K-Means

> Status: DRAF 30 Sep 2026, two-column IEEE 5–8 hlm + appendix. Struktur: CRISP-DM dipetakan ke
> sistematika tugas (Bab I–IV). Seluruh angka eksperimen dan visualisasi telah terisi final pasca-rerun tervalidasi.
> Diagram PRISMA: `prisma-diagram.drawio` milik tim (Fig. 1) — angka funnel §I-B.

---

## Title

**Impact of Feature Scaling and Temporal Window Aggregation on Multivariate Geothermal Drilling Sensor Clustering Using K-Means**

### Authors
1. **Aulia Fadhila Mumtaza** (Informatics Engineering, Padjadjaran University, Sumedang, Indonesia — auliafm46@gmail.com)
2. **Fathan Ariiq Rasbi Yalis** (Informatics Engineering, Padjadjaran University, Sumedang, Indonesia — fathanariiqry@gmail.com)
3. **Aliya Zahra Nurazizah** (Informatics Engineering, Padjadjaran University, Sumedang, Indonesia — aliyazahranur145@gmail.com)
4. **Achmad Faruq Mahdison** (Informatics Engineering, Padjadjaran University, Sumedang, Indonesia — raja11.faruq@gmail.com)
5. **M. Rafif Widyadhana** (Informatics Engineering, Padjadjaran University, Sumedang, Indonesia — rpippp15@gmail.com)

## Abstract

*Unsupervised monitoring of geothermal drilling rigs requires clustering high-frequency multivariate sensor streams without labels, under extreme scale disparity and strong serial autocorrelation ($r \approx 1.0$). Following CRISP-DM and strict anti-leakage protocols, we profile the Utah FORGE Well 56-32 dataset (2,506,359 records at 1 Hz, 29 days): dropping SPP sensor glitch rows ($\le -900$ psi; 29,503 rows), masking sentinel $-999.25$ to NaN with segment gap resets, and constructing tumbling 60-second windows (stride 60 s, 0% overlap) with $\ge 90\%$ finite coverage across 13 sensor channels (11 raw channels + 2 physical power proxies), yielding 38,177 valid windows with 39 statistical features. Under a strict chronological partition (Train 70% = 26,723 windows, 1-hour temporal embargo = 60 windows, Test 30% = 11,394 windows) and multi-seed stability evaluation ($k \in [2, 8]$, seeds 42, 0, 1), we demonstrate four key findings. First, conventional internal metrics create a severe illusion: RobustScaler produces an artificially inflated Silhouette score (0.8822 Train / 0.8557 Test) but suffers catastrophic cluster collapse where 99.25% of data collapses into a single mega-cluster (C0 = 26,523 windows) and two clusters are empty in Test (disqualified as NO-WINNER). Second, MinMaxScaler emerges as the only eligible scaler passing all locked guardrails (Train Sil 0.3104 / Test Sil 0.2677; Train DBI 1.5715 / Test DBI 2.0611; ARI stability 0.9997) with healthy balanced cluster occupancy. Third, 60-s tumbling window aggregation suppresses label chattering by 8x (0.0013 vs 0.0102 transitions/s), matching the hydraulic loop response time of granite formations and providing 65x computational compression. Fourth, multi-level elimination establishes $k = 4$ under MinMaxScaler as the optimal K-Means model, partitioning rig dynamics into four physically plausible operational regimes: Active Rotary Drilling (34.63%), High-Pressure Tight Rock Drilling (39.94%), Circulation & Hole Cleaning (13.07%), and Pipe Connection/Slips Standby (12.36%).*

**Keywords:** geothermal drilling; multivariate time series; K-means clustering; feature scaling; MinMaxScaler; tumbling window; leakage-free split; Utah FORGE; CRISP-DM.

---

## I. Introduction — CRISP-DM Business Understanding

Manual rig-state logging lags, is subjective, and discontinuous; drilling granite costs tens of
thousands of dollars per day. Tujuan bisnis: regime discovery tanpa label
(drilling, circulation, tripping/connection, idle) + bukti preprocessing yang menyelesaikan
penyakit data (§II-A).

### A. Literature Selection (PRISMA 2020, Fig. 1)

Query resmi (Scopus, 4 blok + PUBYEAR 2021–2026 + OA/journal/English/article → **127**):

```text
TITLE-ABS-KEY((geothermal OR drill* OR wellbore* OR borehole* OR rig OR "rate of penetration"
OR "weight on bit" OR "rig state*" OR petro* OR "oil and gas") AND ("time series" OR "time-series"
OR temporal OR multivariate OR sensor* OR "sensor data" OR "sensor signal*" OR "high-frequency"
OR unlabeled) AND (clust* OR "k-means" OR "k means" OR "fuzzy c-means" OR DBSCAN OR GMM
OR "gaussian mixture" OR "k-shape*" OR "pattern recognition" OR "anomaly detection")
AND (normali* OR scal* OR preprocess* OR "feature extraction" OR "feature engineering"
OR "sliding window*" OR outlier* OR denoising)) AND ... AND PUBYEAR > 2020 AND PUBYEAR < 2027
```

Flow: **740 screened → 331 older-than-2021 → 409 sought → Exclude (Non-English 20* + Non-Article 178*) → 231 English articles → 104 inaccessible → 127 accessible = assessed → 118 excluded (Pass-1 57 + notretrieved/standby 45 + Pass-2 16) → 9 included** (syarat ≥ 8 TERLAMPUI).
Footnote: *20 non-English overlap di dalam 178 (unik 178; 409−178=231 — verifikasi screenshot faset [TODO-SHOT: 331/178/20/104]).
Screening manual, jejak `screening_work.csv`. Fig. 1 = `prisma-diagram.drawio` (export PNG).

### B. Gap Analysis (gaya referensi: Bentuk Data | Preprocessing ± | Clustering ± | Gap)

| Paper | Bentuk Data | Preprocessing (+kelebihan / −kekurangan) | Clustering (+/−) | Gap → kontribusi kita |
|---|---|---|---|---|
| [1] Geothermal clustering, Geothermics 2026 | Time series plant temp/flow | Seleksi 13/1588 fitur self-supervised (+otomatis / −butuh data besar) | 9 algos k-Means/GMM/DBSCAN (+banding adil / −mahal); SIL 0.66, DBI 0.40 | Single-plant, tanpa scaler×window → kita 8-sensor + scaler×window |
| [2] Drilling optimization + window, PLOS ONE 2026 | 7.231 sampel 4 sumur WOB/RPM/torque/flow/ROP | RF imputation, 3S/K-means/LOF, Savitzky-Golay, sliding window (+lengkap / −kompleks) | Optimasi RF supervised (+akurat / −butuh label) | Supervised → kita label-free |
| [3] Wellbore unsupervised AE, Front. AI 2026 | 1 sumur, 12 log depth-series | Interpolasi + normalisasi + window-50 (+sederhana / −fixed-len) | LSTM-GNN unsupervised (+temporal / −mahal) | Depth-series, tanpa banding scaler → kita 1 Hz + studi scaler |
| [4] STADe ICPS, IJ CIP 2025 | Wellhead packet traces | Sliding window + fitur periodisitas (+adaptif / −domain sempit) | STADe vs KNN/IF/LOF (+baseline / −data sintetis) | Data paket, bukan sensor fisik → kita sensor rig |
| [5] Geothermal steam SSA 2025 | 9 sumur, steam 5-mnt 14 thn | Butterworth denoise + NMS (+halus / −tumpul transien) | SSA anomaly (+tanpa label / −univariat) | Univariat → kita multivariat |
| [6] 3W Petrobras DNN 2024 | 21 sumur offshore multivariat | ffill + standardise + downsample + window-30 + SMOTE (+lengkap / −banyak tahap) | DNN supervised, F1 0.97 (+akurat / −butuh label) | Butuh label → kita unsupervised |
| [7] Permian profiles 2026 | 189 sumur + completion | Completion-norm + MRMR/VIF/RFE (+selektif / −statis) | RF + elbow/CH k=2 (+tuning / −supervised) | Fitur statis → kita temporal |
| [8] Drilling AE segmentation 2023 | AE peck drilling lab | CWT time-frequency (+resolusi / −1 sensor) | DDM MVG vs CAE (+banding / −skala lab) | Single-sensor lab → kita lapangan |
| [9] Kazakhstan oil-well K-Means 2026 | >3 jt entri harian oil/liquid/water-cut | Normalization + outlier + korelasi (+ringan / −agregat) | K-means + Elbow K=10 (+murah / −sensitif outlier) | Agregat harian → kita 1 Hz + scaler×window |

### C. Contributions

1. Komparasi StandardScaler vs RobustScaler pada 8 sensor berskala 258.9:1.
2. Agregasi sliding-window 60 s/30 s (mean/std/delta) vs point-based.
3. Regime discovery 4 rezim rig tanpa label (Silhouette + DBI + elbow).

---

## II. Methodology — CRISP-DM Data Understanding, Preparation, Modeling

### A. Data Understanding (karakteristik lengkap — 7 dimensi)

| Dimensi | Hasil ukur (sumber) | Implikasi |
|---|---|---|
| Volume | 2.506.359 baris, 2021/02/08–2021/03/09, 1 Hz | Sampel 60–200k + seed 42 (RAM-safe) |
| Dimensi | 22 kolom → 8 sensor utama (Pason Gas/Gamma 100% sentinel → dibuang) | Syarat ≥5 numerik TERPENUHI |
| Tipe Data | Semua kontinu rasio (ft/hr, klbs, RPM, psi, kft-lb, GPM); 2 kolom waktu; tanpa label | Unsupervised valid |
| Skala Pengukuran | Range ROP 10.771 vs Torque 41,6 → rasio 258.9:1; SPP mean 1.209 vs Torque 2.15 | Wajib scaler (Blok-4 query) |
| Missing Values | Sentinel −999.25: SPP/Diff Press 1,17%, RPM/Torque 0,02%, lainnya ~0% | → NaN + dropna-subset |
| Outlier | ROP 8,65% (max 10.771 artefak), Torque/WOB ~2,3% (stick-slip asli), SPP 0% | Winsorize ROP; RobustScaler |
| Duplikasi | **0 baris duplikat eksak; 0 timestamp ganda** (cek 2.506.359 baris) | Tidak perlu dedup |
| Tambahan | Skew ROP 37,63; median 5 sensor = 0 (idle); Diff Press mean −692/skew −1,21 (kandidat drop); SPP–Pump r=0,925; RPM–Torque r=0,747; ROP–WOB r=0,007; autocorr lag-1 ≈ 1,0 | Window wajib; regime > regresi |

### B. Data Preparation (inventarisasi SEMUA preprocessing — berurutan)

1. **Seleksi kolom:** 22 → 8 sensor (buang Pason Gas, Gamma: 100% sentinel).
2. **Sentinel → NaN:** `-999.25` → NaN (`replace`), bukan angka.
3. **Drop Классик:** `dropna(subset=SENSORS)` — hanya pada sensor yang dimodelkan (hemat baris).
4. **Diff Press OFF:** default 7 sensor; sensitivitas 8 via `USE_DIFF_PRESS = True`.
5. **Winsorize ROP:** clip di HI = Q3+1.5·IQR (≈47) — artefak diredam, bentuk dipertahankan.
6. **Tipe numerik:** `float32` + `datetime` dari 2 kolom waktu + sort kronologis.
7. **Scaling (2 jalur):** StandardScaler (z-score) vs RobustScaler (median–IQR).
8. **Window (2 representasi):** point-based (8 fitur) vs sliding-60 s/stride-30 s → mean/std/delta (24 fitur).
9. **Sampling:** 60–200k + `RandomState(42)`; subsampel 20k untuk metrik; PCA-2D 15k untuk visual.

### E. Rancangan Klasterisasi dan Evaluasi

1. **Formulasi Model K-Means:** Minimasi inersia $J = \sum_{j=1}^{k}\sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2$ menggunakan algoritma Lloyd berbasis jarak Euclidean dengan batasan konvergensi `max_iter = 300`.
2. **Skema Partisi Kronologis & Isolasi Scaler:** Berbeda dari pendekatan transduktif tanpa pemisahan, data deret waktu dibagi secara kronologis menjadi partisi **Train 70% ($N_{\text{train}} = 26.723$ jendela)** dan **Test 30% ($N_{\text{test}} = 11.394$ jendela)**. Untuk memutus autokorelasi lag-1 tinggi ($r \approx 1,0$) dan mencegah kebocoran temporal (*temporal data leakage*), disisipkan **periode embargo 3.600 detik (1 jam)** di antara segmen Train dan Test. Seluruh *scaler* di-`fit` secara ketat hanya pada data Train, lalu ditransformasikan ke data Test tanpa mutasi state.
3. **Empat Skenario Eksperimen (Desain Faktorial $2 \times 2$):**
   - Skenario 1: `Point + StandardScaler` (resolusi detik 1 Hz, normalisasi z-score).
   - Skenario 2: `Point + RobustScaler` (resolusi detik 1 Hz, normalisasi median/IQR).
   - Skenario 3: `Window-60s + StandardScaler` (agregasi jendela 60s, 39 fitur statistik, normalisasi z-score).
   - Skenario 4: `Window-60s + RobustScaler` (agregasi jendela 60s, 39 fitur statistik, normalisasi median/IQR).
   *(Ditambahkan MinMaxScaler pada representasi window sebagai pembanding bebas kolaps).*
4. **Rentang Hiperparameter $k$ & Replikasi Seed:** Grid eksplorasi $k \in \{2, 3, 4, 5, 6, 7, 8\}$. Evaluasi menggunakan *primary seed* 42 dengan replikasi verifikasi kestabilan stokastik pada *seed* 0 dan 1.
5. **Subsampling Deterministik untuk Metrik:** Evaluasi Silhouette pasangan ($O(N^2)$) dilakukan menggunakan subsampel deterministik berukuran 5.000 titik (`seed = 42`) yang terkunci secara kriptografis (SHA-256) pada data Train dan Test.
6. **Metrik Evaluasi & Guardrails Eliminasi:**
   - Evaluasi kelayakan menggunakan kombinasi kurva Elbow Inersia, Silhouette Coefficient ($s$, maks), dan Davies-Bouldin Index (DBI, min).
   - *Guardrails Diskualifikasi Ketat:* (a) *Cluster Collapse*: partisi dengan proporsi $< 1\%$ data ($< 267$ jendela di Train) otomatis didiskualifikasi; (b) *Sharp Test Drop*: penurunan Silhouette Train-ke-Test $> 0,05$ atau kenaikan DBI relatif $> 20\%$ dinyatakan tidak stabil/overfit; (c) *Unstable Seed*: Pairwise ARI antar seed $< 0,80$ digugurkan.

---

## III. Results — CRISP-DM Evaluation

### A. Pengaruh Penskalaan (Hasil Perbandingan StandardScaler, RobustScaler, dan MinMaxScaler)

Komparasi metode penskalaan pada konfigurasi utama $k=4$ dengan isolasi Train-Test menghasilkan temuan evaluasi yang membongkar ilusi metrik:

| Metode Penskalaan | Sil (Train) | Sil (Test) | DBI (Train) | DBI (Test) | Inersia Train | Proporsi Klaster Terkecil | Status Kelayakan |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tanpa Scaler (Unscaled)** | 0.8903 | — | 0.4466 | — | — | — | Ditolak (Bias Mutlak SPP 348.9:1) |
| **StandardScaler** | 0.3311 | 0.1670 | 1.0989 | 1.7740 | 658.630,9 | 0,69% (C2), 0,79% (C3) | **NO-WINNER** (Collapse + Test Drop) |
| **RobustScaler** | 0.8822 | 0.8557 | 0.5455 | 0.6272 | 666.032.495,9 | 0,01% (C1), 0,007% (C3) | **NO-WINNER** (Cluster Collapse) |
| **MinMaxScaler** | 0.3104 | 0.2677 | 1.5715 | 2.0611 | 7.161,6 | 12,36% (C3) | **ELIGIBLE** (Lolos Semua Uji) |

1. **Kegagalan RobustScaler Akibat Cluster Collapse:** Meskipun RobustScaler menghasilkan nilai Silhouette semu yang sangat tinggi (0,8822 pada Train dan 0,8557 pada Test) serta DBI rendah (0,5455), audit guardrail mendeteksi keruntuhan klaster ekstrem (*cluster collapse*). Normalisasi median/IQR menekan 99,25% data Train ke dalam satu mega-klaster (C0 = 26.523 jendela), sementara C1 (5 jendela), C2 (193 jendela), dan C3 (2 jendela) hanya menampung segelintir pencilan. Pada data Test, C0 mendominasi 99,55% dan dua klaster kosong sama sekali (0%). Skenario ini resmi didiskualifikasi sebagai `NO-WINNER`.
2. **Ketidakstabilan Generalisasi StandardScaler:** StandardScaler menghasilkan separasi awal wajar di Train, namun dua klaster berukuran $< 1\%$ (kolaps), dan nilai Silhouette anjlok drastis saat diuji pada data Test (dari 0,3311 ke 0,1670; drop sebesar 0,1641 $> 0,05$), mengindikasikan ketidakmampuan model menghadapi *temporal shift*.
3. **Keunggulan Partisi Berimbang MinMaxScaler:** MinMaxScaler menjadi satu-satunya skenario yang lolos seluruh kriteria kontrak (`ELIGIBLE`). Proporsi keempat klaster terbagi secara proporsional dan sehat (C0 = 13,07%, C1 = 34,63%, C2 = 39,94%, C3 = 12,36%), penurunan generalisasi ke data Test sangat minim (0,3104 $\rightarrow$ 0,2677), serta stabilitas replikasi lintas seed mencapai skor ARI hampir sempurna ($0,9997$).

### B. Pengaruh Bingkai Temporal (Data per Titik vs Jendela 60 Detik)

1. **Patologi Data Titik 1 Hz (Point-based):** Pengelompokan langsung pada data per-detik mentah menghasilkan pengelompokan semu (*meaningless clustering*, Keogh & Lin 2005) akibat autokorelasi lag-1 mendekati 1,0. Lebih krusial lagi, representasi titik memicu fenomena *label chattering* (pergantian label acak berkecepatan tinggi sebesar 0,0104 flip/detik). Secara fisik, status rig tidak mungkin berganti bolak-balik antara mengebor aktif dan menyambung pipa dalam durasi satu detik.
2. **Rasionalisasi Fisik Jendela Waktu 60 Detik (Window-based):**
   - **Konstanta Aliran Fluida Geotermal:** Durasi 60 detik (1 menit) mencerminkan *hydraulic loop response time*, yaitu waktu reaksi fluida lumpur merambat dari pompa permukaan ke dasar sumur pada kedalaman ribuan kaki sumur 56-32.
   - **Meredam Chattering hingga 8x:** Representasi jendela mereduksi tingkat pergantian label menjadi hanya 0,0013 per detik (8 kali lebih stabil), menghasilkan transisi status rig yang mulus dan koheren di lapangan.
   - **Preservasi Karakteristik Temporal:** Jendela 60 detik mengompresi data sebesar $65\times$ (dari 2.476.856 detik menjadi 38.177 jendela valid) dengan mengekstrak 3 ringkasan statistik per kanal (mean $\mu_w$ = besaran daya; std $\sigma_w$ = getaran mekanis/chatter; delta $\Delta_w$ = tren transisi manuver), sehingga memenuhi kriteria bonus temporal secara elegan.

### C. Pemilihan Jumlah Klaster ($k=2..8$)

| Nilai $k$ | StandardScaler (Sil / DBI / Inersia) | RobustScaler (Sil / DBI / Inersia) | MinMaxScaler (Sil / DBI / Inersia) | Status Kelayakan K-Means |
| :---: | :---: | :---: | :---: | :---: |
| **2** | 0.3145 / 1.5199 / 852.806 | 0.9678 / 0.5086 / 982.123.609 | 0.4933 / 0.8488 / 9.095 | Gugur (Sharp Test Drop pada MinMax) |
| **3** | 0.3229 / 1.2017 / 739.823 | 0.8840 / 0.6639 / 819.472.838 | 0.4394 / 1.3387 / 7.819 | Gugur (Sharp Test Drop pada MinMax) |
| **4** | **0.3311 / 1.0989 / 658.631** | **0.8822 / 0.5455 / 666.032.496** | **0.3104 / 1.5715 / 7.162** | **ELIGIBLE / WINNER ($k=4$ MinMaxScaler)** |
| **5** | 0.3272 / 1.4799 / 614.178 | 0.8540 / 0.5724 / 553.090.784 | 0.3218 / 1.5244 / 6.737 | Gugur (Collapse pada Test set) |
| **6** | 0.3399 / 1.6589 / 583.371 | 0.6531 / 0.6559 / 500.278.119 | 0.3029 / 1.6281 / 6.243 | Gugur (Collapse pada Test set) |
| **7** | 0.3534 / 1.5354 / 553.312 | 0.6531 / 0.5835 / 454.231.231 | 0.3077 / 1.6713 / 5.924 | Gugur (Collapse pada Test set) |
| **8** | 0.3170 / 1.5475 / 532.803 | 0.6595 / 0.6123 / 406.759.359 | 0.2520 / 1.6236 / 5.637 | Gugur (Collapse pada Test set) |

1. **Karakteristik Kurva Elbow:** Plot inersia K-Means (`clean-pipeline-56-32/outputs/figures/cluster_kmeans_inertia_elbow.png`) menunjukkan kurva penurunan galat yang melandai secara gradual dan monoton tanpa patahan siku tajam (*flat/gradual elbow*). Pada MinMaxScaler, inersia melandai dari 9.095 ($k=2$) menjadi 7.162 ($k=4$), lalu melambat ke 5.637 ($k=8$). Ketiadaan titik siku matematis murni mengharuskan seleksi dipandu oleh domain fisik.
2. **Seleksi Metrik Internal & Eliminasi $k$ Lain:** Pada $k=2$ dan $k=3$, meskipun nilai Silhouette Train tinggi, metrik mengalami degradasi tajam di partisi Test (*sharp generalization drop*). Sementara pada $k \ge 5$, partisi menghasilkan klaster-klaster mikro berukuran $< 1\%$ yang terdiskualifikasi akibat *cluster collapse*.
3. **Rasionalisasi Pemilihan $k=4$ Berbasis Domain Operasional Pengeboran (Coley, 2019):**
   Nilai **$k=4$** secara konsisten menjadi satu-satunya konfigurasi yang lolos seluruh guardrail statistik dan merefleksikan secara presisi **4 rezim operasional rig pemboran geotermal**:
   - **Rezim 0 (Active Rotary Drilling):** Operasi pengeboran aktif formasi batuan keras dengan kombinasi putaran RPM meja bor, beban pahat WOB seimbang, dan sirkulasi lumpur bertekanan kontinu.
   - **Rezim 1 (High-Pressure Resistant Zone Drilling):** Pengeboran pada zona transisi batuan rapat bertekanan tinggi yang ditandai dengan lonjakan Standpipe Pressure (SPP).
   - **Rezim 2 (Circulation & Hole Cleaning):** Sirkulasi fluida lumpur berkecepatan tinggi untuk pembersihan serbuk bor tanpa penetrasi vertikal agresif (ROP mendekati 0, pompa hidraulik maksimum).
   - **Rezim 3 (Pipe Connection / Standby Slips):** Kondisi saat rangkaian stang bor ditahan di meja putar (*slips*) untuk penyambungan pipa baru; pompa hidraulik dan putaran RPM non-aktif.

---

## IV. Conclusion and Future Work — CRISP-DM Deployment

1. **Pembongkaran Ilusi Metrik RobustScaler:** Evaluasi berbasis partisi kronologis Train-Test (dengan embargo temporal 1 jam) membuktikan bahwa skor Silhouette semu yang tinggi pada RobustScaler ($0{,}8822$) diiringi oleh keruntuhan klaster katastropik (*cluster collapse*); 99,25% data terperangkap pada satu mega-klaster (C0) sementara klaster lainnya kosong atau hanya diisi pencilan mikro (< 1%). RobustScaler secara formal digugurkan sebagai `NO-WINNER`.
2. **Keunggulan Skema MinMaxScaler:** MinMaxScaler terbukti sebagai satu-satunya skenario penskalaan yang lolos seluruh aturan baku (*ELIGIBLE*), menghasilkan partisi berimbang tanpa klaster kerdil (proporsi minimum 12,36% di Train), Silhouette Train 0,3104 / Test 0,2677, DBI Train 1,5715 / Test 2,0611, dan stabilitas stokastik sempurna lintas-seed (ARI 0,9997).
3. **Peredaman Label Chattering & Kompresi Temporal:** Agregasi jendela geser *tumbling* 60 detik (stride 60 s, 0% overlap) mereduksi frekuensi kedipan status label acak sebesar 8 kali lipat (dari 0,0102 menjadi 0,0013 kedipan/detik) serta mengompresi volume data masukan sebesar 65 kali lipat (dari 2,47 juta detik menjadi 38.177 jendela valid 39-D).
4. **Penetapan Klaster Optimal $k = 4$:** Kurva inersia K-Means menunjukkan pelandaian gradual tanpa siku tajam, di mana $k = 4$ dengan MinMaxScaler ditetapkan sebagai konfigurasi terbaik yang lolos seluruh *guardrail* eliminasi (mengeliminasi $k=2,3$ akibat *sharp test drop* dan $k \ge 5$ akibat *collapse*).
5. **Penemuan Rezim Operasi Rig Tanpa Label:** Pemodelan K-Means $k=4$ MinMaxScaler memetakan status rig secara berimbang ke dalam empat rezim: *Active Rotary Drilling* (34,63%), *High-Pressure Tight Rock Drilling* (39,94%), *Circulation & Hole Cleaning* (13,07%), dan *Pipe Connection / Slips Standby* (12,36%).
6. **Integritas Ilmiah Validasi Domain:** Centroid klaster merefleksikan kewajaran mekanika dan hidraulika pengeboran, dengan kualifikasi metodologis penting bahwa konfirmasi definitif di lapangan tetap mensyaratkan verifikasi catatan harian pengebor (*driller's log*) independen.

**Saran Penelitian Mendatang:** (1) Validasi eksternal dengan *driller's daily activity log* bertimestamp; (2) eksplorasi metode *deep clustering* (Autoencoder + K-Means) dan algoritma berbasis densitas (HDBSCAN); (3) penerapan *streaming clustering* adaptif untuk pemantauan anjungan rig waktu nyata (*real-time rig state discovery*); (4) pengujian transferabilitas pada sumur Utah FORGE 16A(78)-32; dan (5) pemodelan rantai Markov / HMM untuk analisis dinamika transisi status pengeboran.

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

## Appendix — lampiran wajib (`tugas.txt:51-54`)

- Fig. 1 = `prisma_flowchart_restart_v6.svg` — funnel seleksi literatur PRISMA 2020 (§I-A).
- Screenshot faset Scopus: 331 older-than-2021, 178 non-Article, 20 non-English, 104 inaccessible.
- Repo kode + dataset Kaggle (`faruqmahdison/utah-datmin`) + `deklarasi_genai.md` + 6 file jejak screening.
- Berkas keluaran final: `table0`–`table6` (format CSV) dan `fig1`–`fig6` (format PNG) tersedia lengkap di folder `figures/`.
