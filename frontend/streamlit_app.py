"""
SCIAS - Home page.
Run with: streamlit run frontend/streamlit_app.py
(run this from the SCIAS project root so `agents.*` imports resolve correctly)
"""

import sys
import os
import tempfile
from pathlib import Path

# Fix path issues for Railway deployment
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Change working directory to project root for consistent file paths
os.chdir(str(project_root))

# Import modules with error handling
try:
    from auth_helper import check_login
    check_login()
except ImportError as e:
    print(f"⚠️ Auth import error: {e}")
    # Fallback: skip auth if not available
    pass

import streamlit as st

# Handle STT imports with fallback
try:
    from stt_helper import transcribe_wav, speak_text
except ImportError:
    # Dummy functions if stt_helper not available
    def transcribe_wav(*args, **kwargs):
        return "Voice transcription not available"
    def speak_text(*args, **kwargs):
        return None

try:
    from orchestrator import run_query
except ImportError as e:
    st.error(f"❌ Failed to import orchestrator: {e}")
    st.stop()

try:
    from db_helper import save_interaction
except ImportError:
    def save_interaction(*args, **kwargs):
        print("⚠️ DB save skipped - db_helper not available")

try:
    from frontend_utils import get_session_id, language_selector, from_english
except ImportError:
    def get_session_id():
        return "default_session"
    def language_selector(key):
        return st.selectbox("Language", ["en", "ur"], key=key)
    def from_english(text, lang):
        return text

try:
    from ui_theme import apply_theme, render_header, render_agent_badge, render_answer, render_footer, render_logout
except ImportError:
    # Fallback UI functions
    def apply_theme():
        st.set_page_config(page_title="SCIAS - Smart Crop Advisory", layout="wide")
    def render_header(*args, **kwargs):
        st.title("🌾 SCIAS")
    def render_agent_badge(agent):
        st.info(f"🤖 Agent: {agent}")
    def render_answer(text):
        st.markdown(f"**Answer:** {text}")
    def render_footer(session_id, text):
        st.caption(text)
    def render_logout():
        pass

# Page config
st.set_page_config(
    page_title="SCIAS - Smart Crop Advisory",
    page_icon="🌾",
    layout="wide"
)

# Apply theme
try:
    apply_theme()
except Exception as e:
    print(f"⚠️ Theme error: {e}")

try:
    render_logout()
except Exception:
    pass

try:
    render_header("", "SCIAS", "Smart Crop Intelligence Advisory System")
except Exception:
    st.title("🌾 SCIAS")
    st.subheader("Smart Crop Intelligence Advisory System")

# Initialize session state
session_id = get_session_id()

# Language selector
try:
    lang = language_selector("home_lang")
except Exception:
    lang = "en"

EXAMPLE_QUERIES = [
    "Will it rain tomorrow?",
    "What's the weather in Islamabad?",
    "My tomato leaves have brown spots",
]

# Initialize session state variables
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

# Clear box if needed
if st.session_state["clear_box_next_run"]:
    st.session_state["main_query_box"] = ""
    st.session_state["clear_box_next_run"] = False

# Example queries as chips
chip_cols = st.columns(len(EXAMPLE_QUERIES))
for col, example in zip(chip_cols, EXAMPLE_QUERIES):
    if col.button(example, use_container_width=True):
        st.session_state["home_query_to_run"] = example
        st.session_state["main_query_box"] = example
        st.session_state["input_was_voice"] = False

# Input area
text_col, mic_col = st.columns([5, 1])

with mic_col:
    audio_value = st.audio_input("🎙️", label_visibility="collapsed")

# Handle voice input
if audio_value is not None and audio_value.file_id != st.session_state["last_audio_id"]:
    st.session_state["last_audio_id"] = audio_value.file_id
    
    # Use temporary file with proper cleanup
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_value.read())
            tmp_path = tmp_file.name
        
        with st.spinner("Transcribing..."):
            try:
                transcript = transcribe_wav(tmp_path, lang="ur")
                st.session_state["main_query_box"] = transcript
                st.session_state["input_was_voice"] = True
            except Exception as e:
                st.error(f"⚠️ Transcription failed: {e}")
                st.session_state["main_query_box"] = ""
                st.session_state["input_was_voice"] = False
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    except Exception as e:
        st.error(f"⚠️ Audio processing failed: {e}")

# Text input
with text_col:
    query = st.text_input(
        "Ask anything",
        placeholder="گندم کی فصل کو کب پانی دینا چاہیے؟  /  What's the wheat price today?",
        label_visibility="collapsed",
        key="main_query_box",
    )

# Submit button
submitted = st.button("Ask", type="primary", use_container_width=True)

# Process query
final_query = st.session_state["home_query_to_run"] or (query if submitted else None)
st.session_state["home_query_to_run"] = None

if final_query and final_query.strip():
    was_voice_input = st.session_state["input_was_voice"]

    with st.spinner("Consulting the field..."):
        try:
            result = run_query(final_query, session_id=session_id)
            
            # Process result
            if was_voice_input:
                if result["detected_language"] != "ur":
                    display_answer = from_english(result["answer_english"], "ur")
                else:
                    display_answer = result["answer"]
            elif lang != result["detected_language"]:
                display_answer = from_english(result["answer_english"], lang)
            else:
                display_answer = result["answer"]
            
            # Save interaction
            try:
                save_interaction(session_id, result["agent_used"], final_query, display_answer)
            except Exception as e:
                print(f"⚠️ Failed to save interaction: {e}")
            
            # Generate voice response
            audio_out_path = None
            if was_voice_input:
                with st.spinner("Generating voice response..."):
                    try:
                        # Use temp directory for audio
                        audio_out_path = speak_text(display_answer, "temp_output", lang="ur")
                    except Exception as e:
                        print(f"⚠️ TTS failed: {e}")
                        audio_out_path = None
            
            # Store in session state
            st.session_state["last_agent_used"] = result["agent_used"]
            st.session_state["last_display_answer"] = display_answer
            st.session_state["last_english_answer"] = result["answer_english"]
            st.session_state["last_audio_out_path"] = audio_out_path
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            st.session_state["last_display_answer"] = f"Error: {str(e)}"
    
    st.session_state["input_was_voice"] = False
    st.session_state["clear_box_next_run"] = True
    st.session_state["show_english"] = False
    st.rerun()

# Display answer
if st.session_state["last_display_answer"]:
    try:
        render_agent_badge(st.session_state["last_agent_used"])
    except:
        st.info(f"🤖 Agent: {st.session_state['last_agent_used']}")
    
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
    
    try:
        render_answer(shown_text)
    except:
        st.markdown(f"**Answer:** {shown_text}")
    
    # Play audio
    if st.session_state["last_audio_out_path"] and not st.session_state["show_english"]:
        try:
            if os.path.exists(st.session_state["last_audio_out_path"]):
                st.audio(st.session_state["last_audio_out_path"])
        except Exception as e:
            print(f"⚠️ Audio playback failed: {e}")

# Footer
try:
    render_footer(session_id, "Full history in the History page")
except:
    st.caption("🤖 SCIAS - Smart Crop Intelligence Advisory System")