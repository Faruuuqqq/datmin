# Rencana Evaluasi Lintas-Sumur (Cross-Well) 16A v1

> Status: **PLANNING_ONLY / READY_FOR_EXECUTION** — Evaluasi Out-of-Distribution (OOD) transferability model bersih 56-32 ke Well 16A(78)-32. Saat ini `kmeans_fits: 0`, `scaler_fits: 0` pada data 16A (zero fits).

## 1. Konteks & Tujuan Evaluasi
- **Objektif Ilmiah:** Menguji transferabilitas representasi klaster tanpa supervisi dari sumur vertikal (56-32) ke sumur miring/directional (16A) pada formasi geothermal Utah FORGE.
- **Model Dasar (Clean Pipeline):** Menggunakan model terlatih bersih dari Train 70% 56-32 (`MinMaxScaler`, K-Means `k=4`, tumbling window 60s, 0% overlap, 39 fitur). Dilarang keras menggunakan artefak atau model leaked lama.
- **Peran 78B vs 16A:** Well 78B-32 tetap berstatus **LOCKED_NEGATIVE / UNSUITABLE_H1** akibat kegagalan sensor bawaan data mentah (Gas mati 100%, Gamma mati ~60%), yang dijadikan studi kasus empiris kegagalan sensor lapangan pada paper. Well 16A menjadi subjek uji transferabilitas lintas-sumur (Cross-Well / OOD).

## 2. Spesifikasi Data 16A
- **Path Berkas:** `Datmin-new/dataset/dataset-lainnya/16A(78)-32_time_data_1s_intervals_standard.csv`
- **Volume:** ~1,2 GB, 5.827.032 baris data mentah.
- **Format:** RigCloud export (50 kolom, native sampling 1 Hz).

## 3. Empat Tahapan Kerja Eksekusi 16A

### Tahap 1 — Intake & Fingerprint
1. Verifikasi integritas fisik berkas tanpa membaca penuh: hitung byte exact, `sha256sum`, dan `wc -l`.
2. Validasi struktur baris awal (`head -n 5`) dan akhir (`tail -n 5`) untuk mendeteksi header ganda atau truncation.
3. Catat manifest fingerprint ke dokumen audit sebelum pemrosesan hilir.

### Tahap 2 — Pemetaan 13 Kanal & Konversi Satuan
1. Petakan 13 kanal operasional standar 56-32 dari 50 kolom RigCloud 16A:
   - ROP, WOB, RPM, SPP, Torque, HookLoad, FlowIn, FlowOut, MudVol, BlockHeight, SPM1, Gas, Gamma.
2. Lakukan konversi satuan matematis agar ekuivalen dengan skala Pason 56-32:
   - Torque: `ft-lbs` ke `kft-lbs` (faktor `/ 1000`).
   - Tekanan / Standpipe: konversi ke `psi` jika diperlukan.
   - Laju alir / volume: konversi ke `GPM` dan `bbl` sesuai nomenklatur 56-32.
3. Dokumentasikan kamus kolom dan rumus konversi secara eksplisit.

### Tahap 3 — QC Metadata Streaming
1. Pemrosesan berbasis streaming chunked (misal `chunksize=50_000`), dilarang memuat 1,2 GB penuh ke RAM.
2. Parsing timestamp 1 Hz; periksa kontinuitas delta waktu (deteksi gap `dt != 1s`, duplikat, dan urutan mundur).
3. Identifikasi dan mask sentinel values (misal `-999.25`, `SPP <= -900`) menjadi `NaN`.
4. Hitung missingness dan rasio validitas per kanal untuk memastikan sensor kritis (Gas & Gamma) aktif.

### Tahap 4 — Ekstraksi Tumbling Window 60s & Evaluasi Lintas-Sumur
1. Pembentukan tumbling window 60s (stride 60s, 0% overlap) dengan ambang coverage minimal 54/60 detik per kanal.
2. Hitung tepat 39 fitur statistik per window (13 kanal × [mean, pop-std `ddof=0`, endpoint-delta]).
3. **Inference Tanpa Fit Baru:**
   - Gunakan `MinMaxScaler` yang sudah di-fit pada Train 70% 56-32 untuk melakukan `transform` pada matriks 39 fitur 16A (`fit=False`).
   - Lakukan inferensi label klaster menggunakan K-Means `k=4` dari 56-32.
4. Hitung metrik evaluasi transferabilitas: Silhouette score, Davies-Bouldin Index (DBI), cluster occupancy, serta deteksi klaster runtuh/dominan (collapse).

## 4. Invarian & Batasan Eksekusi
- **Zero Fit pada 16A:** Dilarang melakukan fitting scaler atau fitting clustering baru pada dataset 16A; 16A murni data inferensi OOD.
- **Anti-Leakage:** Parameter normalisasi dan centroid klaster murni berasal dari subset Train 56-32.
- **RAM Bounded:** Ekstraksi dan QC wajib streaming/chunked; memory footprint terjaga rendah.
- **Reporting:** Jika klaster runtuh atau metrik buruk, laporkan apa adanya sebagai limitasi transferabilitas geometri sumur (vertikal vs directional).
