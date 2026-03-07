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
from soniclit.utils import safe_extract_zip, validate_zip_contents, is_file_size_valid, sanitize_markdown, get_column_index

def parse_observer_input(obs_loc_str):
    """
    Parses observer location string.
    Supports both Python list syntax (e.g., [[x,y,z], ...])
    and CSV/Newline separated format (e.g., x, y, z \n ...).
    """
    try:
        # Try parsing as Python list
        return ast.literal_eval(obs_loc_str)
    except:
        # Fallback: Try parsing as CSV/Lines
        val = []
        for line in obs_loc_str.strip().split('\n'):
            if line.strip():
                # Remove brackets if user mixed formats, split by comma
                clean_line = line.replace('[', '').replace(']', '')
                parts = [float(x.strip()) for x in clean_line.split(',')]
                if len(parts) == 3:
                    val.append(parts)
                else:
                    raise ValueError("Invalid CSV line")
        return val

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

st.set_page_config(page_title="SonicLit Web GUI", page_icon="🔊", layout="wide")

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

        obs_mode = st.radio("**Observer Location**", ["Single Point", "Coordinate List"], horizontal=True, help="Choose how to define observer coordinates.")

        if obs_mode == "Single Point":
            oc1, oc2, oc3 = st.columns(3)
            with oc1: ox = st.number_input("Observer X (m)", value=0.0, step=1.0, format="%.1f", help="X Coordinate in meters")
            with oc2: oy = st.number_input("Observer Y (m)", value=0.0, step=1.0, format="%.1f", help="Y Coordinate in meters")
            with oc3: oz = st.number_input("Observer Z (m)", value=1.0, step=1.0, format="%.1f", help="Z Coordinate in meters")
            obs_loc_str = str([[ox, oy, oz]])
        else:
            obs_loc_str = st.text_area("Coordinates List", value="[[0.0, 0.0, 1.0]]", max_chars=5000, help="List of coordinates [x,y,z] or CSV format. Example:\n[[0, 0, 10], [0, 10, 10]]\nOR\n0, 0, 10\n0, 10, 10")
            st.caption("Example Format: `[[x1, y1, z1], [x2, y2, z2]]` OR CSV (one coord per line)")

        # Validation for obs_loc
        obs_valid = True
        try:
            if len(obs_loc_str) > 5000:
                st.error("Input too long (max 5000 characters).")
                obs_valid = False
            else:
                val = parse_observer_input(obs_loc_str)

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
                    if obs_valid:
                        st.caption(f"✅ Ready to compute for **{len(val)}** observer(s).")
                        if obs_mode == "Coordinate List" and len(val) > 0:
                            with st.expander("Preview Parsed Coordinates"):
                                preview_df = pd.DataFrame(val, columns=["X (m)", "Y (m)", "Z (m)"])
                                st.dataframe(preview_df, hide_index=True)
        except:
            st.error("Invalid format. Use Python list syntax `[[x,y,z]]` OR CSV `x, y, z`")
            obs_valid = False

        dt_val = st.number_input("Time Step (s)", value=0.01, format="%.4f", help="Simulation time step in seconds.")
        steps_val = st.number_input("Number of Steps", value=10, step=1, min_value=1, max_value=100000, help="Total number of time steps to process.")
        # Security: Enforce backend limit to prevent DoS
        steps_val = min(steps_val, 100000)

        total_sim_time = dt_val * steps_val
        st.caption(f"⏱️ Total Simulation Time: **{total_sim_time:.4f} s**")

        st.markdown("**Mach Vector Components**")
        mc1, mc2, mc3 = st.columns(3)
        with mc1: mx = st.number_input("Mx", value=0.0, step=0.1, format="%.2f", help="Mach X")
        with mc2: my = st.number_input("My", value=0.0, step=0.1, format="%.2f", help="Mach Y")
        with mc3: mz = st.number_input("Mz", value=0.0, step=0.1, format="%.2f", help="Mach Z")
        ma_str = str([mx, my, mz])

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


        # UX Enhancement: Explain why the run button is disabled
        button_help = "Start the FWH solver"
        if uploaded_surf_zip is None:
            button_help = "Upload a surface data ZIP first to run the solver"
        elif not obs_valid:
            button_help = "Fix observer coordinates format to run"
        elif not ma_valid:
            button_help = "Fix Mach vector format to run"

        run_btn = st.button(
            "Run FWH Solver",
            type="primary",
            disabled=not (obs_valid and ma_valid and uploaded_surf_zip is not None),
            help=button_help
        )


    with col2:
        st.subheader("Results")
        result_container = st.container()
        if not run_btn:
             result_container.info("👋 Configure parameters and run the solver to see results here.")
             result_container.markdown("""
                **Expected Results:**
                - A downloadable ZIP archive containing the computed acoustic data.
                - Preview images of the generated plots (if applicable).
             """)

    if run_btn:
        if uploaded_surf_zip is None:
            st.error("Please upload a ZIP file containing surface data.")
        else:
            try:
                st.toast("🚀 Starting FWH Solver...", icon="🚀")
                # Parse inputs
                obs_loc = parse_observer_input(obs_loc_str)
                ma = ast.literal_eval(ma_str)
                t_src = [i*dt_val for i in range(int(steps_val))]

                # Create temp directories
                with tempfile.TemporaryDirectory() as temp_dir:
                    surf_dir = os.path.join(temp_dir, "surf_data")
                    out_dir = os.path.join(temp_dir, "output")
                    os.makedirs(surf_dir, exist_ok=True)
                    os.makedirs(out_dir, exist_ok=True)

                    prefix = None
                    msg = None

                    with st.status("Processing Simulation...", expanded=True) as status:
                        st.write("📂 Extracting surface data...")
                        # Extract ZIP
                        with zipfile.ZipFile(uploaded_surf_zip, 'r') as zip_ref:
                            safe_extract_zip(zip_ref, surf_dir)

                        st.write("⚙️ Configuring solver...")
                        # Identify prefix
                        # We expect files like prefixAvg.csv, prefix0.csv
                        # Let's find Avg.csv
                        files = os.listdir(surf_dir)
                        avg_files = [f for f in files if f.endswith("Avg.csv")]

                        if not avg_files:
                            # Maybe it's in a subdir?
                            # For now assume flat structure in zip
                            st.error("Could not find *Avg.csv in the uploaded ZIP.")
                            status.update(label="Validation Failed", state="error", expanded=True)
                            prefix = None
                        else:
                            # Take the first one found
                            avg_file = avg_files[0]
                            prefix = avg_file.replace("Avg.csv", "")
                            # Full path prefix
                            full_prefix = os.path.join(surf_dir, prefix)

                            # Output prefix
                            out_prefix = os.path.join(out_dir, "fwh_out")

                            st.write("🚀 Running FWH Solver...")
                            # Run FWH
                            msg = fwh.stationary_serial(full_prefix, out_prefix, obs_loc, t_src, ma, perm_val, write=True, ambient_temperature=temp_val)

                            st.write("📦 Packaging results...")
                            # List generated files
                            out_files = os.listdir(out_dir)
                            # Create a zip of results
                            result_zip_path = os.path.join(temp_dir, "results.zip")
                            with zipfile.ZipFile(result_zip_path, 'w') as res_zip:
                                for f in out_files:
                                    res_zip.write(os.path.join(out_dir, f), arcname=f)

                            status.update(label="Simulation Complete!", state="complete", expanded=False)
                            st.toast("✅ Simulation Complete!", icon="✅")

                    if prefix is not None:
                        st.success(msg)

                        with open(result_zip_path, "rb") as fp:
                            st.download_button(
                                label="Download Results (ZIP)",
                                data=fp,
                                file_name="fwh_results.zip",
                                mime="application/zip",
                                help="Download a ZIP archive containing the computed acoustic data and preview images."
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
                        key="download_sample_spectral",
                        help="Download sample data containing `signal.csv` to test the spectral analysis."
                    )

        if uploaded_sig:
            if not is_file_size_valid(uploaded_sig, MAX_CSV_SIZE_MB):
                st.error(f"File too large. Please upload a CSV file smaller than {MAX_CSV_SIZE_MB}MB.")
                uploaded_sig = None
            else:
                df = pd.read_csv(uploaded_sig)

                with st.expander("Preview Uploaded Data"):
                    st.dataframe(df.head(), use_container_width=True)

                st.caption(f"✅ Loaded **{len(df)}** rows, **{len(df.columns)}** columns.")

                # Smart default selection
                time_candidates = ["time", "t", "seconds", "s"]
                time_idx = get_column_index(df.columns, time_candidates)
                time_col = st.selectbox("Select Time Column", df.columns, index=time_idx, help="Select the column containing time data (must be in seconds).")

                sig_candidates = ["pressure", "p", "signal", "velocity", "u", "amplitude"]
                available_cols = [c for c in df.columns if c != time_col]
                # Recalculate index for the filtered list
                sig_idx = get_column_index(available_cols, sig_candidates)

                if available_cols:
                    sig_col = st.selectbox("Select Signal Column", available_cols, index=sig_idx, help="Select the column containing the measurement data to analyze (e.g., pressure, velocity).")
                else:
                    st.warning("No signal columns available (the file only has 1 column). Please upload a file with at least two columns.")
                    sig_col = None

                method = st.selectbox("Method", ["FFT", "Welch"], help="Choose 'FFT' for standard spectrum or 'Welch' for smoothed periodogram.")

                if method == "Welch":
                    col_w1, col_w2 = st.columns(2)
                    with col_w1:
                        chunks = st.number_input("Chunks", value=4, step=1, min_value=1, max_value=1000, help="Number of segments to split the signal into (higher = smoother but lower frequency resolution).")
                        chunks = min(chunks, 1000)
                    with col_w2:
                        overlap = st.number_input("Overlap (Fraction)", value=0.5, min_value=0.0, max_value=0.99, help="Fraction of overlap between segments (typically 0.5 or 50%).")

    with col2:
        if uploaded_sig and sig_col is not None:
             try:
                time_vals = df[time_col].values
                sig = df[sig_col].values

                # Calculate metrics
                fs = sa.sampling_freq(time_vals)
                nyquist = fs / 2.0

                # Display metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Sampling Rate", f"{fs} Hz", help="Number of samples recorded per second. Determines the maximum resolvable frequency.")
                m2.metric("Nyquist Freq", f"{nyquist} Hz", help="Maximum frequency that can be accurately represented without aliasing (half of the sampling rate).")

                with st.spinner("Computing spectrum..."):
                    fig, ax = plt.subplots()

                    if method == "FFT":
                        freq, df_bin, psd = sa.fft_spectrum(time_vals, sig)
                        ax.loglog(freq, psd)
                        ax.set_title(f"FFT Spectrum: {sig_col}")
                    elif method == "Welch":
                        freq, df_bin, psd = sa.welch_spectrum(time_vals, sig, chunks=chunks, overlap=overlap)
                        ax.loglog(freq, psd)
                        ax.set_title(f"Welch Spectrum: {sig_col}")

                    m3.metric("Freq Resolution", f"{df_bin:.3f} Hz", help="Frequency spacing between points in the spectrum. Finer resolution requires longer time segments.")

                    ax.set_xlabel("Frequency (Hz)")

                    # Heuristic for units
                    if "pressure" in sig_col.lower() or "p" == sig_col.lower():
                        y_unit = "Pa²/Hz"
                    elif "velocity" in sig_col.lower() or "u" in sig_col.lower():
                        y_unit = "(m/s)²/Hz"
                    else:
                        y_unit = "Units²/Hz"

                    ax.set_ylabel(f"PSD ({y_unit})")
                    ax.grid(True, which="both", linestyle='--', alpha=0.7)

                    st.pyplot(fig)

                    # Export results
                    spectrum_df = pd.DataFrame({"Frequency (Hz)": freq, "PSD": psd})
                    csv_data = spectrum_df.to_csv(index=False).encode('utf-8')

                    st.download_button(
                        label="Download Spectrum CSV",
                        data=csv_data,
                        file_name="spectrum_analysis.csv",
                        mime="text/csv",
                        help="Download the calculated Power Spectral Density data."
                    )

             except Exception as e:
                 st.error(f"Error: {e}")
        elif uploaded_sig and sig_col is None:
             st.info("⚠️ Please upload a CSV file with at least two columns to proceed with spectral analysis.")
        else:
             st.info("👋 Upload a CSV file on the left to get started with spectral analysis.")
             st.markdown("""
                **Expected Format:**
                - A CSV file with at least two columns.
                - One column for **Time** (s).
                - One column for **Signal** (Pressure, Velocity, etc.).
             """)
