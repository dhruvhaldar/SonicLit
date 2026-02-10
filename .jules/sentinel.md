## 2026-02-10 - DoS via ast.literal_eval in Streamlit
**Vulnerability:** Input fields in Streamlit web app (`obs_loc_str` and `ma_str`) were parsed using `ast.literal_eval` without length limits. This allowed attackers to send massive strings (e.g., millions of characters), causing high CPU usage and potential Denial of Service (DoS) during parsing.
**Learning:** `ast.literal_eval` is safe from code execution but not from resource exhaustion. Deeply nested structures or massive literals can crash the process or hang it.
**Prevention:** Always enforce a maximum length limit on input strings before passing them to parsing functions like `ast.literal_eval` or `json.loads`. For Streamlit, explicit length checks are necessary as `st.text_input` doesn't enforce backend limits automatically.
