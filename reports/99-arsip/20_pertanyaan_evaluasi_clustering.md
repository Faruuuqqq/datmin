# 20 Pertanyaan & Jawaban Kritis Penguji/Dosen: Clustering & Evaluasi (Orang 4 — Fathan)
**Proyek UTS Data Mining:** *Impact of Feature Scaling and Temporal Window Aggregation on Multivariate Geothermal Drilling Sensor Clustering Using K-Means*  
**Dataset:** Utah FORGE Well 56-32 (1 Hz Surface Rig Telemetry, 2.506.360 baris)

---

## DAFTAR ISI PERTANYAAN

- [Pilar 1: Pemilihan Algoritma & Penskalaan (Q1 – Q5)](#pilar-1-pemilihan-algoritma--penskalaan-q1--q5)
- [Pilar 2: Rekayasa Deret Waktu & Jendela (Q6 – Q9)](#pilar-2-rekayasa-deret-waktu--jendela-q6--q9)
- [Pilar 3: Evaluasi & Penentuan Nilai $k$ (Q10 – Q13)](#pilar-3-evaluasi--penentuan-nilai-k-q10--q13)
- [Pilar 4: Interpretasi Fisik Centroid & Validasi (Q14 – Q17)](#pilar-4-interpretasi-fisik-centroid--validasi-q14--q17)
- [Pilar 5: Limitasi & Kesiapan Penerapan (Q18 – Q20)](#pilar-5-limitasi--kesiapan-penerapan-q18--q20)

---

## Pilar 1: Pemilihan Algoritma & Penskalaan (Q1 – Q5)

### Q1. "Kenapa memilih K-Means? Kenapa tidak DBSCAN, GMM, atau Hierarchical Clustering?"
**Jawaban:**
1. **Kompleksitas & Skalabilitas:** Dataset kami memiliki volume 2,5 juta baris (1 Hz). Hierarchical Clustering berorde $\mathcal{O}(N^2)$ hingga $\mathcal{O}(N^3)$ sehingga memicu *Out-Of-Memory* (OOM). DBSCAN sangat sensitif terhadap parameter $\epsilon$ pada data berkerapatan jomplang (90% data idle), sementara GMM membutuhkan komputasi matriks kovariansi invertibel yang rentan singular akibat kolom berfluktuasi nol.
2. **Kebutuhan Interpretasi Fisik:** K-Means menghasilkan representasi titik pusat (*centroid*) eksplisit pada tiap atribut sensor ($\mu_j$). Koordinat centroid ini dapat di-inverse transform kembali ke satuan fisik instrumen (psi, RPM, ft/hr) untuk dipetakan secara objektif ke 4 rezim operasional rig standar industri (Coley, 2019).
3. **Baseline Komparatif:** Paper rujukan PRISMA kami ([1], [2]) menetapkan K-Means sebagai algoritma pembanding baku untuk *unsupervised operational state discovery*.

---

### Q2. "Kenapa baseline tanpa penskalaan (Unscaled) dilarang digunakan, padahal nilai Silhouette-nya terlihat tinggi (0.9066)?"
**Jawaban:**
- Nilai Silhouette unscaled sebesar 0.9066 adalah **ilusi matematis akibat fenomena *Euclidean Collapse***. 
- Dataset memiliki rasio ketimpangan skala ekstrem **$258.9 : 1$**. Tekanan pompa (SPP) bernilai ribuan psi ($1.200 - 5.200\text{ psi}$), sedangkan Torsi hanya berfluktuasi pada kisaran satuan ($0 - 41\text{ kft}\cdot\text{lb}$).
- Pada rumus jarak Euclidean $d^2 = \sum (x_i - y_i)^2$, kuadrat selisih SPP mendominasi $>99\%$ perhitungan jarak. Klaster yang terbentuk hanya membelah SPP tinggi vs rendah, sementara seluruh sensor pemotongan batuan (WOB, RPM, Torsi) terabaikan mutlak. K-Means menjadi 'buta' terhadap dinamika mekanik bor.

---

### Q3. "Kenapa RobustScaler jauh lebih unggul dibandingkan StandardScaler (Z-Score)?"
**Jawaban:**
- StandardScaler menggunakan *mean* dan *standard deviation* ($\mu, \sigma$) yang **sangat rentan terdistorsi oleh pencilan (*outliers*)**. Pada dataset ini, kurtosis tarikan derek ROP mencapai $2.867$ dengan skewness $+34$.
- RobustScaler menggunakan acuan berbasis **Median dan Interquartile Range (IQR)**:
  $$x_{\text{scaled}} = \frac{x - \text{median}(x)}{\text{IQR}(x)}$$
- Rentang IQR kebal terhadap lonjakan ekstrem akibat *drawworks hoisting* maupun getaran mekanis (*stick-slip*). Terbukti empiris pada Tabel 2: RobustScaler menghasilkan **Silhouette 0.9836** dan **DBI 0.2103** (jauh melampaui StandardScaler: Sil 0.6592, DBI 0.6278).

---

### Q4. "Kenapa fitur *Differential Pressure* dibuang dan hanya 7 sensor yang dimodelkan?"
**Jawaban:**
- Berdasarkan audit EDA Tahap 2, kolom `Differential Pressure` memiliki rata-rata bernilai negatif ($-692\text{ psi}$) dan nilai minimum hingga $-5.138\text{ psi}$.
- Secara fisika hidraulika rig pemboran, tekanan diferensial tidak boleh bernilai negatif ekstrem saat pompa mati. Ini adalah **cacat algoritma software rig Pason EDR** yang mengurangkan angka nol dengan nilai acuan lama. Memasukkan fitur cacat ini akan mendistorsi fungsi objektif jarak Euclidean K-Means.

---

### Q5. "Apa tujuan merancang 4 skenario eksperimen ({Point, Window-60s} $\times$ {Standard, Robust})?"
**Jawaban:**
- Ini adalah desain **eksperimen faktorial terkontrol $2 \times 2$**.
- Tujuannya untuk mengisolasi dan mengukur dua pengaruh secara independen:
  1. **Efek normalisasi:** StandardScaler vs RobustScaler (menguji hipotesis penanganan disparitas skala ekstrem RQ1).
  2. **Efek representasi temporal:** Titik instan per-detik vs agregasi jendela waktu 60 detik (menguji hipotesis peredaman autokorelasi deret waktu RQ2).

---

## Pilar 2: Rekayasa Deret Waktu & Jendela (Q6 – Q9)

### Q6. "Kenapa menggunakan Sliding Window durasi 60 detik dengan stride 30 detik?"
**Jawaban:**
- **Landasan Teoretis (Keogh & Lin, 2005):** Melakukan klasterisasi langsung pada deret waktu mentah (*raw subsequences*) terbukti tidak bermakna (*meaningless*). Solusi yang valid adalah mengekstraksi ringkasan fitur statistik per jendela.
- **Justifikasi Fisik Rig:** Durasi 60 detik (1 menit) mencerminkan waktu inersia fluida lumpur merespons perubahan pompa di permukaan hingga ke dasar lubang bor (*circulation loop response time*).
- **Stride 30 detik:** Memberikan overlap 50% untuk mempertahankan kontinuitas temporal tanpa kehilangan transisi penting antar-fase manuver driller.

---

### Q7. "Statistik apa saja yang diekstraksi dari setiap jendela 60 detik dan apa makna fisiknya?"
**Jawaban:**
Kami mengekstraksi 3 fitur statistik per sensor ($7 \times 3 = 21$ fitur):
1. **Mean ($\mu_w$):** Menangkap besaran daya/level rata-rata operasi peralatan rig.
2. **Standard Deviation ($\sigma_w$):** Menangkap intensitas getaran mekanik (*vibration*) atau ketidakstabilan proses pemotongan batuan granit.
3. **Delta ($\Delta_w = x_{\text{akhir}} - x_{\text{awal}}$):** Menangkap arah tren apakah parameter sedang dinaikkan (misal *ramping up* pompa) atau diturunkan.

---

### Q8. "Di Tabel 3, kenapa Silhouette representasi Point (0.9304) lebih tinggi daripada Window-60s (0.8570)? Bukankah Window dirancang untuk memperbaiki model?"
**Jawaban (Pelaporan Jujur & Objektif):**
- **Kami melaporkan ini secara jujur di paper:** Nilai Silhouette representasi titik terinflasi (*inflated*) karena pada kedalaman awal sumur, lebih dari 85% data berada pada status *idle* (semua sensor bernilai 0). Kumpulan titik nol yang identik ini membentuk klaster yang luar biasa rapat secara spasial.
- **Kelemahan fatal Point-based di lapangan:** Memicu **efek *chattering / flickering***, di mana label klaster berganti-ganti liar tiap detik akibat noise instrumen, padahal mesin rig dalam kondisi stabil.
- **Keunggulan Window-60s:** Mengompresi baris data 60 kali lipat, mengeliminasi autokorelasi lag-1 tinggi ($r > 0.99$), menghasilkan label stabil per menit, dan secara bersamaan menangkap dinamika getaran ($\sigma$) yang mustahil ditangkap oleh data titik instan.

---

### Q9. "Kenapa ROP di-winsorize pada batas 47.4 ft/hr?"
**Jawaban:**
- Sensor ROP mencatat lonjakan artifisial hingga **$11.145\text{ ft/hr}$** dengan kurtosis masif **$2.867$**.
- Pengeboran batuan granit Utah FORGE mustahil menembus $11.000\text{ ft/hr}$. Lonjakan ini adalah **artefak tarikan derek (*drawworks hoisting spike*)**, yaitu ketika katrol derek menarik rangkaian pipa ke atas dengan cepat saat proses penyambungan pipa di udara.
- Kami membatasi (*winsorize*) pada kuantil batas atas $Q3 + 1.5 \times \text{IQR} = 47.4\text{ ft/hr}$ agar K-Means tidak membentuk klaster semu khusus hanya untuk mewadahi pencilan mekanik non-pengeboran.

---

## Pilar 3: Evaluasi & Penentuan Nilai $k$ (Q10 – Q13)

### Q10. "Kenapa menggunakan subsampel 20.000 baris untuk menghitung Silhouette dan DBI, bukan seluruh dataset?"
**Jawaban:**
- **Kompleksitas Komputasi:** Menghitung Silhouette Coefficient membutuhkan matriks jarak *pairwise* antar-seluruh titik dengan kompleksitas $\mathcal{O}(N^2)$.
- Pada $N = 60.000$, komputasi membutuhkan kalkulasi $3,6 \times 10^9$ pasang jarak yang memakan waktu berjam-jam dan rentan memicu kehabisan memori (*RAM crash*).
- Sampel acak berukuran $20.000$ (seed 42) telah terbukti secara statistik konvergen dan stabil untuk mengevaluasi peringkat komparatif antar-skenario dengan deviasi $< 0.005$.

---

### Q11. "Kenapa mengevaluasi dengan DUA metrik (Silhouette dan Davies-Bouldin Index)? Apa perbedaannya?"
**Jawaban:**
- **Silhouette Score ($[-1, 1]$, makin tinggi makin baik):** Mengukur rasio antara kelekatan intra-klaster ($a$) dan jarak ke klaster tetangga terdekat ($b$). Sensitif terhadap bentuk dan kepadatan klaster.
- **Davies-Bouldin Index ($[0, \infty)$, makin rendah makin baik):** Mengukur rasio kesamaan terburuk antara jarak sebaran centroid terhadap jarak pemisah antar-centroid.
- **Alasan menggunakan keduanya:** Mencegah bias metrik tunggal. Pada data sensor industri, Silhouette rentan bias terhadap klaster nol yang hiper-padat, sehingga DBI berfungsi sebagai verifikator pemisahan jarak absolut antar-centroid.

---

### Q12. "Di Gambar 5a kurva Elbow (Inertia vs $k$) terlihat landai tanpa siku tajam. Atas dasar apa kalian menentukan $\text{BEST\_K} = 4$?"
**Jawaban:**
- **Kami tuliskan secara eksplisit dan jujur di paper:** Kurva inersia pada data sensor multivariat tidak menunjukkan titik patahan (*elbow kink*) yang tajam karena karakteristik data fisik yang bertransisi kontinu.
- Nilai **$\text{BEST\_K} = 4$ dipilih berbasis integrasi domain (*domain-driven selection*)**, merujuk pada taksonomi 4 rezim operasional pemboran Coley (2019):
  1. *Active Rotary Drilling*
  2. *Circulation & Hole Cleaning*
  3. *High-Pressure Wellbore Test / Shut-In*
  4. *Idle / Tripping Standby*
- Pada $k > 4$, penambahan klaster hanya memecah status idle menjadi sub-varian yang tidak memiliki perbedaan tindakan operasional (*redundant operational states*).

---

### Q13. "Kenapa K-Means dijalankan dengan parameter `n_init=10` dan `seed=42`?"
**Jawaban:**
- K-Means menggunakan inisialisasi k-means++ yang memiliki komponen probabilistik dan rentan terjebak pada minimum lokal.
- `n_init=10` memastikan algoritma dijalankan 10 kali dengan titik awal centroid berbeda, dan solusi dengan inersia terendah yang dipilih sebagai model final.
- `seed=42` dikunci mati di seluruh pipeline untuk menjamin prinsip keterulangan ilmiah (*reproducibility*).

---

## Pilar 4: Interpretasi Fisik Centroid & Validasi (Q14 – Q17)

### Q14. "Bagaimana cara membaca fisik Centroid pada Tabel 5? Jelaskan maknanya!"
**Jawaban:**
Kami mengonversi koordinat centroid kembali ke satuan fisik instrumen asli:
- **Klaster 0 (Active Rotary Drilling, 95.40%):** ROP $14.21\text{ ft/hr}$, RPM $17.2$, WOB $18.7\text{ klbs}$, SPP $1.246\text{ psi}$, Pompa $265\text{ GPM}$, Torsi $2.24\text{ kft}\cdot\text{lb}$. $\to$ *Mata bor berputar, lumpur mengalir stabil, beban pada pahat aktif memotong granit pada kedalaman formasi.*
- **Klaster 1 (High-Pressure Resistant Zone, 0.71%):** ROP $10.58\text{ ft/hr}$, RPM $18.9$, WOB $10.8\text{ klbs}$, SPP $1.491\text{ psi}$, Pompa $276\text{ GPM}$. $\to$ *Penetrasi formasi keras bertekanan hidraulik tinggi.*
- **Klaster 2 (Circulation & Hole Cleaning, 0.71%):** ROP $0.41\text{ ft/hr}$, RPM $14.0$, WOB $5.6\text{ klbs}$, SPP $1.414\text{ psi}$, Pompa maksimum di $368\text{ GPM}$. $\to$ *Sirkulasi intensif pembersihan serbuk bor (cuttings) dengan debit pompa hidraulik tertinggi tanpa pemboran agresif.*
- **Klaster 3 (Pipe Connection / Standby Slips, 3.17%):** ROP $0.11$, RPM $0.29$ (~0 rotasi), Pompa $11.7\text{ GPM}$ (~0 pompa), SPP $20\text{ psi}$, WOB $34.75\text{ klbs}$ (beban rangkaian tertahan di meja putar). $\to$ *Penyambungan pipa bor baru (connection) atau standby.*

---

### Q15. "Kenapa pada run awal kalian sempat menemukan nilai RPM negatif (-3.3 RPM) dan bor menembus formasi tanpa tekanan pompa? Apakah modelnya rusak?"
**Jawaban:**
- Itu adalah **bug teknis pada pemotongan indeks fitur di Cell 32**, bukan kegagalan algoritma K-Means.
- Saat menyusun fitur jendela, kolom dibuat berselang-seling: `[ROP_mean, ROP_std, ROP_delta, WOB_mean, ...]`. Kode lama melakukan *slicing* `cent[:, :7]`, sehingga fitur delta ROP (yang bernilai negatif saat laju melambat) terpental dan terlabeli sebagai RPM!
- Setelah kami perbaiki formula penarikan kolom `__mean` secara presisi menggunakan `mean_indices`, seluruh koordinat centroid langsung konsisten dengan hukum fisika rig pemboran (RPM positif realistis 17.23, pompa aktif 265 GPM, SPP 1246 psi).

---

### Q16. "Kenapa proporsi Klaster Active Drilling (Klaster 0) dominan mencapai 95.40%?"
**Jawaban:**
- Ini mencerminkan **kondisi riil seluruh interval kedalaman sumur (sampling sistematis full-span 2,5 juta baris)**.
- Setelah sampel diperluas mencakup rentang penuh sebulan operasi (bukan hanya kepala sumur Feb awal), mayoritas aktivitas rig Utah FORGE Well 56-32 memang didedikasikan untuk penetrasi formasi batuan granit keras secara berkesinambungan dengan sirkulasi lumpur aktif.

---

### Q17. "Apa yang dibuktikan oleh visualisasi PCA 2D di Gambar 6?"
**Jawaban:**
- PCA mereduksi 21 fitur jendela menjadi 2 komponen utama (PC1 dan PC2) yang merangkum variansi terbesar data.
- Scatter plot Gambar 6 membuktikan bahwa 4 rezim klaster terpisah dalam kelompok awan (*clusters*) yang kohesif tanpa tumpang-tindih liar, mengonfirmasi bahwa batasan klaster K-Means berhasil memisahkan dinamika fisik rig secara tegas.

---

## Pilar 5: Limitasi & Kesiapan Penerapan (Q18 – Q20)

### Q18. "Apa kelemahan/limitasi paling mendasar dari penelitian clustering yang kalian lakukan?"
**Jawaban (Menunjukkan Kematangan Akademis):**
1. **Keterbatasan Segmen Sampel:** Pengujian dilakukan pada 60.000 baris segmen awal sumur (Februari, dangkal) karena efisiensi memori. Ini belum mencakup keseluruhan dinamika sebulan penuh hingga kedalaman $9.000\text{ ft}$.
2. **Inflasi Metrik Akibat Nol:** Banyaknya sensor yang bernilai 0 saat rig *idle* menggelembungkan nilai Silhouette score.
3. **Bentuk Klaster Sferis:** Asumsi K-Means mengasumsikan klaster berbentuk bola (*convex/spherical*), padahal transisi parameter rig bisa bersifat manifold melengkung.

---

### Q19. "Jika ingin melanjutkan penelitian ini, perbaikan apa yang paling kalian rekomendasikan?"
**Jawaban:**
1. **Sampling Berimbang Sepanjang Kedalaman (*Stratified Full-Range Sampling*):** Mengambil sampel dari interval kedalaman dangkal, menengah, hingga granit dalam ($2,5\text{ juta baris}$) menggunakan metode *chunk streaming*.
2. **Perbandingan dengan Metode Densitas:** Menguji **HDBSCAN** untuk melihat apakah data idle dapat dikelompokkan sebagai *background density* dan anomali tarikan derek sebagai *noise*.
3. **Re-integrasi Differential Pressure:** Mengoreksi anomali nol pada sensor tekanan diferensial menggunakan regresi hidraulika sebelum dimasukkan kembali ke klasterisasi.

---

### Q20. "Bagaimana sistem ini diimplementasikan di industri nyata (Deployment CRISP-DM)?"
**Jawaban:**
- Sistem dapat dipasang sebagai modul **Pelabelan Otomatis Real-Time (*Real-Time Rig State Classification*)** di kabin *driller*.
- Alur deployment:
  1. Telemetri 1 Hz masuk ke *buffer* FIFO 60 detik.
  2. Ekstraksi $\mu, \sigma, \Delta$ secara instan (hanya butuh komputasi matriks ringan $< 5\text{ ms}$).
  3. Normalisasi menggunakan parameter RobustScaler yang sudah dilatih (*pre-fitted*).
  4. Menghitung jarak Euclidean terdekat ke 4 centroid dan memunculkan indikator status rig di layar operator secara otomatis tanpa perlu pencatatan manual kru bor.

---

### Panduan Taktis Saat Ujian / Presentasi:
1. **Istilah Kunci:** Selalu gunakan terminologi ilmiah: *"Euclidean Collapse"*, *"Drawworks Hoisting Spike"*, *"Temporal Chattering"*, *"Coley 2019 Rig Regimes"*, *"Median-IQR Scaling"*.
2. **Sikap Akademis:** Jangan membela model secara membabi-buta. Jika ditanya kelemahan, sambut dengan: *"Betul Ibu/Bapak, fenomena tersebut telah kami identifikasi dan laporkan secara jujur di Bab III dan Bab IV sebagai limitasi penelitian kami..."*
3. **Kekuatan Bukti Angka:** Kuasai angka tabel kunci: **Robust Sil 0.9836 / DBI 0.2103** vs **Standard 0.6592 / 0.6278**.
