import os
import pytest
import numpy as np
import pandas as pd
from src.soniclit.fwh_solver import stationary_serial

# Helper to generate data
def generate_fwh_data(prefix="dummy_surf_", steps=10):
    os.makedirs(os.path.dirname(prefix) if os.path.dirname(prefix) else '.', exist_ok=True)
    n_panels = 1
    # Geometry: point at origin
    geom = np.zeros((n_panels, 7))
    geom[:, 3] = 1.0 # n1
    geom[:, 6] = 0.1 # dS

    # Data columns: 0-6 geom, 7 dummy, 8 rho, 9-11 u, 12 T, 13 p
    data_base = np.zeros((n_panels, 14))
    data_base[:, 0:7] = geom
    data_base[:, 8] = 1.225 # rho
    data_base[:, 12] = 298.0 # T
    data_base[:, 13] = 101325.0 # p_mean

    # Save Avg
    pd.DataFrame(data_base).to_csv(f"{prefix}Avg.csv", header=False, index=False)

    dt = 0.01
    for i in range(steps):
        t = i * dt
        data = data_base.copy()
        data[:, 13] += 10.0 * np.sin(2 * np.pi * 10.0 * t) # p'
        pd.DataFrame(data).to_csv(f"{prefix}{i}.csv", header=False, index=False)

@pytest.fixture
def fwh_setup(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    prefix = str(data_dir / "surf_")
    generate_fwh_data(prefix, steps=20)

    out_dir = tmp_path / "output"
    out_dir.mkdir()
    out_file = str(out_dir / "result")

    return prefix, out_file

def test_stationary_serial(fwh_setup):
    surf_file, out_file = fwh_setup

    observer_locations = [[10.0, 0.0, 0.0]]
    dt = 0.01
    source_times = [i * dt for i in range(20)]
    mach_number = [0.1, 0.0, 0.0]
    is_permeable = False

    # Run the function
    stationary_serial(surf_file, out_file, observer_locations, source_times, mach_number, is_permeable)

    # Check output
    res_file = out_file + "0.csv"
    assert os.path.exists(res_file)
    df = pd.read_csv(res_file)
    assert not df.empty
    assert "p'" in df.columns
    # Check if there are some non-zero values (not guaranteed if observer is too far or time too short, but likely)
    # With 20 steps, we might capture some signal

# Helper to generate data for permeable surface
def generate_fwh_data_permeable(prefix="dummy_surf_perm_", steps=10):
    os.makedirs(os.path.dirname(prefix) if os.path.dirname(prefix) else '.', exist_ok=True)
    n_panels = 10
    # Geometry: point at origin
    geom = np.zeros((n_panels, 7))
    geom[:, 3] = 1.0 # n1
    geom[:, 6] = 0.1 # dS

    # Data columns: 0-6 geom, 7 dummy, 8 rho, 9-11 u, 12 T, 13 p
    data_base = np.zeros((n_panels, 14))
    data_base[:, 0:7] = geom
    data_base[:, 8] = 1.225 # rho
    data_base[:, 9] = 10.0 # u_x
    data_base[:, 10] = 0.0 # u_y
    data_base[:, 11] = 0.0 # u_z
    data_base[:, 12] = 298.0 # T
    data_base[:, 13] = 101325.0 # p_mean

    # Save Avg
    pd.DataFrame(data_base).to_csv(f"{prefix}Avg.csv", header=False, index=False)

    dt = 0.01
    for i in range(steps):
        t = i * dt
        data = data_base.copy()
        data[:, 13] += 10.0 * np.sin(2 * np.pi * 10.0 * t) # p'
        # Vary velocity slightly
        data[:, 9] += 1.0 * np.sin(2 * np.pi * 10.0 * t)
        pd.DataFrame(data).to_csv(f"{prefix}{i}.csv", header=False, index=False)

@pytest.fixture
def fwh_perm_setup(tmp_path):
    data_dir = tmp_path / "data_perm"
    data_dir.mkdir()
    prefix = str(data_dir / "surf_perm_")
    generate_fwh_data_permeable(prefix, steps=20)

    out_dir = tmp_path / "output_perm"
    out_dir.mkdir()
    out_file = str(out_dir / "result_perm")

    return prefix, out_file

def test_stationary_serial_permeable(fwh_perm_setup):
    surf_file, out_file = fwh_perm_setup

    observer_locations = [[10.0, 0.0, 0.0]]
    dt = 0.01
    source_times = [i * dt for i in range(20)]
    mach_number = [0.1, 0.0, 0.0]
    is_permeable = True

    # Run the function
    stationary_serial(surf_file, out_file, observer_locations, source_times, mach_number, is_permeable)

    # Check output
    res_file = out_file + "0.csv"
    assert os.path.exists(res_file)
    df = pd.read_csv(res_file)
    assert not df.empty
    assert "p'" in df.columns
