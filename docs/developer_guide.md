# Developer Guide

## Project Structure

```
dhvani/
├── src/
│   └── dhvani/
│       ├── fwh.py                 # FWH Solver core logic
│       ├── spectral_analysis.py   # Signal processing library
│       └── gui/
│           ├── desktop/           # Tkinter application
│           └── web/               # Streamlit application
├── tests/
│   ├── acoustics/                 # Unit tests for core libraries
│   ├── generate_dummy_data.py     # Utility to create test data
│   ├── test_gui_e2e.py            # End-to-End tests for Desktop GUI
│   └── test_web_app.py            # Tests for Streamlit Web App
├── scripts/
│   ├── run_desktop.py             # Entry point for Desktop App
│   └── run_web.sh                 # Entry point for Web App
└── docs/                          # Documentation
```

## Running Tests

### Unit Tests
Run the standard unit tests using `pytest` or `python`:

```bash
python tests/acoustics/test_spectral_analysis.py
```

### End-to-End (E2E) Tests
The GUI tests require a display environment.

**On a desktop with a display:**
```bash
python tests/test_gui_e2e.py
```

**On a headless server (CI/CD):**
Use `xvfb` to simulate a display:
```bash
xvfb-run -a python tests/test_gui_e2e.py
```

**Web App Tests:**
```bash
python tests/test_web_app.py
```

## Generating Dummy Data
To generate sample CSV files for testing the FWH solver or Spectral Analysis manually:

```bash
python tests/generate_dummy_data.py
```
This will create:
*   `tests/data/surf_*.csv`: Dummy surface data for FWH.
*   `tests/data/signal.csv`: Dummy signal for spectral analysis.

## Dependency Management
The project uses `pip` and `requirements.txt` / `pyproject.toml`.
To install dependencies for development:

```bash
pip install -e .
pip install streamlit # For the web app
```
