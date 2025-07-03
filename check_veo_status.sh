#!/bin/bash
curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json; charset=utf-8" \
     -d '{"operationName": "projects/taajirah/locations/us-central1/publishers/google/models/veo-3.0-generate-preview/operations/694e5148-2a7e-4e0f-aa01-cfd58b7445bd"}' \
     "https://us-central1-aiplatform.googleapis.com/v1/projects/taajirah/locations/us-central1/publishers/google/models/veo-3.0-generate-preview:fetchPredictOperation" > /Users/abdullah/Documents/Manual_Library/Github/82ndrop/video_result.json