from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from api import fetch_forecast
from config import DISEASE_OPTIONS
from data import flatten_features, prepare_disease_df
from map_view import build_map


st.set_page_config(
    page_title="WI Crop Disease Risk Forecast",
    page_icon="🌽",
    layout="wide",
)

st.title("🌽 Wisconsin Crop Disease Risk Forecast")
st.caption(
    "Daily risk forecast from the UW–Madison Ag Forecasting API (Wisconet stations). "
    "Data is cached on disk for 24 h per (date, risk_days)."
)


def sidebar_controls():
    with st.sidebar:
        st.header("Controls")
        selected_date = st.date_input(
            "Forecasting date",
            value=date.today() - timedelta(days=1),
            max_value=date.today(),
        )
        risk_days = st.slider("Risk days", min_value=1, max_value=7, value=1)
        disease_label = st.selectbox("Disease model", list(DISEASE_OPTIONS.keys()))
        if st.button("🔄 Refresh data"):
            fetch_forecast.clear()
            st.rerun()
    return selected_date, risk_days, disease_label


def show_metrics(df: pd.DataFrame) -> None:
    active = df[~df["risk_class"].isin(["Inactive", "Unknown"])]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stations", len(df))
    col2.metric("Active models", len(active))
    col3.metric("High risk", int((df["risk_class"] == "High").sum()))
    col4.metric("Moderate risk", int((df["risk_class"] == "Moderate").sum()))


def show_table(df: pd.DataFrame, risk_field: str, class_field: str) -> None:
    with st.expander("Station data table"):
        cols = [
            "station_id", "station_name", "city", "county", "region",
            "latitude", "longitude", risk_field, class_field, "forecasting_date",
        ]
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols].sort_values(class_field), use_container_width=True)


def main() -> None:
    selected_date, risk_days, disease_label = sidebar_controls()
    risk_field, class_field = DISEASE_OPTIONS[disease_label]

    try:
        payload = fetch_forecast(selected_date.isoformat(), risk_days)
    except requests.HTTPError as err:
        st.error(f"API returned an error: {err.response.status_code} — {err.response.text[:200]}")
        return
    except requests.RequestException as err:
        st.error(f"Could not reach the forecasting API: {err}")
        return

    df = flatten_features(payload)
    if df.empty:
        st.warning("No station data returned for this date.")
        return

    map_df = prepare_disease_df(df, risk_field, class_field)

    show_metrics(map_df)
    st.plotly_chart(build_map(map_df, disease_label), use_container_width=True)
    show_table(map_df, risk_field, class_field)

    st.caption(f"Last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
