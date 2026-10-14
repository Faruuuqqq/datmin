# TABEL GAP ANALYSIS LITERATUR (TAHAP 1 UTS DATA MINING)

## 1. Deskripsi Singkat
Tabel ini merangkum 9 paper acuan utama hasil seleksi sistematis menggunakan pedoman **PRISMA 2020** (*Preferred Reporting Items for Systematic Reviews and Meta-Analyses*). Alur reduksi literatur dimulai dari **740** rekaman awal dari basis data Scopus, disaring berdasarkan batas tahun dan relevansi subjek menjadi **175** paper, dikerucutkan melalui penapisan judul/abstrak tahap pertama (*Pass-1 screening*) menjadi **127** paper kandidat, dan akhirnya disaring secara teliti melalui telaah teks lengkap (*Full-text eligibility assessment*) menjadi **9 paper inti**. 

Sebagai pembanding kontribusi, disematkan baris **Penelitian Kita (Well 56-32 Clean Pipeline)** untuk memetakan kebaruan (*novelty*), mitigasi kelemahan metodologis dari literatur terdahulu (terutama terkait pencegahan *data leakage*, penanganan ketimpangan variansi ekstrem, dan preservasi dependensi temporal 1 Hz), serta posisi ilmiah riset UTS Data Mining ini.

---

## 2. Tabel Gap Analysis 9 Paper PRISMA & Penelitian Kita

| Penelitian | Karakteristik Data | Preprocessing | Metode Klasterisasi | Limitasi & Gap yang Diselesaikan |
|---|---|---|---|---|
| **Abrasaldo et al. (2026)**<br/>*Geothermics (Elsevier)* | Data operasional sensor termodinamika pembangkit geotermal Wairakei, Selandia Baru (suhu, tekanan, laju alir fluida). | Seleksi fitur *self-supervised* (13 dari 1.588 fitur *tsfresh*), standardisasi *Z-score*. | *Feature-based time-series clustering* ($k$-Means, Agglomerative, GMM, DBSCAN) dievaluasi dengan *Silhouette* ($0{,}66$) dan *Davies-Bouldin Index* ($0{,}40$). | Fokus pada fasilitas pembangkit geotermal permukaan tunggal; tidak menguji variasi penskalaan (*Standard* vs *Robust*) terhadap bias variansi ekstrem dan tidak mengevaluasi representasi jendela multi-kanal sensor mekanik pemboran. |
| **Li et al. (2026)**<br/>*PLOS ONE* | Sensor mekanik pemboran darat 4 sumur minyak (7.231 baris sampel; WOB, RPM, SPP, Torque, Flow Rate, ROP). | Imputasi *Random Forest*, pemfilteran *Savitzky-Golay*, fusi *LOF/k-Means*, segmentasi *sliding window*. | *k-Means* dikombinasikan dengan optimasi parameter pemboran berbasis model *Hydraulic-Mechanical Specific Energy* (HMSE). | Pendekatan berorientasi optimasi terarah (*supervised/target-driven*) dengan sampel data kecil; belum memecahkan masalah *unsupervised operational regime discovery* tanpa label pada aliran data masif frekuensi tinggi 1 Hz. |
| **Wang et al. (2026)**<br/>*Energy Exploration & Exploitation (Sage)* | Profil produksi & komplesi 189 sumur minyak/gas non-konvensional Permian Basin (agregasi bulanan). | Normalisasi skala atribut (*StandardScaler* global), seleksi fitur *MRMR*, reduksi dimensi *MDS*. | *Unsupervised clustering* (*k-Means*, *Hierarchical*, GMM) dengan *Elbow Method* dan evaluasi *Silhouette Score*. | Menggunakan data statis agregat bulanan makro sehingga kehilangan dinamika temporal transien; tidak menangani ketimpangan varians dinamis pada sensor frekuensi tinggi. |
| **Bayazitova et al. (2024)**<br/>*Geoenergy Science and Engineering (Elsevier)* | Benchmark 3W Petrobras (21 sumur lepas pantai, sensor tekanan dan laju alir multivariat). | *Standard Z-score* global, *forward-fill missing values*, *downsampling* 1 menit, *windowing* sekuensial (panjang 30 sampel). | *Deep Neural Networks* (Random Forest, MLP, BiLSTM) untuk klasifikasi rezim aliran dan deteksi anomali. | Sangat bergantung pada ketersediaan anotasi label manual pakar (*supervised*) yang mahal dan subjektif; tidak menyediakan solusi klasterisasi murni tanpa label (*unsupervised*) untuk eksplorasi data mentah. |
| **Singh et al. (2026)**<br/>*Frontiers in AI / Energy Research* | 12 log sensor trajektori sumur bor dan parameter mekanik pengeboran terarah. | Interpolasi data hilang, *quantile normalization*, segmentasi jendela operasional sumur (panjang 50 sampel). | *Unsupervised Graph Feature Representation* + LSTM *Autoencoder* untuk deteksi deviasi trajektori sumur. | Berfokus pada domain kedalaman (*depth-domain*) dengan arsitektur *deep learning* berbiaya komputasi tinggi; rentan risiko *data leakage* pada pemisahan deret waktu dan belum membandingkan efektivitas algoritma partisional klasik pada data temporal 1 Hz. |
| **Mohammed et al. (2025)**<br/>*Int. Journal of Critical Infrastructure Protection (Elsevier)* | Jejak telemetri sensor kontrol jaringan industri migas (*Industrial Cyber-Physical Systems* / ICPS). | Segmentasi *sliding time-windows* dan pengukuran deviasi pola periodik operasional mesin. | STADe (*Spatiotemporal Anomaly Detection*), KNN, *Isolation Forest*, *Local Outlier Factor* (LOF). | Terbatas pada domain telemetri paket siber kontrol ICPS, bukan dinamika interaksi fisik mekanik-batuan-lumpur pada mata bor; tidak memetakan transisi status operasi mesin pemboran. |
| **Azuma & Hashimoto (2025)**<br/>*Engineering Proceedings (MDPI)* | Deret waktu produksi uap 9 sumur geotermal selama 14 tahun. | Filter *Butterworth*, rekonstruksi matriks *Lagged Trajectory Embedding*. | *Singular Spectrum Analysis* (SSA) untuk deteksi deviasi anomali deret waktu geotermal. | Analisis univariat pada satu sensor laju uap jangka panjang; tidak mengakomodasi korelasi multivariat simultan antar-sensor mekanik dan hidraulik rig pengeboran. |
| **Qiu et al. (2025)**<br/>*Energies (MDPI)* | Deret waktu multi-fase produksi sumur minyak lepas pantai. | Pembersihan *outlier* hibrida 3-Sigma Rule + *One-Class SVM* (OC-SVM), pemisahan tahapan dinamis. | *One-Class SVM* (OC-SVM) *anomaly detection* dan klasifikasi tahapan dinamis sumur. | Diterapkan pada fase eksploitasi fluida statis-dinamis, bukan operasi pemboran formasi granit bersuhu tinggi (*Enhanced Geothermal Systems* / EGS); tidak mengevaluasi protokol pemisahan data temporal yang bebas kebocoran informasi (*leakage-free split*). |
| **Hadiyeva et al. (2026)**<br/>*SOCAR Proceedings / Satbayev Univ. (Kazakhstan)* | Lebih dari 3 juta entri data agregat harian selama 2 tahun pada sumur migas lapangan Kazakhstan. | Normalisasi *Z-score* standar, eliminasi *outlier* statistik univariat, analisis korelasi fitur. | *k-Means Clustering* dengan penentuan jumlah klaster optimal via kurva *Elbow* ($k=10$). | Analisis agregasi makro harian tanpa preservasi dependensi temporal frekuensi tinggi; tidak meneliti mitigasi *data leakage* (fit *scaler* pada seluruh dataset) dan rentan bias skala variansi. |
| **Penelitian Kita (Well 56-32 Clean Pipeline)** | Aliran sensor frekuensi tinggi 1 Hz sumur geotermal granit EGS Utah FORGE Well 56-32 ($2.506.359$ baris kontinu, 13 kanal sensor, durasi 29,06 hari). | Filter fisik `SPP <= -900 psi`, *masking sentinel* `-999.25` $\to$ `NaN`, *tumbling window* 60s (*stride* 60s, 0% overlap, *coverage* $\ge 54/60$ valid) dengan reset adaptif di 8 titik celah *sampling* ($38.177$ *window* valid $\times$ 39 fitur statistik), *chronological split* 70:30 dengan *safety embargo* $\ge 1$ jam ($3.600$s), *scaler fit Train-only* (*Standard* vs *Robust* vs *MinMax*). | *Unsupervised k-Means* dan GMM ($k \in [2, 8]$) dengan evaluasi terpisah *Train/Test* (*Silhouette*, *Davies-Bouldin Index*, analisis *occupancy*, uji kestabilan lintas *seed*), aturan ketat *NO-WINNER* bila kolaps, penamaan objektif $C_0 \dots C_k$. | **Menyelesaikan gap utama literatur:** (1) Mengeliminasi *data leakage* lewat pemisahan kronologis ber-embargo dan *scaler* fit *Train-only*; (2) Mengatasi bias variansi dominan SPP ($>95\%$ variansi); (3) Melestarikan dependensi waktu 1 Hz tanpa *chattering*; (4) Menetapkan benchmark evaluasi objektif tanpa fabrikasi label semu saat tanpa *driller log*. |

---

## 3. Catatan Integrasi ke Naskah Publikasi (Bab I)

File ini dirancang khusus agar siap ditransfer langsung ke dalam naskah **Paper IEEE UTS Data Mining** (format Microsoft Word maupun LaTeX):

### A. Panduan Penggunaan di Microsoft Word (.doc / .docx)
1. Sorot seluruh area tabel Markdown pada Bagian 2 di atas.
2. Salin (*Copy*, `Ctrl+C`).
3. Buka dokumen naskah Word pada Bab I (*Introduction / Related Work*).
4. Tempelkan (*Paste*, `Ctrl+V`). Microsoft Word secara otomatis mengonversi teks Markdown tabel menjadi tabel native Word.
5. Terapkan gaya tabel standar IEEE:
   - Font: *Times New Roman*, ukuran 8 pt atau 9 pt.
   - Paragraf: *Single spacing*, *padding cell* atas/bawah 2 pt.
   - Border: Berikan garis horizontal tebal (*top border*, *bottom border*, dan batas bawah *header*), tanpa garis vertikal (*no vertical lines*), sesuai kaidah tabel IEEE format terbuka.

### B. Siap Pakai di LaTeX (.tex)
Gunakan kode LaTeX di bawah ini jika naskah disusun menggunakan *IEEEtran*:

```latex
\begin{table*}[!t]
\caption{Tabel Gap Analysis Literatur Terhadap Penelitian Ini (PRISMA 2020)}
\label{tab:gap_analysis_9_paper}
\centering
\scriptsize
\renewcommand{\arraystretch}{1.3}
\setlength{\tabcolsep}{3.5pt}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{2.3cm} X X X X@{}}
\toprule
\textbf{Penelitian} & \textbf{Karakteristik Data} & \textbf{Preprocessing} & \textbf{Metode Klasterisasi} & \textbf{Limitasi \& Gap yang Diselesaikan} \\
\midrule
Abrasaldo \textit{et al.} (2026) \cite{abrasaldo2026} & Data sensor termodinamika PLTP Wairakei (tekanan, temperatur, debit fluida). & Seleksi fitur \textit{self-supervised} (13 dari 1588 fitur \textit{tsfresh}), Z-score. & \textit{Time-series clustering} ($k$-Means, GMM, DBSCAN); Sil ($0{,}66$), DBI ($0{,}40$). & Terbatas pada fasilitas permukaan tunggal; tanpa uji penskalaan (\textit{Robust} vs \textit{Standard}) pada variansi ekstrem sensor pemboran. \\
\addlinespace
Li \textit{et al.} (2026) \cite{li2026} & Sensor pemboran darat 4 sumur (7.231 baris; WOB, RPM, SPP, Torque, Flow, ROP). & Imputasi RF, filter Savitzky-Golay, fusi LOF/$k$-Means, \textit{sliding window}. & $k$-Means + optimasi parameter terarah model HMSE. & Bersifat terarah (\textit{supervised}) dengan sampel kecil; belum memetakan rezim operasional tanpa label pada 2,5 juta baris 1 Hz. \\
\addlinespace
Wang \textit{et al.} (2026) \cite{wang2026} & Profil produksi 189 sumur Permian Basin (agregasi bulanan). & Normalisasi skala global (\textit{StandardScaler}), MRMR, MDS. & \textit{k-Means}, Hierarchical, GMM; seleksi $k$ via Elbow \& Silhouette. & Menggunakan data agregat bulanan statis; kehilangan dinamika temporal transien dan tidak menangani disparitas varians dinamis 1 Hz. \\
\addlinespace
Bayazitova \textit{et al.} (2024) \cite{bayazitova2024} & Benchmark 3W Petrobras (21 sumur lepas pantai, laju alir/tekanan). & Z-score, forward-fill, \textit{downsampling} 1 menit, sekuensial window 30. & Deep Neural Networks (RF, MLP, BiLSTM) terarah. & Sangat bergantung anotasi label manual pakar; tidak menyediakan solusi klasterisasi murni tanpa label (\textit{unsupervised}). \\
\addlinespace
Singh \textit{et al.} (2026) \cite{singh2026} & 12 log sensor trajektori dan parameter mekanik pemboran terarah. & Interpolasi, \textit{quantile normalization}, segmentasi window 50. & Graph Feature Representation + LSTM Autoencoder. & Berfokus pada \textit{depth-domain} dengan komputasi tinggi; rentan \textit{data leakage} temporal dan belum menguji partisional klasik 1 Hz. \\
\addlinespace
Mohammed \textit{et al.} (2025) \cite{mohammed2025} & Telemetri sensor paket jaringan kontrol industri migas (ICPS). & Segmentasi \textit{sliding time-window}, deteksi deviasi pola periodik. & STADe, KNN, Isolation Forest, Local Outlier Factor (LOF). & Terbatas pada paket siber kontrol ICPS, bukan parameter fisik interaksi mekanik batuan-lumpur rig pemboran. \\
\addlinespace
Azuma \& Hashimoto (2025) \cite{azuma2025} & Deret waktu produksi uap 9 sumur geotermal (14 tahun). & Filter Butterworth, \textit{Lagged Trajectory Matrix Embedding}. & Singular Spectrum Analysis (SSA) deteksi anomali. & Analisis univariat pada satu sensor uap jangka panjang; tidak mengakomodasi korelasi multivariat simultan sensor rig. \\
\addlinespace
Qiu \textit{et al.} (2025) \cite{qiu2025} & Deret waktu dinamis produksi sumur minyak lepas pantai. & 3-Sigma Rule + One-Class SVM (OC-SVM) filter outlier transien. & OC-SVM \textit{anomaly detection} \& pemisahan tahapan dinamis. & Diterapkan pada produksi fluida eksploitasi, bukan pemboran granit EGS; mengabaikan protokol \textit{leakage-free chronological split}. \\
\addlinespace
Hadiyeva \textit{et al.} (2026) \cite{hadiyeva2026} & $>3$ juta entri agregat harian (2 tahun) sumur migas Kazakhstan. & Normalisasi Z-score, eliminasi pencilan, korelasi fitur. & $k$-Means Clustering, penentuan klaster via Elbow ($k=10$). & Agregasi harian makro tanpa preservasi dependensi temporal 1 Hz; tanpa pencegahan \textit{data leakage} dan rentan bias skala variansi. \\
\midrule
\textbf{Penelitian Kita (Well 56-32 Clean Pipeline)} & \textbf{Aliran sensor 1 Hz geotermal granit EGS Utah FORGE 56-32 (2.506.359 baris, 13 kanal, 29,06 hari).} & \textbf{Filter fisik SPP $\le -900$, mask sentinel $-999.25$, tumbling window 60s (stride 60s, reset 8 gap, 38.177 window $\times$ 39 fitur), chronological split 70:30 ber-embargo $\ge 1$ jam, scaler fit Train-only.} & \textbf{\textit{k-Means} \& GMM ($k=2..8$) dievaluasi terpisah Train/Test (Silhouette, DBI, occupancy, collapse check), aturan ketat NO-WINNER, label $C_0..C_k$.} & \textbf{Menyelesaikan gap utama:} (1) Zero data leakage via split kronologis \& fit Train-only; (2) Meredam distorsi varians dominan SPP ($>95\%$); (3) Preservasi temporal 1 Hz bebas chattering; (4) Benchmark objektif tanpa pseudo-regime. \\
\bottomrule
\end{tabularx}
\end{table*}
```
