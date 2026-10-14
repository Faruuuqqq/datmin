# Rencana Pipeline Bersih Sumur 56-32 v1

> Status: **PLANNING_ONLY** — dokumen ini mendefinisikan pekerjaan UTS, bukan bukti rerun, fit, evaluasi, atau pemenang. Counter saat ini tetap `kmeans_fits: 0`, `scaler_fits: 0`; C2/C3 **NOT TESTED**.

## Tujuan dan ruang lingkup

Fokus inti Proyek UTS Data Mining adalah pipeline bersih Well 56-32 untuk klasterisasi deret waktu sensor multivariat tanpa label. Output ilmiah hanya boleh memakai hasil yang direproduksi dan lolos aturan di bawah; nama klaster tetap kode statistik `C0..Ck`, bukan rezim fisik tanpa driller log.

## Lima Strict Rules Sol

1. **Anti-Leakage.** Semua keputusan model, pemilihan `k`, dan pemilihan scaler dibuat dari Train; Test hanya untuk evaluasi akhir terpisah.
2. **Scaler Isolation.** Fit `StandardScaler`, `RobustScaler`, atau `MinMaxScaler` hanya pada fitur Train; Test hanya memakai `transform` dari scaler Train yang sama.
3. **Integritas Deret Waktu.** Urutan kronologis tidak diacak; reset segmen pada timestamp bukan tepat +1 detik; window tidak boleh melintasi gap atau batas split/embargo.
4. **Evaluasi Jujur & NO-WINNER.** Laporkan Silhouette, DBI, occupancy, dan cluster collapse untuk Train serta Test secara terpisah. Jika metrik/occupancy tidak stabil atau collapse, statusnya **NO-WINNER**, bukan pemenang dipaksakan.
5. **Pembatasan Klaim.** Klaster adalah pola statistik `C0..Ck`; klaim rezim operasi fisik memerlukan driller log atau validasi domain independen.

## Fase A — Data Prep & Windowing Bersih 56-32

**Kegiatan**
- Baca data 1 Hz secara bounded/chunked; filter seluruh baris dengan `SPP <= -900`.
- Ubah sentinel `-999.25` menjadi `NaN`; jangan menyamakan filter SPP dengan masking seluruh kanal.
- Urutkan/validasi timestamp dan reset segmen pada gap, duplikat, atau waktu mundur.
- Bentuk tumbling window 60 detik: stride 60 detik, overlap 0%.
- Terima window hanya bila setiap kanal memiliki coverage minimal 54 dari 60 detik.
- Untuk 13 kanal, hasilkan `[mean, pop-std (ddof=0), endpoint-delta]`: tepat 39 fitur per window.

**Kriteria penerimaan**
- Tidak ada sentinel/`NaN`/`inf` pada matriks 39 fitur yang lolos; setiap window punya timestamp awal/akhir dan ID berurutan.
- Tidak ada window yang melewati reset segmen; coverage per kanal tercatat dan memenuhi `>=54/60`.
- Kontrak feature list, aturan filter/masking, dan jumlah kandidat/diterima terdokumentasi tanpa mengklaim hasil fit.

## Fase B — Split Kronologis & Scaler Terisolasi

**Kegiatan**
- Urutkan window valid secara kronologis; alokasikan 70% awal sebagai Train dan 30% akhir sebagai Test.
- Sisipkan embargo minimal 3.600 detik (1 jam) di antara akhir Train dan awal Test; window di buffer tidak masuk kedua set.
- Fit setiap kandidat scaler hanya pada Train lalu transform Train dan Test dengan objek scaler identik.

**Kriteria penerimaan**
- Membership split, batas waktu, ukuran Train/Test, dan durasi embargo dapat diaudit.
- Tidak ada window Test atau embargo dalam `fit`; tidak ada window melewati split/embargo.
- Bukti scaler mencatat `fit_rows == n_train` dan transform Test tidak memanggil fit/fit_transform.

## Fase C — K-Means, GMM, dan Evaluasi Terpisah

**Kegiatan**
- Latih K-Means dan Gaussian Mixture Model (GMM) pada Train untuk setiap `k=2..8` dan scaler yang diizinkan.
- Prediksi/evaluasi Train dan Test terpisah dengan Silhouette serta Davies–Bouldin Index (DBI), bila definisi metrik valid untuk jumlah label yang terbentuk.
- Catat occupancy setiap klaster, cluster kosong/collapse, seed, konfigurasi, dan alasan metrik tidak terdefinisi.

**Kriteria penerimaan**
- Tabel hasil memisahkan Train dari Test serta tidak memakai Test untuk memilih konfigurasi.
- Konfigurasi runtuh, metrik invalid, atau ketidakstabilan menghasilkan **NO-WINNER** yang eksplisit.
- Label keluaran hanya `C0..Ck`; tidak ada pemaknaan fisik tanpa bukti eksternal.

## Fase D — Paper IEEE UTS

**Kegiatan**
- Tulis paper `.doc` IEEE dua kolom 5–8 halaman sesuai brief UTS.
- Sertakan PRISMA (minimal 8 paper utama), Gap Analysis, metodologi Fase A–C, hasil, diskusi keterbatasan, kesimpulan, tautan kode/dataset, dan deklarasi Gen-AI.

**Kriteria penerimaan**
- Paper membedakan rancangan, hasil terukur, keterbatasan, dan hasil negatif/NO-WINNER.
- Klaim temporal, anti-leakage, dan evaluasi merujuk artefak bukti yang dapat ditelusuri.
- Tidak mempromosikan klaster menjadi rezim fisik tanpa driller log/validasi domain.

## Dataset sekunder dan status terkunci

- **16A:** opsional untuk ekstensi/cross-well dalam diskusi paper; bukan pemblokir pipeline inti 56-32. Status intake tetap `DESIGN_ONLY / NOT_OPENED` sampai gate terpisah terpenuhi.
- **78B:** tetap `LOCKED_NEGATIVE / UNSUITABLE_H1`; dapat disebut sebagai temuan kelayakan negatif, bukan holdout atau sumber fit/evaluasi.

## Batas status saat ini

Rencana ini tidak membuka raw/holdout, tidak mengesahkan eksekusi, dan tidak mengubah `INPUT_REPRODUCTION_FAILED`, `INSUFFICIENT_CLEAN_HOLDOUT`, status paper **HOLD**, maupun kebutuhan review independen lintas-keluarga.
