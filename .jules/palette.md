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

## 2026-05-04 - Streamlit Selectbox vs Radio for Binary Choices
**Learning:** Using an `st.selectbox` for a simple binary choice (e.g., "FFT" vs "Welch") hides the available options and forces the user to make two clicks (open dropdown, select item).
**Action:** Always prefer a horizontal `st.radio` (`horizontal=True`) over a selectbox when there are only two mutually exclusive options, making the choices immediately visible and reducing interaction cost to a single click.

## 2026-05-04 - Formatting Large Numbers in Streamlit Metrics
**Learning:** Displaying raw large numbers (e.g., 44100) in `st.metric` components makes them difficult to scan and comprehend quickly, increasing cognitive load.
**Action:** Always format large numerical outputs, such as frequencies or sample rates, with thousands separators (e.g., `f"{value:,.0f}"` or `f"{value:,.1f}"`) to improve scannability and professional polish.

## 2026-05-04 - Exposing Abstract Calculations in Streamlit
**Learning:** Abstract inputs (like "Ambient Temperature") that drive critical physics calculations (like "Speed of Sound") leave users guessing about the exact values being used under the hood until the simulation runs.
**Action:** Surface derived calculations instantly in the UI. When a user changes an abstract input, calculate the dependent physical property and display it immediately below the input using an `st.caption`. This provides instant, helpful feedback and builds trust in the simulation.

## 2026-05-04 - Playwright Selectors for Streamlit Widgets
**Learning:** Streamlit does not map Python widget `key` arguments to DOM element attributes (like `key="btn_load"`). Attempting to use CSS locators like `page.locator("button[key='btn_load']")` will silently fail and timeout in Playwright.
**Action:** When testing Streamlit UIs with Playwright, always locate interactive elements using user-facing attributes like role and exact text (e.g., `page.get_by_role("button", name="📦 Load Built-in Sample Data")`). If elements are duplicated across tabs, use `.nth()` or scope the search to the active tab container.

## 2024-06-03 - Form Layout Density Improvement
**Learning:** In data-dense Streamlit applications with many scalar configuration inputs (e.g., FWH Solvers or Spectral Analysis parameter forms), stacking all inputs vertically creates excessive scrolling and reduces cognitive parsing. Explicitly grouping related parameters (like Time Step/Number of Steps, or Time Column/Signal Column selection) into horizontal `st.columns` blocks significantly improves the form's density and usability.
**Action:** When working on Streamlit forms, evaluate if sequential scalar inputs or selectboxes share a logical relationship (e.g., simulation temporal parameters or axis data selection). If so, wrap them in `st.columns` to reduce vertical height and clearly convey their relationship to the user.
## 2026-06-12 - Usable Float Steps in Streamlit Number Inputs
**Learning:** In Streamlit, `st.number_input` widgets for floating-point values implicitly default to a step size of `0.01`. For inputs representing larger physical quantities (like Ambient Temperature around 298.0 K), this default makes the widget's native `+` and `-` spin buttons practically useless, as adjusting the value by 1 degree requires 100 clicks.
**Action:** Always evaluate the physical domain of a floating-point `st.number_input`. Explicitly define a contextually meaningful `step` parameter (e.g., `step=1.0` or `step=0.1`) to ensure the increment/decrement interactions are intuitive and helpful rather than tedious.
