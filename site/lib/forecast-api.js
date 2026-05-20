/* Live client for the UW–Madison Ag Forecasting API.

   Called when the user changes the forecast date in the picker —
   skips a rebuild by fetching the JSON directly from the same
   endpoint the Python build script uses. CORS-dependent: if the API
   blocks browser origins the fetch throws and app.js falls back to
   the bundled snapshot. */

(function (root) {
  "use strict";

  // Preferred: server-side proxy at /proxy/forecast.
  //   • Docker deploy   → nginx → FastAPI backend (backend/main.py)
  //   • Netlify deploy  → /proxy/forecast rewrite → netlify/functions/forecast.js
  // Both handle CORS for us; the browser only talks same-origin.
  //
  // Fallback: direct upstream URL — useful for Node tests, almost
  // never works in a real browser because of CORS.
  const PROXY_URL  = "/proxy/forecast";
  const DIRECT_URL =
    "https://connect.doit.wisc.edu/ag_forecasting_api/v2/ag_models_wrappers/wisconet_g";

  // The dashboard is fixed at one-day risk; ignore any caller override
  // so we never accidentally bloat a response with multi-day arrays.
  const RISK_DAYS = 1;

  // In-memory cache: dateIso → { payload, source, expires }.
  // 1-hour TTL matches the proxy's Cache-Control max-age, so a stale
  // value here never lives longer than what the network layer allows.
  const CACHE_TTL_MS = 60 * 60 * 1000;
  const cache = new Map();

  function getCached(dateIso) {
    const hit = cache.get(dateIso);
    if (hit && hit.expires > Date.now()) return hit;
    if (hit) cache.delete(dateIso);
    return null;
  }

  function putCached(dateIso, payload, source) {
    cache.set(dateIso, {
      payload, source,
      expires: Date.now() + CACHE_TTL_MS,
    });
    // Trim the cache if it grows unbounded over a long session.
    if (cache.size > 50) {
      const firstKey = cache.keys().next().value;
      cache.delete(firstKey);
    }
  }

  async function fetchForecast(dateIso /*, riskDays — ignored */) {
    const rd = RISK_DAYS;

    // 0) In-memory cache — instant if we already fetched this date.
    const cached = getCached(dateIso);
    if (cached) {
      root.ForecastAPI.lastSource = cached.source + "-cache";
      return cached.payload;
    }

    // 1) Try the proxy first. The proxy is whichever runtime is
    //    hosting the site:
    //      • Netlify     → netlify/functions/forecast.js
    //      • Docker VM   → nginx location /api/forecast (nginx.conf)
    //    Both expect the upstream's native param name `forecasting_date`,
    //    so this URL passes through unchanged on either side. We let
    //    the browser HTTP cache help too — the proxy returns
    //    Cache-Control: max-age=3600.
    root.ForecastAPI.lastSource = null;
    try {
      const proxyUrl =
        `${PROXY_URL}?forecasting_date=${encodeURIComponent(dateIso)}` +
        `&risk_days=${rd}`;
      const resp = await fetch(proxyUrl, {
        headers: { Accept: "application/json" },
      });
      if (resp.ok) {
        const payload = await resp.json();
        putCached(dateIso, payload, "proxy");
        root.ForecastAPI.lastSource = "proxy";
        return payload;
      }
      // Treat 404 specially — the proxy isn't deployed here, fall through.
      if (resp.status !== 404) {
        throw new Error(`Proxy returned ${resp.status}`);
      }
    } catch (err) {
      // Swallow network/404 and try the direct URL as a last resort.
      console.warn("Proxy unavailable, trying direct API:", err.message || err);
    }

    // 2) Direct upstream — works in Node, sometimes in browsers if CORS allows.
    const directUrl =
      `${DIRECT_URL}?forecasting_date=${encodeURIComponent(dateIso)}` +
      `&risk_days=${rd}`;
    const resp = await fetch(directUrl, {
      headers: { Accept: "application/json" },
    });
    if (!resp.ok) throw new Error(`Forecast API ${resp.status}`);
    const payload = await resp.json();
    putCached(dateIso, payload, "direct");
    root.ForecastAPI.lastSource = "direct";
    return payload;
  }

  function clearCache() { cache.clear(); }

  /**
   * Flatten the FeatureCollection payload into one record per station.
   * Mirrors features/data.py:flatten_features but takes only the most
   * recent timeseries entry (risk_days=1) per station.
   */
  function flattenForecast(payload, normalizeClass) {
    const rows = [];
    for (const feature of payload.features || []) {
      const station = feature.station || {};
      const coords = station.coordinates || {};
      // Use the last timeseries entry (most recent forecasting_date).
      const series = feature.timeseries || [];
      if (!series.length) continue;
      const ts = series[series.length - 1];

      const row = {
        id: String(station.station_id),
        name: String(station.station_name),
        lat: coords.latitude,
        lon: coords.longitude,
        city: station.city,
        county: station.county,
        region: station.region,
      };
      for (const item of ts.data || []) {
        const key = item.fieldname;
        const val = item.value;
        // Class fields get normalized so "HIGH" / " high " all match.
        if (key && key.endsWith("_class")) {
          row[key] = normalizeClass(val);
        } else {
          row[key] = val;
        }
      }
      rows.push(row);
    }
    return rows;
  }

  function normalizeClass(value) {
    if (value == null) return "Unknown";
    const t = String(value).trim();
    if (!t) return "Unknown";
    // Title-case to match features/data.py:normalize_class.
    return t.replace(/\w\S*/g, (w) =>
      w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()
    );
  }

  root.ForecastAPI = {
    fetchForecast,
    flattenForecast,
    normalizeClass,
    clearCache,
    // "proxy" | "direct" | "proxy-cache" | "direct-cache" | null
    // — read by app.js after a load.
    lastSource: null,
  };
})(window);
