# ============================================================
# COLAB SIAP-PASTE: Buktiin "penyakit" dataset Utah FORGE 56-32
# Cara pakai di https://colab.research.google.com/:
#   PILIH SALAH SATU:
#   (A) Upload manual: panel Files kiri > Upload "56-32 1sec data 27029986.csv"
#       ATAU run Cell 1A (files.upload).
#   (B) Load dari Kaggle: run Cell 1B (kagglehub, tanpa upload manual).
#   Lalu run Cell 2 -> 5 berurutan.
# Catatan: file ~2.5 jt baris. Kode ini baca HANYA 8 sensor + sampling
#   agar tidak OOM di Colab Free. Hasil tetap valid untuk laporan.
# ============================================================

# ---------- CELL 1A: upload manual (pilih A ATAU B, jangan dua-duanya) ----------
from google.colab import files
import io, os, glob

uploaded = files.upload()  # pilih file "56-32 1sec data 27029986.csv"
print("File terupload:", list(uploaded.keys()))

# ---------- CELL 1B: load dari Kaggle (alternatif, tanpa upload manual) ----------
# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
import kagglehub
from kagglehub import KaggleDatasetAdapter

DATASET_SLUG = "faruqmahdison/utah-datmin"

# Langkah 1: download folder dataset untuk intip nama file di dalamnya
# (file_path di snippet kamu masih "" — harus diisi nama csv yang benar)
dl_path = kagglehub.dataset_download(DATASET_SLUG)
print("Dataset terdownload di:", dl_path)
import glob as _glob, os as _os
dalam = _glob.glob(_os.path.join(dl_path, "**"), recursive=True)
print("Isi dataset:")
for p in dalam[:30]:
    print(" ", p)

# Langkah 2: arahkan CSV ke file Kaggle (otomatis, tahan spasi)
csvs = [p for p in dalam if p.lower().endswith(".csv")]
CSV_KAGGLE = None
for p in csvs:
    if "56-32" in p or "27029986" in p:
        CSV_KAGGLE = p
        break
if CSV_KAGGLE is None and csvs:
    CSV_KAGGLE = csvs[0]
print("CSV_KAGGLE =", CSV_KAGGLE)

# Langkah 3 (opsional, sesuai snippet kamu): load via Pandas adapter
# Ganti FILE_IN_DATASET dengan nama file dari output "Isi dataset" di atas,
# contoh: "56-32 1sec data 27029986.csv" (hanya nama file, bukan full path).
FILE_IN_DATASET = "56-32 1sec data 27029986.csv"  # <-- sesuaikan jika beda
try:
    df_kaggle = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        DATASET_SLUG,
        FILE_IN_DATASET,
    )
    print("load_dataset OK, shape:", df_kaggle.shape)
    print("First 5 records:", df_kaggle.head().to_string())
except Exception as e:
    print("load_dataset gagal (biasanya nama file salah). Pakai CSV_KAGGLE langsung.")
    print("Error:", e)

# ---------- CELL 2: config + load ----------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# auto-deteksi CSV: utamakan dari Kaggle (Cell 1B), fallback ke upload manual (Cell 1A)
CSV = None
try:
    if "CSV_KAGGLE" in dir() and CSV_KAGGLE and os.path.exists(CSV_KAGGLE):
        CSV = CSV_KAGGLE
except NameError:
    pass
if CSV is None:
    csv_candidates = glob.glob("*.csv") + glob.glob("/content/*.csv")
    for c in csv_candidates:
        if "56-32" in c or "27029986" in c:
            CSV = c
            break
    if CSV is None and csv_candidates:
        CSV = csv_candidates[0]
print("CSV dipakai:", CSV)
assert CSV is not None, "CSV tidak ketemu! Run Cell 1A (upload) ATAU Cell 1B (kagglehub) dulu."

SENSORS = [
    "Rate Of Penetration (ft_per_hr)",
    "Weight on Bit (klbs)",
    "Rotary RPM (RPM)",
    "Standpipe Pressure (psi)",
    "Rotary Torque (kft_lb)",
    "Hook Load (klbs)",
    "Differential Pressure (psi)",
    "Total Pump Output (gal_per_min)",
]
SENTINEL = -999.25
SAMPLE_N = 200_000  # sampel acak untuk stats/korelasi/boxplot (cepat & cukup)
RANDOM_STATE = 42

# Baca ringan dulu: hanya 8 sensor, skip baris rusak
df_sample = pd.read_csv(
    CSV, usecols=SENSORS, engine="python",
    skip_blank_lines=True,
).sample(n=min(SAMPLE_N, 2_500_000), random_state=RANDOM_STATE)
print("Shape sampel:", df_sample.shape)
print(df_sample.head(3).to_string())

# ---------- CELL 3: PENYAKIT 1 — scale disparity ----------
desc = df_sample.replace(SENTINEL, np.nan).describe(
    percentiles=[0.25, 0.5, 0.75]).T
desc["range"] = desc["max"] - desc["min"]
print("\n=== DESKRIPTIF (NaN = sentinel dibuang) ===")
print(desc[["count", "mean", "std", "min", "25%", "50%", "75%", "max", "range"]].round(2).to_string())

# rasio skala ekstrem: max range vs min range
rng = desc["range"].sort_values()
print("\nRange terkecil:", rng.index[0], "=", round(rng.iloc[0], 2))
print("Range terbesar :", rng.index[-1], "=", round(rng.iloc[-1], 2))
print("Rasio skala    : %.1f : 1" % (rng.iloc[-1] / max(rng.iloc[0], 1e-9)))
print("-> Kalau >100:1, Euclidean tanpa scaler PASTI didominasi sensor besar (penyakit scale disparity TERBUKTI).")

# skew (kemiringan) — butuh scipy? pakai pandas saja
skew = df_sample.replace(SENTINEL, np.nan).skew(numeric_only=True).sort_values(ascending=False)
print("\n=== SKEWNESS (makin + = ekor kanan/outlier) ===")
print(skew.round(2).to_string())

# ---------- CELL 4: PENYAKIT 2 — missing/sentinel + outlier IQR ----------
total = len(df_sample)
print("\n=== SENTINEL -999.25 (sensor offline Pason) ===")
for s in SENSORS:
    c = (df_sample[s] == SENTINEL).sum()
    print(f"{s:35s} : {c:7d} ({c/total*100:5.2f}%)")

print("\n=== OUTLIER IQR per sensor (Q1-1.5*IQR, Q3+1.5*IQR) ===")
clean = df_sample.replace(SENTINEL, np.nan)
for s in SENSORS:
    x = clean[s].dropna()
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    pct = ((x < lo) | (x > hi)).mean() * 100
    print(f"{s:35s} : lo={lo:10.2f} hi={hi:10.2f} outlier={pct:5.2f}%")

# ---------- CELL 5: PENYAKIT 3 — korelasi + temporal dependency + visual ----------
print("\n=== KORELASI PEARSON (bukti kopel fisik rig) ===")
corr = clean.corr(numeric_only=True)
print(corr.round(3).to_string())
print("\nContoh bacaan: SPP vs Pump Out ~0.9 = kopel hidrolik; RPM vs Torque ~0.7 = kopel rotasi; ROP vs WOB ~0 = nonlinier di granit.")

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, fmt=".2f", square=True)
plt.title("Korelasi 8 sensor Utah FORGE (sampel 200k)")
plt.tight_layout()
plt.show()

# Temporal: autocorr lag 1/5/10/60 detik pada 3 sensor (bukti urutan waktu saling terikat)
print("\n=== AUTOCORR (bukti temporal dependency) ===")
# pakai urutan asli file (bukan sampel acak): baca 5 menit pertama berurutan
seq = pd.read_csv(CSV, usecols=["Rotary RPM (RPM)", "Standpipe Pressure (psi)", "Rate Of Penetration (ft_per_hr)"],
                  engine="python", nrows=20000).replace(SENTINEL, np.nan).ffill()
for col in seq.columns:
    ac = [seq[col].autocorr(lag=l) for l in [1, 5, 10, 60]]
    print(f"{col:35s} : lag1={ac[0]:.3f} lag5={ac[1]:.3f} lag10={ac[2]:.3f} lag60={ac[3]:.3f}")
print("-> Kalau lag1 > 0.9: point-based rapuh, wajib sliding-window mean/std/delta (bonus temporal).")

# Boxplot cepat (distribusi + outlier visual)
fig, ax = plt.subplots(figsize=(10, 4))
plot_df = clean.melt(var_name="sensor", value_name="value")
# batasi titik agar cepat: ambil 5k per sensor
plot_df = plot_df.groupby("sensor", group_keys=False).apply(
    lambda g: g.sample(min(len(g), 5000), random_state=RANDOM_STATE))
sns.boxplot(data=plot_df, x="sensor", y="value", ax=ax)
ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
ax.set_title("Sebaran 8 sensor (skala asli — lihat dominasi SPP)")
plt.tight_layout()
plt.show()

print("\nSELESAI. Angka dari cell ini = bahan Tabel Penyakit di laporan:")
print("1) rasio skala, 2) % sentinel & outlier, 3) korelasi terkuat, 4) autocorr lag1.")
