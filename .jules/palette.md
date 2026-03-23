## 2025-06-25 - Duplicate Widget IDs in Streamlit Tabs
**Learning:** Streamlit evaluates the entire script globally. If multiple buttons with the same text label (e.g., "Load Built-in Sample Data") exist, even if they are placed inside separate `st.tabs` blocks, Streamlit will throw a `DuplicateWidgetID` error unless explicitly provided with a unique `key`.
**Action:** Always assign explicit, unique `key` parameters (e.g., `key="btn_load_fwh"`) to all Streamlit widgets, especially when reusing common action labels like "Clear", "Load", or "Submit" across different sections or tabs of the application.

## 2025-06-25 - Auto-populating Data Columns in Tkinter
**Learning:** Relying on users to manually type CSV column names in `ttk.Entry` widgets frequently leads to syntax/capitalization errors, resulting in runtime parsing exceptions (`ValueError: Columns not found`).
**Action:** When a user selects a data file via a file browser, proactively read the file header (`pd.read_csv(..., nrows=0)`) and dynamically populate `ttk.Combobox` options with the actual available column names. This transforms an error-prone text input into a robust, guided selection.
