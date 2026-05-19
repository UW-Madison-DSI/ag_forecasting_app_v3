"""Reusable building blocks for the WI crop disease forecast dashboard.

Submodules:
    config     -- shared constants (API URL, TTL, disease list, colors)
    api        -- cached HTTP client for the forecasting API
    data       -- payload → tidy DataFrame transformations
    map_view   -- plotly map figure construction

The top-level ``app.py`` composes these into the Streamlit UI.
"""
