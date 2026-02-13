import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
import zipfile
import ast
import tempfile
# Import SonicLit modules
import soniclit.fwh_solver as fwh
import soniclit.signal_processing as sa
from soniclit.utils import safe_extract_zip, validate_zip_contents, is_file_size_valid, sanitize_markdown

# Security Constants
MAX_CSV_SIZE_MB = 10
MAX_ZIP_SIZE_MB = 50

# Locate dummy data for sample download
data_path = "dummy_data.zip"
if not os.path.exists(data_path):
    # Try relative to this file
    app_dir = os.path.dirname(os.path.abspath(__file__))
    # adjust path relative to src/soniclit/gui/web/app.py -> root/dummy_data.zip
    data_path = os.path.abspath(os.path.join(app_dir, "../../../../dummy_data.zip"))

has_sample_data = os.path.exists(data_path)

st.set_page_config(page_title="SonicLit Web GUI", layout="wide")

st.title("SonicLit: Aeroacoustics & Signal Processing")

tab_fwh, tab_spectral = st.tabs(["FWH Solver", "Spectral Analysis"])

# --- FWH Solver Tab ---
with tab_fwh:
    st.header("Ffowcs-Williams Hawkings Solver")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Configuration")

        # Surface Data Input
        # Since FWH requires a set of files (0.csv, 1.csv, Avg.csv, etc.)
        # We will ask user to upload a ZIP file containing these.
        uploaded_surf_zip = st.file_uploader("Upload Surface Data (ZIP)", type="zip", help="Zip file should contain surface CSVs (Avg.csv, 0.csv, 1.csv...)")

        if uploaded_surf_zip:
            if not is_file_size_valid(uploaded_surf_zip, MAX_ZIP_SIZE_MB):
                st.error(f"File too large. Please upload a ZIP file smaller than {MAX_ZIP_SIZE_MB}MB.")
                uploaded_surf_zip = None
            else:
                is_valid, msg = validate_zip_contents(uploaded_surf_zip, "Avg.csv")

                # Sanitize output to prevent Markdown/XSS injection
                safe_msg = sanitize_markdown(msg.replace('Found ', ''))

                if is_valid:
                    st.success(f"✅ Valid surface data found: {safe_msg}")
                else:
                    st.warning(f"⚠️ Validation Warning: {sanitize_markdown(msg)}")

        if has_sample_data:
            with st.expander("Need sample data?"):
                st.markdown("Download this sample ZIP to test the FWH solver.")
                with open(data_path, "rb") as f:
                    st.download_button(
                        label="Download Sample Data (ZIP)",
                        data=f,
                        file_name="sample_surface_data.zip",
                        mime="application/zip",
                        help="Download sample data to test the solver."
                    )

        obs_loc_str = st.text_input("Observer Locations (e.g. [[0,0,10]])", value="[[0.0, 0.0, 1.0]]", max_chars=5000, help="List of coordinates [x,y,z]. Example: [[0, 0, 10], [0, 10, 10]]")

        # Validation for obs_loc
        obs_valid = True
        try:
            if len(obs_loc_str) > 5000:
                st.error("Input too long (max 5000 characters).")
                obs_valid = False
            else:
                val = ast.literal_eval(obs_loc_str)
                if not isinstance(val, (list, tuple)):
                    st.error("Observer locations must be a list of coordinates (e.g. [[0,0,10]]).")
                    obs_valid = False
                elif len(val) > 100:
                    st.error("Too many observer locations (max 100).")
                    obs_valid = False
                else:
                    for item in val:
                        if not isinstance(item, (list, tuple)) or len(item) != 3:
                            st.error("Each observer location must be a list of 3 coordinates [x, y, z].")
                            obs_valid = False
                            break
                        if not all(isinstance(x, (int, float)) for x in item):
                            st.error("Coordinates must be numbers.")
                            obs_valid = False
                            break
        except:
            st.error("Invalid format. Use Python list syntax, e.g. [[0,0,10]]")
            obs_valid = False

        dt_val = st.number_input("Time Step (dt)", value=0.01, format="%.4f", help="Simulation time step in seconds.")
        steps_val = st.number_input("Number of Steps", value=10, step=1, min_value=1, max_value=100000, help="Total number of time steps to process.")
        # Security: Enforce backend limit to prevent DoS
        steps_val = min(steps_val, 100000)

        ma_str = st.text_input("Mach Number (e.g. [0.1, 0, 0])", value="[0.0, 0.0, 0.0]", max_chars=5000, help="Mach vector [Mx, My, Mz]. Example: [0.1, 0.0, 0.0]")

        # Validation for ma
        ma_valid = True
        try:
            if len(ma_str) > 5000:
                st.error("Input too long (max 5000 characters).")
                ma_valid = False
            else:
                val = ast.literal_eval(ma_str)
                if not isinstance(val, (list, tuple)):
                    st.error("Mach Number must be a list (vector).")
                    ma_valid = False
                elif len(val) != 3:
                    st.error("Mach Number must have 3 components [Mx, My, Mz].")
                    ma_valid = False
        except:
            st.error("Invalid format. Use Python list syntax, e.g. [0.1, 0, 0]")
            ma_valid = False

        temp_val = st.number_input("Temperature (K)", value=298.0, help="Ambient temperature in Kelvin (affects speed of sound).")
        perm_val = st.checkbox("Permeable Surface", value=False, help="Enable if using a permeable integration surface.")

        run_btn = st.button("Run FWH Solver", type="primary", disabled=not (obs_valid and ma_valid))

    with col2:
        st.subheader("Results")
        result_container = st.container()
        if not run_btn:
             result_container.info("Configure parameters and run the solver to see results here.")

    if run_btn:
        if uploaded_surf_zip is None:
            st.error("Please upload a ZIP file containing surface data.")
        else:
            try:
                # Parse inputs
                obs_loc = ast.literal_eval(obs_loc_str)
                ma = ast.literal_eval(ma_str)
                t_src = [i*dt_val for i in range(int(steps_val))]

                # Create temp directories
                with tempfile.TemporaryDirectory() as temp_dir:
                    surf_dir = os.path.join(temp_dir, "surf_data")
                    out_dir = os.path.join(temp_dir, "output")
                    os.makedirs(surf_dir, exist_ok=True)
                    os.makedirs(out_dir, exist_ok=True)

                    # Extract ZIP
                    with zipfile.ZipFile(uploaded_surf_zip, 'r') as zip_ref:
                        safe_extract_zip(zip_ref, surf_dir)

                    # Identify prefix
                    # We expect files like prefixAvg.csv, prefix0.csv
                    # Let's find Avg.csv
                    files = os.listdir(surf_dir)
                    avg_files = [f for f in files if f.endswith("Avg.csv")]

                    if not avg_files:
                         # Maybe it's in a subdir?
                         # For now assume flat structure in zip
                         st.error("Could not find *Avg.csv in the uploaded ZIP.")
                         prefix = None
                    else:
                        # Take the first one found
                        avg_file = avg_files[0]
                        prefix = avg_file.replace("Avg.csv", "")
                        # Full path prefix
                        full_prefix = os.path.join(surf_dir, prefix)

                        # Output prefix
                        out_prefix = os.path.join(out_dir, "fwh_out")

                        # Run FWH
                        with st.spinner("Running FWH Solver..."):
                            msg = fwh.stationary_serial(full_prefix, out_prefix, obs_loc, t_src, ma, perm_val, write=True, Ta=temp_val)
                            st.success(msg)

                            # Display/Download results
                            # List generated files
                            out_files = os.listdir(out_dir)
                            # Create a zip of results
                            result_zip_path = os.path.join(temp_dir, "results.zip")
                            with zipfile.ZipFile(result_zip_path, 'w') as res_zip:
                                for f in out_files:
                                    res_zip.write(os.path.join(out_dir, f), arcname=f)

                            with open(result_zip_path, "rb") as fp:
                                st.download_button(
                                    label="Download Results (ZIP)",
                                    data=fp,
                                    file_name="fwh_results.zip",
                                    mime="application/zip"
                                )

                            # Plot preview if PNGs exist
                            png_files = [f for f in out_files if f.endswith(".png")]
                            for png in png_files:
                                st.image(os.path.join(out_dir, png), caption=png)

            except Exception as e:
                st.error(f"Error occurred: {str(e)}")


# --- Spectral Analysis Tab ---
with tab_spectral:
    st.header("Spectral Analysis")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_sig = st.file_uploader("Upload Signal CSV", type="csv", help="CSV file with time and signal columns.")

        if has_sample_data:
             with st.expander("Need sample data?"):
                st.markdown("Download the sample ZIP which contains `signal.csv`.")
                with open(data_path, "rb") as f:
                    st.download_button(
                        label="Download Sample Data (ZIP)",
                        data=f,
                        file_name="sample_signal_data.zip",
                        mime="application/zip",
                        key="download_sample_spectral"
                    )

        if uploaded_sig:
            if not is_file_size_valid(uploaded_sig, MAX_CSV_SIZE_MB):
                st.error(f"File too large. Please upload a CSV file smaller than {MAX_CSV_SIZE_MB}MB.")
                uploaded_sig = None
            else:
                df = pd.read_csv(uploaded_sig)
                st.dataframe(df.head())

                time_col = st.selectbox("Select Time Column", df.columns)
                sig_col = st.selectbox("Select Signal Column", [c for c in df.columns if c != time_col])

                method = st.selectbox("Method", ["FFT", "Welch"], help="Choose 'FFT' for standard spectrum or 'Welch' for smoothed periodogram.")

                if method == "Welch":
                    col_w1, col_w2 = st.columns(2)
                    with col_w1:
                        chunks = st.number_input("Chunks", value=4, step=1, min_value=1, max_value=1000, help="Number of segments to split the signal into (higher = smoother but lower frequency resolution).")
                        chunks = min(chunks, 1000)
                    with col_w2:
                        overlap = st.number_input("Overlap", value=0.5, min_value=0.0, max_value=0.99, help="Fraction of overlap between segments (typically 0.5 or 50%).")

    with col2:
        if uploaded_sig:
             try:
                time = df[time_col].values
                sig = df[sig_col].values

                with st.spinner("Computing spectrum..."):
                    fig, ax = plt.subplots()

                    if method == "FFT":
                        freq, df_bin, psd = sa.fft_spectrum(time, sig)
                        ax.loglog(freq, psd)
                        ax.set_title("FFT Spectrum")
                    elif method == "Welch":
                        freq, df_bin, psd = sa.welch_spectrum(time, sig, chunks=chunks, overlap=overlap)
                        ax.loglog(freq, psd)
                        ax.set_title("Welch Spectrum")

                    ax.set_xlabel("Frequency (Hz)")
                    ax.set_ylabel("PSD")
                    ax.grid(True)

                    st.pyplot(fig)

             except Exception as e:
                 st.error(f"Error: {e}")
        else:
             st.info("👋 Upload a CSV file on the left to get started with spectral analysis.")
             st.markdown("""
                **Expected Format:**
                - A CSV file with at least two columns.
                - One column for **Time** (s).
                - One column for **Signal** (Pressure, Velocity, etc.).
             """)
