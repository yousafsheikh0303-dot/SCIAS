import math
import re
from agents.weather_agent import get_forecast, DEFAULT_LOCATION

# Kc (crop coefficient) values per FAO-56 "Crop Evapotranspiration" reference
# tables: {initial, mid, late/end}. These are standard reference values --
# actual local extension recommendations can vary by variety and region, so
# treat these as a solid general baseline rather than an exact local figure.
CROP_KC = {
    "wheat": {"initial": 0.4, "mid": 1.15, "late": 0.4},
    "cotton": {"initial": 0.35, "mid": 1.2, "late": 0.6},
    "rice": {"initial": 1.05, "mid": 1.2, "late": 0.9},
    "sugarcane": {"initial": 0.4, "mid": 1.25, "late": 0.75},
    "maize": {"initial": 0.3, "mid": 1.2, "late": 0.6},
    "potato": {"initial": 0.5, "mid": 1.15, "late": 0.75},
    "chickpea": {"initial": 0.4, "mid": 1.0, "late": 0.35},
    "sunflower": {"initial": 0.35, "mid": 1.15, "late": 0.35},
    "onion": {"initial": 0.7, "mid": 1.05, "late": 0.75},
    "tomato": {"initial": 0.6, "mid": 1.15, "late": 0.8},
    "barley": {"initial": 0.3, "mid": 1.15, "late": 0.25},
    "mustard": {"initial": 0.35, "mid": 1.1, "late": 0.35},
    "groundnut": {"initial": 0.4, "mid": 1.15, "late": 0.6},
    "soybean": {"initial": 0.4, "mid": 1.15, "late": 0.5},
    "sorghum": {"initial": 0.3, "mid": 1.05, "late": 0.55},
}

# Extra recognized words that should also point to a given crop key, since
# farmers may use a different common name than the CROP_KC key itself.
CROP_ALIASES = {
    "canola": "mustard",
    "rapeseed": "mustard",
    "peanut": "groundnut",
    "peanuts": "groundnut",
    "jowar": "sorghum",
    "gram": "chickpea",
    "spuds": "potato",
}

# Broader stage vocabulary -- covers common ways a farmer might phrase each
# growth stage in English, beyond just the single keyword used before.
INITIAL_STAGE_WORDS = [
    "early", "seedling", "initial", "germination", "sowing", "planting",
    "nursery", "transplanting", "transplant", "just sown", "just planted",
    "emergence", "sprouting", "first stage", "start stage", "starting stage",
    "beginning stage", "early stage", "new crop", "newly sown", "newly planted",
]

LATE_STAGE_WORDS = [
    "late", "maturity", "mature", "harvest", "harvesting", "ripening",
    "ripe", "grain filling", "senescence", "pre-harvest", "final stage",
    "end stage", "last stage", "closing stage", "near harvest", "almost ready",
    "drying stage", "yellowing", "final phase", "end phase",
]

MID_STAGE_WORDS = [
    "mid", "middle", "flowering", "flower", "booting", "heading",
    "tillering", "vegetative", "growing", "growth stage", "development",
    "reproductive", "fruiting", "podding", "mid stage", "middle stage",
    "growing stage", "vegetative stage", "flowering stage",
]


def estimate_solar_radiation_from_cloud(cloud_cover_pct: float) -> float:
    """Rough proxy (MJ/m²/day) since free weather APIs don't return solar radiation directly."""
    clear_sky_radiation = 25.0
    return round(clear_sky_radiation * (1 - 0.75 * (cloud_cover_pct / 100)), 2)


def calculate_eto(temp_max, temp_min, humidity, wind_speed_ms, solar_rad):
    """Simplified FAO-56 Penman-Monteith reference evapotranspiration (mm/day)."""
    temp_mean = (temp_max + temp_min) / 2
    delta = (4098 * (0.6108 * math.exp(17.27 * temp_mean / (temp_mean + 237.3)))) / (temp_mean + 237.3) ** 2
    gamma = 0.665e-3 * 101.3
    es = 0.6108 * math.exp(17.27 * temp_mean / (temp_mean + 237.3))
    ea = es * humidity / 100
    eto = (0.408 * delta * solar_rad + gamma * (900 / (temp_mean + 273)) * wind_speed_ms * (es - ea)) / \
          (delta + gamma * (1 + 0.34 * wind_speed_ms))
    return round(eto, 2)


def crop_water_need(crop: str, stage: str, eto: float) -> float:
    crop = crop.lower()
    if crop not in CROP_KC:
        raise ValueError(f"Unknown crop '{crop}'. Supported: {list(CROP_KC.keys())}")
    if stage not in CROP_KC[crop]:
        raise ValueError(f"Unknown stage '{stage}'. Supported: initial, mid, late")
    kc = CROP_KC[crop][stage]
    return round(eto * kc, 2)


def _parse_crop_and_stage(query: str):
    """Keyword extraction using word boundaries to avoid substring false-matches."""
    q = query.lower()

    crop = "wheat"
    for c in CROP_KC:
        if re.search(rf"\b{re.escape(c)}\b", q):
            crop = c
            break
    else:
        # No direct CROP_KC key matched -- check aliases (e.g. "canola" -> "mustard")
        for alias, real_crop in CROP_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", q):
                crop = real_crop
                break

    if any(re.search(rf"\b{re.escape(w)}\b", q) for w in INITIAL_STAGE_WORDS):
        stage = "initial"
    elif any(re.search(rf"\b{re.escape(w)}\b", q) for w in LATE_STAGE_WORDS):
        stage = "late"
    elif any(re.search(rf"\b{re.escape(w)}\b", q) for w in MID_STAGE_WORDS):
        stage = "mid"
    else:
        stage = "mid"  # default when no stage word is found at all

    return crop, stage


def irrigation_agent(query: str, location: str = DEFAULT_LOCATION) -> dict:
    crop, stage = _parse_crop_and_stage(query)

    try:
        data = get_forecast(location=location, days=3)
    except Exception as e:
        return {"answer": f"Weather data unavailable for irrigation calculation ({e}).", "agent": "irrigation"}

    forecast_days = data.get("forecast", {}).get("forecastday", [])
    if not forecast_days:
        return {"answer": "No forecast data available to calculate irrigation need.", "agent": "irrigation"}

    today = forecast_days[0]["day"]
    temp_max = today.get("maxtemp_c")
    temp_min = today.get("mintemp_c")
    humidity = today.get("avghumidity")
    wind_kph = today.get("maxwind_kph", 0)
    wind_ms = round(wind_kph * 0.27778, 2)
    cloud_cover = forecast_days[0]["hour"][12].get("cloud", 30)
    solar_rad = estimate_solar_radiation_from_cloud(cloud_cover)

    eto = calculate_eto(temp_max, temp_min, humidity, wind_ms, solar_rad)
    etc = crop_water_need(crop, stage, eto)

    rain_upcoming = sum(day["day"].get("totalprecip_mm", 0) for day in forecast_days)

    lines = [
        f"Irrigation advisory for {crop} ({stage} stage):",
        f"Reference evapotranspiration (ETo): {eto} mm/day",
        f"Crop water requirement (ETc): {etc} mm/day",
        f"Rainfall expected over next {len(forecast_days)} days: {round(rain_upcoming, 1)} mm",
    ]

    if rain_upcoming >= etc * 2:
        lines.append("Recommendation: Hold off irrigation — expected rainfall should cover crop water needs.")
    elif rain_upcoming >= etc:
        lines.append("Recommendation: Rainfall may partially cover needs — monitor soil moisture before irrigating.")
    else:
        lines.append(f"Recommendation: Irrigate soon — expected rainfall is insufficient for {crop}'s {stage}-stage demand.")

    return {"answer": "\n".join(lines), "agent": "irrigation"}