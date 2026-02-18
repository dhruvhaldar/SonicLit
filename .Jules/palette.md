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
