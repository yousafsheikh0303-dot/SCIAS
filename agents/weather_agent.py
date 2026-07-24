import os
import difflib
import requests
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "http://api.weatherapi.com/v1/forecast.json"
DEFAULT_LOCATION = "Lahore"

# Common Pakistani cities to detect in free-text queries.
PAKISTANI_CITIES = [
    # Punjab
    "Islamabad", "Lahore", "Faisalabad", "Multan", "Rawalpindi", "Sialkot",
    "Gujranwala", "Sargodha", "Bahawalpur", "Sheikhupura", "Rahim Yar Khan",
    "Gujrat", "Kasur", "Okara", "Sahiwal", "Dera Ghazi Khan", "Jhang",
    "Chiniot", "Kamoke", "Sadiqabad", "Burewala", "Kohat", "Khanewal",
    "Muzaffargarh", "Vehari", "Jhelum", "Chakwal", "Attock", "Mianwali",
    "Bhakkar", "Layyah", "Toba Tek Singh", "Hafizabad", "Nankana Sahib",
    "Pakpattan", "Narowal", "Mandi Bahauddin",

    # Sindh
    "Karachi", "Hyderabad", "Sukkur", "Larkana", "Nawabshah", "Mirpur Khas",
    "Jacobabad", "Shikarpur", "Khairpur", "Dadu", "Thatta", "Badin",

    # Khyber Pakhtunkhwa
    "Peshawar", "Mardan", "Abbottabad", "Mingora", "Kohat", "Bannu",
    "Dera Ismail Khan", "Swabi", "Nowshera", "Charsadda", "Mansehra",
    "Haripur", "Chitral",

    # Balochistan
    "Quetta", "Gwadar", "Turbat", "Khuzdar", "Sibi", "Chaman", "Zhob",

    # Azad Kashmir / Gilgit-Baltistan
    "Muzaffarabad", "Mirpur", "Gilgit", "Skardu",
]

# Flattened lookup: individual words from every city name (handles multi-word
# cities like "Dera Ghazi Khan" by also matching on "Dera", "Ghazi", "Khan").
_CITY_WORD_MAP = {}
for _city in PAKISTANI_CITIES:
    for _word in _city.lower().split():
        _CITY_WORD_MAP.setdefault(_word, _city)


def _parse_location(query: str, default: str):
    """
    Looks for a known city name in the query text.

    Returns a tuple: (resolved_location, status)
      status == "matched"    -> an exact city name was found in the query
      status == "default"    -> no city-like word was found; safe to use default
      status == "misspelled" -> a word closely resembles a city name but doesn't
                                 exactly match; likely a typo, don't silently default
    """
    q = query.lower()

    # 1. Exact match first (handles multi-word city names like "dera ghazi khan")
    for city in PAKISTANI_CITIES:
        if city.lower() in q:
            return city, "matched"

    # 2. No exact match -- check each word for a close-but-not-exact resemblance
    #    to a known city word, which suggests a typo rather than "no city given"
    words = [w.strip(".,?!\"'") for w in q.split()]
    known_words = list(_CITY_WORD_MAP.keys())

    for word in words:
        if len(word) < 4:
            continue  # skip short common words to avoid false-positive fuzzy matches
        close = difflib.get_close_matches(word, known_words, n=1, cutoff=0.75)
        if close:
            suggested_city = _CITY_WORD_MAP[close[0]]
            return suggested_city, "misspelled"

    # 3. Nothing resembling a city at all -- genuinely no location mentioned
    return default, "default"


def get_forecast(location: str = DEFAULT_LOCATION, days: int = 7) -> dict:
    """Fetch forecast. Free tier caps at 3 days regardless of `days` requested."""
    params = {
        "key": WEATHER_API_KEY,
        "q": location,
        "days": days,
        "aqi": "no",
        "alerts": "no",
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _spray_advisory_24h(forecast_today: dict) -> list:
    advisories = []
    for hour in forecast_today.get("hour", []):
        rain_chance = hour.get("chance_of_rain", 0)
        wind_kph = hour.get("wind_kph", 0)
        time_only = hour.get("time", "").split(" ")[-1]
        if rain_chance > 60:
            advisories.append(f"{time_only}: Avoid spraying — {rain_chance}% chance of rain")
        elif wind_kph > 15:
            advisories.append(f"{time_only}: Avoid spraying — wind {wind_kph} kph too high (drift risk)")
    return advisories


def _frost_heat_warnings(forecast_days: list) -> list:
    warnings = []
    for day in forecast_days:
        date = day.get("date")
        min_temp = day["day"].get("mintemp_c")
        max_temp = day["day"].get("maxtemp_c")
        if min_temp is not None and min_temp < 4:
            warnings.append(f"{date}: Frost risk — min temp {min_temp}°C")
        if max_temp is not None and max_temp > 42:
            warnings.append(f"{date}: Heat stress risk — max temp {max_temp}°C")
    return warnings


def _irrigation_outlook(forecast_days: list) -> list:
    summary = []
    for day in forecast_days:
        date = day.get("date")
        rain_mm = day["day"].get("totalprecip_mm", 0)
        rain_chance = day["day"].get("daily_chance_of_rain", 0)
        if rain_mm > 5 or rain_chance > 70:
            summary.append(f"{date}: Rain expected ({rain_mm}mm, {rain_chance}% chance) — hold irrigation")
        else:
            summary.append(f"{date}: Dry — irrigation likely needed")
    return summary


def weather_agent(query: str, location: str = None) -> dict:
    if location:
        resolved_location, status = location, "matched"
    else:
        resolved_location, status = _parse_location(query, DEFAULT_LOCATION)

    if status == "misspelled":
        return {
            "answer": (
                f"I couldn't recognize the city name in your question. "
                f"Did you mean **{resolved_location}**? Please check the spelling and try again."
            ),
            "agent": "weather",
        }

    try:
        data = get_forecast(location=resolved_location, days=7)
    except Exception as e:
        return {"answer": f"Weather data unavailable right now ({e}). Please try again shortly.", "agent": "weather"}

    forecast_days = data.get("forecast", {}).get("forecastday", [])
    if not forecast_days:
        return {"answer": f"No forecast data available for {resolved_location}.", "agent": "weather"}

    today = forecast_days[0]
    spray_advisory = _spray_advisory_24h(today)
    frost_heat = _frost_heat_warnings(forecast_days)
    outlook = _irrigation_outlook(forecast_days)

    lines = [f"Weather advisory for {resolved_location} ({len(forecast_days)}-day forecast available):"]

    if spray_advisory:
        lines.append("\n24-hour spray window alerts:")
        lines.extend(spray_advisory[:6])
    else:
        lines.append("\n24-hour spray window: conditions look fine for spraying today.")

    if frost_heat:
        lines.append("\nFrost/Heat warnings:")
        lines.extend(frost_heat)

    lines.append(f"\n{len(forecast_days)}-day irrigation planning outlook:")
    lines.extend(outlook)

    return {"answer": "\n".join(lines), "agent": "weather"}