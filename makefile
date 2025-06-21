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
		--port 8000 \
		--service-account ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},\
GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},\
REASONING_ENGINE_ID=${REASONING_ENGINE_ID},\
ENV=${ENV}"

deploy-with-auth:
	@echo "[Deploy with Firebase Auth] Deploying agent with Firebase authentication..."
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

check-auth:
	@echo "[Check Authentication] Testing authentication status..."
	curl -X GET "https://drop-agent-service-855515190257.us-central1.run.app/" \
		-H "Content-Type: application/json"

test-agent:
	@echo "[Test Agent] Testing agent with authentication..."
	curl -X POST "https://drop-agent-service-855515190257.us-central1.run.app/run" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer test-token" \
		-d '{"appName": "drop_agent", "userId": "test-user", "sessionId": "test-session", "newMessage": {"parts": [{"text": "Hello"}], "role": "user"}}'

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
	@echo "  make check-auth                  - Test if deployed service requires auth"
	@echo "  make deploy-gcloud              - Deploy agent with Firebase authentication using gcloud run deploy"
	@echo "  make deploy-with-auth            - Deploy agent with Firebase authentication"
	@echo "  make test-agent                  - Test agent with authentication"
	@echo "  make logs                        - View recent Cloud Run logs"
	@echo ""
	@echo "AUTHENTICATION NOTE:"
	@echo "When deploying, answer 'N' to 'Allow unauthenticated invocations?' to enable authentication"