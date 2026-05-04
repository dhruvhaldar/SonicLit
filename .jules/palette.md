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

## 2025-06-25 - Ephemeral Interaction States in Streamlit
**Learning:** In Streamlit, rendering results and dependent interactive elements (like a "Download" button) purely inside an `if st.button('Run'):` block causes a jarring UX failure. The moment the user clicks the rendered "Download" button, Streamlit reruns the script, the 'Run' button evaluates to False, and the results vanish mid-interaction.
**Action:** Always persist successful operation results (like paths, flags, or data) in `st.session_state` and use this persistent state variable to conditionally render follow-up elements, ensuring they remain visible until explicitly cleared or invalidated.

## 2025-06-25 - Graceful Error Handling for Streamlit File Parsing
**Learning:** In Streamlit applications, failing to wrap file parsing operations (like `pd.read_csv`) in `try...except` blocks causes malformed or invalid uploads to crash the application, displaying a full, intimidating stack trace directly to the end user.
**Action:** Always wrap user-provided file parsing operations in `try...except` blocks. Display user-friendly, actionable error messages using `st.error` and ensure downstream dependent variables (like `df` or selected columns) are safely reset or bypassed to prevent cascading errors.
## 2026-05-04 - Tkinter Loading State Cursor Feedback
**Learning:** During long-running background thread operations in Tkinter desktop GUIs, simply disabling buttons is sometimes insufficient feedback if the application appears frozen to the user.
**Action:** Always provide explicit, immediate visual feedback for long-running operations by changing the root cursor to a waiting state (e.g., `self.root.config(cursor="watch")`) before launching the thread, and strictly ensure it is reset back to normal (`self.root.config(cursor="")`) within a `finally` block using `self.root.after`.
