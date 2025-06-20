
include drop_agent/.env

install:
	pip install -r requirements.txt

deploy:
	@echo "[Deploy with UI + Managed] Deploying agent with UI"
	adk deploy cloud_run \
	--project=${GOOGLE_CLOUD_PROJECT} \
	--region=${GOOGLE_CLOUD_LOCATION} \
	--service_name=${AGENT_SERVICE_NAME} \
	--app_name=${APP_NAME} \
	--with_ui \
	./drop_agent


deploy-include-vertex-session-storage:
	@echo "[Deploy with UI + Managed] Deploying agent with UI and managed session service..."
	@if [ -z "${REASONING_ENGINE_ID}" ]; then \
		echo "❌ Error: REASONING_ENGINE_ID environment variable is not set."; \
		echo "Set it in your .env file or export it: export REASONING_ENGINE_ID=your-agent-engine-resource-id"; \
		exit 1; \
	fi
	adk deploy cloud_run \
	--project=${GOOGLE_CLOUD_PROJECT} \
	--region=${GOOGLE_CLOUD_LOCATION} \
	--service_name=${AGENT_SERVICE_NAME} \
	--app_name=${APP_NAME} \
	--session_db_url=agentengine://${REASONING_ENGINE_ID} \
	--with_ui \
	./drop_agent


deploy-frontend:
	cd frontend && ng build --configuration=production && firebase deploy --only hosting:82ndrop --project=${GOOGLE_CLOUD_PROJECT}