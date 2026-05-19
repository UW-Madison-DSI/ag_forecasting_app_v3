"""Configuration constants for the forecasting dashboard.

Edit this file to add new disease models, retune the color palette,
change the API endpoint, or adjust the daily cache TTL. Nothing here
performs I/O, so it's safe to import from any other module.
"""

# Wisconet daily-risk forecasting endpoint (UW–Madison DoIT).
API_URL = "https://connect.doit.wisc.edu/ag_forecasting_api/v2/ag_models_wrappers/wisconet_g"

# How long a cached API response stays fresh. 24 h means one network
# call per (forecasting_date, risk_days) pair per day.
CACHE_TTL_SECONDS = 86_400

# Sidebar label  →  (numeric risk field, discrete risk-class field).
# Add a new disease by appending another entry here; the sidebar and
# map will pick it up automatically.
DISEASE_OPTIONS = {
    "Tar Spot (corn)": ("tarspot_risk", "tarspot_risk_class"),
    "Gray Leaf Spot (corn)": ("gls_risk", "gls_risk_class"),
    "Frogeye Leaf Spot (soybean)": ("fe_risk", "fe_risk_class"),
    "White Mold — Non-irrigated (soybean)": ("whitemold_nirr_risk", "whitemold_nirr_risk_class"),
    "White Mold — Irrigated 30in (soybean)": ("whitemold_irr_30in_risk", "whitemold_irr_30in_class"),
    "White Mold — Irrigated 15in (soybean)": ("whitemold_irr_15in_risk", "whitemold_irr_15in_class"),
}

# Marker colors per risk class. Keys must match the normalized class
# strings produced by ``features.data.normalize_class``.
CLASS_COLORS = {
    "Low": "#2ecc71",
    "Moderate": "#f39c12",
    "High": "#e74c3c",
    "Inactive": "#95a5a6",
    "No Risk": "#2ecc71",
    "Unknown": "#bdc3c7",
}

# Legend display order — riskiest first so the eye lands on it.
CLASS_ORDER = ["High", "Moderate", "Low", "No Risk", "Inactive", "Unknown"]

# Default map center: roughly the geographic middle of Wisconsin.
WI_CENTER = {"lat": 44.6, "lon": -89.7}
