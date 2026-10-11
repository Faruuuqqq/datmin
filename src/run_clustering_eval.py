"""End-to-end execution of Clustering & Evaluation Pipeline (Utah FORGE 56-32)
Orang 4 — Fathan: Clustering & Evaluasi
Generates table0-table6 and fig1-fig6 into figures/ directory.
Uses pure matplotlib (no seaborn required).
"""
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score

# 1. Constants
SENSOR_8 = [
    'Rate Of Penetration (ft_per_hr)',
    'Weight on Bit (klbs)',
    'Rotary RPM (RPM)',
    'Standpipe Pressure (psi)',
    'Rotary Torque (kft_lb)',
    'Hook Load (klbs)',
    'Total Pump Output (gal_per_min)',
    'Differential Pressure (psi)'
]
CSV_NAME = '56-32 1sec data 27029986.csv'
SEED = 42
N_EDA, N_SCALE, N_WIN_SRC, N_FINAL = 80000, 20000, 30000, 60000

def resolve_input(csv=CSV_NAME):
    candidates = [
        Path('dataset') / csv,
        Path('../dataset') / csv,
        Path.cwd() / 'dataset' / csv,
        Path(f'C:/Users/LENOVO/.cache/kagglehub/datasets/faruqmahdison/utah-datmin/versions/1/{csv}')
    ]
    for c in candidates:
        if c.exists():
            return c
    root = Path('/kaggle/input')
    if root.exists():
        hits = list(root.rglob(csv))
        if hits:
            return hits[0]
    raise FileNotFoundError(f"Dataset {csv} not found.")

def main():
    t_start = time.time()
    path = resolve_input()
    out_dir = Path('figures')
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[1/6] Input: {path} | Output: {out_dir}")

    # -------------------------------------------------------------
    # Step 1: EDA & Understanding
    # -------------------------------------------------------------
    print("[2/6] Running Step 1: EDA & Understanding...")
    usecols = ['YYYY/MM/DD', 'HH:MM:SS'] + SENSOR_8
    eda = pd.read_csv(path, usecols=usecols, nrows=N_EDA * 2, low_memory=True)
    rng = np.random.RandomState(SEED)
    eda = eda.iloc[np.sort(rng.choice(len(eda), min(len(eda), N_EDA), replace=False))].reset_index(drop=True)
    for c in SENSOR_8:
        eda[c] = pd.to_numeric(eda[c], errors='coerce').astype('float32')
    eda['datetime'] = pd.to_datetime(eda['YYYY/MM/DD'] + ' ' + eda['HH:MM:SS'], format='%Y/%m/%d %H:%M:%S', errors='coerce')

    # table0: sensor taxonomy
    tax = pd.DataFrame({
        'Sensor / Dataset Column': SENSOR_8,
        'Abbreviation': ['ROP', 'WOB', 'RPM', 'SPP', 'Torque', 'Hookload', 'Pump Out', 'Diff Press'],
        'Unit': ['ft/hr', 'klbs', 'RPM', 'psi', 'kft-lb', 'klbs', 'gal/min', 'psi'],
        'Physical Domain': ['Drilling', 'Mechanical', 'Rotational', 'Hydraulic', 'Rotational', 'Hoisting', 'Hydraulic', 'Hydraulic'],
        'Role in Paper': [
            'Primary response (speed)', 'Primary input (weight on bit)', 'Primary input (drill string rotation)',
            'Primary input (mud pump pressure)', 'Response / formation resistance', 'Rig state indicator (drilling vs tripping)',
            'Primary input (mud circulation rate)', 'Secondary / excluded (software calculation anomaly)'
        ]
    })
    tax.to_csv(out_dir / 'table0_sensor_taxonomy.csv', index=False)

    # table1: descriptive statistics
    desc = eda[SENSOR_8].replace(-999.25, np.nan).describe(percentiles=[.25, .5, .75]).T
    desc['skewness'] = eda[SENSOR_8].replace(-999.25, np.nan).skew()
    desc.round(2).to_csv(out_dir / 'table1_descriptive.csv')

    # fig1: correlation heatmap
    corr_mat = eda[SENSOR_8].replace(-999.25, np.nan).corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.matshow(corr_mat, cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)
    short_labels = ['ROP', 'WOB', 'RPM', 'SPP', 'Torque', 'Hookload', 'Pump', 'DiffPress']
    ax.set_xticks(range(len(short_labels)))
    ax.set_yticks(range(len(short_labels)))
    ax.set_xticklabels(short_labels, rotation=45, ha='left')
    ax.set_yticklabels(short_labels)
    for i in range(len(short_labels)):
        for j in range(len(short_labels)):
            val = corr_mat.iloc[i, j]
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', color='black' if abs(val) < 0.7 else 'white', fontsize=8)
    plt.title('Fig 1. Pearson Correlation Heatmap (8 Utah FORGE Sensors)', pad=20)
    plt.tight_layout()
    plt.savefig(out_dir / 'fig1_correlation.png', dpi=150)
    plt.close()

    # fig2: boxplots
    fig, axes = plt.subplots(2, 4, figsize=(14, 6))
    for ax, c, lbl in zip(axes.flat, SENSOR_8, short_labels):
        s_data = eda[c].replace(-999.25, np.nan).dropna()
        ax.boxplot(s_data, showfliers=True, flierprops={'marker': '.', 'markersize': 2, 'alpha': 0.3})
        ax.set_title(lbl, fontsize=9)
    plt.suptitle('Fig 2. Sensor Value Distributions & Outliers (Boxplots)', fontsize=12)
    plt.tight_layout()
    plt.savefig(out_dir / 'fig2_boxplots.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # Step 2: Scaling Comparison
    # -------------------------------------------------------------
    print("[3/6] Running Step 2: Scaler Comparison...")
    s = pd.read_csv(path, usecols=SENSOR_8, nrows=N_SCALE * 2, low_memory=True)
    for c in SENSOR_8:
        s[c] = pd.to_numeric(s[c], errors='coerce').astype('float32')
    s = s.replace(-999.25, np.nan).dropna().reset_index(drop=True)

    rop_q1, rop_q3 = s['Rate Of Penetration (ft_per_hr)'].quantile(0.25), s['Rate Of Penetration (ft_per_hr)'].quantile(0.75)
    iqr = rop_q3 - rop_q1
    ROP_HI = float(rop_q3 + 1.5 * iqr) if iqr > 0 else 47.4
    s['Rate Of Penetration (ft_per_hr)'] = s['Rate Of Penetration (ft_per_hr)'].clip(upper=ROP_HI)
    s = s.sample(min(len(s), N_SCALE), random_state=SEED).to_numpy()

    res_scaler = {}
    for name, sc in [('unscaled', None), ('standard', StandardScaler()), ('robust', RobustScaler())]:
        X = s if sc is None else sc.fit_transform(s)
        lab = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit_predict(X)
        res_scaler[name] = {
            'silhouette': float(silhouette_score(X, lab)),
            'dbi': float(davies_bouldin_score(X, lab))
        }
    df_scaler = pd.DataFrame(res_scaler).T.round(4)
    df_scaler.to_csv(out_dir / 'table2_scaler_compare.csv')
    print("Table 2 (Scaler comparison):")
    print(df_scaler)

    # fig3: scaling histogram
    fig, axes = plt.subplots(1, 3, figsize=(12, 3))
    raw_spp = s[:, 3]
    std_spp = StandardScaler().fit_transform(s)[:, 3]
    rob_spp = RobustScaler().fit_transform(s)[:, 3]
    axes[0].hist(raw_spp, bins=30, color='gray'); axes[0].set_title('Raw SPP')
    axes[1].hist(std_spp, bins=30, color='orange'); axes[1].set_title('StandardScaler SPP')
    axes[2].hist(rob_spp, bins=30, color='green'); axes[2].set_title('RobustScaler SPP')
    plt.tight_layout()
    plt.savefig(out_dir / 'fig3_scaling_hist.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # Step 3: Temporal Windowing
    # -------------------------------------------------------------
    print("[4/6] Running Step 3: Windowing vs Point...")
    W, STEP = 60, 30
    uw = pd.read_csv(path, usecols=['YYYY/MM/DD', 'HH:MM:SS'] + SENSOR_8, nrows=N_WIN_SRC, low_memory=True)
    for c in SENSOR_8:
        uw[c] = pd.to_numeric(uw[c], errors='coerce').astype('float32')
    uw = uw.replace(-999.25, np.nan).dropna().reset_index(drop=True)
    uw['Rate Of Penetration (ft_per_hr)'] = uw['Rate Of Penetration (ft_per_hr)'].clip(upper=ROP_HI)
    uw['datetime'] = pd.to_datetime(uw['YYYY/MM/DD'] + ' ' + uw['HH:MM:SS'], format='%Y/%m/%d %H:%M:%S', errors='coerce')
    uw = uw.sort_values('datetime').reset_index(drop=True)

    rows_win = []
    for st in range(0, len(uw) - W + 1, STEP):
        ch = uw.iloc[st:st + W]
        rec = {'t0': ch['datetime'].iloc[0]}
        for c in SENSOR_8:
            v = ch[c].to_numpy(dtype='float64')
            rec[c + '__mean'] = float(v.mean())
            rec[c + '__std'] = float(v.std())
            rec[c + '__delta'] = float(v[-1] - v[0])
        rows_win.append(rec)
    win_df = pd.DataFrame(rows_win)
    feat_win = [c for c in win_df.columns if c != 't0']

    Xp = RobustScaler().fit_transform(uw[SENSOR_8].sample(min(15000, len(uw)), random_state=SEED))
    lp = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit_predict(Xp)
    Xw = RobustScaler().fit_transform(win_df[feat_win].to_numpy())
    lw = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit_predict(Xw)

    df_temporal = pd.DataFrame({
        'representation': ['point', 'window-60s'],
        'silhouette': [float(silhouette_score(Xp, lp)), float(silhouette_score(Xw, lw))],
        'dbi': [float(davies_bouldin_score(Xp, lp)), float(davies_bouldin_score(Xw, lw))]
    }).round(4)
    df_temporal.to_csv(out_dir / 'table3_temporal_compare.csv', index=False)
    print("Table 3 (Temporal comparison):")
    print(df_temporal)

    # fig4: temporal trace
    plt.figure(figsize=(10, 3))
    plt.plot(uw['datetime'].iloc[:3000], uw['Standpipe Pressure (psi)'].iloc[:3000], color='navy', lw=1)
    plt.title('Fig 4. Standpipe Pressure 1 Hz Trace (First 3000 seconds)')
    plt.xlabel('Time'); plt.ylabel('SPP (psi)')
    plt.tight_layout()
    plt.savefig(out_dir / 'fig4_temporal_trace.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # Step 4: Final Clustering (4 Scenarios x k=2..8, subsample 20k)
    # -------------------------------------------------------------
    print("[5/6] Running Step 4: Final Clustering (4 scenarios x k=2..8)...")
    fd = pd.read_csv(path, usecols=['YYYY/MM/DD', 'HH:MM:SS'] + SENSOR_8, nrows=N_FINAL * 2, low_memory=True)
    fd = fd.iloc[np.sort(np.random.RandomState(SEED).choice(len(fd), N_FINAL, replace=False))].reset_index(drop=True)
    for c in SENSOR_8:
        fd[c] = pd.to_numeric(fd[c], errors='coerce').astype('float32')
    fd = fd.replace(-999.25, np.nan)

    # Winsorize ROP with floor to protect against pure-idle head sample
    rop_q1, rop_q3 = fd['Rate Of Penetration (ft_per_hr)'].quantile(0.25), fd['Rate Of Penetration (ft_per_hr)'].quantile(0.75)
    iqr = rop_q3 - rop_q1
    ROP_HI = float(rop_q3 + 1.5 * iqr) if iqr > 0 else 47.4
    fd['Rate Of Penetration (ft_per_hr)'] = fd['Rate Of Penetration (ft_per_hr)'].clip(upper=ROP_HI)
    print(f"Final sample ROP winsorized at HI = {ROP_HI:.2f}")

    # Exclude Differential Pressure (7 modeling sensors)
    USE_DIFF_PRESS = False
    SENSORS = SENSOR_8 if USE_DIFF_PRESS else [c for c in SENSOR_8 if c != 'Differential Pressure (psi)']
    print(f"Modeling sensors ({len(SENSORS)}): {SENSORS}")
    fd = fd.dropna(subset=SENSORS).reset_index(drop=True)
    fd['datetime'] = pd.to_datetime(fd['YYYY/MM/DD'] + ' ' + fd['HH:MM:SS'], format='%Y/%m/%d %H:%M:%S', errors='coerce')

    def windowed_final(d, w=60, step=30):
        d = d.sort_values('datetime').reset_index(drop=True)
        out = []
        for s_ in range(0, len(d) - w + 1, step):
            ch = d.iloc[s_:s_ + w]
            rec = {'t0': ch['datetime'].iloc[0]}
            for c in SENSORS:
                v = ch[c].to_numpy(dtype='float64')
                rec[c + '__mean'] = v.mean()
                rec[c + '__std'] = v.std()
                rec[c + '__delta'] = v[-1] - v[0]
            out.append(rec)
        return pd.DataFrame(out)

    scen = {
        'point-standard': (fd[SENSORS].to_numpy(), StandardScaler()),
        'point-robust': (fd[SENSORS].to_numpy(), RobustScaler())
    }
    wf = windowed_final(fd)
    feat2 = [c for c in wf.columns if c != 't0']
    scen['window60-standard'] = (wf[feat2].to_numpy(), StandardScaler())
    scen['window60-robust'] = (wf[feat2].to_numpy(), RobustScaler())
    print("Scenario shapes:", {k: v[0].shape for k, v in scen.items()})

    K_RANGE = range(2, 9)
    rows_k = []
    for name, (X, sc) in scen.items():
        Xs = sc.fit_transform(X)
        idx = np.random.RandomState(SEED).choice(len(Xs), min(len(Xs), 20000), replace=False)
        Xe = Xs[idx]
        for k in K_RANGE:
            km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Xe)
            lab = km.labels_
            rows_k.append({
                'scenario': name,
                'k': k,
                'inertia': float(km.inertia_),
                'silhouette': float(silhouette_score(Xe, lab)),
                'dbi': float(davies_bouldin_score(Xe, lab))
            })
    res_k = pd.DataFrame(rows_k)
    res_k.to_csv(out_dir / 'table4_elbow_metrics.csv', index=False)

    print("\n--- SILHOUETTE PIVOT (k=2..8) ---")
    piv_sil = res_k.pivot_table(index='k', columns='scenario', values='silhouette').round(4)
    print(piv_sil)

    print("\n--- DAVIES-BOULDIN PIVOT (k=2..8) ---")
    piv_dbi = res_k.pivot_table(index='k', columns='scenario', values='dbi').round(4)
    print(piv_dbi)

    print("\n--- INERTIA PIVOT (k=2..8) ---")
    piv_ine = res_k.pivot_table(index='k', columns='scenario', values='inertia').round(2)
    print(piv_ine)

    # fig5: Elbow curves (inertia & silhouette)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for name, g in res_k.groupby('scenario'):
        ax[0].plot(g['k'], g['inertia'], marker='o', label=name)
        ax[1].plot(g['k'], g['silhouette'], marker='o', label=name)
    ax[0].set_title('Fig 5a. Elbow — Inertia vs k'); ax[0].set_xlabel('k'); ax[0].set_ylabel('Inertia')
    ax[1].set_title('Fig 5b. Silhouette vs k (higher better)'); ax[1].set_xlabel('k'); ax[1].set_ylabel('Silhouette')
    ax[0].legend(fontsize=8); ax[1].legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / 'fig5_elbow_silhouette.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # Step 5: Best Model Refit & Centroid Interpretation
    # -------------------------------------------------------------
    print("[6/6] Refitting best model and extracting physical centroids...")
    BEST_SCENARIO = 'window60-robust'
    BEST_K = 4
    Xb, scb = scen[BEST_SCENARIO]
    Xbs = scb.fit_transform(Xb)
    kmf = KMeans(n_clusters=BEST_K, n_init=10, random_state=SEED).fit(Xbs)
    labf = kmf.labels_
    cent = scb.inverse_transform(kmf.cluster_centers_)

    # Correct extraction of mean columns (resolves indexing bug)
    if 'window' in BEST_SCENARIO:
        mean_indices = [i for i, c in enumerate(feat2) if c.endswith('__mean')]
        mean_cols = [c.replace('__mean', '') for c in feat2 if c.endswith('__mean')]
        ctab = pd.DataFrame(cent[:, mean_indices], columns=mean_cols)
    else:
        ctab = pd.DataFrame(cent, columns=SENSORS)
    ctab.index.name = 'cluster'
    ctab.round(2).to_csv(out_dir / 'table5_centroids.csv')

    share = pd.Series(labf).value_counts(normalize=True).round(4)
    share.index.name = 'cluster'
    share.to_csv(out_dir / 'table6_cluster_share.csv', header=['share'])

    print("\n--- TABLE 5: CENTROIDS (in physical units) ---")
    print(ctab.round(2))
    print("\n--- TABLE 6: CLUSTER SHARE ---")
    print(share)

    # Also compute point-robust k=4 centroids for comparison
    X_pr, sc_pr = scen['point-robust']
    X_prs = sc_pr.fit_transform(X_pr)
    km_pr = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(X_prs)
    cent_pr = sc_pr.inverse_transform(km_pr.cluster_centers_)
    ctab_pr = pd.DataFrame(cent_pr, columns=SENSORS)
    ctab_pr.index.name = 'cluster'
    ctab_pr.round(2).to_csv(out_dir / 'table5_centroids_point_robust.csv')
    share_pr = pd.Series(km_pr.labels_).value_counts(normalize=True).round(4)
    share_pr.to_csv(out_dir / 'table6_cluster_share_point_robust.csv', header=['share'])
    print("\n--- POINT-ROBUST CENTROIDS (k=4) ---")
    print(ctab_pr.round(2))

    # fig6: PCA 2D scatter
    p2 = PCA(n_components=2, random_state=SEED).fit_transform(Xbs[np.random.RandomState(SEED).choice(len(Xbs), min(len(Xbs), 15000), replace=False)])
    ls = labf[np.random.RandomState(SEED).choice(len(labf), p2.shape[0], replace=False)]
    plt.figure(figsize=(6, 5))
    plt.scatter(p2[:, 0], p2[:, 1], c=ls, s=6, cmap='tab10', alpha=0.6)
    plt.title(f'Fig 6. PCA 2D — {BEST_SCENARIO} k={BEST_K}')
    plt.xlabel('PC1'); plt.ylabel('PC2')
    plt.tight_layout()
    plt.savefig(out_dir / 'fig6_pca_clusters.png', dpi=150)
    plt.close()

    print(f"\n[DONE] Pipeline completed in {time.time() - t_start:.1f}s. All outputs in {out_dir}/.")

if __name__ == '__main__':
    main()
