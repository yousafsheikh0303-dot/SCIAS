import streamlit as st
from db_helper import load_history, load_session_ids
from ui_theme import apply_theme, render_header, render_agent_badge, PALETTE
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Conversation History", page_icon="\U0001F4DC", layout="wide")
apply_theme()
render_header("", "Conversation History")

session_ids = load_session_ids()
filter_choice = st.selectbox(
    "Filter by session",
    ["All sessions"] + session_ids,
    label_visibility="collapsed",
)

rows = load_history(limit=200)

if not rows:
    st.markdown(
        f'<div class="scias-answer">No history yet. Ask something on one of the agent pages first.</div>',
        unsafe_allow_html=True,
    )
else:
    for session_id, role, message, agent_used, rowid in rows:
        if filter_choice != "All sessions" and session_id != filter_choice:
            continue
        icon = "\U0001F9D1\u200D\U0001F33E" if role == "user" else "\U0001F916"
        with st.chat_message("user" if role == "user" else "assistant"):
            if role != "user" and agent_used:
                render_agent_badge(agent_used)
            st.write(message)