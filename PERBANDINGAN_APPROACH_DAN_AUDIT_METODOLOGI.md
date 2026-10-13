# Perbandingan pendekatan dan audit metodologi

> **Tujuan dokumen.** Dokumen ini membandingkan secara akademis pendekatan yang terekam pada repo `datmin/` dengan rancangan pipeline audit baru untuk Well 56-32. Kritik diarahkan pada validitas inferensi dan reproduksibilitas, **bukan** pada individu atau niat pembuat repo.
>
> **Batas bukti dan status.** Temuan upstream di bawah bersumber dari kode, notebook, tabel, dan laporan yang tersedia pada tree ini. Pipeline bersih Rafif (`clean-pipeline-56-32/`) **sudah tereksekusi**: fase A 38.177 window valid, fase B train 26.723 + embargo 3600 s + test 11.394 dengan `fit_rows == 26723`, fase C 126 run dengan 42 verdict (`NO-WINNER` 38, `ELIGIBLE` 4) — lihat `outputs/manifests/phase_{a,b,c}_manifest.json` dan `outputs/metrics/verdict_ledger.csv`. Dokumen ini tidak me-rerun notebook upstream; istilah *leakage*, *collapse*, dan *klaim rapuh* dipakai sebagai diagnosis metodologis berdasarkan implementasi/bukti yang tersedia, bukan vonis universal atas semua kemungkinan rerun.

## 1. Ringkasan eksekutif

Repo upstream memiliki kekuatan yang patut diapresiasi: eksplorasi beberapa representasi (point dan window), pembandingan `StandardScaler`/`RobustScaler`, metrik internal, serta upaya menghubungkan pusat klaster dengan konteks operasi rig. Namun, kesimpulan ilmiah tidak dapat hanya mengikuti tingginya Silhouette atau rendahnya Davies–Bouldin Index (DBI). Untuk data deret waktu sensor yang sangat berkorelasi, validitas juga bergantung pada unit analisis yang independen, batas waktu yang terjaga, isolasi transformasi, integritas segmen, keseimbangan okupansi, kestabilan lintas-split, dan validasi eksternal atas makna domain.

Audit menemukan enam kerentanan utama pada jalur upstream:

1. **Window 60 detik dengan stride 30 detik** membuat window bertetangga berbagi 30 dari 60 observasi (50%). Jika window yang saling tumpang-tindih dipakai untuk fit dan evaluasi tanpa pemisahan waktu/embargo, skor evaluasi tidak dapat dibaca sebagai bukti generalisasi temporal yang independen.
2. **Scaler di-fit pada seluruh sampel yang dievaluasi**, termasuk pada jalur perbandingan dan final. Ini membiarkan statistik skala dari data evaluasi ikut membentuk representasinya sendiri.
3. **`-999.25 → NaN → dropna()` tanpa reset gap** menghapus baris lalu menyambungkan kembali indeks tersisa; pembentukan window berbasis baris dapat melintasi interval waktu yang tidak lagi kontinu.
4. **Cluster collapse/ketimpangan okupansi** sangat kuat pada hasil `k=4`: C0 95,40%, C1 0,71%, C2 0,71%, C3 3,17%. Geometri seperti ini tidak cukup mendukung narasi empat rezim yang sama-sama terpetakan dengan baik.
5. **`BEST_K = 4` ditetapkan oleh prior empat rezim**, bukan oleh aturan seleksi yang dibekukan dan diuji kestabilannya pada split terpisah.
6. **Nama rezim fisik** diberikan tanpa driller log, daily rig report, atau penilaian ahli independen yang dibutakan; centroid statistik bukan ground truth operasional.

Karena alasan itu, pendekatan audit baru memilih arsitektur yang lebih konservatif: window tumbling, split kronologis dengan embargo, scaler train-only, reset pada gap, coverage gate, evaluasi Train/Test terpisah, pelaporan okupansi, dan kemungkinan keputusan **`NO-WINNER`**. Pendekatan ini tidak menjamin hasil yang lebih tinggi; justru ia menerima kemungkinan bahwa tidak ada kandidat yang layak dipromosikan.

## 2. Unit pembanding, sumber, dan cara membaca dokumen

| Komponen | Repo `datmin/` (upstream) | Pipeline audit baru |
|---|---|---|
| Tujuan umum | Clustering sensor pemboran geothermal tanpa label; membandingkan scaler dan representasi point/window. | Menguji kandidat clustering secara leakage-safe pada deret waktu 56-32, dengan hak eksplisit untuk menyimpulkan `NO-WINNER`. |
| Bukti yang dipakai di dokumen ini | Implementasi `src/kaggle_utils.py`, `src/run_clustering_eval.py`, laporan Tahap 3, dan CSV occupancy yang tersedia. | `clean-pipeline-56-32/protocol.json`, `clean-pipeline-56-32/scripts/prepare_windows.py`, `clean-pipeline-56-32/scripts/split_scale.py`, manifest fase A/B/C, dan metrik `train_*` di `clean-pipeline-56-32/outputs/`. |
| Status hasil | Angka/artefak upstream dibaca sebagai klaim yang terdokumentasi, belum direplikasi ulang di dokumen ini. | Pipeline bersih Rafif sudah tereksekusi (38.177 window valid; train 26.723 + embargo 3600 s + test 11.394; `fit_rows == 26723`); detail EDA train-only ada di dokumen STATISTIK. |
| Prinsip interpretasi | Metrik internal menjelaskan geometri sampel yang dianalisis. | Metrik internal perlu lolos guard split, occupancy, dan stabilitas sebelum dipakai untuk seleksi. |
| Statistik deskriptif & EDA | Arsip upstream: 8 sensor global pada subset ~200k (lihat `reports/03-sintesis/tahap2_final.md`; bukan isi dokumen STATISTIK saat ini). | Dokumen [`STATISTIK_DESKRIPTIF_DAN_EDA.md`](STATISTIK_DESKRIPTIF_DAN_EDA.md) saat ini = **hasil Rafif**: 13 channel → 39 fitur window tumbling 60/60, diisolasi pada Train (70%) ber-embargo. |

**Rincian EDA saat ini.** Dokumen [`STATISTIK_DESKRIPTIF_DAN_EDA.md`](STATISTIK_DESKRIPTIF_DAN_EDA.md) **bukan lagi EDA upstream 8-sensor**; ia adalah EDA train-only pipeline bersih Rafif (taksonomi 13 channel, tabel 39 fitur n=26.723, korelasi Pearson+Spearman level window, attrition fase A, isolasi Train+embargo fase B, artefak `eda_*`). Angka upstream lama (8 sensor, Diff Press, rasio 258.9:1, r=0.925/0.747) hanya tersisa sebagai arsip di `reports/03-sintesis/tahap2_final.md` dan tidak boleh dibaca sebagai isi dokumen STATISTIK.

**Catatan tentang istilah.** *Train* adalah bagian awal kronologis yang diizinkan untuk fit dan seleksi; *Test* adalah bagian akhir yang hanya dipakai untuk evaluasi terpisah. *Embargo* adalah interval buffer yang dikeluarkan dari keduanya agar dukungan waktu/window tidak berbagi batas. *Coverage gate* adalah syarat minimum observasi valid per kanal sebelum window diterima.

## 3. Rekonstruksi pendekatan upstream yang tersedia

Pada jalur final upstream, skrip menyatakan empat skenario: point atau window 60 s/stride 30 s, masing-masing dengan `StandardScaler` atau `RobustScaler`; K-Means dipindai pada `k=2..8` dengan `n_init=10` dan seed 42. Window menyusun mean, simpangan baku, dan delta per sensor. Laporan Tahap 3 lalu menetapkan `BEST_SCENARIO = 'window60-robust'` dan `BEST_K = 4`.

Secara spesifik, bukti kode menunjukkan pola berikut:

- `build_windows()` menjalankan `range(0, len(df) - window + 1, step)` dengan `window=60`, `step=30`, setelah pengurutan waktu saja; tidak ada pemeriksaan selisih timestamp atau reset segmen ([`src/kaggle_utils.py:106-123`](src/kaggle_utils.py#L106-L123)).
- `clean_frame()` mengganti sentinel dengan `NaN`, kemudian melakukan `dropna(subset=SENSOR_8).reset_index(drop=True)` ([`src/kaggle_utils.py:96-103`](src/kaggle_utils.py#L96-L103)).
- Jalur temporal di evaluator menerapkan `uw.replace(-999.25, np.nan).dropna().reset_index(drop=True)`, lalu membuat window 60/30 dan memanggil `RobustScaler().fit_transform(...)` pada data yang kemudian sekaligus diberi label dan dinilai ([`src/run_clustering_eval.py:162-192`](src/run_clustering_eval.py#L162-L192)).
- Jalur final kembali memilih sampel, membuat seluruh skenario, lalu memanggil `sc.fit_transform(X)` sebelum K-Means dan metrik pada sampel yang sama ([`src/run_clustering_eval.py:211-269`](src/run_clustering_eval.py#L211-L269)). Refit final juga memakai `scb.fit_transform(Xb)` atas seluruh `Xb` ([`src/run_clustering_eval.py:299-307`](src/run_clustering_eval.py#L299-L307)).
- Laporan upstream sendiri menulis bahwa `BEST_K=4` berbasis prior empat rezim operasi, bukan semata kurva metrik ([`reports/03-sintesis/tahap3_final.md:43-45`](reports/03-sintesis/tahap3_final.md#L43-L45)).

Temuan ini tidak mengatakan bahwa K-Means, RobustScaler, atau summary feature selalu salah. Ia menjelaskan mengapa skor yang dihasilkan dalam desain tersebut tidak cukup untuk mendukung klaim validasi temporal, pilihan model final, atau identifikasi rezim fisik.

## 4. Critical flaws: bukti, mekanisme, dan dampak

### 4.1 Leakage temporal dari stride 30 detik

**Bukti yang tersedia.** Upstream membangun window berdurasi 60 detik setiap 30 detik. Window pada waktu `t` dan `t+30` berbagi 30 observasi mentah; tingkat overlap adalah `(60 - 30) / 60 = 50%`. Implementasi mengiterasi indeks baris pada stride tersebut tanpa audit split atau embargo ([`src/kaggle_utils.py:106-123`](src/kaggle_utils.py#L106-L123); [`src/run_clustering_eval.py:231-243`](src/run_clustering_eval.py#L231-L243)).

**Mengapa ini masalah.** Dua sampel evaluasi yang berbagi separuh input bukan realisasi temporal yang independen. Bila satu window mempengaruhi fit/scaler atau berada dekat sekali dengan sampel evaluasi, representasi yang dievaluasi mengandung dukungan mentah yang sama atau sangat berkorelasi. Skor Silhouette/DBI dapat tetap dihitung dengan benar secara komputasional, tetapi inferensi “model bekerja pada waktu yang belum terlihat” menjadi terlalu optimistis.

**Batas klaim yang tepat.** Overlap tidak otomatis membatalkan analisis deskriptif dalam satu segmen. Namun, overlap **harus** diaudit jika hasil dipakai untuk klaim generalisasi, pemilihan pemenang, atau perbandingan Train/Test. Dalam tree yang diperiksa, jalur final melakukan fit/evaluasi full-span tanpa split temporal eksplisit; maka klaim validasi temporal tidak didukung oleh bukti ini.

**Perbaikan rancangan.** Gunakan tumbling window 60 s/stride 60 s, atau jika overlap diperlukan untuk pertanyaan lain, tetapkan split pada unit episode/dukungan mentah dan purge semua window yang berbagi observasi lintas batas. Embargo tidak boleh sekadar angka dekoratif: harus memiliki manifest timestamp/window-ID dan audit overlap.

### 4.2 Leakage dari scaler yang di-fit pada populasi evaluasi

**Bukti yang tersedia.** Pada upstream, `fit_transform` dipanggil atas matriks `X` yang kemudian dipakai untuk K-Means dan metrik dalam jalur sama: `sc.fit_transform(X)` pada grid final, serta `scb.fit_transform(Xb)` pada refit ([`src/run_clustering_eval.py:255-269`](src/run_clustering_eval.py#L255-L269), [`:299-307`](src/run_clustering_eval.py#L299-L307)). Jalur temporal juga memanggil `RobustScaler().fit_transform(...)` sebelum evaluasi point/window ([`src/run_clustering_eval.py:184-192`](src/run_clustering_eval.py#L184-L192)).

**Mengapa ini masalah.** `StandardScaler` memakai rerata/simpangan baku, dan `RobustScaler` memakai statistik kuantil/IQR. Jika statistik tersebut dipelajari dari data yang kelak dianggap Test/evaluasi, informasi distribusi Test telah masuk ke representasi Train. Dengan data nonstasioner, kebocoran ini dapat meredam pergeseran skala yang justru harus dihadapi oleh model pada masa depan.

**Nuansa penting.** Jika tujuan semata visualisasi/segmentasi deskriptif atas satu kumpulan tertutup, fit pada seluruh data dapat dinyatakan sebagai transformasi transduktif—tetapi hasilnya tidak boleh disajikan sebagai evaluasi generalisasi. Kritik di sini muncul ketika skor yang sama dipakai untuk menyebut pemenang atau hasil final.

**Perbaikan rancangan.** Split kronologis dilakukan terlebih dahulu. Fit scaler hanya pada fitur Train; gunakan objek scaler yang sama untuk `transform(Train)` dan `transform(Test)`. Catat jumlah baris saat fit dan buktikan bahwa `fit_rows == n_train`; Test/embargo tidak boleh memanggil `fit` maupun `fit_transform`.

### 4.3 Sentinel/missing dan putusnya kontinuitas waktu

**Bukti yang tersedia.** `clean_frame()` dan jalur evaluator mengganti `-999.25` menjadi `NaN`, kemudian menghapus baris dengan `dropna()` dan mereset indeks ([`src/kaggle_utils.py:96-103`](src/kaggle_utils.py#L96-L103); [`src/run_clustering_eval.py:163-180`](src/run_clustering_eval.py#L163-L180)). Setelah itu, pembentukan window mengambil irisan baris berurutan, bukan memverifikasi bahwa timestamp antarbaris berselisih tepat satu detik.

**Mekanisme kegagalan.** Misalkan observasi pukul 10:00:20 hilang karena sentinel. Setelah `dropna`, baris 10:00:19 dan 10:00:21 menjadi bertetangga. Window sepanjang 60 **baris** masih dapat terlihat penuh, tetapi sesungguhnya tidak merepresentasikan 60 detik kontinu dan delta `last-first` melompati observasi yang hilang. Jika banyak missing terjadi, window dapat menyatukan beberapa gap tanpa jejak eksplisit.

**Dampak metodologis.** Fitur mean/std/delta mengasumsikan dukungan temporal yang konsisten. Ketika asumsi tersebut rusak, variasi yang dipelajari dapat mencampurkan perubahan proses dan artefak hilangnya data. Penghapusan baris juga mengubah jarak antar-window serta membuat perhitungan “stride 30 detik” sebenarnya menjadi 30 baris tersisa, bukan niscaya 30 detik nyata.

**Perbaikan rancangan.** Sentinel di-mask per kanal sebagai `NaN`; baris yang dibuang karena filter instrumen (misalnya SPP) dan semua interval timestamp `!= +1s` memicu **gap reset**. Window hanya dibangun di dalam segmen kontinu. Sebelum agregasi, setiap kanal harus memenuhi coverage minimal 54 dari 60 detik; tail segmen dibuang dan tidak boleh disambung ke segmen sesudah gap.

### 4.4 Cluster collapse dan ketimpangan okupansi

**Bukti yang tersedia.** CSV occupancy upstream mencatat C0 `0.954`, C3 `0.0317`, C2 `0.0071`, C1 `0.0071` ([`notebooks/final_clustering_outputs06/table6_cluster_share.csv:1-5`](notebooks/final_clustering_outputs06/table6_cluster_share.csv#L1-L5)). Laporan Tahap 3 menyatakan angka yang sama dan memberi empat interpretasi fisik ([`tahap3_final.md:47-56`](reports/03-sintesis/tahap3_final.md#L47-L56)).

**Mengapa ini masalah.** Dominasi C0 95,40% tidak membuktikan adanya empat rezim berbeda yang termodelkan dengan kualitas serupa. C1 dan C2 masing-masing hanya 0,71%; pada 60.000 sampel ini kira-kira 426 sampel per klaster, dan dukungan efektif bahkan dapat lebih kecil bila sampel berkorelasi/overlap. Silhouette tinggi masih mungkin bila mayoritas padat dan minoritas ekstrem/terisolasi; metrik internal tidak memberi jaminan bahwa minoritas stabil, berulang lintas-seed, mewakili episode yang bermakna, atau bukan ekor/noise/artifak.

**Apa yang tidak boleh disimpulkan.** Ketimpangan sendiri tidak membuktikan bahwa data rig “salah”—operasi pemboran memang dapat tidak seimbang. Yang tidak sah adalah melompat dari proporsi sangat timpang menuju klaim bahwa semua klaster merupakan rezim operasional yang tervalidasi. Untuk itu diperlukan setidaknya occupancy per split/blok, dukungan episode/durasi, stabilitas assignment/centroid, dan bukti eksternal.

**Perbaikan rancangan.** Laporkan occupancy setiap kandidat pada Train dan Test, beserta klaster kosong, minimum/maksimum share, durasi/episode pendukung, dan stabilitas lintas seed/blok. Konfigurasi yang runtuh atau melanggar guard tidak “diselamatkan” oleh skor rata-rata; ia diberi status **`NO-WINNER`**.

### 4.5 `BEST_K = 4` yang dipaksakan oleh prior domain

**Bukti yang tersedia.** Upstream memindai `k=2..8`, tetapi laporan menyatakan secara eksplisit bahwa `BEST_K=4` dipilih karena empat rezim operasi rig ([`tahap3_final.md:31-45`](reports/03-sintesis/tahap3_final.md#L31-L45)). Kode kemudian mengunci `BEST_SCENARIO='window60-robust'` dan `BEST_K=4` untuk refit ([`src/run_clustering_eval.py:299-306`](src/run_clustering_eval.py#L299-L306)).

**Mengapa ini rapuh.** Prior domain boleh menjadi hipotesis atau batas kandidat, tetapi bukan pengganti protokol seleksi. Pada clustering tanpa label, banyak `k` dapat memberi metrik yang berdekatan atau berbeda menurut metrik. Memilih `k` untuk mencocokkan empat kategori yang diharapkan menimbulkan *confirmation bias*: struktur data dipaksa mengikuti taksonomi awal, lalu hasil yang telah dipilih digunakan untuk mendukung taksonomi itu.

**Bukti yang dibutuhkan sebelum menyebut “best”.** Aturan harus dibekukan sebelum hasil dibaca: kandidat, metric primer, tie-break, skala split, seed, unit resampling, ambang occupancy, dan ambang stabilitas. Kandidat harus menunjukkan performa dan profil yang memadai secara konsisten pada development blocks; Test tidak dipakai untuk mencari `k`. Jika aturan tidak menghasilkan kandidat admissible, keluaran yang valid adalah **`NO-WINNER`**, bukan pemilihan post-hoc.

### 4.6 Overclaiming “rezim fisik pemboran” tanpa validasi lapangan

**Bukti yang tersedia.** Laporan menyematkan label seperti *Active Rotary Drilling*, *High-Pressure Resistant Zone Drilling*, dan *Circulation & Hole Cleaning*, lalu menyatakan “Physics Gate Passed” ([`tahap3_final.md:47-58`](reports/03-sintesis/tahap3_final.md#L47-L58)). Bukti yang tersedia pada jalur ini adalah centroid dan aturan interpretasi internal; tidak terlihat driller log, daily rig report, catatan operasi bertimestamp, ataupun penilaian independen yang menghubungkan episode klaster dengan keadaan rig.

**Mengapa klaim tidak dapat diturunkan dari centroid saja.** Klaster adalah partisi statistik berdasarkan fitur yang dipilih, transformasi, jarak, dan `k`. Centroid dengan ROP/RPM/pompa tertentu dapat konsisten dengan beberapa keadaan operasi; ia tidak membuktikan penyebab, maksud operator, kondisi batuan, atau kejadian rig. Pemetaan satu-ke-satu pasca-hoc juga rentan terhadap label yang dipilih setelah melihat pusat klaster.

**Perbaikan rancangan.** Nama keluaran sementara harus `C0..Ck`. Klaim rezim fisik baru mungkin setelah ada protokol validasi yang membekukan episode, unit/denominator, aturan pencocokan, dan metrik agreement sebelum label eksternal dibuka; kemudian lakukan pencocokan dengan driller log atau panel ahli independen, idealnya dengan pelabelan buta terhadap ID klaster. Laporkan cakupan, ketidaksepakatan, dan keterbatasan—bukan hanya kasus yang cocok.

## 5. Mengapa pipeline audit baru berbeda

Perbedaan bukan soal “lebih banyak preprocessing” atau mengejar skor lebih tinggi. Ia memindahkan fokus dari kecocokan geometri satu sampel menuju **ketertelusuran batas informasi** dan **kejujuran keputusan**.

### 5.1 Kontrak arsitektur bersih

1. **Tumbling window 60 s, stride 60 s.** Setiap observasi mentah mendukung maksimal satu window yang diterima; overlap nominal 0%. Ini menyederhanakan audit keanggotaan serta menghindari kebocoran langsung antar-window bertetangga.
2. **Partisi kronologis 70:30 dengan embargo minimal satu jam.** 70% window awal dipakai sebagai Train, 30% akhir sebagai Test; buffer 3.600 detik tidak masuk keduanya. Window tidak boleh melintasi batas split/embargo.
3. **Scaler train-only.** Kandidat scaler di-fit pada Train saja. Test hanya ditransformasi menggunakan objek yang telah di-fit pada Train.
4. **Gap reset dan coverage gate.** Sentinel menjadi `NaN`, tetapi tidak diizinkan menghilangkan batas waktu secara diam-diam. Setiap timestamp tidak tepat +1 detik memutus segmen; window perlu minimal 54/60 observasi valid per kanal.
5. **Evaluasi terpisah dan transparan.** Silhouette/DBI, occupancy, metrik tak-terdefinisi, serta collapse dicatat terpisah untuk Train dan Test. Hasil Test tidak memilih model/scaler.
6. **`NO-WINNER` sebagai hasil sah.** Ketidakstabilan, degenerasi, share ekstrem, metrik invalid, atau pelanggaran guard mengalahkan dorongan untuk menetapkan pemenang.
7. **Label statistik terlebih dahulu.** Klaster diberi kode `C0..Ck`; interpretasi fisik ditunda sampai validasi eksternal tersedia.

Kontrak tersebut didefinisikan di [`clean-pipeline-56-32/protocol.json`](clean-pipeline-56-32/protocol.json) dan **sudah tereksekusi**: 38.177 window valid (train 26.723 + embargo 3600 s + test 11.394), scaler `fit_rows == 26723`, grid 126 run (3 scaler × 2 algoritma × 7 k × 3 seed) dengan 42 verdict (`NO-WINNER` 38, `ELIGIBLE` 4) — lihat [`phase_a_manifest.json`](clean-pipeline-56-32/outputs/manifests/phase_a_manifest.json), [`phase_b_manifest.json`](clean-pipeline-56-32/outputs/manifests/phase_b_manifest.json), [`phase_c_manifest.json`](clean-pipeline-56-32/outputs/manifests/phase_c_manifest.json), dan [`verdict_ledger.csv`](clean-pipeline-56-32/outputs/metrics/verdict_ledger.csv).

## 6. Matriks komparasi metodologis

| Parameter | Repo Faruq (`datmin/`) | Pipeline Audit Baru | Dampak Metodologis |
|---|---|---|---|
| Unit window | Window 60 s, stride 30 s; 50% overlap antar-window. | Tumbling 60 s, stride 60 s; target 0% overlap. | Mengurangi ketergantungan langsung dan memudahkan audit support antarpartisi. |
| Integritas waktu | Sort timestamp, tetapi window berindeks baris setelah `dropna`; reset gap tidak terlihat pada fungsi window. | Reset pada gap/duplikat/waktu mundur; tidak ada window melintasi segmen. | Mencegah fitur waktu merangkum interval yang tidak kontinu. |
| Missing/sentinel | `-999.25 → NaN → dropna()` untuk kanal model. | Mask sentinel per kanal, reset gap, lalu coverage gate. | Missing tidak berubah menjadi kontinuitas semu setelah indeks direset. |
| Coverage | Tidak ada ambang coverage per kanal pada window yang ditunjukkan. | Minimal 54/60 detik valid per kanal. | Membatasi window dengan dukungan data terlalu tipis tanpa mengimputasi diam-diam. |
| Fitur | 7/8 sensor × mean/std/delta; konfigurasi berganti antara jalur. | 13 kanal × mean/pop-std/delta = 39 fitur, dengan kontrak eksplisit. | Skema fitur dan attrition lebih mudah ditelusuri; tetap perlu ablation/justifikasi di masa depan. |
| Sampling/split | Full-span/subsampel dan fit/evaluasi satu populasi pada jalur final yang diperiksa. | 70% awal Train, embargo ≥1 jam, 30% akhir Test. | Menguji perpindahan waktu dan memisahkan evaluasi dari fit. |
| Scaling | `fit_transform` pada matriks yang juga dikelompokkan/dinilai. | `fit` hanya pada Train; Test hanya `transform`. | Mencegah statistik Test masuk ke representasi fit. |
| Seleksi model | `k=2..8`, tetapi `BEST_K=4` dikaitkan dengan prior empat rezim. | Grid `k=2..8` tereksekusi dengan guard terkunci (collapse <1%, rentang Silhouette, ARI); Test bukan alat seleksi; 38 `NO-WINNER` vs 4 `ELIGIBLE` pada seed primer 42. | Mengurangi pemilihan pasca-hoc dan confirmation bias. |
| Model yang dibandingkan | K-Means dengan Standard/Robust dan point/window di jalur utama. | K-Means dan GMM tereksekusi pada Train untuk `k=2..8` × 3 scaler (126 run). | Perbandingan hanya bermakna bila budget, split, dan guard sama; lihat `verdict_ledger.csv`. |
| Evaluasi | Silhouette/DBI internal; nilai dihitung pada sampel yang sama dengan label fit di jalur final. | Metrik Train/Test terpisah tereksekusi (Silhouette sampel 5.000, DBI, occupancy, collapse), dengan alasan NA/collapse dicatat di `clustering_results_all.csv`. | Memisahkan diagnosis fit dari indikasi generalisasi temporal. |
| Occupancy/collapse | Share final dipublikasikan, tetapi ketimpangan 95,40/0,71/0,71/3,17% tetap dipromosikan sebagai rezim. | Share/empty/collapse dilaporkan per kandidat dan menjadi guard (`primary_collapse_runs` 27 pada seed primer); pelanggar = `NO-WINNER`. | Mencegah metrik internal menjadi alasan untuk menutupi partisi sepele. |
| Stabilitas | Seed 42 digunakan; bukti stabilitas lintas-split/episode tidak tersedia pada jalur yang diperiksa. | Diuji lintas 3 seed (42/0/1) via rentang Silhouette/DBI dan ARI pairwise; `unstable` = `NO-WINNER`. | Menguji apakah pola bertahan, bukan hanya muncul sekali. |
| Nama klaster | Pemetaan langsung ke empat rezim fisik dan “physics gate”. | `C0..Ck` terlebih dahulu. | Menjaga perbedaan antara struktur statistik dan keadaan operasi nyata. |
| Validasi domain | Tidak ada driller log/panel independen yang ditautkan pada bukti ini. | Wajib log operasi atau validasi ahli independen sebelum klaim rezim. | Menutup celah antara centroid numerik dan ground truth lapangan. |
| Hasil ketika bukti gagal | Narasi “best/final/physics passed” tersedia pada laporan. | `NO-WINNER` (38/42 verdict primer) atau `ELIGIBLE` (4/42) adalah status tereksekusi di `verdict_ledger.csv`. | Mengurangi overclaim dan menjaga keputusan dapat diaudit. |

## 7. Apa yang tetap bernilai dari repo upstream

Evaluasi yang konstruktif tidak perlu menyamakan semua komponen dengan kegagalan. Beberapa elemen upstream tetap dapat dipakai sebagai bahan hipotesis atau baseline deskriptif setelah batasnya dinyatakan:

- perbandingan StandardScaler dan RobustScaler memberi hipotesis bahwa distribusi/outlier memengaruhi geometri K-Means;
- perbandingan point dan window menegaskan adanya trade-off antara pemisahan internal dan *chattering* label;
- feature summary mean/std/delta adalah representasi ringkas yang dapat diuji ulang dengan segmen dan split yang benar;
- tabel centroid serta occupancy adalah artefak diagnostik yang berguna, terutama karena memperlihatkan ketimpangan yang perlu diuji, bukan disembunyikan;
- prior domain empat aktivitas rig dapat diperlakukan sebagai hipotesis **validasi** atau daftar kandidat penilaian, bukan sebagai bukti jumlah klaster.

Dengan demikian, rekomendasi audit bukan membuang pekerjaan lama, melainkan mengubah posisinya dari “hasil final tervalidasi” menjadi **baseline eksploratif yang perlu dievaluasi ulang di bawah protokol yang lebih ketat**.

## 8. Batas kesimpulan dan langkah validasi yang diperlukan

Dokumen ini tidak menyatakan bahwa pipeline audit baru sudah unggul, sudah bebas seluruh bias, atau sudah siap dipublikasikan. Rancangan audit sendiri masih membutuhkan bukti eksekusi yang dapat ditelusuri: manifest input/split/window, hash, attrition, log perintah/exit, hasil Train/Test, occupancy, dan review independen.

Sebelum klaim ilmiah dinaikkan, bukti minimal berikut diperlukan:

1. manifest raw dan output dengan hash, schema, rentang waktu, serta attrition setiap tahap;
2. audit window-ID/timestamp yang membuktikan tidak ada support mentah melintasi gap, split, atau embargo;
3. bukti fit scaler dan model yang menunjukkan hanya Train dipakai untuk fit/seleksi;
4. tabel kandidat yang memisahkan Train/Test, seed/blok, occupancy, collapse, dan metrik `NaN` beserta alasannya;
5. aturan seleksi yang dibekukan sebelum hasil dibaca, termasuk kondisi eksplisit `NO-WINNER`;
6. protokol validasi domain dengan driller log atau ahli independen, denominator/coverage yang jelas, dan pelaporan disagreement;
7. review independen atas artefak stabil sebelum menyebut pemenang, rezim fisik, atau generalisasi.

## 9. Referensi bukti lokal utama

- [`STATISTIK_DESKRIPTIF_DAN_EDA.md`](STATISTIK_DESKRIPTIF_DAN_EDA.md): EDA train-only pipeline Rafif (13 channel → 39 fitur, n=26.723, Pearson+Spearman, attrition fase A, embargo fase B).
- [`clean-pipeline-56-32/protocol.json`](clean-pipeline-56-32/protocol.json): kontrak tumbling 60/60, 13 channel, split 70:30 + embargo ≥1 jam, scaler train-only.
- [`clean-pipeline-56-32/scripts/prepare_windows.py`](clean-pipeline-56-32/scripts/prepare_windows.py): definisi 11 raw + 2 proxy (`Hydraulic_P`, `Mech_P`), fitur mean/std/delta, gap reset, coverage gate 54/60.
- [`clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv`](clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv): sumber tabel 39 fitur Train.
- [`clean-pipeline-56-32/outputs/metrics/train_pearson_corr.csv`](clean-pipeline-56-32/outputs/metrics/train_pearson_corr.csv) dan [`clean-pipeline-56-32/outputs/metrics/train_spearman_corr.csv`](clean-pipeline-56-32/outputs/metrics/train_spearman_corr.csv): matriks korelasi 39×39 Train.
- [`clean-pipeline-56-32/outputs/manifests/phase_a_manifest.json`](clean-pipeline-56-32/outputs/manifests/phase_a_manifest.json) dan [`clean-pipeline-56-32/outputs/manifests/phase_b_manifest.json`](clean-pipeline-56-32/outputs/manifests/phase_b_manifest.json): bukti attrition, split, embargo, hash, dan `fit_rows == 26723`.
- [`src/kaggle_utils.py`](src/kaggle_utils.py): implementasi `clean_frame()` dan `build_windows()` upstream yang menjadi dasar diagnosis sentinel/gap/stride.
- [`src/run_clustering_eval.py`](src/run_clustering_eval.py): implementasi scaler, windowing, grid metrik, serta refit `BEST_K` upstream.
- [`reports/03-sintesis/tahap2_final.md`](reports/03-sintesis/tahap2_final.md): arsip EDA upstream 8-sensor global (bukan isi dokumen STATISTIK saat ini).
- [`reports/03-sintesis/tahap3_final.md`](reports/03-sintesis/tahap3_final.md): klaim hasil, `BEST_K=4`, centroid, dan interpretasi rezim.
- [`notebooks/final_clustering_outputs06/table6_cluster_share.csv`](notebooks/final_clustering_outputs06/table6_cluster_share.csv): occupancy `k=4` yang tersedia.
- [`clean-pipeline-56-32/outputs/metrics/verdict_ledger.csv`](clean-pipeline-56-32/outputs/metrics/verdict_ledger.csv): 42 verdict primer (`NO-WINNER` 38, `ELIGIBLE` 4) beserta alasan guard.
- [`clean-pipeline-56-32/outputs/manifests/phase_c_manifest.json`](clean-pipeline-56-32/outputs/manifests/phase_c_manifest.json): bukti grid 126 run, threshold guard, dan hash output clustering.

---

**Kesimpulan.** Perbedaan pokok antara dua approach bukan “repo lama buruk, repo baru benar”. Perbedaan yang relevan secara ilmiah adalah bahwa repo lama memusatkan keputusan pada metrik internal dan prior domain dalam satu alur evaluasi, sedangkan rancangan audit baru berusaha membatasi aliran informasi, menjaga kontinuitas temporal, menguji kandidat pada partisi yang berbeda, dan menerima hasil negatif. Sampai seluruh bukti eksekusi dan validasi eksternal tersedia, kedua sisi harus menghindari klaim model final atau rezim fisik tervalidasi.
