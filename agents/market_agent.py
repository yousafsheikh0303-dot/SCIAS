"""
Market intelligence agent for SCIAS.

Given a natural-language query mentioning a crop, pulls its historical
weekly mandi price series from SQLite, fits a Prophet model, and returns
a short-term price forecast alongside the current price.

Designed to be wired into the orchestrator's agent_map, and easily wrapped
as a LangGraph tool node (see `as_tool_node` at the bottom).
"""

import re
import sqlite3
import pandas as pd
from prophet import Prophet

DB_PATH = "db/scias.db"
SUPPORTED_CROPS = [
    'Apple', 'Banana', 'Bell Pepper', 'Black Pepper', 'Brinjal', 'Broccoli', 'Cabbage',
    'Capsicum', 'Carrot', 'Cauliflower', 'Cherry', 'Chickpea', 'Coriander', 'Cotton',
    'Cucumber', 'Garlic', 'Ginger', 'Gourd', 'Grapes', 'Green Chilli', 'Guava',
    'Jackfruit', 'Kiwi', 'Lemon', 'Lettuce', 'Litchi', 'Maize', 'Mango', 'Mint',
    'Mushroom', 'Muskmelon', 'Onion', 'Orange', 'Papaya', 'Pear', 'Peas', 'Pineapple',
    'Pomegranate', 'Potato', 'Pumpkin', 'Radish', 'Rice', 'Strawberry', 'Sugarcane',
    'Sweet Potato', 'Tamarind', 'Tomato', 'Turnip', 'Watermelon', 'Wheat',
]


def _parse_crop(query: str) -> str:
    q = query.lower()
    # sort longest-name-first so "Bell Pepper" is checked before any shorter overlap
    for crop in sorted(SUPPORTED_CROPS, key=len, reverse=True):
        pattern = r"\b" + re.escape(crop.lower()) + r"\b"
        if re.search(pattern, q):
            return crop
    return "Wheat"  # default fallback, mirrors yield_agent's pattern


def _load_price_history(crop: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT date, price_pkr FROM mandi_prices WHERE crop = ? ORDER BY date",
        conn, params=(crop,)
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


def _forecast_price(df: pd.DataFrame, periods: int = 4) -> pd.DataFrame:
    """Fit Prophet on weekly price history, forecast `periods` weeks ahead."""
    prophet_df = df.rename(columns={"date": "ds", "price_pkr": "y"})

    model = Prophet(
        weekly_seasonality=False,   # we only have one point per week already
        yearly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.8,
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods, freq="W")
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)


def market_agent(query: str, forecast_weeks: int = 4) -> dict:
    crop = _parse_crop(query)

    try:
        history = _load_price_history(crop)
        if len(history) < 5:
            return {
                "answer": f"Not enough price history for {crop} yet to build a reliable forecast "
                          f"(only {len(history)} data points). Need at least a few weeks of data.",
                "agent": "market"
            }

        current_price = history.iloc[-1]["price_pkr"]
        current_date = history.iloc[-1]["date"].date().isoformat()

        forecast = _forecast_price(history, periods=forecast_weeks)

        lines = [f"Current {crop} price ({current_date}): approx. {current_price:.0f} PKR"]
        lines.append(f"\n{forecast_weeks}-week price forecast for {crop}:")
        for _, row in forecast.iterrows():
            lines.append(
                f"  {row['ds'].date()}: {row['yhat']:.0f} PKR "
                f"(range {row['yhat_lower']:.0f}\u2013{row['yhat_upper']:.0f})"
            )

        return {"answer": "\n".join(lines), "agent": "market"}

    except Exception as e:
        return {"answer": f"Could not generate a forecast for {crop}: {e}", "agent": "market"}


def as_tool_node(state: dict) -> dict:
    """
    LangGraph-compatible node wrapper.
    Expects state['query'] (str), optionally state['forecast_weeks'] (int).
    Returns state updated with state['market_result'].
    """
    query = state.get("query", "")
    weeks = state.get("forecast_weeks", 4)
    result = market_agent(query, forecast_weeks=weeks)
    state["market_result"] = result
    return state