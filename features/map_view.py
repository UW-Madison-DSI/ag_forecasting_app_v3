"""Plotly map figure construction for the dashboard."""

import pandas as pd
import plotly.express as px

from features.config import CLASS_COLORS, CLASS_ORDER, WI_CENTER


def build_map(map_df: pd.DataFrame, disease_label: str):
    """Build the interactive station map for one selected disease.

    Renders a ``scatter_mapbox`` with one marker per station, colored
    by ``risk_class``. The legend shows only classes actually present
    in the data (in risk-priority order), and hover tooltips surface
    station metadata + the formatted risk value.

    Args:
        map_df: DataFrame from :func:`features.data.prepare_disease_df`.
            Must include ``latitude``, ``longitude``, ``risk_class``,
            ``risk_display``, and the station metadata columns.
        disease_label: Human-readable disease name, used in the legend title.

    Returns:
        A configured ``plotly.graph_objects.Figure`` ready for
        ``st.plotly_chart``.
    """
    # Only include classes that actually appear, but in our preferred order.
    present_classes = [c for c in CLASS_ORDER if c in map_df["risk_class"].unique()]

    fig = px.scatter_mapbox(
        map_df,
        lat="latitude",
        lon="longitude",
        color="risk_class",
        color_discrete_map=CLASS_COLORS,
        category_orders={"risk_class": present_classes},
        hover_name="station_name",
        hover_data={
            "station_id": True,
            "city": True,
            "county": True,
            "region": True,
            "risk_class": True,
            "risk_display": True,
            "latitude": False,
            "longitude": False,
        },
        zoom=5.8,
        height=620,
    )
    fig.update_traces(marker=dict(size=14, opacity=0.85))
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center=WI_CENTER,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend_title_text=f"{disease_label} risk",
    )
    return fig
