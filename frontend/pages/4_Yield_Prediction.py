import streamlit as st
from agents.yield_agent import yield_agent, get_yield_options
from db_helper import save_interaction
from frontend_utils import language_selector, from_english, get_session_id
from ui_theme import apply_theme, render_header, render_answer, render_footer
from auth_helper import check_login
check_login()
st.set_page_config(page_title="Yield Prediction", page_icon="\U0001F4C8", layout="wide")
apply_theme()
render_header("", "Yield Prediction", "XGBoost estimate, tons/hectare")

session_id = get_session_id()
lang = language_selector("yield_lang")

options = get_yield_options()

# Not clear_on_submit: these are configuration fields a farmer will tweak
# incrementally (change one value, re-predict), not a single message.
with st.form("yield_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop", options["Crop"])
        region = st.selectbox("Region", options["Region"])
        soil_type = st.selectbox("Soil Type", options["Soil_Type"])
        weather_condition = st.selectbox("Weather Condition", options["Weather_Condition"])

    with col2:
        rainfall_mm = st.number_input("Rainfall (mm)", min_value=0.0, value=500.0, step=10.0)
        temperature_c = st.number_input("Temperature (\u00b0C)", min_value=-10.0, value=28.0, step=0.5)
        days_to_harvest = st.number_input("Days to Harvest", min_value=1, value=120, step=1)
        fertilizer_used = st.checkbox("Fertilizer Used", value=True)
        irrigation_used = st.checkbox("Irrigation Used", value=True)

    submitted = st.form_submit_button("Predict Yield", type="primary", use_container_width=True)

if submitted:
    overrides = {
        "Crop": crop,
        "Region": region,
        "Soil_Type": soil_type,
        "Weather_Condition": weather_condition,
        "Rainfall_mm": rainfall_mm,
        "Temperature_Celsius": temperature_c,
        "Days_to_Harvest": days_to_harvest,
        "Fertilizer_Used": int(fertilizer_used),
        "Irrigation_Used": int(irrigation_used),
    }

    with st.spinner("Predicting..."):
        result = yield_agent(f"yield prediction for {crop}", **overrides)
        final_answer = from_english(result["answer"], lang)

    render_answer(final_answer)

    with st.expander("Show English version"):
        st.write(result["answer"])

    save_interaction(session_id, "yield", f"Yield form: {overrides}", final_answer)

render_footer(session_id)