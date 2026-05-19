# Wisconsin Crop Disease Risk Forecast

Streamlit dashboard that visualizes daily crop-disease risk forecasts for
Wisconet weather stations across Wisconsin. Data comes from the UW–Madison
Ag Forecasting API.

## What it shows

For a chosen forecasting date and disease model, the app renders an
interactive map of every Wisconet station, color-coded by risk class
(`High` / `Moderate` / `Low` / `Inactive`). A summary metrics row and a
sortable station table sit alongside the map.

Supported disease models:

- Tar Spot (corn)
- Gray Leaf Spot (corn)
- Frogeye Leaf Spot (soybean)
- White Mold — Non-irrigated / Irrigated 30 in / Irrigated 15 in (soybean)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens the app at http://localhost:8501.

## How the daily cache works

Network calls go through `fetch_forecast()` in `api.py`, decorated with:

```python
@st.cache_data(ttl=86_400, persist="disk", ...)
```

- **`ttl=86_400`** — entries expire after 24 h.
- **`persist="disk"`** — entries are also written under `.streamlit/cache/`,
  so the cache survives app restarts. A given `(forecasting_date,
  risk_days)` pair hits the API **at most once per day total**, even if
  the server restarts in between.
- The sidebar **🔄 Refresh data** button calls `fetch_forecast.clear()`
  to force a fresh fetch.

## Project layout

```
ag_forecasting_streamllit_app/
├── app.py          # Streamlit UI / page composition
├── api.py          # Cached HTTP client for the forecasting API
├── data.py         # Reshape the API payload into a tidy DataFrame
├── map_view.py     # Plotly map figure construction
├── config.py       # API URL, TTL, disease → field map, colors
└── requirements.txt
```

Each module has a single responsibility:

| Module | Responsibility | Edit when… |
|---|---|---|
| `config.py` | Constants — API URL, TTL, disease list, color palette | adding a disease, changing colors, swapping endpoints |
| `api.py` | HTTP + caching | changing cache behavior or auth headers |
| `data.py` | Payload → DataFrame, class normalization | API response shape changes |
| `map_view.py` | Plotly figure construction | restyling the map |
| `app.py` | Sidebar, metrics, layout | UI changes |

## API reference

The app calls:

```
GET https://connect.doit.wisc.edu/ag_forecasting_api/v2/ag_models_wrappers/wisconet_g
    ?forecasting_date=YYYY-MM-DD
    &risk_days=N
```

Response is a FeatureCollection-style object: a top-level `fields`
schema plus a `features` list, each containing a `station` block (id,
name, lat/lon, county, region) and a `timeseries` list of daily
records. `data.flatten_features()` pivots the `timeseries[].data[]`
key/value pairs into named columns.

### Risk values

- Numeric fields (`tarspot_risk`, `gls_risk`, …) are probabilities in
  `[0, 1]`, with `-1` meaning "model inactive for this station/date".
- The matching `*_class` fields hold the discrete label
  (`Low` / `Moderate` / `High` / `Inactive`).
- Out of season, all stations report `-1` / `Inactive` — the map will
  be mostly gray. Pick a mid-growing-season date to see live colors.
