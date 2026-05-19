"""Cached HTTP client for the UW–Madison Ag Forecasting API."""

import requests
import streamlit as st

from features.config import API_URL, CACHE_TTL_SECONDS


@st.cache_data(
    ttl=CACHE_TTL_SECONDS,
    persist="disk",
    show_spinner="Fetching forecast from Wisconet…",
)
def fetch_forecast(forecasting_date: str, risk_days: int = 1) -> dict:
    """Fetch a daily risk forecast for every Wisconet station.

    Cached on disk for 24 h (see ``CACHE_TTL_SECONDS``) keyed by
    ``(forecasting_date, risk_days)``, so the network call happens at
    most once per day per combination even across app restarts. Call
    ``fetch_forecast.clear()`` to force a refetch (the sidebar's
    "Refresh data" button does this).

    Args:
        forecasting_date: ISO date string, e.g. ``"2026-07-15"``.
        risk_days: Forecast horizon in days (1–7 per the API).

    Returns:
        The parsed JSON FeatureCollection-style payload.

    Raises:
        requests.HTTPError: Non-2xx response from the API.
        requests.RequestException: Network/transport failure.
    """
    response = requests.get(
        API_URL,
        params={"forecasting_date": forecasting_date, "risk_days": risk_days},
        headers={"accept": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()
