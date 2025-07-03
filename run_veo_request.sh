#!/bin/bash
curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json; charset=utf-8" \
     "https://us-central1-aiplatform.googleapis.com/v1/projects/taajirah/locations/us-central1/publishers/google/models/veo-3.0-generate-preview:predictLongRunning" \
     -d @request.json
