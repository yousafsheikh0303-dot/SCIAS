"""
Shared UI/translation helpers used across every SCIAS Streamlit page.

Keeps the language-selector + translate-in/translate-out pattern in one
place instead of repeating it on every page.
"""

import uuid
import streamlit as st
from agents.translation_agent import detect_and_translate_to_english, translate_from_english
import streamlit as st
from stt_helper import get_model

@st.cache_resource
def load_vosk_model():
    return get_model()
LANG_OPTIONS = {
    "English": "en",
    "Urdu (اردو)": "ur",
    "Punjabi (ਪੰਜਾਬੀ)": "pa",
}


def get_session_id() -> str:
    """One stable session_id per browser session, for grouping history."""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    return st.session_state["session_id"]


def language_selector(key: str) -> str:
    """Renders a language dropdown and returns the ISO code (en/ur/pa)."""
    choice = st.selectbox("Language / زبان / ਭਾਸ਼ਾ", list(LANG_OPTIONS.keys()), key=key)
    return LANG_OPTIONS[choice]


def to_english(text: str, lang_code: str) -> str:
    """Translates farmer input to English if needed; passes through if already English."""
    if lang_code == "en" or not text.strip():
        return text
    result = detect_and_translate_to_english(text)
    return result["english_text"]


def from_english(text: str, lang_code: str) -> str:
    """Translates the English agent answer back into the farmer's chosen language."""
    return translate_from_english(text, lang_code)
