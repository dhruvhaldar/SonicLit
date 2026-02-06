# Palette's Journal

## 2025-02-18 - [Initial Entry]
**Learning:** UX improvements should be small, impactful, and accessible.
**Action:** Always check for empty states, help text, and accessibility labels.

## 2025-02-18 - Empty States in Analysis Tools
**Learning:** Users often don't know why a result area is blank in analysis tools like Streamlit.
**Action:** Implement conditional empty states that guide the user to the input controls.

## 2025-02-18 - Streamlit Layout Consistency
**Learning:** Content generated outside of `st.column` context breaks the grid layout, appearing at the bottom.
**Action:** Always wrap result generation inside `with container:` or `with col:` to maintain visual hierarchy.
