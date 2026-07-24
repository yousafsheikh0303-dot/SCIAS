import streamlit as st
from agents.irrigation_agent import irrigation_agent
from db_helper import save_interaction
from frontend_utils import language_selector, to_english, from_english, get_session_id
from ui_theme import apply_theme, render_header, render_answer, render_footer, render_logout
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Irrigation Advisory", layout="wide")
apply_theme()
render_logout()
render_header("", "Irrigation Advisory")

session_id = get_session_id()

col_lang, col_loc = st.columns([1, 1])
with col_lang:
    lang = language_selector("irrigation_lang")
with col_loc:
    location = st.text_input("Location", value="Lahore")

with st.form("irrigation_form", clear_on_submit=True):
    query = st.text_input(
        "Query",
        placeholder="گندم کی فصل کو کب پانی دینا چاہیے؟  /  wheat mid stage watering",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Get Irrigation Advice", type="primary", use_container_width=True)

if submitted and query.strip():
    with st.spinner("Calculating..."):
        english_query = to_english(query, lang)
        result = irrigation_agent(english_query, location=location)
        final_answer = from_english(result["answer"], lang)

    render_answer(final_answer)

    with st.expander("Show English version"):
        st.write(result["answer"])

    save_interaction(session_id, "irrigation", query, final_answer)

render_footer(session_id)