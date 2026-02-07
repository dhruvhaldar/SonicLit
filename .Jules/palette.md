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
