#!/bin/sh
# Container entrypoint — runs both uvicorn (the proxy backend) and
# nginx (static site + reverse proxy) in the same container, matching
# the COA-builder pattern. Tini handles signals as PID 1.
set -e

# Start the FastAPI backend in the background. Bind to loopback only;
# nginx is the only thing that talks to it.
uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --log-level info \
    --no-access-log &
UVICORN_PID=$!

# Forward SIGTERM/SIGINT to both processes for a clean shutdown.
trap 'kill -TERM "$UVICORN_PID" 2>/dev/null; nginx -s quit 2>/dev/null; exit 0' INT TERM

# Give uvicorn a moment to bind before nginx starts proxying to it.
# (nginx itself starts fine either way thanks to runtime DNS resolve,
#  but this avoids a first-request 502 race.)
sleep 1

# nginx in the foreground = container PID-tracked process.
exec nginx -g 'daemon off;'
