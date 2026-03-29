## 2025-06-25 - Duplicate Widget IDs in Streamlit Tabs
**Learning:** Streamlit evaluates the entire script globally. If multiple buttons with the same text label (e.g., "Load Built-in Sample Data") exist, even if they are placed inside separate `st.tabs` blocks, Streamlit will throw a `DuplicateWidgetID` error unless explicitly provided with a unique `key`.
**Action:** Always assign explicit, unique `key` parameters (e.g., `key="btn_load_fwh"`) to all Streamlit widgets, especially when reusing common action labels like "Clear", "Load", or "Submit" across different sections or tabs of the application.

## 2025-06-25 - Auto-populating Data Columns in Tkinter
**Learning:** Relying on users to manually type CSV column names in `ttk.Entry` widgets frequently leads to syntax/capitalization errors, resulting in runtime parsing exceptions (`ValueError: Columns not found`).
**Action:** When a user selects a data file via a file browser, proactively read the file header (`pd.read_csv(..., nrows=0)`) and dynamically populate `ttk.Combobox` options with the actual available column names. This transforms an error-prone text input into a robust, guided selection.

## 2025-06-25 - Emoji Icons for Streamlit Buttons
**Learning:** Adding string emojis to Streamlit `st.button` and `st.download_button` via the `icon` parameter significantly improves visual parsing and cognitive processing for primary action elements without requiring any custom CSS or additional dependencies.
**Action:** Whenever introducing primary interactive buttons or download actions in Streamlit, assign a relevant emoji or standard icon to the `icon` parameter to enhance visual hierarchy and affordance.

## 2025-06-25 - Explicit Inner Labels for Multi-Component Widgets in Tkinter
**Learning:** When encapsulating multiple related scalar inputs (like vector components X, Y, Z) into a single `ttk.Frame`, relying solely on the parent frame's label (e.g., "Observer Location (Ox, Oy, Oz)") causes high cognitive load and formatting errors, as users must mentally map the order of inputs to the blank entry boxes.
**Action:** Always provide explicit, individual inner labels (e.g., `ttk.Label(frame, text="X:")`) immediately preceding each `ttk.Entry` field within the nested grid layout to drastically improve clarity and prevent data entry mistakes.
