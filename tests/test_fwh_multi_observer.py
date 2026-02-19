import os
import pytest
import numpy as np
import pandas as pd
from src.soniclit.fwh_solver import stationary_serial

def generate_fwh_data(prefix, steps=10):
    os.makedirs(os.path.dirname(prefix) if os.path.dirname(prefix) else '.', exist_ok=True)
    n_panels = 2
    geom = np.zeros((n_panels, 7))
    geom[:, 3] = 1.0 # n1
    geom[:, 6] = 0.1 # dS

    # Create fake data
    for i in range(steps):
        data = np.zeros((n_panels, 14))
        data[:, 0:7] = geom
        data[:, 8] = 1.225 # rho
        data[:, 13] = 101325.0 + 10.0 * np.sin(i * 0.1) # p

        # Save
        if i == 0:
            # Avg file
            pd.DataFrame(data).to_csv(f"{prefix}Avg.csv", header=False, index=False)

        pd.DataFrame(data).to_csv(f"{prefix}{i}.csv", header=False, index=False)

def test_multi_observer_correctness(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    prefix = str(data_dir / "surf_")
    generate_fwh_data(prefix, steps=10)

    out_dir = tmp_path / "output"
    out_dir.mkdir()
    out_base = str(out_dir / "res")

    observers = [[10.0, 0.0, 0.0], [0.0, 10.0, 0.0]]
    times = [i * 0.01 for i in range(10)]
    mach = [0.1, 0.0, 0.0]

    # Run combined
    stationary_serial(prefix, out_base + "_combined", observers, times, mach, is_permeable=False, write=True)

    # Run separate
    stationary_serial(prefix, out_base + "_single0", [observers[0]], times, mach, is_permeable=False, write=True)
    stationary_serial(prefix, out_base + "_single1", [observers[1]], times, mach, is_permeable=False, write=True)

    # Compare
    df_c0 = pd.read_csv(out_base + "_combined0.csv")
    df_s0 = pd.read_csv(out_base + "_single00.csv")
    pd.testing.assert_frame_equal(df_c0, df_s0)

    df_c1 = pd.read_csv(out_base + "_combined1.csv")
    df_s1 = pd.read_csv(out_base + "_single10.csv") # Note: single run output is indexed 0
    pd.testing.assert_frame_equal(df_c1, df_s1)
