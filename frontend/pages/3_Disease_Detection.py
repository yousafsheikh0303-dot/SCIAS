import os
import tempfile
import streamlit as st
from agents.disease_agent import disease_agent
from db_helper import save_interaction
from frontend_utils import language_selector, to_english, from_english, get_session_id
from ui_theme import apply_theme, render_header, render_answer, render_footer, PALETTE
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Disease Detection", page_icon="\U0001F343", layout="wide")
apply_theme()
render_header("", "Disease Detection", "Photo gives a confirmed diagnosis; text alone gives a best-guess match")

session_id = get_session_id()
lang = language_selector("disease_lang")

with st.form("disease_form", clear_on_submit=True):
    uploaded_image = st.file_uploader("Leaf photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    query = st.text_input(
        "Symptoms",
        placeholder="e.g. brown spots on tomato leaves",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Diagnose", type="primary", use_container_width=True)

if uploaded_image and not submitted:
    st.image(uploaded_image, caption="Uploaded image", width=280)

if submitted:
    image_path = None
    tmp_file = None

    if uploaded_image is not None:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_image.name)[1])
        tmp_file.write(uploaded_image.read())
        tmp_file.close()
        image_path = tmp_file.name

    if not image_path and not query.strip():
        st.warning("Please upload a photo or describe the symptoms.")
    else:
        with st.spinner("Analyzing..."):
            english_query = to_english(query, lang) if query.strip() else ""
            result = disease_agent(english_query, image_path=image_path)
            final_answer = from_english(result["answer"], lang)

        confidence_note = (
            "Confirmed diagnosis from photo" if result.get("diagnosis_type") == "confirmed"
            else "Best-guess match (not a confirmed diagnosis)"
        )
        st.markdown(
            f'<span class="scias-badge" style="background:{PALETTE["bg_soft"]};'
            f'color:{PALETTE["green_deep"]};border:1px solid {PALETTE["border"]}">{confidence_note}</span>',
            unsafe_allow_html=True,
        )
        render_answer(final_answer)

        with st.expander("Show English version"):
            st.write(result["answer"])

        save_interaction(session_id, "disease", query or "[image uploaded]", final_answer)

        if tmp_file:
            os.unlink(image_path)

render_footer(session_id)