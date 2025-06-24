import numpy as np

for fname in ["feats_stats.npz", "energy_stats.npz", "pitch_stats.npz"]:
    print(f"Processing {fname}...")
    data = np.load(fname, allow_pickle=True)
    np.savez(fname, **data)
    print(f"Re-saved {fname} as plain NumPy .npz (no pickle).")