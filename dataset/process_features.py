"""
Skrip Pemisahan Metadata, Filtering Sentinel, dan Feature Engineering
Dataset Pengeboran Sumur Geotermal Utah FORGE 56-32

Output:
1. dataset/56-32_metadata.csv.gz (Kolom waktu, kedalaman, dan on-bottom flag)
2. dataset/56-32_features_clean.csv.gz (Sensor mekanik bersih untuk penskalaan & clustering)
"""

import sys
import time
import pandas as pd
import numpy as np

RAW_PATH = "dataset/56-32 1sec data 27029986.csv"
META_OUT = "dataset/56-32_metadata.csv.gz"
FEAT_OUT = "dataset/56-32_features_clean.csv.gz"

METADATA_COLS = [
    'YYYY/MM/DD',
    'HH:MM:SS',
    'Hole Depth (feet)',
    'Bit Depth (feet)',
    'Pason Lag Depth (feet)'
]

DROP_COLS = [
    'Pason Gas (percent)',
    'Gamma (api)'
]

def main():
    print(f"[1/4] Memulai proses ekstraksi dataset: {RAW_PATH}")
    t0 = time.time()
    
    # Baca data per chunk untuk hemat RAM
    chunk_size = 250000
    meta_chunks = []
    feat_chunks = []
    
    total_raw = 0
    total_valid = 0
    total_sentinel_dropped = 0
    
    for i, chunk in enumerate(pd.read_csv(RAW_PATH, chunksize=chunk_size)):
        total_raw += len(chunk)
        
        # 1. Filter baris sentinel SPP <= -900 (sensor mati / artefak saat rig offline)
        mask_valid = chunk['Standpipe Pressure (psi)'] > -900
        dropped_count = (~mask_valid).sum()
        total_sentinel_dropped += dropped_count
        
        valid_chunk = chunk[mask_valid].copy()
        total_valid += len(valid_chunk)
        
        # 2. Pemisahan Metadata & Feature Engineering Kedalaman
        meta = valid_chunk[METADATA_COLS].copy()
        delta_depth = meta['Hole Depth (feet)'] - meta['Bit Depth (feet)']
        meta['Delta_Depth (feet)'] = delta_depth
        # Bit dikatakan on-bottom jika selisih kedalaman <= 0.5 ft dan bit depth > 0
        meta['Is_On_Bottom'] = ((delta_depth <= 0.5) & (meta['Bit Depth (feet)'] > 0)).astype(np.int8)
        meta_chunks.append(meta)
        
        # 3. Pemisahan Fitur Mekanik & Feature Engineering Sensor
        # Drop kolom metadata dan kolom sampah (jika ada)
        feat = valid_chunk.drop(columns=METADATA_COLS + DROP_COLS, errors='ignore').copy()
        
        # Feature Engineering:
        # a. Hydraulic Power Proxy (SPP * Total Pump Output)
        feat['Hydraulic_Energy_Proxy'] = np.maximum(0.0, feat['Standpipe Pressure (psi)']) * np.maximum(0.0, feat['Total Pump Output (gal_per_min)'])
        # b. Mechanical Power Proxy (Torque * RPM)
        feat['Mechanical_Power_Proxy'] = np.maximum(0.0, feat['Rotary Torque (kft_lb)']) * np.maximum(0.0, feat['Rotary RPM (RPM)'])
        # c. Delta Depth disisipkan ke fitur sebagai indikator jarak mata bor ke dasar
        feat['Delta_Depth (feet)'] = delta_depth
        feat['Is_On_Bottom'] = meta['Is_On_Bottom']
        
        feat_chunks.append(feat)
        print(f"      Memproses chunk {i+1} ({total_raw:,} baris terbaca)...")
        
    print(f"\n[2/4] Selesai membaca data ({time.time() - t0:.1f}s):")
    print(f"      Total baris mentah     : {total_raw:,}")
    print(f"      Sentinel SPP <= -900   : {total_sentinel_dropped:,} baris dibuang ({total_sentinel_dropped/total_raw*100:.2f}%)")
    print(f"      Total baris bersih     : {total_valid:,}")
    
    print("\n[3/4] Menggabungkan dan menyimpan Metadata...")
    df_meta = pd.concat(meta_chunks, ignore_index=True)
    df_meta.to_csv(META_OUT, index=False, compression='gzip')
    print(f"      Metadata tersimpan di -> {META_OUT}")
    del df_meta, meta_chunks
    
    print("\n[4/4] Menggabungkan dan menyimpan Features Bersih...")
    df_feat = pd.concat(feat_chunks, ignore_index=True)
    df_feat.to_csv(FEAT_OUT, index=False, compression='gzip')
    print(f"      Features tersimpan di -> {FEAT_OUT}")
    print(f"      Jumlah kolom fitur    : {len(df_feat.columns)}")
    print(f"      Daftar kolom fitur    : {df_feat.columns.tolist()}")
    
    print(f"\n[SELESAI] Total waktu eksekusi: {time.time() - t0:.1f} detik.")

if __name__ == "__main__":
    main()
