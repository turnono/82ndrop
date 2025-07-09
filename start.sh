#!/bin/bash
echo "PORT is set to: $PORT"
exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 0 main:app 