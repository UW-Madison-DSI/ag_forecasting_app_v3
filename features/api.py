"""Cached HTTP client for the UW–Madison Ag Forecasting API."""

from datetime import date, timedelta

import requests
import streamlit as st

from features.config import (
    API_URL,
    CACHE_TTL_SECONDS,
    MODEL_INFO_TTL_SECONDS,
    MODEL_INFO_URL_TEMPLATE,
)


@st.cache_data(
    ttl=CACHE_TTL_SECONDS,
    persist="disk",
    show_spinner="Fetching forecast from Wisconet…",
)
def fetch_forecast(forecasting_date: str, risk_days: int = 1) -> dict:
    """Fetch a daily risk forecast for every Wisconet station.

    **Date semantics.** The user passes the day they want a forecast
    *for* (e.g. "show me May 18's risk"). Internally the upstream API
    treats its ``forecasting_date`` parameter as the model-run date and
    returns a forecast for ``model_run_date + 1``. So to deliver a
    forecast labeled May 18 we have to query the API with May 17.
    This shift is applied here once; every caller (Streamlit app,
    backend proxy, build_site.py) gets the intuitive behavior.

    Cached on disk for 24 h (see ``CACHE_TTL_SECONDS``) keyed by the
    user's target date, so the network call happens at most once per
    day per combination across app restarts.

    Args:
        forecasting_date: ISO date string of the day to forecast FOR
            (e.g. ``"2026-05-18"`` → the forecast for May 18).
        risk_days: Forecast horizon in days (1–7 per the API).

    Returns:
        The parsed JSON FeatureCollection-style payload. The inner
        ``forecasting_date`` field on each timeseries entry will match
        the ``forecasting_date`` argument the caller passed in.

    Raises:
        requests.HTTPError: Non-2xx response from the API.
        requests.RequestException: Network/transport failure.
    """
    # Shift the user's "forecast target date" → API's "model-run date".
    try:
        target = date.fromisoformat(forecasting_date)
        query_date = (target - timedelta(days=1)).isoformat()
    except ValueError:
        # Pass non-ISO strings through unchanged — let the API reject them.
        query_date = forecasting_date

    response = requests.get(
        API_URL,
        params={"forecasting_date": query_date, "risk_days": risk_days},
        headers={"accept": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(
    ttl=MODEL_INFO_TTL_SECONDS,
    persist="disk",
    show_spinner=False,
)
def fetch_model_info(model_name: str) -> dict | None:
    """Fetch static metadata for one forecasting model.

    Returns the model's description, input variables, model type,
    risk-output scale, inactive rule, and version. Cached on disk for
    a week — this content is essentially static.

    Args:
        model_name: The API's short model id (e.g. ``"tarspot"``).

    Returns:
        Parsed JSON dict on success, or ``None`` if the API returns
        4xx/5xx or is unreachable. Callers should show a graceful
        fallback when ``None``.
    """
    url = MODEL_INFO_URL_TEMPLATE.format(model_name=model_name)
    try:
        response = requests.get(
            url,
            headers={"accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    return response.json()
