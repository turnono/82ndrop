"""
Test configuration and fixtures for 82ndrop project
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, AsyncGenerator
import firebase_admin
from firebase_admin import credentials, auth, db
from google.adk import Agent
from google.adk.tools import FunctionTool

# Test configuration
TEST_PROJECT_ID = "test-project"
TEST_USER_ID = "test-user-123"
TEST_SESSION_ID = "test-session-456"
TEST_AUTH_TOKEN = "test-auth-token"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_firebase_admin():
    """Mock Firebase Admin SDK"""
    with patch('firebase_admin.initialize_app') as mock_init:
        with patch('firebase_admin.auth.get_user') as mock_get_user:
            with patch('firebase_admin.db.reference') as mock_db_ref:
                # Mock user with permissions
                mock_user = Mock()
                mock_user.custom_claims = {
                    "can_generate_video": True,
                    "access_level": "pro",
                    "agent_access": True
                }
                mock_get_user.return_value = mock_user
                
                # Mock database reference
                mock_ref = Mock()
                mock_ref.set.return_value = None
                mock_ref.update.return_value = None
                mock_ref.get.return_value = {"status": "pending"}
                mock_db_ref.return_value = mock_ref
                
                yield {
                    "init_app": mock_init,
                    "get_user": mock_get_user,
                    "db_ref": mock_db_ref,
                    "user": mock_user,
                    "ref": mock_ref
                }

@pytest.fixture
def mock_vertex_ai():
    """Mock Vertex AI services"""
    with patch('google.cloud.aiplatform.init') as mock_init:
        with patch('google.cloud.aiplatform.Model') as mock_model:
            mock_model.predict.return_value = Mock()
            yield {
                "init": mock_init,
                "model": mock_model
            }

@pytest.fixture
def mock_gemini_agent():
    """Mock Gemini agent for testing"""
    agent = Mock(spec=Agent)
    agent.name = "test_agent"
    agent.model = "gemini-2.0-flash"
    agent.run = AsyncMock(return_value="Test response")
    return agent

@pytest.fixture
def sample_video_prompt():
    """Sample video prompt for testing"""
    return {
        "user_input": "Create a video about morning routines",
        "expected_output": {
            "top_third": "Morning Routine That Changed My Life",
            "center_scene": "A young professional in a bright, minimalist bedroom",
            "bottom_third": ["Wake up at 5:30 AM", "10 minutes meditation", "Cold shower + coffee"]
        }
    }

@pytest.fixture
def sample_veo_job_data():
    """Sample Veo job data for testing"""
    return {
        "jobId": "test-job-123",
        "status": "pending",
        "prompt": "Test video prompt",
        "userId": TEST_USER_ID,
        "userTier": "pro",
        "model": "veo-3.0-generate-preview",
        "parameters": {
            "aspectRatio": "9:16",
            "durationSeconds": 8,
            "sampleCount": 1,
            "personGeneration": "allow_adult",
            "generateAudio": True
        }
    }

@pytest.fixture
def auth_headers():
    """Authentication headers for API testing"""
    return {
        "Authorization": f"Bearer {TEST_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def mock_environment():
    """Mock environment variables"""
    env_vars = {
        "GOOGLE_CLOUD_PROJECT": TEST_PROJECT_ID,
        "GOOGLE_CLOUD_LOCATION": "us-central1",
        "FIREBASE_DATABASE_URL": f"https://{TEST_PROJECT_ID}-default-rtdb.firebaseio.com/",
        "LOCAL_DEV_TOKEN": "test-dev-token"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
async def mock_agent_system():
    """Mock complete agent system"""
    # Mock root agent
    root_agent = Mock(spec=Agent)
    root_agent.name = "task_master_agent"
    root_agent.model = "gemini-2.0-flash"
    root_agent.run = AsyncMock(return_value="Generated video prompt")
    
    # Mock sub-agents
    guide_agent = Mock(spec=Agent)
    guide_agent.name = "guide_agent"
    guide_agent.run = AsyncMock(return_value="Vertical composition analysis")
    
    search_agent = Mock(spec=Agent)
    search_agent.name = "search_agent"
    search_agent.run = AsyncMock(return_value="Trending hashtags and viral formats")
    
    prompt_writer_agent = Mock(spec=Agent)
    prompt_writer_agent.name = "prompt_writer_agent"
    prompt_writer_agent.run = AsyncMock(return_value="Natural language Master Prompt")
    
    root_agent.sub_agents = [guide_agent, search_agent, prompt_writer_agent]
    
    return {
        "root_agent": root_agent,
        "guide_agent": guide_agent,
        "search_agent": search_agent,
        "prompt_writer_agent": prompt_writer_agent
    }

@pytest.fixture
def cost_calculation_data():
    """Test data for cost calculations"""
    return {
        "official_veo_pricing": {
            "veo_3_video": 0.50,  # $0.50/second from official Google pricing
            "veo_3_video_audio": 0.75,  # $0.75/second from official Google pricing
            "veo_2_video": 0.50,  # $0.50/second from official Google pricing
        },
        "test_scenarios": [
            {
                "duration": 8,
                "samples": 1,
                "audio": False,
                "expected_cost": 4.00  # 8 seconds * $0.50
            },
            {
                "duration": 8,
                "samples": 1,
                "audio": True,
                "expected_cost": 6.00  # 8 seconds * $0.75
            },
            {
                "duration": 5,
                "samples": 2,
                "audio": False,
                "expected_cost": 5.00  # 5 seconds * $0.50 * 2 samples
            }
        ]
    }

@pytest.fixture
def tier_config_data():
    """Test data for user tier configurations"""
    return {
        "basic": {
            "max_duration": 5,
            "audio_enabled": False,
            "max_samples": 1,
            "watermark": True
        },
        "pro": {
            "max_duration": 8,
            "audio_enabled": True,
            "max_samples": 2,
            "watermark": False
        },
        "enterprise": {
            "max_duration": 8,
            "audio_enabled": True,
            "max_samples": 4,
            "watermark": False
        }
    }

@pytest.fixture
def content_safety_test_data():
    """Test data for content safety and restrictions"""
    return {
        "person_generation_options": ["dont_allow", "allow_adult", "allow_all"],
        "safe_prompts": [
            "A professional barista making coffee in a modern cafe",
            "Time-lapse of a sunset over a city skyline",
            "A chef preparing a delicious meal in a kitchen"
        ],
        "restricted_prompts": [
            "Generate a video with explicit adult content",
            "Create content featuring a specific celebrity",
            "Make a video promoting harmful activities"
        ]
    }

# Helper functions for tests
def create_mock_response(status_code: int = 200, json_data: Dict[Any, Any] = None):
    """Create a mock HTTP response"""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = str(json_data) if json_data else ""
    return mock_response

def create_mock_firebase_user(user_id: str, custom_claims: Dict[str, Any] = None):
    """Create a mock Firebase user"""
    user = Mock()
    user.uid = user_id
    user.custom_claims = custom_claims or {"can_generate_video": True}
    return user 