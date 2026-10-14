# H1-78B Negative Lock v1

## 1. Status & Keputusan

- Tanggal keputusan: 2026-10-13.
- Status: DESIGN_ONLY / LOCKED_NEGATIVE.
- Dataset 78B dikunci permanen sebagai hasil negatif: tidak sesuai sebagai clean holdout H1.
- `status: LOCKED_NEGATIVE`
- `78B_holdout_verdict: UNSUITABLE_H1`

## 2. Rasional Unsuitable H1

- Sentinel `-999.25` memengaruhi 100% baris 78B.
- Gas absen pada 100% baris; Gamma terdampak 60,3%, Flow sekitar 5,27%, dan RPM 2,13%.
- Trial pipeline cleaning r2 menolak 60,1% kandidat window karena coverage; memaksa cleaning akan merusak kontrak 39-fitur dan komparabilitas.
- Audit exposure menyatakan sembilan gap belum terbukti: riwayat exposure, ID unit stabil, zona waktu, rekonsiliasi membership, effective support penuh, horizon korelasi/embargo, purge accounting, persetujuan, dan review independen.
- Verdict audit: `exposure_verdict: INSUFFICIENT_CLEAN_HOLDOUT`.

## 3. Batasan & Invarian

- `H1 NOT_OPENED`; `opened: false`.
- `kmeans_fits: 0`; `scaler_fits: 0`.
- Tidak ada evaluasi, seleksi, maupun fit pada 78B.
- Status proyek tetap `project PARTIAL/HOLD`.
- `C2/C3 NOT TESTED final scope-out`.
- `Tahap1 BLOCKED`.
- `frontier_cross_family: OPEN`.

## 4. Dampak Paper

- 78B dilaporkan jujur sebagai temuan negatif/studi kelayakan holdout.
- Tidak ada klaim bahwa evaluasi holdout H1 berhasil menggunakan 78B.
- Tidak ada forcing cleaning, evaluasi, seleksi, atau fit demi menghasilkan klaim positif.

## 5. Literal Anchors

```text
status: LOCKED_NEGATIVE
78B_holdout_verdict: UNSUITABLE_H1
H1 NOT_OPENED
opened: false
kmeans_fits: 0
scaler_fits: 0
project PARTIAL/HOLD
C2/C3 NOT TESTED final scope-out
Tahap1 BLOCKED
exposure_verdict: INSUFFICIENT_CLEAN_HOLDOUT
frontier_cross_family: OPEN
```

Catatan: lock ini tidak mengubah status proyek, ruang lingkup C2/C3, atau gate review frontier.
