import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
import zipfile
import ast
import tempfile

# Import Dhvani modules
import dhvani.fwh as fwh
import dhvani.spectral_analysis as sa

st.set_page_config(page_title="Dhvani Web GUI", layout="wide")

st.title("Dhvani: Aeroacoustics & Signal Processing")

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

        obs_loc_str = st.text_input("Observer Locations (e.g. [[0,0,10]])", value="[[0.0, 0.0, 1.0]]")
        dt_val = st.number_input("Time Step (dt)", value=0.01, format="%.4f")
        steps_val = st.number_input("Number of Steps", value=10, step=1)
        ma_str = st.text_input("Mach Number (e.g. [0.1, 0, 0])", value="[0.0, 0.0, 0.0]")
        temp_val = st.number_input("Temperature (K)", value=298.0)
        perm_val = st.checkbox("Permeable Surface", value=False)

        run_btn = st.button("Run FWH Solver")

    with col2:
        st.subheader("Results")
        result_container = st.container()

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
                        zip_ref.extractall(surf_dir)

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
        uploaded_sig = st.file_uploader("Upload Signal CSV", type="csv")

        if uploaded_sig:
            df = pd.read_csv(uploaded_sig)
            st.dataframe(df.head())

            time_col = st.selectbox("Select Time Column", df.columns)
            sig_col = st.selectbox("Select Signal Column", [c for c in df.columns if c != time_col])

            method = st.selectbox("Method", ["FFT", "Welch"])

            if method == "Welch":
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    chunks = st.number_input("Chunks", value=4, step=1, min_value=1)
                with col_w2:
                    overlap = st.number_input("Overlap", value=0.5, min_value=0.0, max_value=0.99)

            plot_spec_btn = st.button("Plot Spectrum")

    with col2:
        if uploaded_sig and plot_spec_btn:
             try:
                time = df[time_col].values
                sig = df[sig_col].values

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
