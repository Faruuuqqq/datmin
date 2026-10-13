# Statistik Deskriptif dan Exploratory Data Analysis (EDA) — Tahap 2 UTS Data Mining

Dokumen ini menyajikan data statistik deskriptif sensor, ketimpangan skala (*scale disparity*), korelasi, dan deteksi pencilan (*outliers*) yang diwajibkan pada Tahap 2 panduan UTS Data Mining.

## 1. Taksonomi Sensor dan Ketimpangan Skala
Data sensor geotermal memiliki perbedaan rentang dan satuan fisik yang sangat lebar (*scale disparity*), yang memvalidasi perlunya standarisasi sebelum klasterisasi:
- Rentang ribuan: Standpipe Pressure (psi), Total Mud Volume (bbl).
- Rentang ratusan: Rotary RPM, Rate of Penetration (ft/hr).
- Rentang puluhan: Weight on Bit (klbs), Hook Load (klbs).
- Rasio skala ekstrim: ROP : Torque mencapai 258.9 : 1.

## 2. Tabel Statistik Deskriptif Sensor Resmi (Train-Only 70%, clean-pipeline-56-32)
Sumber resmi: `clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv` ($N = 26.723$ jendela 60 detik bebas bocor):

| Fitur Kanal | Satuan/Proksi | Mean | Std (ddof=0) | Min | Median | Max | Skewness | Interpretasi Fisik |
|---|---|---|---|---|---|---|---|---|
| ROP_mean | ft/hr | 20,43 | 79,84 | 0,00 | 0,00 | 4.303,23 | 20,98 | Kecepatan penetrasi, ekor pencilan derek |
| WOB_mean | klbs | 24,40 | 23,95 | 0,00 | 24,13 | 172,86 | 1,04 | Beban pada mata bor |
| RPM_mean | rpm | 21,52 | 25,94 | 0,00 | 0,06 | 104,27 | 0,86 | Kecepatan putaran stang bor |
| SPP_mean | psi | 1.603,41 | 1.536,53 | 0,00 | 1.643,31 | 5.131,09 | 0,03 | Tekanan sirkulasi hidraulik lumpur |
| Torque_mean | kft-lb | 3,01 | 3,76 | 0,00 | 0,00 | 25,74 | 1,15 | Torsi kontak pemotongan batuan |
| HookLoad_mean | klbs | 109,63 | 57,12 | 0,00 | 118,45 | 360,46 | 0,24 | Beban gantung traveling block |
| Flow_mean | % | 46,26 | 34,12 | -1,48 | 66,51 | 133,66 | -0,24 | Laju alir balik lumpur pemboran |
| PumpOut_mean | gal/min | 365,01 | 327,00 | 0,00 | 460,82 | 1.757,69 | -0,07 | Debit lumpur pemboran |
| MudVol_mean | barrels | 407,27 | 64,36 | 195,25 | 422,88 | 597,27 | -1,08 | Kapasitas volume tangki |
| BlockHeight_mean | feet | 80,02 | 41,43 | -8,54 | 78,96 | 192,47 | 0,37 | Elevasi ketinggian derek |
| SPM1_mean | spm | 46,51 | 42,38 | 0,00 | 72,68 | 119,43 | -0,11 | Frekuensi kayuhan pompa 1 |
| Hydraulic_P_mean | psi $\cdot$ GPM | $1{,}07 \times 10^6$ | $1{,}06 \times 10^6$ | 0,00 | $8{,}91 \times 10^5$ | $6{,}34 \times 10^6$ | 0,13 | Proksi daya hidraulik sirkulasi |
| Mech_P_mean | kft-lb $\cdot$ rpm | 145,30 | 218,70 | 0,00 | 0,00 | 1.777,36 | 2,08 | Proksi daya mekanik pemotongan |

*Catatan Audit Skala:* Rasio magnitudo Daya Hidraulik ($10^6$) terhadap Torsi ($10^0$) mencapai $> 10^5 : 1$. Ini mewajibkan penskalaan fitur sebelum klasterisasi jarak Euclidean.

## 3. Analisis Korelasi Antar-Sensor Bebas Bocor (Train Pearson Correlation)
Sumber: `clean-pipeline-56-32/outputs/metrics/train_pearson_corr.csv`:
- **Kopel Hidraulik Sangat Kuat:** SPP_mean $\leftrightarrow$ PumpOut_mean ($r = 0,9575$) dan SPP_mean $\leftrightarrow$ Hydraulic_P_mean ($r = 0,9839$).
- **Kopel Rotasi Mekanik Kuat:** RPM_mean $\leftrightarrow$ Torque_mean ($r = 0,8192$) dan RPM_mean $\leftrightarrow$ Mech_P_mean ($r = 0,9041$).
- **Sirkulasi Lumpur:** Flow_mean $\leftrightarrow$ PumpOut_mean ($r = 0,7897$).
- **Independensi Linier:** ROP_mean $\leftrightarrow$ WOB_mean ($r = 0,0838$), menunjukkan hubungan non-linear kompleks pada formasi granit yang menjustifikasi *unsupervised clustering*.

## 4. Analisis Outlier, Sentinel, dan Rekayasa Jendela
- **Anomali Sentinel $-999{,}25$:** Masked to NaN (tidak diimputasi rata-rata).
- **Eliminasi Anomali SPP:** Baris SPP $\le -900$ psi (29.503 baris) dibuang pada tahap pembersihan chunk.
- **Pemisahan Segmen Waktu:** Setiap celah waktu $\ne +1$ detik memicu reset batas segmen (28 segmen kontinu, 27 reset).
- **Jendela Tumbling 60 Detik:** Stride 60 detik (0% overlap, anti-leakage). Threshold kelengkapan $\ge 54/60$ detik valid menyaring **38.177 jendela valid**.

## 5. Inventaris Artefak Visualisasi Resmi
Tersedia di `clean-pipeline-56-32/outputs/figures/`:
- `eda_correlation_heatmap.png`: Heatmap korelasi Pearson 39 fitur partisi Train.
- `eda_scale_disparity_boxplots.png`: Boxplot disparitas skala antar kanal sensor (symlog scale).
- `eda_scaler_comparison_distributions.png`: Perbandingan histogram distribusi sebelum dan sesudah standarisasi (Standard, Robust, MinMax).
- `cluster_kmeans_inertia_elbow.png`: Kurva inersia Elbow K-Means Train ($k=2..8$).
- `cluster_silhouette_train_vs_test.png` & `cluster_dbi_train_vs_test.png`: Perbandingan metrik Train vs Test multi-panel.

## 6. Audit Kesimpulan Penskalaan (Phase C Ledger)
Pada evaluasi klasterisasi Train vs Test:
- **RobustScaler:** Terdiskualifikasi sebagai **`NO-WINNER`** akibat *Cluster Collapse* katastropik (99,25% data menumpuk di C0). Silhouette tinggi ($0{,}8822$) terbukti merupakan ilusi geometris isolasi pencilan.
- **StandardScaler:** Terdiskualifikasi sebagai **`NO-WINNER`** akibat *Sharp Test Drop* (Silhouette anjlok $> 0{,}16$) dan kolaps pada C2/C3 ($<1\%$).
- **MinMaxScaler:** Ditetapkan sebagai satu-satunya pemenang resmi (**`ELIGIBLE`**) pada K-Means $k=4$, menghasilkan partisi sehat (proporsi min 12,36%), Silhouette stabil (Train 0,3104 / Test 0,2677), DBI (Train 1,5715 / Test 2,0611), dan kestabilan stokastik ARI 0,9997.

