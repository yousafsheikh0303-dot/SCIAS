import streamlit as st
from agents.rag_agents import rag_query
from db_helper import save_interaction
from frontend_utils import language_selector, to_english, from_english, get_session_id
from ui_theme import apply_theme, render_header, render_answer, render_footer
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Knowledge Base", page_icon="\U0001F4D6", layout="wide")
apply_theme()
render_header("", "Farming Knowledge Base")

session_id = get_session_id()
lang = language_selector("knowledge_lang")

with st.form("knowledge_form", clear_on_submit=True):
    query = st.text_input(
        "Query",
        placeholder="What is the recommended seed rate for late-sown wheat?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Ask", type="primary", use_container_width=True)

if submitted and query.strip():
    with st.spinner("Searching knowledge base..."):
        english_query = to_english(query, lang)
        result = rag_query(english_query)
        final_answer = from_english(result["answer"], lang)

    render_answer(final_answer)

    with st.expander("Show English version"):
        st.write(result["answer"])

    save_interaction(session_id, "knowledge_rag", query, final_answer)

render_footer(session_id)