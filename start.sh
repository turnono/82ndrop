#!/bin/bash
echo "PORT is set to: $PORT"
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --server-header \
    --date-header \
    --timeout-keep-alive 120 \
    --http h11 