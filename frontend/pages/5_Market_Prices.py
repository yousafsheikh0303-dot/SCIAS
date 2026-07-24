import streamlit as st
from agents.market_agent import market_agent
from db_helper import save_interaction
from frontend_utils import language_selector, to_english, from_english, get_session_id
from ui_theme import apply_theme, render_header, render_answer, render_footer
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Market Prices", page_icon="\U0001F3F7\uFE0F", layout="wide")
apply_theme()
render_header("", "Mandi Price Advisory")

session_id = get_session_id()
lang = language_selector("market_lang")

with st.form("market_form", clear_on_submit=True):
    query = st.text_input(
        "Query",
        placeholder="What's the current price of wheat in the mandi?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Check Prices", type="primary", use_container_width=True)

if submitted and query.strip():
    with st.spinner("Fetching prices..."):
        english_query = to_english(query, lang)
        result = market_agent(english_query)
        final_answer = from_english(result["answer"], lang)

    render_answer(final_answer)

    with st.expander("Show English version"):
        st.write(result["answer"])

    save_interaction(session_id, "market", query, final_answer)

render_footer(session_id)