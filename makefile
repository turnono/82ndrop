# 82ndrop Agent Deployment Makefile
# 
# IMPORTANT: When deploying with ADK, you will be prompted:
# "Allow unauthenticated invocations to [your-service-name] (y/N)?"
# Answer: N (or press Enter) to REQUIRE authentication
# This enables ADK's built-in authentication at the Cloud Run level

include drop_agent/.env

install:
	pip install -r requirements.txt

# Verify enhanced workflow components
verify-workflow:
	@echo "🔍 Verifying enhanced workflow components..."
	@for file in drop_agent/agent.py drop_agent/prompts.py \
		drop_agent/sub_agents/guide/agent.py \
		drop_agent/sub_agents/search/agent.py \
		drop_agent/sub_agents/prompt_writer/agent.py \
		drop_agent/sub_agents/video_generator/agent.py; do \
		if [ ! -f "$$file" ]; then \
			echo "❌ Error: Required file $$file not found"; \
			exit 1; \
		fi; \
	done
	@echo "✅ All workflow components present"

# Deploy with ADK and Vertex AI session storage
deploy: verify-workflow
	@echo "[Deploy with ADK + Vertex] Deploying with ADK authentication and Vertex AI session storage..."
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
		--app_name=drop_agent \
		--session_db_url=agentengine://${REASONING_ENGINE_ID} \
		--with_ui \
		./drop_agent

# Deploy with gcloud (fallback option)
deploy-gcloud: verify-workflow
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
ENV=staging,\
FIREBASE_PROJECT_ID=${GOOGLE_CLOUD_PROJECT}"

# Deploy production environment
deploy-production: verify-workflow
	@echo "[Deploy Production] Deploying production service with enhanced workflow (FIREBASE AUTH REQUIRED)..."
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
		--memory 4Gi \
		--cpu 4 \
		--min-instances 1 \
		--max-instances 10 \
		--service-account ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},\
GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},\
REASONING_ENGINE_ID=${REASONING_ENGINE_ID},\
ENV=production,\
FIREBASE_PROJECT_ID=${GOOGLE_CLOUD_PROJECT}"

# Deploy frontend
deploy-frontend:
	@echo "[Deploy Frontend] Deploying Angular frontend to Firebase Hosting..."
	cd frontend && ng build --configuration=production && firebase deploy --only hosting:82ndrop --project=${GOOGLE_CLOUD_PROJECT}

# Development and testing commands
run-local:
	@echo "🚀 Running local development server..."
	python main.py

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

deploy-staging: verify-workflow
	@echo "[Deploy Staging] Deploying staging service with enhanced workflow (OPEN ACCESS for testing)..."
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
		--memory 2Gi \
		--cpu 2 \
		--min-instances 0 \
		--max-instances 2 \
		--service-account ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},\
GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},\
REASONING_ENGINE_ID=${REASONING_ENGINE_ID},\
ENV=staging,\
FIREBASE_PROJECT_ID=${GOOGLE_CLOUD_PROJECT}"
	@echo "\n✅ Staging Deployment Complete!"
	@echo "🧪 Test the enhanced workflow:"
	@echo "1. Guide Agent Analysis:   curl -X POST $$(gcloud run services describe drop-agent-staging --format='value(status.url)' --region=${GOOGLE_CLOUD_LOCATION})/analyze"
	@echo "2. Search Agent Research:  curl -X POST $$(gcloud run services describe drop-agent-staging --format='value(status.url)' --region=${GOOGLE_CLOUD_LOCATION})/research"
	@echo "3. Prompt Writer:         curl -X POST $$(gcloud run services describe drop-agent-staging --format='value(status.url)' --region=${GOOGLE_CLOUD_LOCATION})/compose"
	@echo "4. Video Generation:      curl -X POST $$(gcloud run services describe drop-agent-staging --format='value(status.url)' --region=${GOOGLE_CLOUD_LOCATION})/generate"

deploy-include-vertex-session-storage: verify-workflow
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

test-workflow-local: verify-workflow
	@echo "[Test Enhanced Workflow] Testing complete workflow locally..."
	@echo "1. Testing Guide Agent..."
	curl -X POST "http://localhost:8000/analyze" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"prompt":"Test video about morning routine"}'
	@echo "\n2. Testing Search Agent..."
	curl -X POST "http://localhost:8000/research" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"concept":"morning routine trends"}'
	@echo "\n3. Testing Prompt Writer..."
	curl -X POST "http://localhost:8000/compose" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"analysis":"morning routine","trends":"trending formats"}'
	@echo "\n4. Testing Video Generator..."
	curl -X POST "http://localhost:8000/generate" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"enhanced_prompt":"complete video prompt"}'

test-workflow-staging:
	@echo "[Test Enhanced Workflow] Testing complete workflow on staging..."
	@echo "1. Testing Guide Agent..."
	curl -X POST "https://drop-agent-staging-855515190257.us-central1.run.app/analyze" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"prompt":"Test video about morning routine"}'
	@echo "\n2. Testing Search Agent..."
	curl -X POST "https://drop-agent-staging-855515190257.us-central1.run.app/research" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"concept":"morning routine trends"}'
	@echo "\n3. Testing Prompt Writer..."
	curl -X POST "https://drop-agent-staging-855515190257.us-central1.run.app/compose" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"analysis":"morning routine","trends":"trending formats"}'
	@echo "\n4. Testing Video Generator..."
	curl -X POST "https://drop-agent-staging-855515190257.us-central1.run.app/generate" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"enhanced_prompt":"complete video prompt"}'

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
		-H "Authorization: Bearer ${FIREBASE_TOKEN}" \
		-d '{"appName": "drop_agent", "userId": "iVZ4Pu9YzXTGOo2dXRLmJhbgEnl1", "sessionId": "test-session", "newMessage": {"parts": [{"text": "Hello, can you help me test the 82ndrop agent functionality?"}], "role": "user"}}'

logs:
	@echo "[View Logs] Viewing recent Cloud Run logs..."
	gcloud run services logs read drop-agent-service --region=${GOOGLE_CLOUD_LOCATION} --project=${GOOGLE_CLOUD_PROJECT} --limit=20

help:
	@echo "82ndrop Agent Deployment Commands:"
	@echo ""
	@echo "  make install                     - Install Python dependencies"
	@echo "  make verify-workflow             - Verify enhanced workflow components"
	@echo "  make deploy                      - Deploy agent with ADK authentication"
	@echo "  make deploy-include-vertex       - Deploy with Vertex AI session storage"
	@echo "  make deploy-frontend             - Deploy Angular frontend"
	@echo "  make test-local                  - Run local development server"
	@echo "  make test-workflow-local         - Test enhanced workflow locally"
	@echo "  make test-auth                   - Test Firebase authentication"
	@echo "  make check-auth                  - Test if deployed service requires auth"
	@echo "  make deploy-gcloud              - Deploy agent with Firebase authentication using gcloud run deploy"
	@echo "  make deploy-staging             - Deploy staging service (open access for testing)"
	@echo "  make deploy-production          - Deploy production service (Firebase auth required)"
	@echo "  make test-agent                  - Test agent with authentication"
	@echo "  make logs                        - View recent Cloud Run logs"
	@echo ""
	@echo "ENHANCED WORKFLOW NOTE:"
	@echo "All deployments now verify and enforce the complete video generation workflow:"
	@echo "1. Guide Agent Analysis"
	@echo "2. Search Agent Research"
	@echo "3. Prompt Writer Composition"
	@echo "4. Video Generator Production"
	@echo ""
	@echo "AUTHENTICATION NOTE:"
	@echo "When deploying, answer 'N' to 'Allow unauthenticated invocations?' to enable authentication"