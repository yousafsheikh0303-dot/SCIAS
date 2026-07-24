import streamlit as st
from agents.weather_agent import weather_agent
from db_helper import save_interaction
from frontend_utils import language_selector, to_english, from_english, get_session_id
from ui_theme import apply_theme, render_header, render_answer, render_footer
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Weather Advisory", page_icon="\u2601\uFE0F", layout="wide")
apply_theme()
render_header("", "Weather Advisory")

session_id = get_session_id()
lang = language_selector("weather_lang")

EXAMPLE_QUERIES = [
    "Will it rain tomorrow?",
    "Is it safe to spray pesticide today?",
    "Any frost warning this week?",
    "Weather in Multan today",
]

if "weather_query_to_run" not in st.session_state:
    st.session_state["weather_query_to_run"] = None

chip_cols = st.columns(len(EXAMPLE_QUERIES))
for col, example in zip(chip_cols, EXAMPLE_QUERIES):
    if col.button(example, use_container_width=True, key=f"chip_{example}"):
        st.session_state["weather_query_to_run"] = example

with st.form("weather_form", clear_on_submit=True):
    query = st.text_input(
        "Query",
        placeholder="Will it rain tomorrow?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Check Weather", type="primary", use_container_width=True)

final_query = st.session_state["weather_query_to_run"] or (query if submitted else None)
st.session_state["weather_query_to_run"] = None

if final_query and final_query.strip():
    with st.spinner("Checking forecast..."):
        english_query = to_english(final_query, lang)
        result = weather_agent(english_query)
        final_answer = from_english(result["answer"], lang)

    render_answer(final_answer)

    with st.expander("Show English version"):
        st.write(result["answer"])

    save_interaction(session_id, "weather", final_query, final_answer)

render_footer(session_id)