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
