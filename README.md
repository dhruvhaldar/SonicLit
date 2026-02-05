# Dhvani

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/dhruvhaldar/dhvani)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Dhvani** is a lightweight Python library for aeroacoustics and signal processing, designed to serve as a post-processing toolkit for computational fluid dynamics (CFD) solvers.

## Features

*   **Ffowcs-Williams Hawkings (FWH) Solver**:
    *   Predict far-field noise from near-field surface data.
    *   Supports stationary and moving sources/observers.
    *   Supports permeable (porous) and impermeable surfaces.
    *   MPI-parallelized for performance (optional).
*   **Spectral Analysis**:
    *   FFT-based signal processing.
    *   Power Spectral Density (PSD) estimation using Welch's method.
    *   Cross-correlation and coherence analysis.
*   **User Interfaces**:
    *   **Desktop App**: A native GUI using Tkinter.
    *   **Web App**: A browser-based dashboard using Streamlit.

## Installation

It is recommended to install Dhvani in a virtual environment.

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate

# Install package
pip install .
```

To run the web application, ensure `streamlit` is installed (it is included in the build requirements):
```bash
pip install streamlit
```

## Usage

### Graphical User Interfaces (GUI)

Dhvani comes with two GUIs for ease of use.

#### 1. Desktop App
Run the local desktop application:
```bash
python scripts/run_desktop.py
```

#### 2. Web App
Run the web dashboard (accessible via browser):
```bash
./scripts/run_web.sh
# OR
streamlit run src/dhvani/gui/web/app.py
```

See the [GUI User Manual](docs/gui_manual.md) for detailed instructions.

### Library Usage

You can also use Dhvani as a library in your Python scripts:

```python
import dhvani.fwh as fwh
import dhvani.spectral_analysis as sa

# Calculate spectrum
freq, df, psd = sa.fft_spectrum(time_array, pressure_array)
```

## Documentation

*   [GUI User Manual](docs/gui_manual.md): Detailed guide on using the Desktop and Web apps.
*   [Developer Guide](docs/developer_guide.md): Instructions for running tests and contributing.

## License

[MIT License](LICENSE)
