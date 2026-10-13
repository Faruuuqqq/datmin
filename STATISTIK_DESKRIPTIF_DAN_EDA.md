# Statistik Deskriptif dan Exploratory Data Analysis (EDA) — Tahap 2 UTS Data Mining

Dokumen ini menyajikan data statistik deskriptif sensor, ketimpangan skala (*scale disparity*), korelasi, dan deteksi pencilan (*outliers*) yang diwajibkan pada Tahap 2 panduan UTS Data Mining.

## 1. Taksonomi Sensor dan Ketimpangan Skala
Data sensor geotermal memiliki perbedaan rentang dan satuan fisik yang sangat lebar (*scale disparity*), yang memvalidasi perlunya standarisasi sebelum klasterisasi:
- Rentang ribuan: Standpipe Pressure (psi), Total Mud Volume (bbl).
- Rentang ratusan: Rotary RPM, Rate of Penetration (ft/hr).
- Rentang puluhan: Weight on Bit (klbs), Hook Load (klbs).
- Rasio skala ekstrim: ROP : Torque mencapai 258.9 : 1.

## 2. Tabel Statistik Deskriptif Sensor (Data Upstream Historis)
Sumber: `reports/03-sintesis/tahap2_final.md` dan `notebooks/final_clustering_outputs06/table1_descriptive.csv` (subset ~200k observasi):

| Sensor | Satuan | Mean | Std | Min | Median | Max | Skewness | Range |
|---|---|---|---|---|---|---|---|---|
| Rate of Penetration (ROP) | ft/hr | 24.91 | 100.46 | 0.00 | 0.00 | 2,860.80 | 37.63 | 2,860.80 |
| Weight on Bit (WOB) | klbs | 7.93 | 11.08 | 0.00 | 0.00 | 66.80 | 1.45 | 66.80 |
| Rotary RPM | RPM | 44.52 | 51.52 | 0.00 | 0.00 | 206.00 | 0.44 | 206.00 |
| Standpipe Pressure (SPP) | psi | 1,209.39 | 1,488.61 | 0.00 | 0.00 | 4,891.00 | 0.55 | 4,891.00 |
| Rotary Torque | kft_lb | 3.51 | 5.37 | 0.00 | 0.00 | 30.60 | 1.83 | 30.60 |
| Hook Load | klbs | 215.11 | 43.18 | 49.30 | 218.40 | 344.80 | -0.74 | 295.50 |
| Flow Out | % | 23.36 | 28.53 | 0.00 | 0.00 | 100.00 | 0.70 | 100.00 |
| Differential Pressure | psi | -692.20 | 1,123.67 | -4,500.00 | 0.00 | 3,745.00 | -1.21 | 8,245.00 |

*Catatan:* Angka skewness tinggi pada ROP (37.63) menunjukkan lonjakan sporadis saat formasi lunak atau penarikan pipa, memvalidasi penggunaan RobustScaler daripada Standard Normal.

## 3. Analisis Korelasi Antar-Sensor (Pearson Correlation Matrix)
Temuan korelasi fisik antar-sensor utama:
- **Sangat Kuat:** SPP ↔ Total Pump Output ($r = 0.925$): Menggambarkan dinamika hidrolika sirkulasi lumpur.
- **Kuat:** Rotary RPM ↔ Rotary Torque ($r = 0.747$): Interaksi mekanis rotasi pahat dan gesekan formasi batuan.
- **Moderat:** RPM ↔ SPP ($r = 0.736$) dan Hook Load ↔ Pump Output ($r = 0.697$).
- **Lemah/Independen:** ROP ↔ WOB ($r = 0.007$): Menunjukkan laju penetrasi tidak berkorelasi linier langsung dengan beban pahat saja pada formasi granit.

## 4. Analisis Outlier dan Noise
- Deteksi pencilan menggunakan metode Interquartile Range (IQR):
  * ROP memiliki proporsi pencilan tertinggi akibat lonjakan non-operasional.
  * SPP dan Torque menunjukkan pencilan pada transisi sambungan pipa (*pipe connection*).
- Anomali Sentinel `-999.25`: Merupakan kode instrumen Pason untuk sensor mati/terputus, wajib dimasking menjadi NaN sebelum analisis distribusi.

## 5. Inventaris Artefak Visualisasi
Tersedia di `notebooks/final_clustering_outputs06/`:
- `fig1_correlation.png`: Heatmap matriks korelasi Pearson.
- `fig2_boxplots.png`: Visualisasi sebaran boxplot deteksi pencilan.
- `fig3_scaling_hist.png`: Perbandingan histogram sebelum dan sesudah standarisasi.

## 6. Catatan Kritis Metodologi Audit
Pada pipeline upstream lama, EDA ini dihitung secara global pada seluruh populasi data. Pada **Pipeline Bersih Baru (v2)**, statistik deskriptif dan fitting scaler wajib diisolasi hanya pada partisi **Train (70%)** untuk mencegah kebocoran informasi (*data leakage*) ke data uji (Test).
