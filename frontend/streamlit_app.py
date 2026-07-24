"""
SCIAS - Home page.

Run with: streamlit run frontend\\streamlit_app.py
(run this from the SCIAS project root so `agents.*` imports resolve correctly)
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from auth_helper import check_login
check_login()

import streamlit as st
from stt_helper import transcribe_wav, speak_text
from orchestrator import run_query
from db_helper import save_interaction
from frontend_utils import get_session_id, language_selector, from_english
from ui_theme import apply_theme, render_header, render_agent_badge, render_answer, render_footer, render_logout

st.set_page_config(page_title="SCIAS - Smart Crop Advisory", layout="wide")
apply_theme()
render_logout()

render_header("", "SCIAS", "Smart Crop Intelligence Advisory System")

session_id = get_session_id()
lang = language_selector("home_lang")

EXAMPLE_QUERIES = [
    "Will it rain tomorrow?",
    "What's the weather in Islamabad?",
    "My tomato leaves have brown spots",
]

if "home_query_to_run" not in st.session_state:
    st.session_state["home_query_to_run"] = None
if "main_query_box" not in st.session_state:
    st.session_state["main_query_box"] = ""
if "last_audio_id" not in st.session_state:
    st.session_state["last_audio_id"] = None
if "input_was_voice" not in st.session_state:
    st.session_state["input_was_voice"] = False
if "clear_box_next_run" not in st.session_state:
    st.session_state["clear_box_next_run"] = False
if "last_agent_used" not in st.session_state:
    st.session_state["last_agent_used"] = None
if "last_display_answer" not in st.session_state:
    st.session_state["last_display_answer"] = None
if "last_english_answer" not in st.session_state:
    st.session_state["last_english_answer"] = None
if "last_audio_out_path" not in st.session_state:
    st.session_state["last_audio_out_path"] = None
if "show_english" not in st.session_state:
    st.session_state["show_english"] = False

if st.session_state["clear_box_next_run"]:
    st.session_state["main_query_box"] = ""
    st.session_state["clear_box_next_run"] = False

chip_cols = st.columns(len(EXAMPLE_QUERIES))
for col, example in zip(chip_cols, EXAMPLE_QUERIES):
    if col.button(example, use_container_width=True):
        st.session_state["home_query_to_run"] = example
        st.session_state["main_query_box"] = example
        st.session_state["input_was_voice"] = False

text_col, mic_col = st.columns([5, 1])

with mic_col:
    audio_value = st.audio_input("🎙️", label_visibility="collapsed")

if audio_value is not None and audio_value.file_id != st.session_state["last_audio_id"]:
    st.session_state["last_audio_id"] = audio_value.file_id
    with open("temp_input.wav", "wb") as f:
        f.write(audio_value.read())
    with st.spinner("Transcribing..."):
        # Voice input is always treated as Urdu -- both for the STT engine
        # itself (so Google recognizes it with the ur-PK model, not
        # whatever the display-language dropdown happens to be set to)
        # and for what shows up in the input box.
        transcript = transcribe_wav("temp_input.wav", lang="ur")
    st.session_state["main_query_box"] = transcript
    st.session_state["input_was_voice"] = True

with text_col:
    query = st.text_input(
        "Ask anything",
        placeholder="گندم کی فصل کو کب پانی دینا چاہیے؟  /  What's the wheat price today?",
        label_visibility="collapsed",
        key="main_query_box",
    )

submitted = st.button("Ask", type="primary", use_container_width=True)

final_query = st.session_state["home_query_to_run"] or (query if submitted else None)
st.session_state["home_query_to_run"] = None

if final_query and final_query.strip():
    was_voice_input = st.session_state["input_was_voice"]

    with st.spinner("Consulting the field..."):
        result = run_query(final_query, session_id=session_id)

        if was_voice_input:
            # Voice queries always answer in Urdu (text + speech), regardless
            # of the dropdown or what language got auto-detected, so voice
            # stays fully consistent end-to-end.
            if result["detected_language"] != "ur":
                display_answer = from_english(result["answer_english"], "ur")
            else:
                display_answer = result["answer"]
        elif lang != result["detected_language"]:
            display_answer = from_english(result["answer_english"], lang)
        else:
            display_answer = result["answer"]

    save_interaction(session_id, result["agent_used"], final_query, display_answer)

    audio_out_path = None
    if was_voice_input:
        with st.spinner("Generating voice response..."):
            audio_out_path = speak_text(display_answer, "temp_output", lang="ur")

    # Persist so it survives the rerun below.
    st.session_state["last_agent_used"] = result["agent_used"]
    st.session_state["last_display_answer"] = display_answer
    st.session_state["last_english_answer"] = result["answer_english"]
    st.session_state["last_audio_out_path"] = audio_out_path

    st.session_state["input_was_voice"] = False
    st.session_state["clear_box_next_run"] = True
    st.session_state["show_english"] = False
    st.rerun()

# Render the most recent answer, if any — lives outside the `if` block above
# so it keeps showing after the rerun that clears the input box.
if st.session_state["last_display_answer"]:
    render_agent_badge(st.session_state["last_agent_used"])

    answer_col, toggle_col = st.columns([5, 1])
    with toggle_col:
        toggle_label = "Show Urdu/Native" if st.session_state["show_english"] else "Show in English"
        if st.button(toggle_label, use_container_width=True):
            st.session_state["show_english"] = not st.session_state["show_english"]
            st.rerun()

    shown_text = (
        st.session_state["last_english_answer"]
        if st.session_state["show_english"]
        else st.session_state["last_display_answer"]
    )
    render_answer(shown_text)

    # Only play the Urdu audio when showing the native-language text --
    # the English toggle is text-only, no separate English audio generated.
    if st.session_state["last_audio_out_path"] and not st.session_state["show_english"]:
        st.audio(st.session_state["last_audio_out_path"])

render_footer(session_id, "Full history in the History page")