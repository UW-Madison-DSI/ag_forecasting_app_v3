"""HTTP proxy that fronts the same Python helpers the Streamlit app uses.

Lives behind nginx in production (nginx forwards /proxy/* to 127.0.0.1:8000).
Lets the static dashboard fetch dynamic data for any date without
shipping wiscopy or the forecast-API call to the browser.
"""
