# Two-stage build:
#   1) Run build_site.py in a Python image to fetch the forecast +
#      wiscopy weather and write site/data/latest.json.
#   2) Copy the finished site/ tree into nginx:alpine, which also
#      acts as the /api/forecast CORS proxy.
#
# Rebuild daily via your VM's cron / Watchtower / a CI job by running
# `docker compose build --no-cache && docker compose up -d`.

# ---------- Stage 1: build the data snapshot ----------
FROM python:3.11-slim AS builder

WORKDIR /build

# OS deps that wiscopy / pandas may need at install time.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r requirements.txt

# Source tree needed by build_site.py.
COPY features/      ./features/
COPY assets/        ./assets/
COPY site/          ./site/
COPY build_site.py  ./

# Build the snapshot. If wiscopy is unreachable from the VM, weather
# + biomass are skipped automatically — the disease forecast still
# loads and the build keeps going.
RUN python build_site.py

# ---------- Stage 2: serve with nginx ----------
FROM nginx:1.27-alpine

# Static site + freshly built data.
COPY --from=builder /build/site /usr/share/nginx/html
# nginx config (CORS proxy + cache headers).
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1
