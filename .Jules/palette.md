# Palette's Journal

## 2025-02-18 - [Initial Entry]
**Learning:** UX improvements should be small, impactful, and accessible.
**Action:** Always check for empty states, help text, and accessibility labels.

## 2025-02-18 - Empty States in Analysis Tools
**Learning:** Users often don't know why a result area is blank in analysis tools like Streamlit.
**Action:** Implement conditional empty states that guide the user to the input controls.

## 2026-02-07 - Contextual Help for Technical Inputs
**Learning:** Even domain experts benefit from reminders about units and formats (e.g., "seconds", "Kelvin"). Adding tooltips reduces the need to consult external documentation.
**Action:** Always populate the `help` parameter for `st.number_input` and `st.text_input` fields involving physical quantities.

## 2026-02-07 - Real-Time Python Literal Validation
**Learning:** Scientific apps often require complex inputs like lists or vectors. Validating these inputs in real-time using `ast.literal_eval` prevents runtime crashes and provides immediate feedback.
**Action:** Use try/except blocks with `ast.literal_eval` for `st.text_input` fields accepting Python literals, and disable action buttons if validation fails.

## 2026-02-18 - Providing Sample Data
**Learning:** Complex input requirements (e.g., multi-file ZIPs) create friction. Providing downloadable sample data directly in the UI significantly aids onboarding.
**Action:** Use `st.download_button` inside an `st.expander` to offer sample files for complex inputs.

## 2025-02-18 - Immediate File Validation
**Learning:** Users can upload invalid archives (e.g. ZIPs without required files) and only discover the error after a long calculation fails. Immediate validation of file structure upon upload provides critical feedback and prevents wasted time.
**Action:** Implement `validate_zip_contents` immediately after `st.file_uploader` to check for required files (e.g., `Avg.csv`) and use `st.success`/`st.warning` for instant feedback. Crucially, always `seek(0)` the file pointer after validation to ensure subsequent processing works.

## 2026-02-12 - AppTest Limitations for File Uploads
**Learning:** Testing Streamlit file upload interactions with `AppTest` is limited; Playwright scripts verifying empty states and static text are a reliable alternative for ensuring UX copy (like detailed format instructions) is present.
**Action:** When enhancing Streamlit forms involving file uploads, prioritize clear empty states and use Playwright for verification if AppTest coverage is insufficient.

## 2026-02-14 - Derived Value Indicators
**Learning:** Users often perform mental math to verify inputs (e.g., Total Time = dt * steps). Explicitly displaying these derived values reduces cognitive load and confirms user intent.
**Action:** When multiple inputs combine to form a critical parameter, add a calculated display (caption or metric) immediately adjacent to the inputs.

## 2026-02-18 - Multi-Step Process Feedback
**Learning:** For long-running processes involving multiple stages (extract, configure, run, package), a single `st.spinner` is opaque. Using `st.status` provides transparency and reassures the user that progress is being made.
**Action:** Replace single-step spinners with `st.status` containers for complex workflows, providing granular updates at each stage.

## 2026-02-18 - Transient Feedback for Process Boundaries
**Learning:** For processes that may take time or occur while the user is looking elsewhere, a persistent status message might be missed or clutter the UI. Transient toasts provide clear start/end signals without requiring dismissal.
**Action:** Use `st.toast` with distinct icons (🚀, ✅) to mark the initiation and completion of significant workflows, complementing the detailed `st.status`.

## 2026-02-18 - Replacing Technical Inputs with Visual Controls
**Learning:** For inputs expecting Python literals (like vectors `[x,y,z]`), replacing text inputs with structured number inputs (e.g., columns of `st.number_input`) dramatically reduces syntax errors and improves accessibility, while maintaining backend compatibility via string construction.
**Action:** Replace `st.text_input` for vector/list data with `st.columns` + `st.number_input` whenever the structure is fixed (e.g., 3D vectors), and offer a toggle for advanced/variable-length inputs.

## 2026-02-21 - Improving Complex List Inputs
**Learning:** For inputs expecting long lists (e.g., coordinate lists), `st.text_input` is too restrictive and error-prone. `st.text_area` provides a better editing experience, and clear examples are critical for complex formats.
**Action:** Replace `st.text_input` with `st.text_area` for multi-line data, and always accompany complex format requirements with `st.caption` showing a concrete example. Also, ensure labels are descriptive (e.g., "Observer X" vs "X") for screen reader context.

## 2025-05-15 - Explicit Units in Input Labels
**Learning:** In scientific applications, ambiguity about units (e.g., meters vs feet) is a critical usability issue. Relying solely on tooltips or documentation is insufficient as users scan forms quickly.
**Action:** Always include units directly in the label of input fields (e.g., "Observer X (m)", "Time Step (s)") to provide immediate, unambiguous context.

## 2026-03-01 - Data Preview for Bulk Text Inputs
**Learning:** For bulk data entry (like coordinate lists), users lack confidence that their custom format (CSV/Python list) was parsed correctly before hitting run. A simple summary (e.g., "2 observers") is good, but a visual table preview guarantees understanding.
**Action:** Implement a data preview using `st.dataframe` inside an `st.expander` for bulk text inputs after parsing, allowing users to verify the exact values and column mappings before execution.

## 2026-03-03 - Contextual Help for Technical Metrics
**Learning:** While input tooltips help users configure settings, derived technical metrics (like "Nyquist Freq" or "Freq Resolution") often leave users guessing about their exact implications on the final results. Adding explicit `help` text to `st.metric` widgets bridges the gap between raw numbers and domain understanding.
**Action:** Always populate the `help` parameter for `st.metric` displays in technical dashboards to explain both the definition and the practical impact of the metric.

## 2026-03-07 - Conditional Empty States for Dynamic Views
**Learning:** When a UI component relies on dynamic data (like available columns from a CSV file), failing to handle invalid conditions (e.g., uploading a 1-column CSV when 2 are needed) can result in completely blank UI areas without feedback.
**Action:** Implement robust conditional checks (`elif`) to render explicit empty states (`st.info` or `st.warning`) for partially invalid data, preventing "dead" UI zones.

## 2026-03-08 - Use Sliders for Fractional Parameters
**Learning:** Number inputs are un-intuitive for fractional bounded ranges (like 0.0 - 0.99 for "Overlap"). Replacing them with `st.slider` provides better tactile feedback and encourages users to explore parameter impacts.
**Action:** Use `st.slider` with appropriate `step` values for any inputs constrained between 0 and 1.

## 2026-03-08 - Contextual Download Filenames
**Learning:** Statically naming exported CSVs (e.g. `spectrum_analysis.csv`) creates friction when users perform multiple analyses in a single session.
**Action:** Always inject dynamic parameters into export filenames (e.g. `spectrum_{method}_{signal}.csv`) to provide immediate context and prevent file overwrites on the user's local machine.