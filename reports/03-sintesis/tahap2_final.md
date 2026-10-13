# TAHAP 2 FINAL — Data Understanding & Preprocessing Plan (terkunci 30 Sep 2026)

> Dataset: Utah FORGE Well 56-32, Pason 1 Hz, 2.506.360 baris × 22 kolom.
> Angka di bawah dari Colab 200k sampel acak (seed 42) + run notebook fathan (80k head-segment).
> Syarat tugas: ≥5 atribut numerik kontinu, beda skala, unlabeled — TERPENUHI (8 sensor).

## 2.1 Taksonomi Sensor & Kanal Fitur (13 Kanal)

| # | Kanal | Satuan / Proksi | Domain | Peran dalam Pemodelan |
|---|---|---|---|---|
| 1 | Rate Of Penetration (ROP) | ft/hr | Kinematika Pemboran | Kecepatan penetrasi vertikal pahat |
| 2 | Weight on Bit (WOB) | klbs | Mekanika Batuan | Gaya aksial pada mata bor |
| 3 | Rotary RPM (RPM) | rpm | Mekanika Rotasi | Kecepatan putaran stang bor |
| 4 | Standpipe Pressure (SPP) | psi | Hidraulika Sirkulasi | Tekanan sirkulasi lumpur permukaan |
| 5 | Rotary Torque (Torque) | kft-lb | Mekanika Rotasi | Torsi gesekan formasi batuan |
| 6 | Hook Load (HookLoad) | klbs | Derek / Pengangkatan | Gaya tarik traveling block |
| 7 | Flow Out (Flow) | % | Sirkulasi Lumpur | Persentase pengembalian fluida |
| 8 | Total Pump Output (PumpOut) | gal/min | Hidraulika Pompa | Laju alir volumetrik lumpur |
| 9 | Total Mud Volume (MudVol) | barrels | Penyimpanan Fluida | Volume tangki lumpur |
| 10 | Block Height (BlockHeight) | feet | Derek / Kinematika | Posisi elevasi blok derek |
| 11 | Pump 1 SPM (SPM1) | spm | Pompa Lumpur | Frekuensi ketukan pompa 1 |
| 12 | Hydraulic Power ($P_{\text{hyd}}$) | psi $\cdot$ GPM | Proksi Daya Hidraulik | $SPP \times PumpOut$ (energi sirkulasi) |
| 13 | Mechanical Power ($P_{\text{mech}}$) | kft-lb $\cdot$ rpm | Proksi Daya Mekanik | $Torque \times RPM$ (energi rotasi) |

*Catatan Eliminasi Kanal:*
- **Pason Gas & Gamma Ray:** 100% bernilai sentinel $-999{,}25$ (dibuang).
- **Differential Pressure:** Dieliminasi karena cacat kalkulasi software rig ($\le -900$ psi saat pompa mati) dan digantikan oleh proksi daya fisik $P_{\text{hyd}}$ & $P_{\text{mech}}$.

---

## 2.2 Statistik Deskriptif Sensor (Partisi Train 70%, $N = 26.723$ Jendela)

Sumber data terisolasi: `clean-pipeline-56-32/outputs/metrics/train_descriptive_stats.csv`.

| Fitur Kanal Mean | Mean | Std (ddof=0) | Min | Median | Max | Skewness | Interpretasi Fisik |
|---|---|---|---|---|---|---|---|
| ROP_mean | 20,43 | 79,84 | 0,00 | 0,00 | 4.303,23 | 20,98 | Ekor panjang lonjakan derek |
| WOB_mean | 24,40 | 23,95 | 0,00 | 24,13 | 172,86 | 1,04 | Beban operasional normal |
| RPM_mean | 21,52 | 25,94 | 0,00 | 0,06 | 104,27 | 0,86 | Bimodal (aktif vs idle slips) |
| SPP_mean | 1.603,41 | 1.536,53 | 0,00 | 1.643,31 | 5.131,09 | 0,03 | Orde ribuan psi |
| Torque_mean | 3,01 | 3,76 | 0,00 | 0,00 | 25,74 | 1,15 | Torsi kontak formasi granit |
| HookLoad_mean | 109,63 | 57,12 | 0,00 | 118,45 | 360,46 | 0,24 | Beban gantung pipa bor |
| Flow_mean | 46,26 | 34,12 | -1,48 | 66,51 | 133,66 | -0,24 | Sirkulasi lumpur kembali |
| PumpOut_mean | 365,01 | 327,00 | 0,00 | 460,82 | 1.757,69 | -0,07 | Debit lumpur sirkulasi |
| MudVol_mean | 407,27 | 64,36 | 195,25 | 422,88 | 597,27 | -1,08 | Kapasitas tangki stabil |
| BlockHeight_mean | 80,02 | 41,43 | -8,54 | 78,96 | 192,47 | 0,37 | Elevasi pergerakan stang |
| SPM1_mean | 46,51 | 42,38 | 0,00 | 72,68 | 119,43 | -0,11 | Ritme kayuhan pompa |
| Hydraulic_P_mean | $1{,}07 \times 10^6$ | $1{,}06 \times 10^6$ | 0,00 | $8{,}91 \times 10^5$ | $6{,}34 \times 10^6$ | 0,13 | Orde jutaan (daya hidraulik) |
| Mech_P_mean | 145,30 | 218,70 | 0,00 | 0,00 | 1.777,36 | 2,08 | Daya mekanik pemotongan |

**Ketimpangan Skala (Scale Disparity):** Rasio magnitudo antara Daya Hidraulik ($10^6$) terhadap Torsi ($10^0$) mencapai $> 10^5 : 1$. Ini memvalidasi keharusan penskalaan fitur sebelum klasterisasi K-Means.

---

## 2.3 Sentinel, Anomali, dan Uji Integritas Temporal

1. **Pembuangan Anomali SPP ($\le -900$ psi):** Menghapus 29.503 baris pembacaan negatif palsu instrumen $\rightarrow$ 2.476.856 baris dipertahankan.
2. **Masking Sentinel $-999{,}25$:** Dikonversi menjadi NaN (tidak diimputasi rata-rata agar tidak memalsukan data saat instrumen mati).
3. **Pemisahan Segmen Waktu (Gap Reset):** Setiap selisih timestamp $\ne +1$ detik memicu reset batas segmen (terbentuk 28 segmen kontinu, 27 reset gap). Jendela tidak diperbolehkan melintasi celah waktu.
4. **Coverage Gate $\ge 90\%$:** Jendela 60 detik hanya diterima jika memiliki minimal 54 detik data valid untuk setiap kanal. Dari 41.271 kandidat, tersaring **38.177 jendela valid** (3.094 ditolak karena data tipis).

---

## 2.4 Korelasi Pearson (Interaksi Fisik Rig pada Partisi Train)

Sumber: `clean-pipeline-56-32/outputs/metrics/train_pearson_corr.csv`.
- **Kopel Hidraulik Kuat:** $SPP\_mean \leftrightarrow PumpOut\_mean$ ($r = 0{,}9575$), $SPP\_mean \leftrightarrow Hydraulic\_P\_mean$ ($r = 0{,}9839$).
- **Kopel Mekanik Kuat:** $RPM\_mean \leftrightarrow Torque\_mean$ ($r = 0{,}8192$), $RPM\_mean \leftrightarrow Mech\_P\_mean$ ($r = 0{,}9041$).
- **Sirkulasi Lumpur:** $Flow\_mean \leftrightarrow PumpOut\_mean$ ($r = 0{,}7897$).
- **Independensi Linier:** $ROP\_mean \leftrightarrow WOB\_mean$ ($r = 0{,}0838$), membuktikan laju penetrasi tidak berkorelasi linier sederhana pada formasi granit keras, sehingga membutuhkan *unsupervised regime discovery*.

---

## 2.5 Preprocessing Plan (clean-pipeline-56-32, FINAL-LOCK)

1. **Pembersihan Chunk:** Drop SPP $\le -900$, mask sentinel $-999{,}25 \rightarrow$ NaN, hitung proksi $P_{\text{hyd}}$ dan $P_{\text{mech}}$.
2. **Jendela Tumbling 60 Detik:** Stride 60 detik (0% overlap); reset saat gap $\ne 1$s; buang partial tail.
3. **Ekstraksi 39 Fitur:** Mean, standard deviasi populasi (ddof=0), dan delta ($last - first finite$) untuk 13 kanal.
4. **Partisi Kronologis Bebas Bocor:**
   - **Train 70%:** 26.723 jendela (berakhir 2021/02/26 21:20:32).
   - **Embargo 1 Jam:** 60 jendela dibuang sebagai penyangga diskontinuitas autokorelasi.
   - **Test 30%:** 11.394 jendela (mulai 2021/02/26 22:20:32).
5. **Penskalaan Train-Only:** Scaler di-fit secara eksklusif hanya pada partisi Train (StandardScaler, RobustScaler, MinMaxScaler) lalu ditransformasikan ke Test tanpa mengubah parameter scaler.

