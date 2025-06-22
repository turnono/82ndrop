# 82ndrop Agent Deployment Makefile
# 
# IMPORTANT: When deploying with ADK, you will be prompted:
# "Allow unauthenticated invocations to [your-service-name] (y/N)?"
# Answer: N (or press Enter) to REQUIRE authentication
# This enables ADK's built-in authentication at the Cloud Run level

include drop_agent/.env

install:
	pip install -r requirements.txt

deploy:
	@echo "[Deploy with Authentication] Deploying 82ndrop agent with ADK authentication..."
	@echo "⚠️  IMPORTANT: When prompted 'Allow unauthenticated invocations?', answer N to enable authentication"
	adk deploy cloud_run \
		--project=${GOOGLE_CLOUD_PROJECT} \
		--region=${GOOGLE_CLOUD_LOCATION} \
		--service_name=drop-agent-service \
		--app_name=drop_agent \
		--with_ui \
		./drop_agent

deploy-gcloud:
	@echo "[Deploy with gcloud] Deploying agent with Firebase authentication using gcloud run deploy..."
	@if [ -z "${GOOGLE_CLOUD_PROJECT}" ]; then \
		echo "❌ Error: GOOGLE_CLOUD_PROJECT environment variable is not set."; \
		echo "Set it in your drop_agent/.env file"; \
		exit 1; \
	fi
	gcloud run deploy drop-agent-service \
		--source . \
		--region ${GOOGLE_CLOUD_LOCATION} \
		--allow-unauthenticated \
		--service-account ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},\
GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},\
REASONING_ENGINE_ID=${REASONING_ENGINE_ID},\
ENV=${ENV}"

deploy-staging:
	@echo "[Deploy Staging] Deploying staging service (OPEN ACCESS for testing)..."
	@if [ -z "${GOOGLE_CLOUD_PROJECT}" ]; then \
		echo "❌ Error: GOOGLE_CLOUD_PROJECT environment variable is not set."; \
		echo "Set it in your drop_agent/.env file"; \
		exit 1; \
	fi
	gcloud run deploy drop-agent-staging \
		--source . \
		--region ${GOOGLE_CLOUD_LOCATION} \
		--allow-unauthenticated \
		--port 8000 \
		--service-account ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},\
GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},\
REASONING_ENGINE_ID=${REASONING_ENGINE_ID},\
ENV=${ENV},\
FIREBASE_PROJECT_ID=${GOOGLE_CLOUD_PROJECT}"

deploy-production:
	@echo "[Deploy Production] Deploying production service (FIREBASE AUTH REQUIRED)..."
	@if [ -z "${GOOGLE_CLOUD_PROJECT}" ]; then \
		echo "❌ Error: GOOGLE_CLOUD_PROJECT environment variable is not set."; \
		echo "Set it in your drop_agent/.env file"; \
		exit 1; \
	fi
	gcloud run deploy drop-agent-service \
		--source . \
		--region ${GOOGLE_CLOUD_LOCATION} \
		--allow-unauthenticated \
		--port 8000 \
		--service-account ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},\
GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},\
REASONING_ENGINE_ID=${REASONING_ENGINE_ID},\
ENV=${ENV},\
FIREBASE_PROJECT_ID=${GOOGLE_CLOUD_PROJECT}"

deploy-include-vertex-session-storage:
	@echo "[Deploy with Authentication + Vertex] Deploying with authentication and managed session service..."
	@echo "⚠️  IMPORTANT: When prompted 'Allow unauthenticated invocations?', answer N to enable authentication"
	@if [ -z "${REASONING_ENGINE_ID}" ]; then \
		echo "❌ Error: REASONING_ENGINE_ID environment variable is not set."; \
		echo "Set it in your .env file or export it: export REASONING_ENGINE_ID=your-agent-engine-resource-id"; \
		exit 1; \
	fi
	adk deploy cloud_run \
		--project=${GOOGLE_CLOUD_PROJECT} \
		--region=${GOOGLE_CLOUD_LOCATION} \
		--service_name=drop-agent-service \
		--app_name=${APP_NAME} \
		--session_db_url=agentengine://${REASONING_ENGINE_ID} \
		--with_ui \
		./drop_agent

deploy-frontend:
	@echo "[Deploy Frontend] Deploying Angular frontend to Firebase Hosting..."
	cd frontend && ng build --configuration=production && firebase deploy --only hosting:82ndrop --project=${GOOGLE_CLOUD_PROJECT}

# Development and testing commands
test-local:
	@echo "[Test Local] Starting local development server..."
	python main.py

test-auth:
	@echo "[Test Authentication] Running Firebase authentication tests..."
	python test_auth.py

check-auth:
	@echo "[Check Authentication] Testing authentication status..."
	curl -X GET "https://drop-agent-service-855515190257.us-central1.run.app/" \
		-H "Content-Type: application/json"

test-agent:
	@echo "[Test Agent] Testing agent with authentication..."
	curl -X POST "https://drop-agent-service-855515190257.us-central1.run.app/run" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjNiZjA1MzkxMzk2OTEzYTc4ZWM4MGY0MjcwMzM4NjM2NDA2MTBhZGMiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiYWJkdWxsYWggYWJyYWhhbXMiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSlVPSWx1SUtVOHQ2aGtmZzQ0NENRcjhORHUzeDJIQkZFaG9YUGJrN3JKWnZUNEJJNF81UT1zOTYtYyIsImFnZW50QWNjZXNzIjp0cnVlLCJhZ2VudF9hY2Nlc3MiOnRydWUsImFjY2Vzc19sZXZlbCI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiYWdlbnRfcGVybWlzc2lvbnMiOnsiODJuZHJvcCI6dHJ1ZSwidmlkZW9fcHJvbXB0cyI6dHJ1ZSwic2VhcmNoX2FnZW50Ijp0cnVlLCJndWlkZV9hZ2VudCI6dHJ1ZSwicHJvbXB0X3dyaXRlciI6dHJ1ZX0sImdyYW50ZWRfYXQiOiIyMDI1LTA2LTIxVDIwOjE1OjAwWiIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS90YWFqaXJhaCIsImF1ZCI6InRhYWppcmFoIiwiYXV0aF90aW1lIjoxNzUwNTgwMjkzLCJ1c2VyX2lkIjoiaVZaNFB1OVl6WFRHT28yZFhSTG1KaGJnRW5sMSIsInN1YiI6ImlWWjRQdTlZelhUR09vMmRYUkxtSmhiZ0VubDEiLCJpYXQiOjE3NTA1OTgxNjgsImV4cCI6MTc1MDYwMTc2OCwiZW1haWwiOiJ0dXJub25vQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTA4NzczNTM5NDI4MDc0MTcxMjE2Il0sImVtYWlsIjpbInR1cm5vbm9AZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.gQxwR5wOh9almpZBfvbac2_jeWYaVU9KVxlITMvaF3ell4_sOn6SvsaOJSuHSjogqQsdVr5WLdXxQmb7IRfs_vNXjSaL08rUhhrOiEURUv9cchwf39J-2mwnY8Y6MqqRTaZmNeP48RUfCduxewB8e2nNxzaX7a4Rab3WuMYouLEtg8uOUEuh5GL6SnotH8z3BBWFHbke_ot16ZDfNRe5EdOTafQc1oXnEiaBLjnkcGi3MmZkUCjlSyQUWyK-kzEN4v14mXAClZusLe2fweRZz3dHxDYyRe-szDeESUbLCAcvMAuM5bTTxS-Fc2ZzzEYvRm6MWpRJmoPuY3TT3yf1Ow" \
		-d '{"appName": "drop_agent", "userId": "iVZ4Pu9YzXTGOo2dXRLmJhbgEnl1", "sessionId": "test-session", "newMessage": {"parts": [{"text": "Hello, can you help me test the 82ndrop agent functionality?"}], "role": "user"}}'

logs:
	@echo "[View Logs] Viewing recent Cloud Run logs..."
	gcloud run services logs read drop-agent-service --region=${GOOGLE_CLOUD_LOCATION} --project=${GOOGLE_CLOUD_PROJECT} --limit=20

help:
	@echo "82ndrop Agent Deployment Commands:"
	@echo ""
	@echo "  make install                     - Install Python dependencies"
	@echo "  make deploy                      - Deploy agent with ADK authentication"
	@echo "  make deploy-include-vertex       - Deploy with Vertex AI session storage"
	@echo "  make deploy-frontend             - Deploy Angular frontend"
	@echo "  make test-local                  - Run local development server"
	@echo "  make test-auth                   - Test Firebase authentication"
	@echo "  make check-auth                  - Test if deployed service requires auth"
	@echo "  make deploy-gcloud              - Deploy agent with Firebase authentication using gcloud run deploy"
	@echo "  make deploy-staging             - Deploy staging service (open access for testing)"
	@echo "  make deploy-production          - Deploy production service (Firebase auth required)"
	@echo "  make test-agent                  - Test agent with authentication"
	@echo "  make logs                        - View recent Cloud Run logs"
	@echo ""
	@echo "AUTHENTICATION NOTE:"
	@echo "When deploying, answer 'N' to 'Allow unauthenticated invocations?' to enable authentication"