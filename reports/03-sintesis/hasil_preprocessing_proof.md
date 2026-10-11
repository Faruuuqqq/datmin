# Hasil Preprocessing Proof — Klasterisasi Sensor Pengeboran Geotermal Utah FORGE 56-32

> **Status:** TERKUNCI dari run v3 (`notebooks/kaggle_outputs_proof05_v2/` →
> `notebooks/kaggle_outputs_proof05_v3/`).
> **Sumber angka:** 8 file CSV + 3 gambar hasil notebook `notebooks/05_preprocessing_proof.ipynb`.
> **Fungsi dokumen:** bahan baku Bab II-B/II-C paper IEEE + bahan belajar tim (Orang 3 — Preprocessing).
> Seluruh istilah teknis di bawah dijelaskan dengan bahasa pendidikan agar mudah dipahami.

---

## 1. Ringkasan eksekutif

Lima keputusan preprocessing diuji berbasis data dengan aturan **gate + rank**:
lapisan *gate* (lolos/gagal) memeriksa kewajaran fisik centroid, lapisan *rank*
memeringkat kandidat yang lolos dengan skor komposit `S = 0,50·Silhouette + 0,50·(1 − DBI)`.

| Keputusan | Pemenang | Bukti kunci | Dipakai di paper |
|---|---|---|---|
| P1 — Penskalaan | RobustScaler (S=0,8847) | Sil 0,9587 vs 0,7518; konvergen 4 vs 7 iterasi; stabil ±10pp | Bab II-B baris 1 |
| P2 — Winsorize ROP | Winsorize HI=1135,46 | Skew 23,54→5,71; gate FAIL→PASS | Bab II-B baris 2 |
| P3 — Set sensor | 7 sensor (Diff-Press OFF) | Seri metrik (ΔS=0,0000); menang atas dasar fisik | Bab II-B baris 3 |
| P4 — Sentinel | dropna-subset (via tie-break) | Seri kualitas (ΔS=0,001); row-loss 1,2% | Bab II-B baris 4 |
| P4b — Drift imputasi | Tak ada diskualifikasi | KS maksimum 0,0036 < 0,01 (negligible) | Bab II-B baris 4 (pendukung) |
| P5 — Representasi | Window-60s/30s (via stabilitas+cost) | Chatter 0,0013 vs 0,0102/detik; kompresi 60x | Bab II-C |

Dua keputusan (P3, P4) dimenangkan lewat aturan tie-break yang jujur, bukan klaim
kemenangan metrik — penjelasannya di Bagian 3.

---

## 2. Bukti penyakit data (Proof 0 — `proof0_disease.csv`)

Sebelum memilih obat, dibuktikan dulu bahwa penyakitnya benar-benar ada di dataset:

| Pemeriksaan | Pengertian | Angka v3 | Makna |
|---|---|---|---|
| Variance share top-1 | Porsi sebaran total yang disumbang satu sensor dominan | 52,68 % | Satu sensor menguasai separuh varians → jarak Euclidean bias → penskalaan wajib |
| Variance share Diff-Press (excluded) | Porsi varians kanal yang dieksklusi, sebagai pembanding | 113,36 % dari total 7 sensor | Kanal Diff-Press sangat dominan sekaligus rusak → eksklusinya berdasar (lihat P3) |
| Range ratio ROP vs Torque | Perbandingan rentang nilai (maks−min) antar sensor | 348,9 : 1 | Perbedaan skala ekstrem → tanpa scaler, sensor kecil terabaikan |
| Autokorelasi lag-1 | Kemiripan nilai detik ini dengan detik sebelumnya (1,0 = identik) | SPP 0,9998; RPM 0,999; ROP 0,9884 | Rekaman saling terikat waktu → klasterisasi per detik akan berkedip (chattering) → windowing wajib (bonus temporal) |
| Sentinel SPP / Diff-Press | Persentase nilai `-999.25` (kode sensor mati) | 1,177 % / 1,177 % | Gangguan instrumen nyata (±29.500 baris, muncul bergerombol) → penanganan missing wajib |
| Skew ROP | Kemiringan distribusi (0 = simetris) | 23,54 | Sangat miring kanan: spike sesekali hingga 11.115 ft/hr |
| Kurtosis ROP | Ketebalan ekor distribusi (data normal ≈ 3) | 643,3 | Ekor sangat tebal: outlier ekstrem mendominasi → winsorize wajib |

---

## 3. Hasil per keputusan

### P1 — Penskalaan: RobustScaler vs StandardScaler vs tanpa scaler (`proof1_scaler.csv`)

*Pengertian:* penskalaan menyamakan rentang antar sensor agar satu sensor tidak
mendominasi jarak Euclidean. StandardScaler memakai mean/std (terpengaruh outlier);
RobustScaler memakai median/IQR (kebal outlier).

| Kandidat | Silhouette | DBI | S | n_iter | fit (s) | Gate | Stabilitas 5 seed |
|---|---|---|---|---|---|---|---|
| **RobustScaler** | 0,9587 | 0,2657 | **0,8847** | 4 | 0,11 | PASS | stabil ±10pp |
| Tanpa scaler | 0,8903 | 0,4466 | 0,8182 | 3 | 0,10 | PASS | stabil |
| StandardScaler | 0,7518 | 0,6893 | 0,7339 | 7 | 0,11 | PASS | stabil |

*Silhouette* (makin tinggi makin baik) mengukur kekompakan klaster;
*DBI/Davies-Bouldin* (makin rendah makin baik) mengukur keterpisahan antar klaster;
*n_iter* = jumlah putaran K-Means sampai konvergen (padanan kecepatan konvergensi).

**Keputusan:** RobustScaler menang skor, lolos gate fisik, dan konvergen tercepat
(4 vs 7 iterasi). Tanpa scaler terlihat bagus (Sil 0,89) tetapi menipu karena
dikuasai massa nol — ditolak oleh argumen varians di atas, bukan oleh gate.
Acuan literatur: Wang et al. 2026 (bahaya bias Euclidean), Bayazitova et al. 2024
(baseline Z-score yang dikalahkan), Qiu et al. 2025 (outlier).

### P2 — Winsorize ROP: mentah vs clip (`proof2_winsor.csv`)

*Pengertian:* winsorisasi memotong nilai di atas ambang HI (*hinge*: Q3 + 1,5·IQR
dari distribusi ROP>0) menjadi tepat HI — spike dibuang, barisnya dipertahankan
(kontinuitas waktu utuh). Lawannya, *trimming* (hapus baris), ditolak tertulis
di bawah.

| Kandidat | HI | Skew | Kurtosis | Max ROP | S | Gate |
|---|---|---|---|---|---|---|
| Mentah | — | 23,54 | 643,3 | 11.115,9 | 0,8929 | **FAIL** (3 aturan) |
| **Winsorized** | 1135,46 | 5,71 | 35,7 | 1135,5 | 0,8847 | **PASS** |

Spike 11.115 ft/hr adalah artefak derek pengangkat (*drawworks* menarik rangkaian
di udara), bukan penetrasi batuan (normal 20–150 ft/hr). Bukti gate: data mentah
menghasilkan centroid mustahil (mis. RPM negatif, bor tanpa pompa); sesudah
clip, centroid lolos uji fisika. Acuan: Li et al. 2026, Qiu et al. 2025.

*Catatan anti-trimming:* menghapus baris ROP>HI akan membuang data dan melubangi
deret 1 Hz dengan gap artifisial (terhitung: loss % + jumlah gap baru per 30 ribu
baris, tercetak di output cell P2) — bertentangan langsung dengan tujuan windowing
(P5). Karena itu trimming ditolak tanpa eksperimen penuh.

### P3 — Set sensor: 7 (Diff-Press OFF) vs 8 (ON) (`proof3_diffsens.csv`)

| Kandidat | Fitur | Silhouette | DBI | S | Gate |
|---|---|---|---|---|---|
| **7 sensor (OFF, locked)** | 7 | 0,9587 | 0,2657 | 0,8847 | PASS |
| 8 sensor (ON, sensitivitas) | 8 | 0,9585 | 0,2657 | 0,8847 | PASS |

**Keputusan jujur:** metrik seri (ΔS = 0,0000) — OFF tidak diklaim menang metrik.
OFF dipilih atas dasar fisik: Differential Pressure rata-rata −692 psi
(min −5.138), yaitu bug formula turunan software Pason saat pompa mati, bukan
bacaan sensor; didukung variance share 113% di Proof 0. Run 8-sensor tetap
dilampirkan sebagai tabel sensitivitas. Acuan: Singh et al. 2026.

### P4 — Sentinel: dropna vs mean-impute vs forward-fill (`proof4_sentinel.csv`)

| Kandidat | Row-loss | Silhouette | DBI | S |
|---|---|---|---|---|
| mean-impute | 0,0 % | 0,6225 | 0,9164 | 0,6665 |
| **dropna-subset (locked)** | 1,2 % | 0,6191 | 0,9176 | 0,6655 |
| forward-fill | 0,0 % | 0,6160 | 0,9209 | 0,6643 |

*Row-loss* = persen baris yang hilang jika dibuang. Sampel memakai stride
full-span (~200 ribu baris, tiap baris ke-12 dari seluruh file) agar burst
outage sistemik benar-benar masuk sampel — sampel head terbukti sentinel-free
dan tidak menguji apa-apa.

**Keputusan jujur (tie-break):** selisih S maksimum 0,001 < ambang seri 0,005 —
ketiga metode seri secara kualitas. Aturan tie-break yang didaftarkan sebelumnya:
di bawah ambang seri, pemenang ditentukan cost + transparansi + fisika.
Dropna hanya kehilangan 1,2% baris, tidak mengarang data, dan tidak berasumsi
apa-apa tentang mekanisme missing yang sistematis (burst outage) — maka dropna
dipilih. Ini praktik baku: missingness <5% + hasil insensitive → hapus baris +
laporkan sensitivitas. Acuan pembanding: Bayazitova et al. 2024 (forward-fill).

### P4b — Drift distribusi imputasi (`proof4b_drift.csv`)

*Pengertian:* uji Kolmogorov-Smirnov (KS) mengukur selisih bentuk distribusi
sebelum vs sesudah cleaning. Dengan n≈200 ribu, semua p-value KS ≈ 0 sehingga
tidak informatif — yang sah dipakai adalah *effect size* D: D<0,01 berarti tidak
ada perbedaan material.

| Kandidat | mean-KS | max-KS | mean-shift | median-shift | std-shift |
|---|---|---|---|---|---|
| mean-impute | 0,0008 | 0,0053 | 2,039 | 0,0 | 0,436 |
| forward-fill | 0,0010 | 0,0066 | 2,739 | 0,0 | 3,626 |
| dropna-subset | 0,0036 | 0,0049 | 0,483 | 0,171 | 0,220 |

**Bacaan jujur:** imputasi sedikit lebih mulus secara KS, tetapi semuanya
<0,01 (negligible) — tidak ada yang didiskualifikasi. KS dropna sedikit lebih
besar justru perilaku yang benar: missingness-nya sistematis (burst outage satu
rezim), sehingga membuangnya menggeser marginal sedikit; imputasi "menang" KS
dengan menempelkan nilai median ke periode mati — marginal mulus, fisika joint
rusak. Maka drift tidak menggugurkan siapa pun; keputusan tetap ikut tie-break P4.

### P5 — Representasi: point vs window-60s/30s (`proof5_temporal.csv`)

*Pengertian:* point = 1 baris per detik (8 fitur); window = tiap 60 detik
diringkas jadi mean/std/delta per sensor (24 fitur, langkah 30 detik).
*Chatter* = fraksi langkah yang label klasternya berganti (kedipan pada rig
yang fisiknya stabil) — dinormalisasi ke per-detik agar adil.

| Kandidat | S | Silhouette | DBI | Chatter/detik | Fit (s) |
|---|---|---|---|---|---|
| point-based | 0,8245 | 0,9211 | 0,4527 | 0,0102 | 0,2 |
| **window-60s/30s (locked)** | 0,7764 | 0,8586 | 0,6037 | **0,0013** | 0,0 |

**Keputusan jujur:** point menang skor S — dilaporkan apa adanya, tidak
disembunyikan. Window dipilih atas dua kaki lain: chatter ~8x lebih tenang
(0,0013 vs 0,0102/detik) + kompresi 60x (30 ribu baris → 999 window) dengan
waktu fit ~0 detik. Ini fondasi klaim bonus temporal. Acuan: Li et al. 2026,
Mohammed et al. 2025, Keogh & Lin 2005 (klasterkan fitur, bukan sub-deret mentah).

---

## 4. Catatan kejujuran metodologi (antisipasi pertanyaan penguji)

1. **"Kenapa point menang S tapi window yang dipakai?"**
   Karena S bukan satu-satunya kriteria: window menang stabilitas label
   (~8x) dan biaya komputasi (60x) sambil mempertahankan karakteristik deret
   waktu — persis syarat bonus tugas. Ketiganya dilaporkan berdampingan.
2. **"Kenapa HI=1135, bukan ~47 seperti estimasi awal?"**
   HI dihitung dari distribusi ROP>0 (saat mengebor beneran), bukan seluruh
   kolom yang 80%-nya nol. Estimasi 47 berasal dari sampel yang salah kaprah;
   1135 memangkas tepat ekor ekstrem (maks 11.115→1135,5) dan lolos gate.
3. **"Kenapa std antar-seed = 0,000000?"**
   Bukan bug loop: 5 seed × n_init=10 konvergen ke partisi identik
   (terkonfirmasi 2 run independen). Dilaporkan sebagai temuan kestabilan
   deterministik (seed-invariant), bukan disembunyikan.
4. **"Kenapa dropna menang padahal kalah 2 metrik?"**
   Karena kalahnya noise-level (ΔS=0,001; ΔKS≈0,003, semua di bawah ambang
   seri yang didaftarkan sebelum hasil keluar). Di bawah ambang seri,
   statistik tidak bisa membedakan metode — maka yang sah memutuskan adalah
   cost, transparansi, dan fisika. Aturannya tertulis di notebook (cell P4),
   bukan karangan pasca-hoc.

---

## 5. Kriteria terima + status kunci

| # | Kriteria | Status v3 |
|---|---|---|
| 1 | HI > 0 (tidak mengenolkan ROP) | ✅ 1135,46 |
| 2 | Gate mentah FAIL → winsorized PASS | ✅ 3 aturan → lolos |
| 3 | Pemenang robust + stabil ±10pp bobot | ✅ S=0,8847, stabil |
| 4 | `row_loss` ≈ 1 % (P4 menguji data beneran) | ✅ 1,2 % |
| 5 | Chatter window/detik < point/detik | ✅ 0,0013 < 0,0102 |
| 6 | Verdict `MISSING: none` (8 CSV + 3 PNG) | ✅ 11 file lengkap |

**Angka di dokumen ini dikunci dari run v3 dan menjadi satu-satunya sumber untuk
Bab II-A/II-B/II-C. Perubahan metode apa pun wajib re-run + re-kunci.**

---

## Lampiran — mapping file → paper

| File output | Isi | Dipakai di |
|---|---|---|
| `proof0_disease.csv` | 10 angka penyakit | Bab II-A, Tabel 1 (justifikasi preprocessing) |
| `proof1_scaler.csv` | Shootout 3 scaler + konvergensi + stabilitas | Bab II-B baris 1 |
| `proof2_winsor.csv` | Mentah vs winsorize + gate | Bab II-B baris 2 |
| `proof3_diffsens.csv` | 7 vs 8 sensor | Bab II-B baris 3 + tabel sensitivitas |
| `proof4_sentinel.csv` | Drop vs 2 imputasi + row-loss | Bab II-B baris 4 |
| `proof4b_drift.csv` | KS + shift distribusi | Bab II-B baris 4 (pendukung) |
| `proof5_temporal.csv` | Point vs window + chatter + waktu | Bab II-C |
| `proof_scoreboard.csv` | 6 verdict final | Bab II-B (tabel utama) |
| `figP1_scaler.png` | Bar S per scaler | Fig Bab II-B |
| `figP2_winsor.png` | Histogram ROP mentah vs clip | Fig Bab II-B |
| `figP5_chattering.png` | Label point (kedip) vs window (stabil) | Fig Bab II-C |
