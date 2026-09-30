# Deklarasi Penggunaan Gen-AI — Proyek UTS Data Mining Utah FORGE

> Lampiran wajib luaran paper (`dataset/tugas.txt:54` — "Perlu melampirkan deklarasi penggunaan Gen-AI").

## Alat yang digunakan

- **Muse Spark (via OpenCode)** — asisten AI untuk: eksplorasi dataset (statistik deskriptif, korelasi, outlier), perancangan string kueri Scopus (Q-RAW v6 + Q-FILTERED), screening Pass-1 judul/abstrak 127 record, ekstraksi Pass-2 full-text Batch 1 + No.161, penyusunan tabel gap dan diagram PRISMA, serta penulisan draf dokumen `reports/`.

## Yang tetap dikerjakan manusia (tim)

1. Keputusan metodologi: pemilihan dataset, penguncian query (verifikasi hits 740/175 di Scopus), kriteria inklusi/eksklusi, aturan "supervised = NETRAL", filter OA-only, dan penetapan final 9 + backup 7.
2. Verifikasi: menjalankan notebook Colab (`notebooks/00_cek_penyakit_colab.ipynb`), export Scopus 175, screenshot hits query, pengecekan spot-check vote AI, dan penulisan paper IEEE final.
3. Semua angka PRISMA dapat ditelusur ke file: `screening-175paper.csv` (export mentah) → `screening_work.csv` (vote) → `sought_list.csv` → `screening_127.csv` → `eligibility_16.csv`.

## Batasan

- Vote screening AI (Reviewer = AI-Pass1) adalah rekomendasi awal; tim wajib spot-check sebelum submit.
- 4 paper E5 (full-text tak terakses) dan inkonsistensi redirect DOI No.161 didokumentasikan apa adanya di `screening_work.csv`, tidak disembunyikan.

Tanggal: 30 September 2026.
