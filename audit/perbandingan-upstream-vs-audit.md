# Perbandingan Upstream `datmin/` vs Sistem Audit Baru

> **Dokumen posisi akademis dan teknis.** Dokumen ini membandingkan artefak upstream lama (`_audit-upstream/datmin/`) dengan perbaikan desain serta bukti audit di `_audit-upstream/`. Ia **bukan** bukti bahwa eksperimen baru masih boleh diaktifkan atau bahwa paper telah layak submit.
>
> **Status per 2026-10-13:** proyek berada pada **PARTIAL/HOLD**. Tahap 1 berstatus **BLOCKED**, H1 belum dibuka, C2/C3 **NOT TESTED**, dan review independen lintas-keluarga masih **OPEN**. Semua istilah seperti *train-only scaler*, *GMM*, atau *NO-WINNER* di bawah harus dibaca menurut bukti artefaknya: sebagian merupakan hasil audit terdahulu, sebagian adalah desain/protokol yang kini dibekukan, bukan izin untuk melakukan fit baru.

---

## 1. Ringkasan Eksekutif & Konteks Tugas UTS Data Mining

Tugas UTS bertema **Analisis Karakteristik Data Sensor Industrial/Geotermal Multivariat dan Pemodelan Klasterisasi Deret Waktu**. Mahasiswa diminta mengolah data sensor multivariat tanpa label, menangani perbedaan skala, ketergantungan temporal, dan noise/outlier; menyusun PRISMA serta *gap analysis*; lalu merancang clustering dan mengevaluasinya dengan metrik internal seperti Silhouette Coefficient atau Davies–Bouldin Index (DBI). Luaran wajibnya adalah paper IEEE 5–8 halaman, lampiran kode/dataset, diagram PRISMA, dan deklarasi penggunaan Gen-AI.

Repo upstream `datmin/` mempunyai nilai penting sebagai eksperimen awal: ia mencoba mengangkat persoalan skala, sentinel, *sliding window*, StandardScaler versus RobustScaler, dan K-Means. Namun, bukti yang tersimpan memperlihatkan perbedaan antara narasi, kode, dan keluaran runtime. Beberapa angka penting tidak memiliki artefak eksekusi yang dapat ditelusuri, window tumpang tindih digunakan dengan *stride* 30 detik, statistik scaler dipelajari dari seluruh data pada baseline lama, dan pemilihan `k=4` lebih dekat pada prior empat rezim domain daripada pemenang aturan seleksi yang dibekukan.

Sistem audit baru tidak sekadar mengganti parameter. Kontribusi utamanya adalah mengubah pertanyaan dari “cluster mana yang tampak paling bagus?” menjadi “apakah bukti cukup untuk mengizinkan klaim itu?” Perubahan ini mencakup:

1. memisahkan fakta artefak, hasil historis, desain yang belum diuji, dan klaim yang dilarang;
2. membuat jendela 60 detik **tumbling/non-overlapping** dengan reset ketika timestamp tidak berjarak tepat 1 detik;
3. menerapkan gerbang cakupan minimal 54 dari 60 sampel valid dan melaporkan data yang tersisih;
4. memisahkan fit scaler pada train dari transformasi test dalam desain split temporal;
5. memperlakukan *cluster collapse*, konflik metrik, dan kegagalan reproduksi sebagai hasil ilmiah negatif, bukan masalah yang disembunyikan;
6. melarang penamaan cluster sebagai rezim fisik tanpa driller log atau validasi ahli independen; dan
7. memakai status **NO-WINNER** ketika kandidat tidak memenuhi guard, alih-alih memaksakan pemenang.

Dengan demikian, audit lebih bernilai untuk penilaian akademis karena menunjukkan *reasoning* metodologis, transparansi keterbatasan, dan keterulangan keputusan. Audit tidak menyatakan bahwa K-Means, GMM, `k=3`, `k=4`, atau `k=5` adalah pemenang akhir. Pada state terkunci saat ini, **tidak ada pemenang final**.

### Ruang lingkup dan batas pembacaan

- **Repo lama** berarti artefak yang ada di `_audit-upstream/datmin/`, dibaca tanpa mengeksekusi notebook atau pipeline.
- **Sistem baru/audit** berarti artefak bukti dan spesifikasi di `_audit-upstream/`; tidak semua komponennya merupakan hasil empiris yang boleh digeneralisasikan.
- “Rezim fisik” berbeda dari “pola statistik”. Cluster dapat berguna untuk eksplorasi tanpa otomatis menjadi bukti aktivitas rig tertentu.
- Data dari satu sumur tidak otomatis berlaku untuk sumur, rig, periode, atau kondisi geologi lain.
- Paper tetap **HOLD** sampai gerbang bukti yang relevan dipenuhi; dokumen perbandingan ini tidak mencabut hold tersebut.

---

## 2. Perbandingan Komprehensif Berdasarkan Tahapan UTS

### 2.1 Tahap 1 — *Business Understanding* & *Literature Review* (PRISMA dan *Gap Analysis*)

#### A. Kesesuaian dengan tujuan UTS

Panduan UTS meminta sedikitnya delapan artikel utama hasil penyaringan PRISMA dan sebuah tabel *gap analysis* yang menjelaskan kontribusi teknik kelompok. Upstream telah memiliki bahan literatur: daftar *eligibility*, sembilan studi inti dan tujuh cadangan dilaporkan, serta narasi mengenai masalah scale disparity, ketergantungan temporal, sentinel, dan clustering. Ini merupakan modal yang berguna, bukan sesuatu yang harus dihapus.

Namun, audit menemukan batas penting pada jenis buktinya. Berkas `eligibility_16.csv` atau `17-paper-elig-Datmin.csv` adalah **data seleksi artikel**, bukan 16 sampel sensor atau 16 window eksperimen. Kebingungan antara tabel literatur dan data eksperimen akan mengaburkan unit analisis. Selain itu, adanya daftar artikel belum dengan sendirinya membuktikan seluruh hitungan PRISMA, alasan eksklusi, keterbacaan *full text*, atau hubungan setiap paper dengan keputusan metodologis sudah lengkap dan konsisten.

#### B. PRISMA yang dapat dipertahankan

Pada jalur yang lebih ketat, PRISMA harus dibaca sebagai jejak keputusan berikut:

1. **Identifikasi:** kata kunci, basis data, rentang tahun, tanggal pencarian, dan hasil awal dicatat.
2. **Screening:** duplikasi dan artikel yang tidak relevan dihapus dengan alasan yang eksplisit.
3. **Eligibility:** *full text* ditinjau terhadap kriteria inklusi/eksklusi, bukan hanya berdasarkan judul.
4. **Inclusion:** minimal delapan artikel utama ditetapkan serta dipetakan ke gap, metode, data, dan metrik yang relevan.

Audit menjaga prinsip ini dengan meminta agar paper yang dipakai benar-benar dapat ditautkan pada keputusan proyek: misalnya alasan membandingkan scaler, kebutuhan gap-safe windowing, keterbatasan K-Means untuk bentuk cluster non-sferis, atau kebutuhan validasi domain. PRISMA yang baik bukan dekorasi gambar; ia harus menjelaskan mengapa pilihan metode tidak muncul setelah melihat skor akhir.

#### C. *Gap analysis*: dari slogan ke keputusan yang dapat diuji

Gap upstream yang bermanfaat meliputi data sensor rig 1 Hz multivariat, perbedaan skala antarsensor, kebutuhan representasi temporal, serta belum adanya label rezim. Namun kontribusi tidak boleh berbunyi “menggunakan K-Means adalah inovasi”. K-Means dan elbow adalah baseline umum. Kontribusi yang lebih defensibel adalah, misalnya, membandingkan representasi titik versus ringkasan jendela dengan protokol waktu yang sama, menguji dampak scaling, mengungkap *attrition* akibat sentinel/gap, atau menunjukkan mengapa data belum mendukung discovery rezim.

Audit juga mengubah hasil negatif menjadi bagian sah dari *gap analysis*: jika tidak tersedia label driller, hasil cluster hanya dapat ditafsirkan sebagai pola statistik; jika holdout bersih tidak tersedia, klaim generalisasi temporal harus ditahan. Pendekatan ini lebih ilmiah daripada mengganti nama cluster agar tampak sesuai operasi rig.

#### D. Status Tahap 1 saat ini

Walaupun material PRISMA dan *gap analysis* tersedia, state proyek tidak boleh disebut PASS empiris. Artefak status menyatakan checklist sembilan butir masih: Fase 0–1 **SEBAGIAN**, Fase 2–6 **BELUM**. Tahap 1 tetap **BLOCKED** karena reproduksi input gagal dan *clean holdout* belum terbukti. Paper dapat memakai temuan audit sebagai limitasi/metodologi, tetapi tidak boleh menjadikannya klaim discovery rezim yang sudah tervalidasi.

### 2.2 Tahap 2 — *Data Understanding* & *Preprocessing*

#### A. Memahami sensor, nilai sentinel, dan unit analisis

Data target adalah deret waktu sensor rig/geotermal tanpa label. Tantangan UTS menuntut perhatian pada skala, ketergantungan waktu, dan noise/outlier. Upstream berfokus pada sensor seperti ROP, WOB, RPM, SPP, torque, hook load, total pump output, dan differential pressure. Ia mengenali bahwa Pason Gas serta Gamma bermasalah dan bahwa sentinel `-999.25` perlu diperlakukan sebagai *missing value*.

Kelemahan metodologis muncul ketika pembersihan hanya diringkas sebagai `-999.25 → NaN → dropna`. Pendekatan ini mudah dipahami, tetapi kehilangan informasi: sensor mana yang gagal, berapa banyak baris yang hilang, apakah nol adalah nilai fisik, dan apakah sebuah window masih memiliki dukungan observasi yang cukup. *Dropna* juga berisiko mengubah distribusi operasi tanpa laporan *attrition*.

Audit mengganti pendekatan “buang semua lalu lanjut” dengan pelacakan yang lebih eksplisit. Pada jalur preprocessing baru, baris dengan SPP sentinel disaring pada tingkat baris sesuai aturan instrumen, nilai `<= -900` pada kanal lain diperlakukan sebagai missing untuk agregasi, dan statistik kehilangan data dicatat. Pason Gas serta Gamma tidak dipakai sebagai fitur model bila kanalnya tidak layak. Kedalaman absolut juga tidak dipakai sebagai masukan K-Means agar model tidak hanya mengelompokkan berdasarkan kedalaman pemboran.

#### B. Windowing: *stride* 30 detik versus tumbling 60 detik

Upstream memakai jendela 60 detik dengan *stride* 30 detik. Artinya, dua jendela berdekatan berbagi kira-kira 30 detik sampel mentah. Overlap dapat berguna untuk eksplorasi resolusi waktu, tetapi ia menciptakan ketergantungan kuat antar-window. Window yang tumpang tindih tidak boleh diperlakukan sebagai observasi independen untuk confidence interval, *split* acak, ataupun klaim stabilitas.

Sistem audit mengadopsi jendela **60 detik tumbling/non-overlapping**: setiap jendela yang diterima menempati segmen 60 detik sendiri dan stride efektifnya 60 detik. Untuk setiap sensor/fitur, diringkas `mean`, simpangan baku populasi, dan perubahan `last-valid − first-valid`. Konstruksi ini mempertahankan konteks temporal dalam bentuk yang sederhana dan mengurangi duplikasi dukungan data mentah antar-window.

Pilihan tumbling bukan dalil bahwa stride 30 detik selalu salah. Ia adalah pilihan konservatif untuk tujuan evaluasi dan audit karena ketergantungan antar-unit lebih mudah dijelaskan. Jika pada masa depan ingin membandingkan stride 30 versus 60, perbandingan harus berlangsung pada protokol, populasi, dan definisi evaluasi yang sama—bukan lewat ranking metrik yang dicampur.

#### C. *Data leakage* pada scaler

Pada baseline upstream, StandardScaler/RobustScaler digunakan dalam skenario yang fit dan evaluasinya berada pada data yang sama atau subset dari interval yang sama. Cara ini boleh dipakai sebagai eksplorasi transduktif jika diungkapkan dengan jujur, tetapi tidak dapat dipakai untuk membuktikan generalisasi temporal. Statistik rata-rata, simpangan baku, median, atau IQR dari masa depan ikut memengaruhi transformasi data sebelumnya.

Desain audit menetapkan split temporal: bagian awal sebagai train dan bagian akhir sebagai test, dengan StandardScaler maupun RobustScaler **di-fit hanya pada train** lalu digunakan untuk mentransformasi test. Ini memisahkan estimasi parameter preprocessing dari evaluasi. Hasil historis split baseline menunjukkan ranking dapat berubah ketika target evaluasi berubah; karena itu skor *full-data* tidak boleh langsung disebut pemenang untuk kondisi temporal.

Namun, state terkunci saat ini harus tetap dijaga: artefak desain tidak sama dengan acceptance empiris masa depan. Tidak boleh ada klaim bahwa semua kebocoran telah “terbukti bersih” hanya karena spesifikasinya telah ditulis.

#### D. *Gap-reset* dan *coverage gate* 54/60

Timestamp 1 Hz tidak selalu kontinu. Bila data memiliki jeda, duplikat, atau urutan waktu mundur, satu window tidak boleh menjembatani kedua sisi gap karena hal itu membuat perubahan `last − first` mencampurkan dua episode yang tidak berdampingan.

Audit menetapkan dua pengaman:

- **Gap-reset:** setiap interval timestamp yang tidak tepat satu detik memutus segmen. Window hanya dibuat di dalam segmen kontinu.
- **Coverage gate:** window 60 detik harus memiliki minimal **54 dari 60** observasi valid (90%) untuk agregasi yang memerlukan dukungan data. Kandidat yang tidak memenuhi ambang dicatat sebagai ditolak, bukan diimputasi diam-diam.

Artefak audit yang mendokumentasikan rerun terdahulu mencatat 27 diskontinuitas, 3.094 kandidat ditolak karena coverage, dan keluaran 38.177 window × 46 kolom dengan 39 fitur model. Angka tersebut membantu menunjukkan *data attrition*, tetapi pada state hold saat ini tidak boleh dipakai sebagai alasan melakukan fit ulang atau seleksi tanpa persetujuan baru.

### 2.3 Tahap 3 — *Time-Series Clustering Design* & *Paper Finalization*

#### A. Pemilihan jumlah cluster (`k`)

Panduan UTS menyebut elbow dan metrik internal sebagai contoh optimasi hiperparameter. Upstream menguji K-Means pada rentang `k`, tetapi akhirnya memilih `k=4` terutama karena terdapat empat rezim yang diharapkan secara domain. Prior domain dapat menjadi hipotesis yang baik; ia tidak dapat menjadi bukti bahwa data memiliki tepat empat cluster.

Sistem audit menuntut tabel seleksi yang menyimpan kandidat, seed, jumlah cluster, populasi fit, scaler, metrik, ukuran cluster, dan alasan penyelesaian konflik. Silhouette tinggi saja tidak cukup. DBI, occupancy, stabilitas, struktur null/ketidakadaan cluster diskret, dan interpretasi episode perlu dipertimbangkan sesuai pertanyaan riset. Jika kandidat gagal guard atau bukti konflik, status yang benar ialah **NO-WINNER**, bukan pemilihan pasca hoc.

Artefak `k-final-selection.md` menyatakan `Decision: no winner; insufficient evidence. P3 is prohibited.` Ini adalah temuan penting: penolakan untuk memilih pemenang ketika bukti tidak cukup adalah keputusan metodologis yang lebih kuat daripada menempelkan label “best”.

#### B. K-Means versus GMM

Upstream terutama menjalankan K-Means. GMM, Agglomerative, DBSCAN, DTW, dan pendekatan lain muncul sebagai alternatif dalam narasi/literatur tetapi tidak mempunyai bukti eksekusi setara pada repo lama. Karena itu, tidak sah menyatakan K-Means “terbaik” dibanding metode-metode tersebut.

Audit memperkenalkan GMM sebagai baseline pembanding yang relevan, bukan sebagai pengganti otomatis K-Means. Secara konseptual, K-Means mengasumsikan cluster yang cenderung kompak/sferis dalam ruang transformasi, sedangkan GMM dapat memodelkan probabilitas keanggotaan dan variasi kovarians tertentu. Namun GMM sendiri dapat tidak stabil, runtuh ke solusi buruk, atau sensitif terhadap inisialisasi. Model yang lebih kompleks tidak otomatis lebih ilmiah.

Dalam dokumen split baseline historis, beberapa kombinasi K-Means dan GMM dibandingkan pada scaler serta split yang sama, dan beberapa prediksi test menghasilkan satu cluster sehingga Silhouette/DBI tidak terdefinisi. Audit mencatat `NaN` apa adanya, bukan memaksa angka agar tabel terlihat lengkap. Seleksi final kemudian tetap berstatus **NO-WINNER** karena guard occupancy, rentang Silhouette, atau stabilitas tidak dipenuhi. Ini menunjukkan fungsi perbandingan baseline: menguji asumsi dan mengenali batas, bukan sekadar mencari angka paling tinggi.

#### C. Fenomena *cluster collapse* 95,4%

Upstream menyimpan share cluster `C0=95,40%`, `C1=0,71%`, `C2=0,71%`, dan `C3=3,17%` untuk hasil K-Means `k=4`. Ketimpangan ini bukan otomatis kesalahan: proses rig memang dapat menghabiskan waktu lebih lama pada satu keadaan. Tetapi ia adalah sinyal yang harus diuji, bukan alasan langsung untuk menyatakan `C0` sebagai aktivitas pengeboran aktif.

Menurut guard audit yang lebih ketat, dua cluster di bawah 1% dan cluster mayoritas di atas 95% tidak memenuhi batas occupancy yang telah ditentukan untuk kandidat sehat. Pada eksperimen audit lainnya bahkan ditemukan collapse sekitar 98,57–99,27% dengan cluster berisi 7 observasi. Silhouette tetap dapat tinggi pada partisi seperti ini karena metrik kompakness/pemisahan tidak membuktikan kegunaan domain, representasi episode, atau keberadaan beberapa rezim fisik.

Makna ilmiahnya ialah sebagai berikut:

- *cluster collapse* harus dilaporkan bersama jumlah anggota dan cakupan, bukan ditutupi oleh rata-rata Silhouette;
- dominasi C0 dapat berarti operasi dominan, artefak fitur, redundansi, pencilan, atau geometri jarak; data saat ini tidak cukup untuk memilih salah satu sebab secara kausal;
- cap ROP univariat C0/C1 tidak memulihkan partisi yang sehat, sehingga temuan negatif tersebut tidak boleh dipasarkan sebagai solusi akhir;
- angka 95,4% merupakan bukti konsistensi tabel upstream, **bukan** validasi rezim fisik atau bukti bahwa fit berasal dari seluruh interval yang diklaim.

#### D. Klaim rezim fisik dan ketiadaan driller log

Nama seperti *Active Rotary Drilling*, *Circulation*, *Connection/Tripping*, atau *Idle* dapat membantu pembaca memahami hipotesis domain. Akan tetapi, pemberian nama berdasarkan centroid sensor adalah interpretasi, bukan ground truth. Tanpa driller log, log operasi, anotasi ahli independen, atau prosedur concordance yang terdokumentasi, cluster wajib dinamai netral (`C0`, `C1`, dan seterusnya) atau “pola statistik sementara”.

Audit secara eksplisit melarang pernyataan bahwa cluster membuktikan rezim fisik, akurasi operasi, keselamatan, generalisasi antarsumur, atau manfaat operasional. Profil centroid dalam satuan asli tetap bermanfaat sebagai *sanity check*, tetapi tidak menggantikan sumber label independen. Ini sangat penting untuk paper UTS: mahasiswa dapat menunjukkan interpretasi yang hati-hati tanpa mengklaim sesuatu yang datanya belum mampu dukung.

#### E. Finalisasi paper: hasil yang boleh dan tidak boleh dibawa

Paper sebaiknya memuat:

- masalah sensor multivariat dan alasan perlunya scaling serta representasi temporal;
- PRISMA dan *gap analysis* yang dapat ditelusuri;
- alur preprocessing, attrition sentinel, gap-reset, dan coverage gate;
- desain evaluasi serta perbedaan eksplorasi transduktif dengan split temporal;
- hasil negatif/no-winner, jika itu yang didukung bukti;
- keterbatasan satu sumur, ketiadaan driller log, conflict metrik, dan status holdout.

Paper tidak boleh memuat:

- “K-Means `k=4` adalah model terbaik” tanpa aturan seleksi yang lulus;
- “C0 adalah Active Drilling” sebagai fakta tanpa validasi log;
- “metode berhasil menggeneralisasi” jika test/holdout tidak bersih atau belum dibuka;
- “C2/C3 berhasil/ gagal secara empiris” karena statusnya **NOT TESTED**;
- angka hasil desain sebagai hasil eksperimen baru.

---

## 3. Tabel Matriks Perbandingan Detail

| Parameter | Repo Lama (`datmin/`) | Sistem Baru (Audit) | Implikasi Ilmiah |
|---|---|---|---|
| Unit analisis | Campuran point, sampel terbatas, dan sliding window; batas populasi fit tidak selalu tertaut ke output runtime. | Unit window didefinisikan, schema/metadata dipisahkan, dan status bukti dibedakan dari desain. | Mengurangi risiko membandingkan hasil dari populasi yang tidak sama. |
| Data mentah/provenance | Raw CSV utama dan beberapa output tidak ada di clone; beberapa angka runtime tidak dapat diverifikasi dari artefak. | Ledger provenance, hash/shape, serta perbedaan fakta versus klaim dicatat; status reproduksi tetap dibatasi. | Keterlacakan membaik, tetapi tidak boleh disebut reproduksi penuh bila gate gagal. |
| Sensor model | Utama: ROP, WOB, RPM, SPP, torque, hook load, pump output, differential pressure; Gas/Gamma disebut bermasalah. | Kanal dievaluasi menurut sentinel/missingness; metadata kedalaman dipisahkan dari fitur cluster; kanal tak layak dikeluarkan dengan alasan eksplisit. | Mencegah *spurious depth clustering* dan menyatakan batas instrumentasi secara jujur. |
| Sentinel `-999.25` | Dikonversi ke NaN lalu `dropna` pada jalur utama; dampak attrition tidak selalu lengkap. | SPP disaring di tingkat baris; sentinel kanal lain menjadi missing untuk agregasi, dengan pelacakan missingness dan coverage. | Pembersihan dapat diaudit, bukan hanya menghasilkan data “bersih”. |
| Pason Gas/Gamma | Dibuang/disebut 100% sentinel pada sejumlah artefak. | Tidak dipromosikan menjadi fitur bila kanal tidak layak; kualitas sensor menjadi temuan data. | Menghindari nilai instrument rusak dianggap sinyal operasi. |
| Window temporal | Window 60 s dengan *stride* 30 s; overlap menghasilkan ketergantungan besar antar-window. | Tumbling 60 s non-overlapping; ringkasan mean/std/delta. | Unit observasi lebih konservatif dan lebih mudah dievaluasi secara temporal. |
| Gap timestamp | Gap-aware diklaim di laporan, tetapi implementasi/keluaran pendukung tidak ditemukan pada clone upstream. | Reset eksplisit saat interval tidak tepat 1 s. | Tidak ada window yang mencampur dua episode terputus. |
| Cakupan window | Tidak ada gerbang coverage eksplisit yang konsisten pada artefak yang tersedia. | Minimal 54/60 (90%) observasi valid; kandidat gagal dicatat sebagai ditolak. | Menghindari ringkasan dari window yang terlalu miskin data serta membuka attrition untuk diperiksa. |
| Fitur window | 8 sensor × mean/std/delta pada sebagian jalur (24 fitur); ada konflik 7 vs 8 sensor. | Output audit terdokumentasi 38.177 × 46 dengan 39 fitur model dan 7 metadata pada jalur yang diaudit. | Schema dan fitur model lebih eksplisit; konflik versi tetap harus ditulis, bukan diasumsikan selesai. |
| Scaling | StandardScaler dan RobustScaler dibandingkan, tetapi baseline lama fit/evaluasi pada data sama. | Statistik scaler di-fit train-only dalam desain split temporal, kemudian test ditransformasi. | Mengurangi leakage untuk klaim temporal; desain saja belum otomatis membuktikan semua gate empiris lulus. |
| Split waktu | Subsampling/head segment dan full-data claim bercampur pada beberapa dokumen. | Split temporal dan embargo dikontrakkan; exposure audit membatasi pembukaan holdout. | Klaim transfer/holdout tidak dilontarkan tanpa dukungan raw dan audit membership. |
| Algoritma utama | K-Means dominan; alternatif banyak disebut tetapi tidak memiliki bukti eksperimen setara. | K-Means serta GMM diposisikan sebagai kandidat/baseline dalam protokol yang sama; kandidat dapat gugur. | Tidak ada alasan untuk mengklaim “terbaik” tanpa pembanding adil. |
| Rentang `k` dan keputusan | `k=4` dipilih selaras empat rezim domain, walau bukan puncak metrik tunggal. | Kandidat dinilai dengan aturan konflik, occupancy, stabilitas, dan status no-winner. | Prior domain menjadi hipotesis, bukan hasil discovery. |
| Metrik internal | Elbow, Silhouette, dan DBI digunakan; beberapa metrik dari populasi/subset berbeda. | Metrik direkam bersama split, seed, NaN, ukuran cluster, dan guard keputusan. | Silhouette/DBI menjadi bukti terbatas, bukan bukti kebenaran rezim. |
| Cluster collapse | `C0` 95,40%; dua cluster 0,71%; klaim rezim fisik tetap diberikan. | Occupancy diperiksa; 95,4% tidak lolos guard sehat yang membatasi mayoritas ≤95% dan tiap cluster ≥1%; status dapat no-winner. | Distribusi cluster adalah bagian inti evaluasi, bukan catatan kaki. |
| Interpretasi cluster | Nama operasi diberikan dari centroid dan prior domain. | Nama netral C0…Ck−1 dipertahankan tanpa driller log/ahli independen. | Membedakan pola statistik dengan ground truth operasi. |
| Validasi domain | Tidak ada driller log atau label operasi independen yang tersedia di bukti lokal. | Ketiadaan log dinyatakan sebagai limitasi; validasi domain menjadi gerbang lanjutan. | Mencegah *overclaiming* fisik dan operasional. |
| Hasil negatif | Konflik dan keluaran hilang lebih banyak muncul sebagai keterbatasan. | Collapse, gagal guard, input reproduction failure, dan no-winner dipertahankan sebagai hasil. | Meningkatkan integritas ilmiah dan mengurangi *publication bias*. |
| Status C2/C3 | Tidak terikat kuat pada gate final dalam narasi lama. | **NOT TESTED final scope-out**; tidak boleh diklaim sebagai bukti empiris. | Melindungi paper dari klaim atas eksperimen yang tidak terjadi. |
| 78B Gas/sentinel | Tidak menjadi fokus sistematis upstream. | 78B dikunci `LOCKED_NEGATIVE`/`UNSUITABLE_H1`: sentinel memengaruhi 100% baris, Gas absen 100%, dan coverage rejection 60,1%. | Menunjukkan bahwa kelayakan dataset/holdout harus diuji sebelum model. |
| Kandidat 16A | Tidak tersedia dalam eksperimen lama. | 16A disiapkan sebagai kandidat intake metadata-only; belum dibuka dan tidak boleh di-fit. | Menjaga opsi data baru tanpa mengubah protokol menjadi hasil prematur. |
| Status akhir | Narasi mengarah ke model/rejim final `k=4`. | `PARTIAL/HOLD`, Tahap 1 BLOCKED, H1 NOT OPENED, C2/C3 NOT TESTED, frontier review OPEN. | Kesimpulan saat ini adalah keterbatasan bukti, bukan pemenang model. |

---

## 4. Analisis Kritis: Mengapa Temuan Audit Ini Lebih Bernilai untuk Penilaian Akademis & Publikasi

### 4.1 Audit mengajarkan metode, bukan sekadar menjalankan algoritma

Untuk mata kuliah Data Mining, nilai akademis tertinggi tidak datang dari grafik cluster yang terlihat meyakinkan saja. Mahasiswa perlu menunjukkan pemahaman atas data, unit observasi, asumsi jarak, pemisahan train/test, evaluasi, dan batas inferensi. Upstream memperlihatkan usaha teknis yang berguna, tetapi audit memperlihatkan *mengapa* beberapa keputusan perlu dikoreksi atau tidak boleh diklaim terlalu jauh.

Contoh sederhana: Silhouette tinggi sering terasa seperti jawaban final. Audit menunjukkan bahwa partisi dengan mayoritas hampir seluruh data di satu cluster tetap dapat memiliki skor internal tinggi. Dari sini mahasiswa belajar bahwa metrik internal mengukur struktur geometris dalam ruang fitur tertentu; metrik itu tidak memberi label lapangan, kausalitas, atau manfaat operasi secara otomatis.

### 4.2 Transparansi negatif lebih kuat daripada pemenang yang dipaksakan

Status NO-WINNER, cluster collapse, dan `UNSUITABLE_H1` mungkin tampak mengecewakan bila tujuan dipersempit menjadi “harus ada model terbaik”. Justru, ketiganya menunjukkan kedewasaan ilmiah:

- kandidat gagal tidak disembunyikan;
- aturan penerimaan tidak diganti setelah hasil dilihat;
- data yang tidak layak tidak dipaksa melalui cleaning agar paper memiliki angka positif;
- ketidaktersediaan holdout atau log domain ditulis sebagai batas klaim.

Dalam publikasi yang baik, hasil negatif yang terdokumentasi dapat menjadi kontribusi jika pertanyaannya jelas dan penalarannya dapat ditelusuri. Sebaliknya, hasil positif dengan provenance lemah, leakage, atau label fisik yang tidak tervalidasi mudah runtuh saat ditanya dosen/reviewer.

### 4.3 Audit menyatukan reproducibility dan validitas ilmiah

Reproducibility bukan hanya menyimpan script. Ia membutuhkan hubungan yang jelas antara sumber data, hash/versi, cleaning, feature schema, split, scaler, seed, model, metrik, assignment, tabel, dan klaim. Upstream menyimpan beberapa potongan penting tetapi masih memiliki output yang tidak ditemukan dan angka yang saling berbeda. Audit mengubah masalah ini menjadi ledger: apa yang benar-benar tersedia, apa yang hanya diklaim, dan apa yang belum dapat diuji.

Perbaikan ini sangat relevan untuk paper IEEE. Reviewer atau dosen dapat mengikuti jalur alasan dari data ke kesimpulan. Jika jalur itu putus, paper harus mengurangi klaim; bukan menutupi celah dengan narasi lebih panjang.

### 4.4 Audit menjaga batas antara domain knowledge dan *confirmation bias*

Pengetahuan domain bahwa rig dapat mengalami drilling, circulation, connection/tripping, dan idle adalah pengetahuan yang berguna untuk merumuskan hipotesis. Namun jika jumlah cluster dipilih karena sudah ingin menemukan empat rezim itu, kemudian centroid diberi nama yang cocok, proses tersebut rentan *confirmation bias*.

Audit tidak menolak domain knowledge. Ia menempatkannya pada fungsi yang tepat: membantu menentukan sensor, pemeriksaan kewajaran, dan pertanyaan untuk log operasi/ahli. Domain knowledge tidak boleh menggantikan validasi independen. Karena driller log belum tersedia, istilah yang aman adalah “pola statistik” atau “hipotesis rezim”, bukan rezim fisik yang telah dibuktikan.

### 4.5 Audit lebih siap menjawab pertanyaan penguji

Berikut contoh pertanyaan yang dapat dijawab lebih baik oleh jalur audit:

| Pertanyaan penguji | Jawaban berbasis audit |
|---|---|
| Mengapa memakai window 60 detik? | Karena unit temporal didefinisikan, sumber fitur dijelaskan, dan window dibuat tanpa menjembatani gap; pemilihan ini bukan klaim universal. |
| Apa yang dilakukan pada sentinel? | Sentinel dipisahkan dari nilai fisik, dampaknya pada baris/window dilaporkan, dan coverage gate mencegah agregasi dari dukungan terlalu sedikit. |
| Mengapa tidak langsung memilih skor Silhouette tertinggi? | Karena skor tidak cukup menjawab occupancy, stabilitas, split temporal, dan validasi domain; konflik bukti menghasilkan NO-WINNER. |
| Apakah cluster bernama Active Drilling benar? | Belum terbukti; tanpa driller log atau ahli independen, nama itu hanya hipotesis centroid dan harus dinetralkan. |
| Mengapa 78B tidak dipakai? | Karena screening menemukan sentinel 100%, Gas absen 100%, penolakan coverage 60,1%, serta holdout belum bersih; menolak data adalah keputusan QC yang sah. |
| Apakah paper sudah siap submit? | Belum. Statusnya PARTIAL/HOLD dengan Tahap 1 BLOCKED dan review lintas-keluarga masih OPEN. |

---

## 5. Rencana Strategis Penggabungan (*Merging Plan*) ke Repositori Git

> Rencana ini adalah desain repositori dan dokumentasi. Ia **bukan** instruksi untuk mengubah branch, memindahkan data besar, mengaktifkan pipeline, atau melakukan fit tanpa persetujuan yang sesuai. Root workspace juga pernah tercatat bukan repository Git; struktur berikut diterapkan pada repository yang benar setelah status Git dan otorisasi diverifikasi.

### 5.1 Strategi branching: `v2-rigorous-audit`

Buat branch integrasi bernama `v2-rigorous-audit` dari commit yang sudah dibekukan/ditentukan setelah inventaris artefak selesai. Tujuannya bukan menghapus sejarah lama, melainkan menjaga eksperimen awal dapat dibaca sambil mencegahnya tampil sebagai bukti final.

Prinsip branch:

1. **Jangan menulis ulang sejarah eksperimen awal.** Simpan sebagai bukti evolusi proyek.
2. **Jangan menggabungkan angka lintas versi tanpa provenance.** Setiap tabel harus menyebut sumber data, schema, dan konfigurasi.
3. **Pisahkan data besar dari artefak Git.** Manifest/hash dan instruksi akses lebih aman daripada meng-*commit* CSV mentah besar.
4. **Gunakan pull request/review untuk perubahan klaim.** Perubahan dokumentasi ilmiah dapat mengubah arti hasil sehingga perlu review seperti perubahan kode.
5. **Tag snapshot paper.** Draft yang masih HOLD harus mempunyai status jelas, misalnya `paper-hold-audit-v1`, agar tidak tertukar dengan naskah siap submit.

Contoh alur konseptual:

```text
main / legacy snapshot
        \
         └── v2-rigorous-audit
                ├── provenance dan claim ledger
                ├── pipeline gap-safe yang terdokumentasi
                ├── evaluasi/hasil negatif yang terversi
                └── audit_reports dan paper status HOLD
```

### 5.2 Struktur direktori dual-track

Struktur berikut mempertahankan pemisahan sejarah, pipeline, dan bukti audit:

```text
repository/
├── legacy_v1/
│   ├── upstream_datmin_snapshot/
│   ├── notebooks_historis/
│   ├── laporan_historis/
│   └── README_LEGACY.md
├── pipeline_v2/
│   ├── preprocessing/
│   ├── windowing/
│   ├── modeling/
│   ├── configs/
│   ├── tests_or_checks/
│   └── README_PIPELINE.md
├── audit_reports/
│   ├── provenance/
│   ├── claim_evidence_ledger/
│   ├── selection_and_ablation/
│   ├── negative_results/
│   ├── holdout_intake/
│   └── acceptance_status/
├── docs/
│   ├── PRISMA/
│   ├── gap_analysis/
│   ├── paper/
│   └── figures_manifest/
├── data_manifests/
│   ├── raw_manifest.example.csv
│   ├── split_manifest.example.csv
│   └── feature_schema.md
└── README.md
```

**`legacy_v1/`** menyimpan konteks asli secara *read-only by convention*: notebook lama, laporan awal, dan catatan bahwa hasilnya historis/terbatas. Folder ini tidak boleh dianggap sebagai pipeline final secara diam-diam.

**`pipeline_v2/`** hanya berisi kode dan konfigurasi yang statusnya jelas. Bila sebuah eksperimen belum diotorisasi atau belum lulus reproduksi, ia harus diberi label spesifikasi/desain, bukan hasil final. Konfigurasi perlu memuat window length/stride, gap policy, feature schema, split, seed, scaler, dan model agar klaim dapat ditelusuri.

**`audit_reports/`** adalah pusat bukti: laporan comparison, status input reproduction, negative lock 78B, intake 16A, selection contract, verdict NO-WINNER, dan acceptance ledger. Menyimpan artefak audit terpisah mencegah laporan ilmiah tertukar dengan output pipeline.

### 5.3 Narasi README yang menghubungkan eksperimen awal dengan audit perbaikan

README utama perlu menceritakan evolusi proyek secara jujur, ringkas, dan tidak defensif. Contoh narasi yang dapat diadaptasi:

> Proyek ini mempelajari clustering deret waktu sensor rig/geotermal multivariat tanpa label. Eksperimen awal (`legacy_v1/`) mengeksplorasi scaling, K-Means, dan ringkasan window. Audit berikutnya menemukan keterbatasan pada provenance keluaran, overlap window, evaluasi temporal, cluster collapse, serta interpretasi rezim tanpa log operasi. Jalur `pipeline_v2/` dan `audit_reports/` menyimpan perbaikan desain dan hasil audit secara terpisah. Pada snapshot saat ini, proyek berstatus **PARTIAL/HOLD**: tidak ada model final atau rezim fisik yang diklaim tervalidasi.

README juga sebaiknya memiliki tabel status eksplisit:

| Komponen | Status aman ditulis |
|---|---|
| Eksperimen K-Means upstream | Historis/eksploratif; bukan bukti final tanpa rekonsiliasi runtime. |
| Window tumbling 60 detik + gap-reset | Desain/audit yang terdokumentasi; klaim empiris mengikuti ledger yang berlaku. |
| Scaler train-only | Kontrak evaluasi temporal; jangan diklaim PASS menyeluruh tanpa bukti acceptance. |
| K-Means vs GMM | Kandidat/baseline yang dibandingkan pada artefak tertentu; bukan kemenangan universal. |
| `k` final | **NO-WINNER** pada keputusan final yang dibekukan. |
| Rezim operasi | Pola statistik/hipotesis; tidak ada ground truth tanpa driller log/ahli independen. |
| 78B | `LOCKED_NEGATIVE` / `UNSUITABLE_H1`. |
| 16A | Kandidat intake, `NOT_OPENED`. |
| Paper IEEE | **HOLD**. |

### 5.4 Aturan migrasi artefak dan klaim

Saat memindahkan dokumen dari jalur lama ke jalur baru, gunakan empat label sederhana:

- **FAKTA TERARSIP:** terlihat pada kode, tabel, file, atau output yang tersedia.
- **HASIL HISTORIS:** pernah dijalankan/dilaporkan, tetapi mungkin tidak dapat direproduksi penuh pada snapshot saat ini.
- **DESIGN_ONLY:** spesifikasi yang belum menjadi bukti empiris.
- **DILARANG DIKLAIM:** misalnya model terbaik, rezim fisik tervalidasi, holdout berhasil, atau C2/C3 selesai ketika gate belum terpenuhi.

Dengan label ini, penggabungan tidak menjadi upaya “memutihkan” eksperimen lama. Ia menjadi catatan ilmiah yang dapat diaudit dan dipahami mahasiswa, dosen, maupun reviewer.

---

## 6. Status Terkini & Langkah Selanjutnya

### 6.1 Kunci negatif 78B

Kandidat 78B telah dikunci sebagai **`LOCKED_NEGATIVE`** dengan verdict **`UNSUITABLE_H1`**. Keputusan ini didasarkan pada temuan bahwa sentinel `-999.25` memengaruhi 100% baris, kanal Gas absen pada 100% baris, Gamma terdampak 60,3%, dan trial cleaning menolak 60,1% kandidat window karena coverage. Memaksa cleaning dalam keadaan tersebut berisiko merusak kontrak 39 fitur dan komparabilitas.

Konsekuensinya tegas:

- H1 tetap **NOT OPENED** (`opened: false`);
- `kmeans_fits: 0` dan `scaler_fits: 0` untuk 78B;
- tidak ada evaluasi, seleksi, atau fit yang boleh diklaim pada dataset itu;
- 78B boleh dilaporkan sebagai hasil negatif/kelayakan holdout, bukan keberhasilan validasi holdout.

### 6.2 Menunggu intake kandidat 16A

Kandidat berikutnya adalah **Well 16A(78)-32 — GDR Submission 1283**. Opsi 1 Hz diprioritaskan bila tersedia dan lolos intake; opsi 10 detik memerlukan adendum windowing sehingga tidak boleh diperlakukan sama dengan data native 1 Hz.

Status 16A masih **DESIGN_ONLY / NOT OPENED**. Saat file tersedia, intake yang diizinkan pada spesifikasi mencakup identitas file, ukuran byte, hash, jumlah baris tanpa memuat penuh, header, pemetaan kolom/unit, serta QC streaming terbatas untuk sentinel/missingness dan kontinuitas timestamp. Tidak ada K-Means, fit scaler, atau pembukaan reserve H1 sebelum exposure dinilai viable dan approval terkunci tersedia.

### 6.3 Progress checklist sembilan butir

Checklist kelayakan paper sembilan butir belum selesai:

| Fase | Status | Makna praktis |
|---|---|---|
| Fase 0–1 | **SEBAGIAN** | Provenance, claim ledger, kontrak seleksi, dan hasil negatif telah didokumentasikan, tetapi belum menutup semua gap. |
| Fase 2–6 | **BELUM** | Tidak ada PASS empiris baru untuk holdout, fit final, validasi domain, keputusan venue, atau finalisasi paper. |
| C2/C3 | **NOT TESTED** | Scope-out final; tidak boleh dipresentasikan sebagai eksperimen selesai. |
| Tahap 1 | **BLOCKED** | Reproduksi input gagal; tidak ada jalan pintas dengan melonggarkan toleransi. |
| H1 | **NOT OPENED** | Exposure masih `INSUFFICIENT_CLEAN_HOLDOUT`; holdout belum dapat digunakan. |
| Review independen lintas-keluarga | **OPEN** | Diperlukan pada snapshot stabil sebelum aktivasi klaim/paper. |

### 6.4 Langkah berikutnya yang aman secara ilmiah

1. **Pertahankan status dan batas klaim.** Jangan mengubah `PARTIAL/HOLD`, `NO-WINNER`, `NOT TESTED`, atau `LOCKED_NEGATIVE` menjadi narasi keberhasilan.
2. **Lengkapi dokumentasi tanpa mengubah bukti.** Konsolidasikan PRISMA, *gap analysis*, provenance, dan ledger klaim bila diminta, dengan label fakta/desain yang jelas.
3. **Jika 16A tersedia, lakukan intake sesuai gate.** Fokus pada fingerprint, header, sensor map, sentinel, dan kontinuitas—bukan pada fit atau clustering.
4. **Sebelum kerja empiris apa pun, siapkan approval terpisah.** Approval perlu mencakup protokol/hash, scope data, compute, split/embargo, dan evaluasi yang dikunci.
5. **Dapatkan validasi domain sebelum penamaan fisik.** Driller log, event log, atau panel ahli independen diperlukan untuk menguji hipotesis rezim.
6. **Siapkan snapshot stabil untuk reviewer independen lintas-keluarga.** Review harus memeriksa artefak nyata terhadap acceptance criteria, bukan hanya merangkum narasi implementer.
7. **Aktifkan/submit paper hanya setelah gerbang terpenuhi.** Paper harus tetap menonjolkan hasil negatif dan limitasi bila bukti positif belum tersedia.

---

## Penutup

Perbedaan terpenting antara repo upstream dan sistem audit bukan semata-mata `stride=30` versus `stride=60`, K-Means versus GMM, atau `k=4` versus kandidat lain. Perbedaannya adalah disiplin inferensi. Repo lama menyediakan eksplorasi awal yang berguna; audit mengajarkan kapan eksplorasi itu boleh menjadi klaim, kapan harus menjadi hipotesis, dan kapan hasil yang paling benar adalah **belum ada pemenang**.

Bagi proyek UTS, sikap tersebut menghasilkan naskah yang lebih kuat: mahasiswa tetap dapat menjelaskan data sensor multivariat, preprocessing temporal, clustering, dan evaluasi; tetapi mereka tidak mengubah pola statistik menjadi fakta fisik tanpa bukti. Bagi publikasi, sikap yang sama menjaga reproducibility, menghormati hasil negatif, dan membuat batas klaim dapat diperiksa oleh pembaca berikutnya.

---

## Jejak Bukti Internal Utama

- `Datmin-new/PROYEK UTS Data Mining.md` — tema, tahapan, dan luaran tugas UTS.
- `_audit-upstream/method-upstream.md` — rekonstruksi faktual artefak upstream.
- `_audit-upstream/method-datmin-new.md` — ekstraksi pipeline/data lokal dan gap yang teridentifikasi.
- `_audit-upstream/method-rubric.md` — rubrik normatif kelayakan clustering time-series.
- `_audit-upstream/step2-split-baseline.md` — desain split temporal, train-only scaler, dan batas interpretasi baseline historis.
- `_audit-upstream/k-final-selection.md` — keputusan `no winner; insufficient evidence`.
- `_audit-upstream/upstream-evidence.md` dan `_audit-upstream/diag-cap01-verdict.md` — occupancy/cluster collapse dan guard sehat.
- `_audit-upstream/h1-78b-negative-lock-v1.md` — 78B `LOCKED_NEGATIVE` / `UNSUITABLE_H1`.
- `_audit-upstream/h1-16a-intake-spec-v1.md` — protokol intake 16A yang masih `DESIGN_ONLY`.
- `_audit-upstream/STATUS-SESI-2026-10-13.md` dan `HANDOFF.md` — state proyek terkini: `PARTIAL/HOLD`.

> **Catatan akhir:** daftar ini adalah penunjuk provenance internal. Pembaca tetap perlu membedakan artefak faktual, hasil historis, dan spesifikasi desain sebelum menarik kesimpulan empiris.
