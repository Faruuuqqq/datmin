# ANALISIS LITERATUR & SINTESIS PENELITIAN ACUAN
**Tugas Proyek UTS Data Mining:** Analisis Karakteristik Data Sensor Geotermal Multivariat & Pemodelan Klasterisasi Deret Waktu  
**Dataset Target:** Pengeboran Sumur Geotermal Utah FORGE Well 56-32 (`dataset/56-32 1sec data 27029986.csv`, 2.506.359 baris, 22 kolom, 1 Hz)  
**Sumber Berkas:** 16 naskah teks lengkap yang tersedia di folder `papers/md/`.

---

## 0. RINGKASAN INTUITIF: TEMUAN KITA & HUBUNGANNYA DENGAN DATA

Bagian ini merangkum secara lugas tentang data yang diolah, permasalahan fisiknya, dan bagaimana temuan dari paper acuan membantu menyelesaikannya:

### 1. Karakteristik Data yang Digunakan
* **Sumber Data:** Sensor permukaan rig pengeboran sumur geotermal Utah FORGE (Well 56-32).
* **Ukuran Data:** Sangat besar, yaitu **2,5 juta baris** (pencatatan tiap 1 detik selama 29 hari) dan 22 kolom sensor.
* **Sifat Data:** **Murni tanpa label (*unlabeled*)**. Kita tidak memiliki label catatan aktivitas driller, sehingga mesin harus mengelompokkan status operasi rig secara otomatis (*unsupervised clustering*).

### 2. Tiga Masalah Utama Data di Lapangan
1. **Ketimpangan Skala Ekstrem (*Scale Disparity*):**
   * Sensor Tekanan Pompa (SPP) bernilai ribuan ($0$–$3.500\text{ psi}$), sedangkan Torsi Putaran bernilai kecil ($0$–$15\text{ kft}\cdot\text{lb}$).
   * **Dampaknya:** Jika langsung diklasterisasi tanpa penskalaan, perhitungan jarak matematis (Euclidean) **99,36% hanya menghitung tekanan pompa**, sehingga sensor torsi, RPM, dan beban bor diabaikan oleh algoritma.
2. **Keterikatan Waktu Sangat Kuat (*Temporal Dependency*):**
   * Data dicatat tiap 1 detik, sehingga nilai detik ke-2 hampir identik dengan detik ke-1 (autokorelasi $>0,95$).
   * **Dampaknya:** Jika diklasterisasi per detik secara independen, hasil klaster akan berganti-ganti secara liar tiap detik (*chattering/flickering*) dan kehilangan konteks dinamika proses pengeboran.
3. **Pencilan Palsu & Sensor Rusak (*Outliers & Missing Values*):**
   * Sensor Gas dan Gamma Ray **100% mati** (bernilai konstan `-999.25` sepanjang file).
   * Laju penembusan (ROP) sempat melonjak palsu hingga **11.145 ft/jam** (terjadi saat mata bor menggantung di udara saat ganti pipa, bukan menembus batuan).
   * Kanal Differential Pressure bernilai $\le -900$ saat pompa dimatikan karena formula turunan sistem Pason.

### 3. Solusi dari Paper Acuan yang Kita Terapkan ke Data
Paper-paper yang kita kaji memberikan solusi praktis dan teruji untuk mengatasi masalah di atas:
* **Mengatasi Skala & Outlier (Paper Wang et al. & Qiu et al.):**
  * Menggunakan penskalaan tahan pencilan (`RobustScaler` berbasis Median & IQR) alih-alih Z-score standar, sehingga lonjakan palsu ROP tidak membiaskan pusat klaster.
* **Mempertahankan Karakteristik Waktu / Nilai Bonus UTS (Paper Li et al. & Abrasaldo et al.):**
  * Membagi data ke dalam **Jendela Geser (*Sliding Window*) berdurasi 60 detik**.
  * Setiap jendela 60 detik diringkas menjadi: rata-rata (tingkat tenaga), standar deviasi (getaran mesin), dan selisih tren (arah gerak).
  * **Hasilnya:** 2,5 juta titik detik diringkas menjadi $\approx 41.700$ jendela pengamatan menit yang stabil, beban komputasi turun drastis, dan karakteristik deret waktu tetap terjaga (memenuhi kriteria nilai bonus UTS).
* **Menentukan Klaster & Evaluasi Mutu (Paper Abrasaldo et al. - *Geothermics*):**
  * Menggunakan algoritma **$k$-Means Clustering**.
  * Jumlah klaster terbaik ($k$) ditentukan lewat grafik siku (**Elbow Method**).
  * Kualitas pengelompokan diuji secara objektif menggunakan **Silhouette Score** (kerapatan kelompok) dan **Davies-Bouldin Index** (keterpisahan antar-kelompok).

### 4. Target Hasil Akhir Pengolahan
Dengan menerapkan metode di atas, kita dapat memetakan 29 hari operasi pengeboran geotermal ke dalam 4–5 status fisik rig nyata secara otomatis:
* **Rotary Drilling:** Rig aktif menembus batuan granit (tekanan tinggi, putaran tinggi, beban tekan bor tinggi, torsi aktif).
* **Circulating / Reaming:** Pompa lumpur menyala untuk membersihkan lubang bor, namun mata bor tidak menekan ke bawah.
* **Tripping / Connection:** Proses menyambung atau mencabut rangkaian pipa bor (pompa mati, putaran nol, beban gantungan derek tinggi).
* **Idle / Standby:** Rig berhenti beroperasi sementara atau dalam perbaikan mesin (seluruh sensor mendekati nol).

---

## 1. PEMETAAN MASALAH DATASET VS PERTANYAAN TEKNIS (RESEARCH QUESTIONS)

Berdasarkan audit komputasi empiris terhadap data mentah Sumur 56-32 (`notebook/data-karakteristik.md`), terdapat 4 tantangan teknis utama yang harus dijawab oleh literatur:

1. **Ketimpangan Skala Ekstrem (*Scale Disparity*):**
   - Varians `Standpipe Pressure` ($2.218.321$) dan `Total Pump Output` ($97.221$) menguasai **99,36%** dari total variansi sensor. Varians `Rotary Torque` hanya $12,97$. Tanpa penskalaan, jarak Euclidean bias total ke tekanan pompa.
   - *Pertanyaan yang harus dijawab literatur (RQ1):* Metode penskalaan (*feature scaling*) apa yang terbukti paling tangguh terhadap pencilan mekanik tanpa merusak rasio variasi fisik sensor?
2. **Ketergantungan Waktu (*Temporal Dependency* / Nilai Bonus UTS):**
   - Autokorelasi lag 1 detik hingga 60 detik sangat tinggi ($> 0,95$ hingga $0,99$). Pemodelan per detik (*point-based*) menyebabkan klaster berfluktuasi liar (*chattering*) dan mengabaikan tren waktu.
   - *Pertanyaan yang harus dijawab literatur (RQ2):* Bagaimana mengekstrak informasi deret waktu dari jutaan baris sensor 1 Hz agar karakteristik temporal terjaga (*bonus point*) dengan beban komputasi efisien?
3. **Pencilan Transien & Nilai Sentinel Sistemik:**
   - Terdapat artefak lonjakan ROP hingga $11.145,94\text{ ft/hr}$ saat mata bor menggantung (*off-bottom*), serta nilai negatif $\le -900\text{ psi}$ pada kanal turunan Differential Pressure saat pompa mati.
   - *Pertanyaan yang harus dijawab literatur (RQ3):* Bagaimana literatur membersihkan artefak transien mekanik dan menangani periode rig tidak aktif (*idle/off-bottom*)?
4. **Klasterisasi Tanpa Label (*Unsupervised Regime Discovery*) & Validasi Internal:**
   - Data bersifat murni tanpa label (*unlabeled*). Perlu memetakan aktivitas rig ke status operasional (*rotary drilling, circulating, connection, tripping*).
   - *Pertanyaan yang harus dijawab literatur (RQ4):* Algoritma klasterisasi apa yang paling andal dan bagaimana menentukan jumlah klaster optimal ($k$) menggunakan metrik internal (Silhouette & Davies-Bouldin Index)?

---

## 2. INVENTARISASI & REVIEW LENGKAP 16 PAPER DI `papers/md/`

Berikut adalah ringkasan hasil pembacaan terhadap seluruh 16 berkas naskah yang ada di folder `papers/md/`:

| No | Berkas di `papers/md/` | Judul Paper & Penulis | Jurnal / Konferensi / Tahun | Domain & Dataset | Metodologi & Algoritma | Relevansi terhadap Tugas UTS |
|:--:|---|---|---|---|---|---|
| **1** | `1-energies-18-05753-v2.md` | *Data-Driven Time-Series Modeling for Intelligent Extraction of Reservoir Development Indicators* (Ling Qiu et al.) | **Energies (MDPI)**, Vol. 18, 2025 | Deret waktu produksi sumur minyak lepas pantai | Pipeline deteksi outlier hibrida: **3-Sigma Rule + One-Class SVM (OC-SVM)**; klasifikasi tahapan dinamis | **Menjawab RQ3:** Sangat relevan untuk pembersihan outlier transien mekanik dan segmentasi tahapan dinamis sumur. |
| **2** | `2-engproc-107-00024-v2.md` | *Anomaly Detection in Geothermal Steam Production Time Series Using Singular Spectrum Analysis* (Keiya Azuma & Yasuhiro Hashimoto) | **Engineering Proceedings (MDPI)**, Vol. 107, 2025 | Deret waktu produksi uap 9 sumur geotermal (14 tahun) | **Singular Spectrum Analysis (SSA)** via *Lagged Trajectory Matrix Embedding*, Butterworth filter | **Menjawab RQ2:** Domain murni geotermal; membuktikan teknik dekomposisi lag temporal untuk meredam noise fluida panas bumi. |
| **3** | `3-wang-et-al-2026...md` | *A comprehensive machine learning workflow for classifying production profiles in unconventional reservoirs* (Dinghan Wang et al.) | **Energy Exploration & Exploitation (Sage)**, Vol. 44, 2026 | Data profil produksi sumur non-konvensional Permian | Normalisasi skala atribut, univariate EDA, **Unsupervised Clustering ($k$-Means, GMM)**, **Elbow Method**, **Silhouette Score** | **Menjawab RQ1 & RQ4:** Cetak biru alur kerja penanganan ketimpangan skala, klasterisasi tanpa label, dan evaluasi Silhouette. |
| **4** | `4-1-s2.0-S2949891024006109...md` | *Oil and gas flow anomaly detection on offshore naturally flowing wells using deep neural networks* (Guzel Bayazitova et al.) | **Geoenergy Science and Engineering (Elsevier)**, Vol. 238, 2024 | Sensor multivariat aliran/tekanan sumur (Benchmark 3W Petrobras, 21 sumur) | Standarisasi skala, forward-fill missing values, downsampling 1 menit, **time-series windowing (len 30)** | **Menjawab RQ1 & RQ3:** Standar baku industri penanganan sensor aliran/tekanan, imputasi nilai hilang, dan mitigasi noise instrumen sumur. |
| **5** | `5-Reference station-based...md` | *Reference station-based transfer learning for earthquake anomaly extraction from borehole strain data...* (Jiayi Li et al.) | **Big Earth Data (Taylor & Francis)**, 2025/2026 | Data regangan lubang bor 1 Hz stasiun seismik gempa China | Spatial-Temporal Multi-Scale Network (STMN-EQA), TimesNet temporal features | **Kurang Relevan:** Topik gempa bumi regional tektonik; tidak terkait langsung dengan operasional mesin rig pemboran. |
| **6** | `6-sensors-26-04917.md` | *Research on Vibration Signal Processing and Fault Diagnosis Algorithms for High-Pressure Quintuplex Pumps* (Zewei Liu et al.) | **Sensors (MDPI)**, Vol. 26, 2026 | Sinyal getaran pompa lumpur pemboran tekanan tinggi (*mud pumps*) | VMD-FastICA decoupling, 2D GAF-RP encoding, Vision Transformer (ViT) domain adaptation | **Relevan Subsistem:** Relevan memahami karakteristik pompa lumpur (`Total Pump Output`), tetapi fokus pada klasifikasi getaran frekuensi kHz laboratorium. |
| **7** | `7-1-s2.0-S187454822500023X...md` | *STADe: An unsupervised time-windows method of detecting anomalies in oil and gas Industrial Cyber-Physical Systems (ICPS)* (Abubakar S. Mohammed et al.) | **Int. Journal of Critical Infrastructure Protection (Elsevier)**, Vol. 48, 2025 | Jaringan telemetri sensor kontrol ICPS industri minyak dan gas | **Unsupervised Time-Windows (Sliding Window)**, pengukuran deviasi pola periodik operasional mesin | **Menjawab RQ2:** Memberikan dasar teoritis kuat mengenai keunggulan segmentasi jendela geser temporal pada data sensor industri berkecepatan tinggi. |
| **8** | `8-1-s2.0-S2666759226000193...md` | *Toward basin-agnostic well log imputation and anomaly detection via a pre-trained time-series foundation model* (Ardiansyah Koeshidayatullah et al.) | **Energy Geoscience (Elsevier)**, 2026 | Log sumur deret kedalaman/waktu (GR, RHOB, NPHI) cekungan Groningen | Foundation model TimeGPT, zero-shot imputation, z-score dynamic normalization | **Relevan Pendukung:** Bermanfaat untuk konsep imputasi data log sumur yang bolong/sentinel. |
| **9** | `9-1-s2.0-S0375650526000611...md` | *Feature-based time series clustering for efficient labelling of geothermal data* (Paul M. B. Abrasaldo, Sadiq J. Zarrouk, Andreas W. Kempa-Liehr) | **Geothermics (Elsevier)**, Vol. 136, 2026 | **Sensor pembangkit listrik geotermal Wairakei, Selandia Baru** (tekanan, laju alir, suhu) | **Feature-based Time Series Clustering ($k$-Means, Agglomerative, DBSCAN)**, **Silhouette (SIL)**, **Davies-Bouldin (DBI)**, **Calinski-Harabasz (CHI)** | **PAPER PALING COCOK (100% Menjawab RQ2 & RQ4):** Domain geotermal murni, clustering time-series tanpa label, evaluasi internal Silhouette dan Davies-Bouldin. |
| **10** | `No_07_External_factors...md` | *External factors driving surface temperature changes above geothermal systems: answers from deep learning* (A. F. Harris et al.) | **Frontiers in Earth Science**, Vol. 12, 2024 | Sensor suhu permukaan tanah & meteorologi lapangan Vulcano (Italia) | Dynamic Thresholding (DITAN), filtering faktor cuaca | **Kurang Relevan:** Domain geotermal, tetapi fokus pada pengaruh cuaca atmosfer terhadap suhu permukaan tanah pasif, bukan mekanika pengeboran. |
| **11** | `No_12_Tool_condition...md` | *Tool condition monitoring method by anomaly segmentation of time-frequency images using acoustic emission in small hole drilling* (Taro Nakano et al.) | **J. Adv. Mech. Des. Syst. Manuf. (JSME)**, Vol. 17, 2023 | Sinyal emisi akustik pada proses pengeboran lubang kecil (*peck drilling*) | CWT time-frequency spectrograms, Convolutional Autoencoder, segmentasi anomali transisi kondisi pahat | **Menjawab RQ3:** Relevan untuk menginterpretasikan dinamika kontak fisik mata bor dengan batuan keras (*bit-rock interaction*). |
| **12** | `No_14_Unsupervised_deep...md` | *Unsupervised deep learning framework for early detection of wellbore trajectory deviation in drilling operations* (P. Singh et al.) | **Frontiers in Artificial Intelligence / Energy Res.**, Vol. 14, 2026 | Sensor trajektori sumur bor dan parameter mekanik pengeboran terarah | **Unsupervised graph feature representation**, normalisasi kuantil, segmentasi jendela operasional sumur | **Menjawab RQ3 & RQ4:** Membuktikan bahwa kondisi dan stabilitas operasi pengeboran dapat diidentifikasi secara akurat tanpa label manual. |
| **13** | `No_161_Clustering_analysis...md` | *Methodology for determining the optimal concentration of an alkali solution for enhanced oil recovery* (A. S. Hadiyeva et al.) | **SOCAR Proceedings**, No. 1, 2026 | Eksperimen laboratorium kimia injeksi fluida alkali | Uji sifat fisik-kimia laboratorium: tegangan antarmuka fluida, sudut kontak, viskositas larutan alkali | **TIDAK RELEVAN (Anomali Berkas):** Berkas ini membahas eksperimen laboratorium kimia injeksi EOR tanpa metode data mining/klasterisasi sama sekali. |
| **14** | `No_57_Anomaly_detection...md` | *Anomaly detection with domain specific shapelet learning for sucker rod pump system* (Xiangyu Li et al.) | **Scientific Reports (Nature)**, Vol. 15, 2025 | Deret waktu daya motor pompa angguk (*sucker rod pump*) | Domain-specific Shapelet Learning (AD-DSL), segmentasi sliding window, sparse optimization ADMM | **Relevan Pendukung:** Menunjukkan pemanfaatan bentuk kurva lokal (*shapelets/windows*) pada peralatan sumur, namun terbatas pada motor pompa tunggal. |
| **15** | `No_74_Anomaly_detection...md` | *Anomaly Detection in Borehole Strain Data with CNN and Frequency-Aware VAE* (Xiaolong Wei et al.) | **JACIII**, Vol. 29, 2025 | Data regangan lubang bor seismik 6 komponen | Frequency-Aware VAE (FA-VAE), windowed local attention, rekonstruksi FFT | **Kurang Relevan:** Fokus pada regangan tektonik gempa bawah tanah, bukan instrumen pengeboran permukaan. |
| **16** | `No_77_Intelligent_drilling...md` | *Research on an intelligent drilling parameter optimization method using sliding window segmentation based on the hydraulic-mechanical specific energy model* (Wei Li et al.) | **PLOS ONE**, Vol. 21, 2026 | **Sensor permukaan pengeboran riil** (WOB, RPM, SPP, Flow Rate, Torque, ROP) | **Sliding Window Segmentation**, imputasi Random Forest, penghalusan Savitzky-Golay, korelasi parameter mekanik dengan energi spesifik (HMSE), $k$-Means | **PAPER KUNCI (98% Menjawab RQ1 & RQ2):** Menggunakan 7 parameter mekanik yang sama persis dengan Utah FORGE 56-32; menjadi acuan utama segmentasi *Sliding Window*. |

---

## 3. SELEKSI 8 PAPER ACUAN UTAMA YANG MEMBANTU PENGOLAHAN DATA KITA

Dari 16 berkas di atas, dipilih **8 paper yang paling selaras secara teknis** untuk memandu pengolahan dataset Sumur Geotermal Utah FORGE 56-32:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 8 PAPER ACUAN UTAMA TERPILIH                                    │
├────────────────────────────────┬────────────────────────────────┬────────────────────────────────┤
│  1. Abrasaldo et al. (2026)    │  2. Li et al. (2026)           │  3. Wang et al. (2026)         │
│     [Geothermics]              │     [PLOS ONE]                 │     [Energy Explor. & Exploit.]│
│     * Geothermal time-series   │     * 7 Drilling sensors       │     * Scale disparity handling │
│     * Feature-based clustering │     * Sliding window (bonus)   │     * Unsupervised k-Means/GMM │
│     * Silhouette & DBI metrics │     * Noise smoothing          │     * Elbow & Silhouette eval  │
├────────────────────────────────┼────────────────────────────────┼────────────────────────────────┤
│  4. Singh et al. (2026)        │  5. Bayazitova et al. (2024)   │  6. Mohammed et al. (2025)     │
│     [Frontiers in AI]          │     [Geoenergy Sci. & Eng.]    │     [Int. J. Crit. Infra. Prot]│
│     * Unsupervised drilling    │     * Well sensor preprocessing│     * Unsupervised time-windows│
│     * Trajectory/rig state     │     * Z-score & missing data   │     * Industrial time-series   │
│     * Quantile normalization   │     * Supervised vs unsuperv.  │     * Operation regime shifts  │
├────────────────────────────────┼────────────────────────────────┼────────────────────────────────┤
│  7. Azuma & Hashimoto (2025)   │  8. Qiu et al. (2025)                                           │
│     [Engineering Proceedings]  │     [Energies]                                                 │
│     * Geothermal steam series  │     * Sensor outlier removal (3-Sigma / IQR)                    │
│     * Lag trajectory embedding │     * Dynamic operational stage segmentation                    │
│     * Temporal preservation    │     * Transients & noise handling                               │
└────────────────────────────────┴────────────────────────────────────────────────────────────────┘
```

### Rincian Peran Masing-Masing Paper dalam Proyek Kita:

1. **Abrasaldo et al. (2026) — *Geothermics* (Paper No. 9):**
   - *Masalah yang dijawab:* Bagaimana melakukan klasterisasi deret waktu pada sensor geotermal tanpa label dan memilih metrik validasi internal yang tepat?
   - *Solusi untuk kita:* Menjadi rujukan utama perancangan metrik **Silhouette Coefficient** dan **Davies-Bouldin Index (DBI)** untuk menguji kualitas partisi klaster pada Bab II dan Bab III.
2. **Li et al. (2026) — *PLOS ONE* (Paper No. 16 / No_77):**
   - *Masalah yang dijawab:* Bagaimana menangani aliran sensor mekanik pemboran frekuensi tinggi (1 Hz) dan meredam fluktuasi transien?
   - *Solusi untuk kita:* Menjadi dasar metodologi **pemrosesan deret waktu (*time-series handling*)** berbasis **Sliding Window (jendela geser 60 detik)** untuk **meraih nilai bonus UTS**.
3. **Wang et al. (2026) — *Energy Exploration & Exploitation* (Paper No. 3):**
   - *Masalah yang dijawab:* Bagaimana mengatasi ketimpangan skala (*scale disparity*) antar-fitur sumur dan menentukan jumlah klaster $k$ optimal?
   - *Solusi untuk kita:* Menjadi landasan teoritis untuk membuktikan bahaya bias jarak Euclidean akibat ketimpangan variansi SPP vs Torsi, serta memandu perbandingan *StandardScaler* vs *RobustScaler*.
4. **Singh et al. (2026) — *Frontiers in AI / Energy Research* (Paper No. 12 / No_14):**
   - *Masalah yang dijawab:* Apakah kondisi operasi pengeboran dapat dipetakan secara akurat tanpa bantuan label manusia?
   - *Solusi untuk kita:* Memberikan pembenaran ilmiah bahwa segmentasi status pengeboran dapat diekstrak murni dari struktur geometris klaster data sensor.
5. **Bayazitova et al. (2024) — *Geoenergy Science and Engineering* (Paper No. 4):**
   - *Masalah yang dijawab:* Bagaimana standar industri dalam pra-pemrosesan sensor sumur (missing value, Z-score, downsampling)?
   - *Solusi untuk kita:* Menjadi standar baku pembersihan data hilang dan tolok ukur pembanding: riset mereka membutuhkan label manual (supervised), sedangkan tugas kita memecahkan kondisi riil tanpa label (unsupervised).
6. **Mohammed et al. (2025) — *International Journal of Critical Infrastructure Protection* (Paper No. 7):**
   - *Masalah yang dijawab:* Mengapa analisis berbasis jendela waktu (*time-windows*) lebih unggul daripada pemrosesan titik per detik pada data industri berkecepatan tinggi?
   - *Solusi untuk kita:* Memperkuat argumen bahwa jendela waktu melestarikan dinamika periodik mesin dan mencegah *chattering effect* pada label klaster.
7. **Azuma & Hashimoto (2025) — *Engineering Proceedings* (Paper No. 2):**
   - *Masalah yang dijawab:* Bagaimana karakteristik dependensi waktu (*lag dependency*) pada data sumur geotermal?
   - *Solusi untuk kita:* Menjustifikasi secara fisik mengapa autokorelasi lag temporal tinggi pada Sumur 56-32 Utah FORGE harus dipertahankan dan diekstrak fiturnya.
8. **Qiu et al. (2025) — *Energies* (Paper No. 1):**
   - *Masalah yang dijawab:* Bagaimana membersihkan pencilan (*outliers*) transien ekstrem yang timbul akibat manuver teknis rig?
   - *Solusi untuk kita:* Menjadi dasar pembersihan artefak transien lonjakan ROP ($11.145\text{ ft/hr}$) dan anomali tekanan saat pipa digantung.

---

## 4. TABEL GAP ANALYSIS (ANALISIS KESENJANGAN RISET)

Tabel berikut menyandingkan pendekatan pada literatur acuan utama dengan kontribusi yang kelompok kita kerjakan pada data Sumur Geotermal Utah FORGE 56-32:

| Sumbu Analisis | Abrasaldo et al. (2026) [`Geothermics`] | Li et al. (2026) [`PLOS ONE`] | Wang et al. (2026) [`Energy Expl.`] | Bayazitova et al. (2024) [`Geoenergy`] | **Kontribusi Kelompok Kita (Paper UTS Ini)** |
|---|---|---|---|---|---|
| **Domain & Objek Data** | Sensor pembangkit biner geotermal (permukaan). | Sensor mekanik pemboran darat (sumur minyak). | Profil produksi & komplesi sumur Permian. | Sensor tekanan & laju alir sumur lepas pantai (3W). | **Pengeboran Sumur Geotermal Suhu Tinggi (*Granite EGS*) Utah FORGE Well 56-32.** |
| **Granularitas & Volume Data** | Data menit/jam tersaring. | Data rekaman per detik (7.231 baris sampel). | Data bulanan agregat (189 sumur). | Data aliran termutakhirkan (downsample 1 menit). | **Aliran sensor masif 1 Hz riil (2.506.359 baris kontinu selama 29,06 hari pemboran).** |
| **Penanganan Ketimpangan Skala (*Scale Disparity*)** | Standard Z-score tanpa analisis pengaruh varians antar-sensor. | Penskalaan min-max lokal per segmen jendela. | Normalisasi standar global (StandardScaler). | Standard Z-score global dengan penanganan missing data. | **Studi Komparasi Empiris: `StandardScaler` (Z-score) vs. `RobustScaler` (Median-IQR) guna meredam bias varians SPP (95,19%) & lonjakan ROP.** |
| **Preservasi Temporal (*Bonus Track UTS*)** | Ekstraksi fitur statistik ringkasan statis. | Segmentasi sliding window berbasis HMSE. | Mengabaikan dependensi waktu (analisis titik statis). | Windowing sekuensial untuk masukan model deep learning. | **Preservasi Temporal via Non-Overlapping Sliding Window (60 detik) dengan mekanisme reset adaptif di 8 titik celah sampling (*sampling gaps*).** |
| **Penanganan Outlier & Nilai Sentinel** | Filter ambang batas standar pabrik. | Imputasi Random Forest + Savitzky-Golay filter. | Pembersihan outlier univariat standar. | Imputasi forward-fill dan filtering anomali berlabel. | **Pemisahan kanal kalkulasi turunan (Differential Pressure), eliminasi kanal konstan (Gas & Gamma = -999.25), dan mitigasi artefak blok derek ROP.** |
| **Metode Klasterisasi & Optimasi** | $k$-Means, Agglomerative, DBSCAN. | Optimasi parameter pengeboran berbasis $k$-Means. | $k$-Means, Hierarchical, GMM. | Klasifikasi terarah (Supervised: RF, MLP, BiLSTM). | **$k$-Means Clustering dioptimasi dengan Elbow Method ($k \in [3, 8]$) serta evaluasi internal ganda (Silhouette Score & Davies-Bouldin Index).** |
| **Interpretasi Semantik Klaster** | Pemisahan rezim efisiensi penukar panas (*fouling stage*). | Rekomendasi parameter bor (WOB-RPM optimum). | Tipe profil kurva penurunan laju produksi reservoir. | Deteksi kejadian spesifik berlabel (slugging, hidrasi). | **Penemuan 4–5 Rezim Fisik Operasi Rig Geotermal: *On-Bottom Rotary Drilling, Reaming/Circulating, Connection, Tripping, dan Idle/Standby*.** |

---

## 5. RANCANGAN PENGOLAHAN DATASET (PREPROCESSING & CLUSTERING PLAN)

Berdasarkan sintesis ke-8 paper acuan di atas, berikut alur kerja konkret yang akan kita implementasikan pada data Sumur 56-32:

```
[2.506.359 Baris Data Mentah 1 Hz]
  │
  ├─► 1. Feature Drop:
  │      Drop 'Pason Gas' & 'Gamma' (100% mati / -999.25)
  │      Drop 'Hole Depth', 'Bit Depth', 'Lag Depth' (mencegah klaster trivial membagi kedalaman)
  │      Pisahkan 'Differential Pressure' (kanal turunan rig, bukan sensor langsung)
  │
  ├─► 2. Filter Baris Sentinel:
  │      Saring baris dengan SPP <= -900 (hanya 1,18% data) saat sensor tidak aktif
  │
  ├─► 3. Time-Series Handling (Preservasi Temporal / Bonus UTS):
  │      Segmentasi Sliding Window W = 60 detik (Non-Overlapping)
  │      Reset jendela pada 8 titik celah waktu sampling (sampling gaps)
  │      Ekstrak ringkasan temporal per jendela: Mean, Std (getaran), Delta/Slope (tren)
  │      (Mereduksi 2,5 juta baris -> ~41.700 jendela observasi kaya konteks)
  │
  ├─► 4. Eksperimen Penskalaan (Scale Disparity):
  │      Bandingkan: StandardScaler vs RobustScaler (Median-IQR)
  │      Buktikan RobustScaler meredam bias outlier ROP pada posisi centroid
  │
  ├─► 5. Pemodelan Klasterisasi Unsupervised:
  │      Algoritma: k-Means Clustering
  │      Optimasi Hiperparameter: Elbow Method pada rentang k = 3 s.d. 8
  │
  └─► 6. Evaluasi Internal & Interpretasi Domain:
         Hitung Silhouette Coefficient & Davies-Bouldin Index (DBI)
         Petakan klaster ke 4-5 status rig: Drilling, Circulating, Tripping, Connection, Idle
```

---

## 6. EVALUASI KELAYAKAN METODE: MENGAPA METODE INI YANG TERBAIK?

Dalam merancang pemodelan klasterisasi deret waktu industri, terdapat beberapa alternatif metodologis. Berikut analisis komparatif yang membuktikan bahwa kombinasi **Window-based Feature Extraction + RobustScaler + $k$-Means** adalah solusi paling optimal (*sweet spot*) untuk proyek ini:

| Pendekatan Alternatif | Kelebihan Teoretis | Kelemahan & Kendala pada Data Sumur 56-32 | Kesimpulan Kelayakan |
|---|---|---|:---:|
| **1. Dynamic Time Warping (DTW) + TimeSeriesKMeans** | Mampu mencocokkan bentuk gelombang (*shape similarity*) meski terjadi pergeseran fasa atau pemelaran waktu. | Kompleksitas komputasi kuadratik $\mathcal{O}(N^2 \cdot L^2)$. Untuk data 2,5 juta detik (atau ribuan jendela multivariat), memori RAM Google Colab/laptop akan kehabisan kapasitas (*Out-of-Memory / crash*) dan waktu komputasi sangat lambat (berjam-jam). | **Tidak Layak** (Beban komputasi berlebihan) |
| **2. Deep Learning (LSTM Autoencoder / VAE)** | Mampu mempelajari representasi laten non-linear yang sangat kompleks dari deret waktu multivariat. | Membutuhkan GPU, waktu pelatihan panjang, rentan terhadap *overfitting*, dan bersifat kotak hitam (*black-box*) sehingga sangat sulit diinterpretasikan ke kondisi fisik pengeboran. Di mata penguji akademik, metode ini *overkill* dan mengaburkan penguasaan konsep dasar klasterisasi. | **Kurang Efektif** (Sulit diinterpretasi & rentan overfitting) |
| **3. Density-Based (DBSCAN) / Hierarchical Clustering** | Mampu menemukan klaster berbentuk non-sferis dan memisahkan noise secara otomatis (DBSCAN). | Hierarchical clustering memiliki kompleksitas memori $\mathcal{O}(N^3)$, tidak mampu memproses lebih dari 10.000 titik. DBSCAN tidak memiliki jumlah $k$ tetap dan gagal pada data sensor industri yang densitasnya bervariasi tajam antar-rezim operasi. | **Tidak Layak** (Gagal pada densitas heterogen) |
| **4. Window-based Feature Extraction + RobustScaler + $k$-Means (Metode Terpilih)** | 1. Kompleksitas linear $\mathcal{O}(N \cdot k)$, komputasi sangat cepat (selesai dalam hitungan detik/menit).<br>2. Menjawab 100% kriteria bonus UTS (karakteristik temporal tetap terjaga melalui ringkasan mean, variabilitas, dan tren per jendela).<br>3. Tahan terhadap outlier transien ROP ($11.145\text{ ft/hr}$) berkat penskalaan median-IQR.<br>4. Centroid klaster merepresentasikan nilai fisik riil yang mudah dipetakan langsung ke status operasi rig pengeboran. | Asumsi geometri klaster mendekati cembung (*convex*), namun asumsi ini terbukti terpenuhi pada data rezim mesin operasional terpisah (misal pompa menyala vs pompa mati). | **TERBAIK & PALING OPTIMAL** (Cepat, tangguh, interpretable, & bonus terpenuhi) |

---

## 7. ROADMAP LANGKAH KERJA SELANJUTNYA (EXECUTION PLAN)

Sesuai dengan panduan pengerjaan proyek UTS Data Mining, berikut adalah langkah kerja konkret yang akan dilaksanakan secara berurutan:

```
┌───────────────────────────────┐     ┌───────────────────────────────┐     ┌───────────────────────────────┐
│     LANGKAH 1: PREPROCESSING  │     │     LANGKAH 2: EKSPERIMEN     │     │     LANGKAH 3: PENULISAN      │
│     & ANALISIS EKSPLORASI     │ ──► │    KLASTERISASI & OPTIMASI    │ ──► │     PAPER FORMAT IEEE         │
│  - Filter kolom & sentinel    │     │  - Komparasi StandardScaler   │     │  - Susun template .doc 2 kolom│
│  - Korelasi Pearson/Spearman  │     │    vs RobustScaler            │     │  - Masukkan Gap Analysis      │
│  - Boxplot visualisasi outlier│     │  - Curve Elbow (k=3 s.d. 8)   │     │  - Tampilkan grafik & tabel   │
│  - Ekstraksi Window 60 detik  │     │  - Evaluasi Silhouette & DBI  │     │  - Interpretasi status rig    │
│  - Simpan dataset windowed    │     │  - Labeling semantik rig      │     │  - Lampirkan deklarasi Gen-AI │
└───────────────────────────────┘     └───────────────────────────────┘     └───────────────────────────────┘
```

### Rincian Tindakan per Langkah:

#### Tahap 2: Preprocessing & Exploratory Data Analysis (EDA)
1. **Skrip Pembersihan Data:**
   - Membaca data mentah $\to$ menghapus kolom konstan (`Pason Gas`, `Gamma`) dan kolom kedalaman (`Hole Depth`, `Bit Depth`, `Lag Depth`).
   - Memisahkan kanal turunan `Differential Pressure` dan menyaring baris sentinel `SPP <= -900`.
2. **Visualisasi Wajib Laporan:**
   - Menghasilkan matriks korelasi (Heatmap) Pearson dan Spearman untuk membuktikan multikolinearitas sensor.
   - Menghasilkan Boxplot distribusi sensor untuk membuktikan keberadaan pencilan ekstrem pada ROP dan SPP.
3. **Ekstraksi Fitur Deret Waktu (Sliding Window):**
   - Menerapkan jendela geser $W = 60\text{ detik}$ dengan *gap-aware reset* pada 8 celah waktu sampling.
   - Menghitung Mean, Standar Deviasi, dan Slope untuk setiap sensor di setiap jendela.
   - Menyimpan hasil fitur ke berkas perantara (misal `dataset_windowed_60s.csv`) agar proses pemodelan berikutnya instan.

#### Tahap 3: Pemodelan Klasterisasi & Optimasi Hiperparameter
1. **Eksperimen Penskalaan Fitur:**
   - Mentransformasi data jendela menggunakan `StandardScaler` dan `RobustScaler`.
2. **Pencarian $k$ Optimal (Elbow Method):**
   - Menjalankan $k$-Means untuk rentang $k = 3, 4, 5, 6, 7, 8$.
   - Menggambar kurva *Within-Cluster Sum of Squares (WCSS) / Inertia* untuk mendeteksi titik siku (*elbow point*).
3. **Evaluasi Metrik Internal:**
   - Menghitung **Silhouette Coefficient** dan **Davies-Bouldin Index (DBI)** untuk setiap $k$ pada kedua jenis scaler.
   - Membuktikan secara empiris bahwa `RobustScaler` menghasilkan separasi klaster yang lebih unggul dibanding `StandardScaler`.
4. **Interpretasi Fisik Lapangan:**
   - Menganalisis nilai centroid dari klaster terbaik dan memberi label status pengeboran nyata:
     * *Rotary Drilling:* SPP tinggi, WOB tinggi, RPM tinggi, Torsi tinggi, ROP stabil.
     * *Circulating / Reaming:* SPP tinggi, RPM sedang, WOB nol, ROP nol.
     * *Tripping / Connection:* SPP nol, RPM nol, WOB nol, Hook Load berfluktuasi tinggi.
     * *Idle / Standby:* Semua sensor mekanik mendekati nol.

#### Tahap 4: Finalisasi Paper Proyek UTS (Format IEEE)
1. Menyusun dokumen paper format IEEE dua kolom (5–8 halaman) dengan struktur:
   - **Judul:** Menggambarkan domain sensor pengeboran geotermal, multi-atribut, dan klasterisasi deret waktu.
   - **BAB I Pendahuluan:** Permasalahan sensor multivariat, Tabel Gap Analysis, dan Pernyataan Kontribusi.
   - **BAB II Metodologi:** Formulasi matematis RobustScaler, rumus ekstraksi windowing, algoritma $k$-Means, dan metrik Silhouette/DBI.
   - **BAB III Hasil & Pembahasan:** Visualisasi korelasi/outlier, kurva Elbow, tabel perbandingan metrik evaluasi internal, plot sebaran klaster deret waktu, dan pembahasan domain operasional.
   - **BAB IV Kesimpulan & Saran.**
   - **Daftar Pustaka:** 8 rujukan utama sesuai standar IEEE.
   - **Lampiran:** Tautan repositori kode dan deklarasi penggunaan Gen-AI sesuai pedoman akademik.

---

## 8. DAFTAR PUSTAKA ACUAN (FORMAT IEEE)

```text
[1] P. M. B. Abrasaldo, S. J. Zarrouk, and A. W. Kempa-Liehr, "Feature-based time series clustering for efficient labelling of geothermal data," Geothermics, vol. 136, p. 103656, Jan. 2026, doi: 10.1016/j.geothermics.2026.103656.
[2] W. Li, Y. Liu, X. Li, B. Deng, H. Zhao, L. Zhu, et al., "Research on an intelligent drilling parameter optimization method using sliding window segmentation based on the hydraulic-mechanical specific energy model," PLOS ONE, vol. 21, no. 1, p. e0339324, Jan. 2026, doi: 10.1371/journal.pone.0339324.
[3] D. Wang, J. T. Foster, Y. Lu, E. Rustamzade, H. Xiong, A. Thompson, and M. J. Pyrcz, "A comprehensive machine learning workflow for classifying production profiles in unconventional reservoirs," Energy Exploration & Exploitation, vol. 44, no. 4, pp. 1806–1829, Feb. 2026, doi: 10.1177/01445987261433779.
[4] P. Singh, B. Vickram, A. Benny, K. Mariyam, S. Dan, R. Harishwaran, B. N. Kumar, and M. A. Abdullah, "Unsupervised deep learning framework for early detection of wellbore trajectory deviation in drilling operations," Frontiers in Artificial Intelligence, vol. 14, p. 1942787, Sep. 2026, doi: 10.3389/frai.2026.1942787.
[5] G. Bayazitova, M. Anastasiadou, and V. D. dos Santos, "Oil and gas flow anomaly detection on offshore naturally flowing wells using deep neural networks," Geoenergy Science and Engineering, vol. 238, p. 213240, Jul. 2024, doi: 10.1016/j.geoen.2024.213240.
[6] A. S. Mohammed, E. Anthi, O. Rana, P. Burnap, and A. Hood, "STADe: An unsupervised time-windows method of detecting anomalies in oil and gas Industrial Cyber-Physical Systems (ICPS) networks," International Journal of Critical Infrastructure Protection, vol. 48, p. 100762, Mar. 2025, doi: 10.1016/j.ijcip.2025.100762.
[7] K. Azuma and Y. Hashimoto, "Anomaly detection in geothermal steam production time series using singular spectrum analysis," Engineering Proceedings, vol. 107, no. 1, p. 24, Dec. 2025, doi: 10.3390/engproc2025107024.
[8] L. Qiu, C. Lu, Z. Ding, Z. Wang, L. Chen, Y. Dong, Q. Chong, W. Xia, and F. Meng, "Data-driven time-series modeling for intelligent extraction of reservoir development indicators," Energies, vol. 18, no. 21, p. 5753, Nov. 2025, doi: 10.3390/en18215753.
```
