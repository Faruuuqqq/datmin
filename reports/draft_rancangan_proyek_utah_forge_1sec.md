# Draft Rancangan Proyek Data Mining & Dokumentasi Sensor Utah FORGE (Interval 1 Detik)

---

## 1. Usulan Judul Paper (Format IEEE)

Berdasarkan ketentuan tugas dosen (harus mencerminkan: **Domain Sensor**, **Jumlah Atribut Multivariat**, dan **Algoritma Clustering**), berikut adalah 3 opsi judul yang siap digunakan:

* **Opsi 1 (Paling Direkomendasikan - Fokus Temporal & Skala):**  
  > *“Analisis Pengaruh Penskalaan dan Agregasi Jendela Waktu terhadap Klasterisasi Delapan Sensor Pemantau Pemboran Geotermal Menggunakan K-Means”*  
  > *(Versi Inggris: "Impact of Feature Scaling and Temporal Window Aggregation on Multivariate Geothermal Drilling Sensor Clustering Using K-Means")*

* **Opsi 2 (Fokus Penemuan Regime Operasi Geotermal):**  
  > *“Klasterisasi Deret Waktu Multivariat Sensor Rig Pengeboran Panas Bumi Utah FORGE Berbasis K-Means untuk Identifikasi Rezim Operasi”*  
  > *(Versi Inggris: "Multivariate Time-Series Clustering of Utah FORGE Geothermal Drilling Sensors for Operational Regime Identification Using K-Means")*

* **Opsi 3 (Ringkas & Langsung):**  
  > *“Pemodelan Klasterisasi Deret Waktu Data Sensor Multivariat Rig Geotermal Menggunakan Algoritma K-Means”*

---

## 2. Tujuan Penelitian & Eksperimen

### A. Tujuan Utama (Business & Engineering Understanding)
1. **Mengidentifikasi Pola Rezim Operasi Pemboran Tanpa Label (*Unsupervised Operational Regime Discovery*)**:  
   Mengelompokkan data sensor mesin bor berkecepatan tinggi (1 detik) ke dalam klaster kondisi operasi nyata (misalnya: *Active Drilling / Penetration*, *Circulation & Hole Cleaning*, *Reaming / Tripping*, dan *Idle / Pipe Connection*) tanpa mengandalkan label manual manusia.
2. **Mengevaluasi Pengaruh Ketimpangan Skala (*Scale Disparity*)**:  
   Menganalisis performa algoritma berbasis jarak Euclidean (K-Means) ketika menghadapi perbedaan skala ekstrem (misalnya tekanan ribuan psi versus kecepatan bor satuan ft/hr), membandingkan teknik penskalaan standar (*StandardScaler*) dengan penskalaan tahan pencilan (*RobustScaler*).
3. **Mempertahankan Ketergantungan Temporal (*Temporal Dependency - Nilai Bonus*)**:  
   Menguji apakah representasi deret waktu menggunakan metode **jendela geser (*sliding window aggregation*)** menghasilkan struktur klaster yang lebih stabil dan bermakna dibandingkan klasterisasi baris per baris secara terpisah (*point-based*).

---

## 3. Penjelasan Lengkap Dataset `56-32 1sec data 27029986.csv`

Dataset ini merupakan data rekaman sensor berkecepatan tinggi (**1 Hz atau 1 catatan setiap 1 detik**) dari komputer pemantau rig (*Pason Data System*) pada pemboran **Sumur Geotermal 56-32 (Utah FORGE)**. Berkas ini mencakup operasi pemboran menembus batuan granit keras dari tanggal 8 Februari 2021 hingga selesai dengan total $\approx 2,5$ juta baris data.

### Penjelasan 22 Kolom Data (Satu per Satu):

| No | Nama Kolom di CSV | Satuan Fisik | Penjelasan Fungsi & Makna Sensor | Rekomendasi Pemodelan |
|:--:|---|:---:|---|:---:|
| 1 | `YYYY/MM/DD` | Tanggal | Tanggal kalender saat data dicatat (Format: Tahun/Bulan/Hari). | **Fitur Waktu (Index)** |
| 2 | `HH:MM:SS` | Jam:Menit:Detik | Waktu presisi tinggi pencatatan sensor (berjalan bertambah per 1 detik). | **Fitur Waktu (Index)** |
| 3 | `Hole Depth (feet)` | Kaki (*ft*) | Kedalaman total lubang sumur yang telah berhasil ditembus dari permukaan tanah. | Atribut Kontekstual |
| 4 | `Bit Depth (feet)` | Kaki (*ft*) | Posisi kedalaman fisik mata bor saat ini. Jika nilainya sama dengan *Hole Depth*, bor berada di dasar batuan (*on-bottom drilling*). Jika lebih dangkal, bor sedang ditarik ke atas (*off-bottom*). | Sensor Kontinu |
| 5 | `Rate Of Penetration (ft_per_hr)` | *ft/hr* | **ROP**: Kecepatan laju mata bor menembus batuan bumi. Nilai tinggi menandakan batuan sedang ditembus cepat; nilai 0 berarti bor sedang berhenti/berputar di tempat. | **Sensor Utama (Wajib)** |
| 6 | `Weight on Bit (klbs)` | *kilo-pounds* ($10^3$ lbs) | **WOB**: Beban tekan vertikal mekanik yang diberikan pada mata bor agar menekan batuan ($0$–$50\text{ klbs}$). | **Sensor Utama (Wajib)** |
| 7 | `Rotary RPM (RPM)` | Putaran per menit | Kecepatan putaran pipa dan mata bor saat berputar menggerus batuan. | **Sensor Utama (Wajib)** |
| 8 | `Standpipe Pressure (psi)` | *psi* | Tekanan hidrolik lumpur pemboran di pipa tegak rig sebelum disuntikkan masuk ke lubang sumur ($0$–$3.500\text{ psi}$). | **Sensor Utama (Wajib)** |
| 9 | `Rotary Torque (kft_lb)` | *kft-lbs* | Torsi/momen puntir yang dibutuhkan motor rig untuk memutar rangkaian pipa di dalam lubang sumur. | **Sensor Utama (Wajib)** |
| 10 | `Hook Load (klbs)` | *kilo-pounds* | Total beban tarikan yang ditahan oleh gantungan menara rig (*derrick hook*), mencerminkan berat seluruh rangkaian pipa bor di dalam sumur ($50$–$250\text{ klbs}$). | **Sensor Utama (Wajib)** |
| 11 | `Differential Pressure (psi)` | *psi* | Selisih tekanan lumpur hidrostatik di motor dasar sumur. | **Sensor Utama (Wajib)** |
| 12 | `Flow (flow_percent)` | Persentase ($\%$) | Sensor persentase laju aliran balik fluida lumpur yang keluar kembali ke permukaan ($0$–$100\%$). | **Sensor Tambahan** |
| 13 | `Total Pump Output (gal_per_min)` | *gal/min* (GPM) | Total debit semprotan pompa lumpur pemboran yang dialirkan ke dalam sumur ($0$–$900\text{ GPM}$). | **Sensor Utama (Wajib)** |
| 14 | `Pason Gas (percent)` | Persentase ($\%$) | Detektor gas alam berbahaya di dalam lumpur. *(Catatan: Nilai `-999.25` adalah kode missing value sensor tidak aktif).* | *Drop / Abaikan* |
| 15 | `Pason Lag Depth (feet)` | Kaki (*ft*) | Perhitungan estimasi kedalaman asal serpihan batuan yang baru saja mencapai permukaan karena jeda waktu sirkulasi lumpur. | Atribut Kontekstual |
| 16 | `Total Mud Volume (barrels)` | Barel ($1\text{ bbl} \approx 159\text{ L}$) | Total volume fluida lumpur sirkulasi yang tersimpan di tangki permukaan (*mud pit*). | Sensor Kontinu |
| 17 | `Block Height (feet)` | Kaki (*ft*) | Posisi ketinggian blok penarik derek (*traveling block*) dari lantai bor rig. | Sensor Kontinu |
| 18 | `PVT Total Mud Gain/Loss (barrels)` | Barel | Pertambahan/kehilangan volume lumpur tangki. Jika nilainya melonjak naik: ada fluida formasi bumi yang masuk (*kick*); jika minus: lumpur meresap bocor ke retakan batuan (*lost circulation*). | Sensor Kontinu |
| 19 | `PVT Monitor Mud Gain/Loss (barrels)` | Barel | Perhitungan gain/loss khusus pada tangki pemantau presisi (*trip tank / monitor pit*). | Sensor Kontinu |
| 20 | `Flow 1 Gain/Loss (percent)` | Persentase ($\%$) | Fluktuasi kenaikan/penurunan persentase aliran sensor 1. | Sensor Kontinu |
| 21 | `Gamma (api)` | Satuan *API* | Sensor radioaktivitas alami batuan formasi (pencatat litologi batuan). Nilai `-999.25` menunjukkan data tidak aktif saat interval ini. | *Drop / Abaikan* |
| 22 | `Pump 1 strokes/min (SPM)` | Kayuhan per menit | Kecepatan kayuhan piston pada pompa lumpur rig nomor 1. | Sensor Kontinu |

---

## 4. Rekomendasi Fitur untuk Pemodelan Klasterisasi

Untuk memenuhi syarat **minimal 5 atribut numerik kontinu** dan menghindari sensor yang tidak aktif (bernilai `-999.25`), disarankan memilih **7–8 sensor utama** berikut:

1. `Rate Of Penetration (ft_per_hr)` (Skala: $0$ – $150$)
2. `Weight on Bit (klbs)` (Skala: $0$ – $50$)
3. `Rotary RPM (RPM)` (Skala: $0$ – $160$)
4. `Standpipe Pressure (psi)` (Skala: $500$ – $3.500$)
5. `Rotary Torque (kft_lb)` (Skala: $1$ – $25$)
6. `Hook Load (klbs)` (Skala: $50$ – $250$)
7. `Total Pump Output (gal_per_min)` (Skala: $0$ – $900$)
8. `Differential Pressure (psi)` (Skala: $0$ – $500$)

### Mengapa Kombinasi Sensor Ini Sempurna untuk Paper UTS?
* **Ketimpangan Skala Jelas**: Perhitungan jarak Euclidean murni akan 100% dikuasai oleh `Standpipe Pressure` (ribuan psi) dan menenggelamkan `Rotary Torque` (satuan/belasan kft-lb) serta `WOB`. Ini menjadi dasar kuat untuk mengkaji perbandingan penskalaan (*StandardScaler* vs *RobustScaler*).
* **Fisika Operasi yang Nyata**:
  * Saat **Pengeboran Aktif (*Drilling*)**: WOB $> 0$, RPM $> 0$, Tekanan Pompa tinggi, ROP $> 0$.
  * Saat **Sirkulasi Pembersihan (*Circulation*)**: WOB $\approx 0$, ROP $= 0$, Pompa tetap jalan tinggi untuk mengangkat serpihan batu.
  * Saat **Penyambungan Pipa (*Pipe Connection*)**: Pompa mati, RPM $= 0$, Hook Load berubah drastis karena pipa diangkat/digantung.
  * Klaster yang dihasilkan K-Means akan memiliki interpretasi fisik yang sangat logis dan elegan saat ditulis di Bab III (Hasil dan Pembahasan) paper IEEE!

---

## 5. Status Eksekusi Tahap 1 & Tahap 2 (Telah Selesai)

Dokumentasi detail eksekusi nyata telah disusun lengkap pada berkas terpisah:
1. **Laporan Bab I & Bab II Lengkap:** [laporan_tahap1_dan_tahap2_utah_forge.md](laporan_tahap1_dan_tahap2_utah_forge.md)
   * **Tahap 1 (PRISMA & Gap Analysis):** Identifikasi literatur Scopus/OpenAlex $N = 655$ hits ($n > 500$ terpenuhi), diagram alir PRISMA 2020 lengkap, serta tabel Gap Analysis kontribusi kelompok.
   * **Tahap 2 (Data Understanding & Preprocessing Plan):** Statistik deskriptif lengkap (mean, std, min, median, max, skewness, kurtosis) dari $2.506.359$ baris data, analisis kode sentinel `-999.25` (Differential Pressure 37,6% offline), matriks korelasi hidrolik/mekanik, analisis outlier IQR, dan rencana 5 langkah preprocessing.
2. **Daftar 16 Paper Acuan Scopus Terverifikasi:** [reference.md](reference.md) (Dilengkapi tautan Scopus via portal kampus Unpad).
3. **Grafik Visualisasi Pendukung (Resolusi Tinggi 300 DPI):**
   * Matriks Korelasi: `korelasi_sensor_utah_forge.png`
   * Komparasi Penskalaan & Outlier: `sebaran_outlier_boxplot.png`
   * Karakteristik Rezim Hidrolik/Mekanik: `sebaran_regim_scatter.png`

