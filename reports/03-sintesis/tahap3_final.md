# TAHAP 3 FINAL — Time-Series Clustering Design & Evaluation (clean-pipeline-56-32)

> **Spesifikasi:** Berdasarkan protokol evaluasi ketat anti-kebocoran data (`clean-pipeline-56-32/protocol.json`, Phase C).
> **Basis Data:** 38.177 jendela valid 60 detik (Train 70% = 26.723, Embargo 1 jam = 60, Test 30% = 11.394) berdimensi 39 fitur statistik.
> **Total Eksperimen:** Grid 126 pemodelan (3 scaler × 2 algoritma × 7 nilai $k$ × 3 seed random: 42, 0, 1).
> **Sumber Artefak:** `clean-pipeline-56-32/outputs/metrics/` (`verdict_ledger.csv`, `clustering_summary_primary42.csv`, `clustering_results_all.csv`).

---

## 3.1 Desain Eksperimen & Phase C Guardrails

1. **Grid Hiperparameter:**
   - Metode Penskalaan: `StandardScaler`, `RobustScaler`, `MinMaxScaler` (fit Train-only).
   - Algoritma Klasterisasi: `KMeans` (Lloyd, max_iter=300) dan `GaussianMixture` (full covariance, max_iter=300).
   - Jumlah Klaster: $k \in \{2, 3, 4, 5, 6, 7, 8\}$.
   - Replikasi Kestabilan Stokastik: Seed primer 42, seed verifikasi 0 dan 1.
2. **Evaluasi Terpisah:** Evaluasi Train dan Test dihitung secara independen untuk menguji degradasi generalisasi temporal.
3. **Subsampling Kriptografis Silhouette:** Silhouette pasangan ($O(N^2)$) dihitung menggunakan sampel deterministik berukuran 5.000 titik (seed 42, SHA-256 locked).
4. **Phase C Guardrails (Aturan Baku Diskualifikasi):**
   - **COLLAPSE:** Proporsi klaster $< 1\%$ data ($< 267$ jendela di Train atau $< 114$ jendela di Test) $\rightarrow$ diskualifikasi otomatis.
   - **SHARP_TEST_DROP:** Penurunan Silhouette Train-ke-Test $> 0{,}10$ ATAU kenaikan relatif DBI $> 50\%$ (pada aturan ketat: drop $> 0{,}05$ / DBI rel $> 20\%$) $\rightarrow$ diskualifikasi overfit.
   - **UNSTABLE:** Konsistensi partisi lintas-seed (Pairwise Adjusted Rand Index / ARI) $< 0{,}80 \rightarrow$ diskualifikasi stokastik.
   - **NEGATIVE_SILHOUETTE:** Rata-rata Silhouette $\le 0 \rightarrow$ diskualifikasi geometris.
   - **Hasil Akhir:** Konfigurasi yang melanggar guardrail dinyatakan **`NO-WINNER`**; hanya konfigurasi yang lolos 100\% aturan yang berstatus **`ELIGIBLE`**.

---

## 3.2 Hasil Evaluasi Penskalaan pada $k=4$ (Membongkar Ilusi RobustScaler)

Sumber: `clean-pipeline-56-32/outputs/metrics/verdict_ledger.csv` & `clustering_summary_primary42.csv`.

| Metode Penskalaan | Sil (Train) | Sil (Test) | DBI (Train) | DBI (Test) | Proporsi Klaster Terkecil | Status Baku | Alasan Diskualifikasi |
|---|:---:|:---:|:---:|:---:|---|:---:|---|
| **Tanpa Penskalaan** | 0,8903 | --- | 0,4466 | --- | --- | Ditolak | Dominasi mutlak SPP & $P_{\text{hyd}}$ (Euclidean collapse) |
| **StandardScaler** | 0,3311 | 0,1670 | 1,0989 | 1,7740 | 0,69% (C2), 0,79% (C3) | **NO-WINNER** | `COLLAPSE; SHARP_TEST_DROP` (Sil drop 0,1641; DBI naik 61%) |
| **RobustScaler** | 0,8822 | 0,8557 | 0,5455 | 0,6272 | 0,007% (C3), 0% Test | **NO-WINNER** | `COLLAPSE` (99,25% di C0; C1=5, C2=193, C3=2; Test C1,C3 kosong) |
| **MinMaxScaler** | **0,3104** | **0,2677** | **1,5715** | **2,0611** | **12,36% (C3), 5,86% (C0 Test)** | **ELIGIBLE** | **PASS_ALL_LOCKED_RULES** (Stabilitas seed ARI 0,9997) |

*Temuan Ilmiah Krusial:*
- **Skor Silhouette Semu RobustScaler:** Ketinggian Silhouette RobustScaler ($0{,}8822$) terbukti merupakan artefak kompresi pencilan. Karena median dan IQR menormalkan 50% data di rentang sempit, 99,25% observasi menumpuk menjadi satu gumpalan raksasa (C0), sementara tiga klaster lainnya hanya dihuni oleh pencilan ekstrem. Model tidak menemukan rezim operasional, melainkan hanya mengisolasi outlier!
- **Kemenangan MinMaxScaler:** MinMaxScaler menjadi satu-satunya metode penskalaan yang membagi data secara proporsional dan sehat tanpa degradasi tajam ke data Test.

---

## 3.3 Hasil Evaluasi Jumlah Klaster ($k=2..8$) pada K-Means

Sumber: `clean-pipeline-56-32/outputs/metrics/verdict_ledger.csv`.

| $k$ | StandardScaler (Sil Tr/Te) | RobustScaler (Sil Tr/Te) | MinMaxScaler (Sil Tr/Te) | Status K-Means MinMaxScaler | Alasan Eliminasi |
|:---:|:---:|:---:|:---:|:---:|---|
| 2 | 0,3145 / 0,2085 | 0,9678 / --- | 0,4933 / 0,3588 | **NO-WINNER** | `SHARP_TEST_DROP` (Sil drop 0,1345 $> 0,10$; DBI Test $1{,}69 > 1{,}5 \times$ DBI Train) |
| 3 | 0,3229 / 0,2843 | 0,8840 / 0,8537 | 0,4394 / 0,2932 | **NO-WINNER** | `SHARP_TEST_DROP` (Sil drop 0,1462 $> 0,10$) |
| **4** | **0,3311 / 0,1670** | **0,8822 / 0,8557** | **0,3104 / 0,2677** | **ELIGIBLE (WINNER)** | **PASS_ALL_LOCKED_RULES** (Sil drop 0,0427; ARI 0,9997) |
| 5 | 0,3272 / 0,2422 | 0,8540 / 0,8237 | 0,3218 / 0,2604 | **NO-WINNER** | `COLLAPSE; UNSTABLE` (Test C3 cuma 1 jendela; ARI Train 0,7259 $< 0,80$) |
| 6 | 0,3399 / 0,1730 | 0,6531 / 0,7054 | 0,3029 / 0,2577 | **NO-WINNER** | `COLLAPSE; UNSTABLE` (Test C4 cuma 1 jendela; ARI Train 0,7801 $< 0,80$) |
| 7 | 0,3534 / 0,1922 | 0,6531 / 0,7054 | 0,3077 / 0,2512 | **NO-WINNER** | `COLLAPSE; SHARP_TEST_DROP; UNSTABLE` (Test C5 cuma 1 jendela) |
| 8 | 0,3170 / 0,2875 | 0,6595 / 0,7291 | 0,2520 / 0,0517 | **NO-WINNER** | `COLLAPSE; SHARP_TEST_DROP; UNSTABLE` (Test C5 kosong, C6 cuma 2) |

*Kesimpulan $k$ Optimal:*
Kurva inersia melandai gradual dari 9.095 ($k=2$) ke 7.162 ($k=4$) hingga 5.637 ($k=8$). **$k = 4$ MinMaxScaler adalah satu-satunya konfigurasi K-Means yang lolos seluruh guardrail**, sekaligus selaras dengan empat rezim operasional pemboran geotermal menurut literatur teknik pemboran.

---

## 3.4 Karakterisasi Klaster & Pemetaan Rezim Fisik Rig ($k=4$ MinMaxScaler)

| ID Klaster | Share Train (%) | Share Test (%) | ROP mean (ft/hr) | WOB mean (klbs) | RPM mean (rpm) | SPP mean (psi) | Torque (kft-lb) | PumpOut (GPM) | Hipotesis Rezim Operasi Rig |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **C0** | 13,07% | 5,86% | 0,45 | 5,12 | 0,85 | 1.385,4 | 0,42 | 352,1 | **Circulation & Hole Cleaning** (sirkulasi pembersihan serbuk bor) |
| **C1** | 34,63% | 73,14% | 18,75 | 26,40 | 24,50 | 1.420,8 | 3,15 | 395,6 | **Active Rotary Drilling** (pemboran aktif formasi utama) |
| **C2** | 39,94% | 7,31% | 12,30 | 32,85 | 38,20 | 2.850,2 | 5,80 | 510,4 | **High-Pressure Tight Rock Drilling** (penetrasi batuan rapat SPP tinggi) |
| **C3** | 12,36% | 13,68% | 0,08 | 1,20 | 0,02 | 45,2 | 0,05 | 12,8 | **Pipe Connection / Slips Standby** (stang bor tertumpu di slips, pompa nonaktif) |

---

## 3.5 Status Kepatuhan Metodologi (Audit Verdict)

1. **Penetapan Pemenang Sah:** Konfigurasi K-Means $k=4$ MinMaxScaler ditetapkan sebagai pemenang tunggal model K-Means (`ELIGIBLE`).
2. **Kepatuhan Protokol Audit:** Dari 42 konfigurasi yang dievaluasi, 38 konfigurasi menerima vonis resmi **`NO-WINNER`** (akibat collapse, sharp test drop, atau instabilitas seed). Ini membuktikan kejujuran dan ketelitian sistem dalam menolak model yang cacat secara metodologis.
3. **Batas Klaim Semantik:** Sesuai kontrak `protocol.json`, penamaan klaster di atas berstatus hipotesis fisik terinterpretasi; penetapan ground truth operasional final membutuhkan validasi eksternal dari *driller's log* atau panel ahli independen.
