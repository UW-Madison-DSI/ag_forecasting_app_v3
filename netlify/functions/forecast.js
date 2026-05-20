/* Netlify Function — server-side proxy in front of the UW–Madison Ag
   Forecasting API.

   Why this exists:  the upstream API at connect.doit.wisc.edu does
   not return Access-Control-Allow-Origin headers, so the browser
   blocks any direct fetch. This function makes the same call from
   Netlify's edge, attaches permissive CORS headers, and forwards the
   JSON back to the browser. Free tier covers far more traffic than
   a dashboard like this will ever generate.

   Endpoint:
       GET /api/forecast?date=YYYY-MM-DD&risk_days=1
   (The /api/forecast path is mapped to this function by netlify.toml.)
*/

const UPSTREAM =
  "https://connect.doit.wisc.edu/ag_forecasting_api/v2/ag_models_wrappers/wisconet_g";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function reply(statusCode, body, extraHeaders) {
  return {
    statusCode,
    headers: {
      ...CORS,
      "Content-Type": "application/json",
      ...(extraHeaders || {}),
    },
    body: typeof body === "string" ? body : JSON.stringify(body),
  };
}

exports.handler = async (event) => {
  // CORS preflight (browsers send OPTIONS before the actual GET).
  if (event.httpMethod === "OPTIONS") return reply(204, "");

  const params = event.queryStringParameters || {};
  const date = params.date || params.forecasting_date;
  const riskDays = params.risk_days || "1";

  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return reply(400, { error: "Missing or invalid `date` (expected YYYY-MM-DD)." });
  }
  if (!/^\d+$/.test(String(riskDays))) {
    return reply(400, { error: "`risk_days` must be an integer." });
  }

  const url =
    `${UPSTREAM}?forecasting_date=${encodeURIComponent(date)}` +
    `&risk_days=${encodeURIComponent(riskDays)}`;

  try {
    const resp = await fetch(url, {
      headers: { Accept: "application/json" },
    });
    const text = await resp.text();
    if (!resp.ok) {
      return reply(resp.status, {
        error: `Upstream API returned ${resp.status}`,
        upstream_body: text.slice(0, 500),
      });
    }
    // Cache successful responses for 1 h at the Netlify edge — the
    // forecast is deterministic per (date, risk_days).
    return reply(200, text, { "Cache-Control": "public, max-age=3600" });
  } catch (err) {
    return reply(502, { error: `Proxy failed: ${err.message || String(err)}` });
  }
};
