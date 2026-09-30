# datmin — Multivariate Geothermal Drilling Sensor Clustering (Utah FORGE 56-32)

UTS Data Mining (S1 Informatika): unsupervised regime discovery pada data sensor rig
geotermal 1 Hz tanpa label — komparasi **StandardScaler vs RobustScaler** ×
**point-based vs sliding-window**, clustering **K-Means**, evaluasi
**Silhouette + Davies–Bouldin + Elbow**.

## Dataset

- Utah FORGE Well 56-32, Pason 1 Hz, 2.506.360 baris × 22 kolom → **8 sensor utama**
  (ROP, WOB, RPM, SPP, Torque, Hookload, Diff Press, Pump Out).
- Hosting: Kaggle `faruqmahdison/utah-datmin` (CSV mentah 340 MB **tidak** di-commit,
  lihat `.gitignore`). Spesifikasi: `dataset/tugas.txt`, `dataset/infodataset.txt`.
- Penyakit terukur (Colab 200k, seed 42): rasio skala **258.9:1**, sentinel `-999.25`,
  outlier ROP 8.65%, SPP–Pump r=0.925, autocorr lag-1 ≈ 1.0.

## Alur kerja & file kunci

| Tahap | Isi | File |
|---|---|---|
| PRISMA (Tahap 1) | Query Q-RAW v6 (740) → Q-FILTERED (175) → screening 127 → sought 70 → **inklusi 9** | `reports/prisma.restart.v6.md`, `reports/prisma.diagram.md` |
| Screening jejak | Export Scopus, vote Pass-1/Pass-2, sought, eligibility | `reports/screening-*.csv`, `reports/sought_list.csv`, `reports/eligibility_16.csv` |
| Final + backup | Tabel 9 final + 7 backup + supporting refs | `reports/tabel_final_backup.md` |
| EDA (Tahap 2) | Taksonomi, deskriptif, sentinel/outlier, korelasi, preprocessing plan | `reports/tahap2_final.md` |
| Clustering (Tahap 3) | Desain 4 skenario × k=2–8, hasil elbow real, limitasi jujur | `reports/tahap3_final.md` |
| Paper | Draft IEEE (Bab I–IV + pustaka) | `reports/draft_paper_ieee.md` |
| Diagram | Generator + PNG/PDF/SVG | `src/generate_prisma.py`, `figures/` |
| Gen-AI | Deklarasi penggunaan AI (wajib tugas) | `reports/deklarasi_genai.md` |

## Cara jalan

```bash
# Diagram PRISMA (angka terkunci di konstanta atas file)
py src/generate_prisma.py        # output -> figures/prisma_flowchart_restart_v6.{png,pdf,svg}

# EDA penyakit (Colab; pilih upload manual ATAU Kaggle)
# notebooks/00_cek_penyakit_colab.ipynb  (cadangan .py)
```

## Ambil dataset via kagglehub

Dataset: https://www.kaggle.com/datasets/faruqmahdison/utah-datmin

```python
# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
import kagglehub
from kagglehub import KaggleDatasetAdapter

# Set the path to the file you'd like to load
file_path = "56-32 1sec data 27029986.csv"

# Load the latest version
df = kagglehub.load_dataset(
  KaggleDatasetAdapter.PANDAS,
  "faruqmahdison/utah-datmin",
  file_path,
  # Provide any additional arguments like
  # sql_query or pandas_kwargs. See the
  # documenation for more information:
  # https://github.com/Kaggle/kagglehub/blob/main/README.md#kaggledatasetadapterpandas
)

print("First 5 records:", df.head())
```

# Pipeline penuh (Kaggle, ~20-30 mnt CPU)
# notebooks/utah_forge_56_32_geothermal_drilling_sensor_clust-fathan.ipynb
```

Setelah re-run notebook: unduh `/kaggle/output/` (`table0–table6`, `fig1–fig6`) ke
`figures/`, isi slot `[TODO-RERUN]` di `draft_paper_ieee.md`, konversi ke .doc
template IEEE, lampirkan repo + dataset + diagram PRISMA.

## Status (30 Sep 2026)

- [x] PRISMA 740 → 9 + backup 7 (terkunci, aritmetika pas)
- [x] Tahap 2 final (angka real) + Tahap 3 desain + hasil awal jujur
- [x] Draft IEEE (Bab I–II penuh; §III-B menunggu re-run)
- [ ] Re-run notebook pasca-perbaikan (winsorize ROP, Diff Press OFF)
- [ ] Finalisasi §III-B + konversi .doc + submit
