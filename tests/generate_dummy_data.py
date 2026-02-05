import pandas as pd
import numpy as np
import os

def generate_fwh_data(prefix="dummy_surf_", steps=10):
    # Create directory if needed
    os.makedirs(os.path.dirname(prefix) if os.path.dirname(prefix) else '.', exist_ok=True)

    # Geometry: A simple sphere or just a point source
    # Let's create a single panel for simplicity
    n_panels = 1
    y1 = np.zeros(n_panels)
    y2 = np.zeros(n_panels)
    y3 = np.zeros(n_panels)
    n1 = np.ones(n_panels) # Normal pointing in x
    n2 = np.zeros(n_panels)
    n3 = np.zeros(n_panels)
    dS = np.ones(n_panels) * 0.1 # Area

    # Base columns 0-6
    geom_cols = [y1, y2, y3, n1, n2, n3, dS]

    # Dummy filler for col 7
    col7 = np.zeros(n_panels)

    # Variables
    # fluctuating pressure p' = sin(omega * t)
    # rho, u, T constant for impermeable (only p matters)

    rho = np.ones(n_panels) * 1.225
    u1 = np.zeros(n_panels)
    u2 = np.zeros(n_panels)
    u3 = np.zeros(n_panels)
    T = np.ones(n_panels) * 298

    # Average file (Time independent)
    # p_mean = 100000
    p_mean = np.ones(n_panels) * 101325.0

    # Construct DataFrame for Avg
    # 0-6: geom
    # 7: dummy
    # 8: rho
    # 9-11: u
    # 12: T
    # 13: p

    data_avg = np.column_stack(geom_cols + [col7, rho, u1, u2, u3, T, p_mean])
    # The code uses usecols=range(8,9) for rho (index 8) and range(13,14) for p (index 13)
    # It also uses range(7) for geometry.
    # So we need at least 14 columns.

    # Save Avg.csv
    # Note: fwh.py reads with header=0 (default) or 'names' argument implies it ignores header?
    # fwh.py: pd.read_csv(..., names=...) usually implies header=None if not specified,
    # BUT if the file has a header, it might read it as data if header=None is inferred, OR if names is given, it expects header=None?
    # Actually: pd.read_csv(file, names=['a', 'b']) will assume no header by default if header='infer' (default).
    # Wait, if names is given, header is NOT None by default?
    # "header : int, list of int, default 'infer'. Row number(s) to use as the column names... If names are passed, the behavior is identical to header=None and valid column names are replaced with names."
    # So if names is passed, it assumes NO header.
    # I should write NO header.

    pd.DataFrame(data_avg).to_csv(f"{prefix}Avg.csv", header=False, index=False)

    # Time dependent files
    dt = 0.01
    freq = 10.0 # Hz

    for i in range(steps):
        t = i * dt
        p_fluc = 10.0 * np.sin(2 * np.pi * freq * t)
        p_total = p_mean + p_fluc

        # u, rho etc stay constant for this dummy setup
        data_t = np.column_stack(geom_cols + [col7, rho, u1, u2, u3, T, p_total])
        pd.DataFrame(data_t).to_csv(f"{prefix}{i}.csv", header=False, index=False)

    print(f"Generated FWH dummy data at {prefix}...")

def generate_signal_data(filename="dummy_signal.csv"):
    t = np.linspace(0, 1.0, 1000)
    # Signal: sum of sines
    sig = 5.0 * np.sin(2 * np.pi * 50 * t) + 2.0 * np.sin(2 * np.pi * 120 * t) + np.random.normal(0, 0.5, len(t))

    df = pd.DataFrame({'Time': t, 'Signal': sig})
    df.to_csv(filename, index=False)
    print(f"Generated signal dummy data at {filename}")

if __name__ == "__main__":
    generate_fwh_data(prefix="tests/data/surf_", steps=20)
    generate_signal_data(filename="tests/data/signal.csv")
