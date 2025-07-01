# 82ndrop Testing Framework

This document describes the comprehensive testing framework implemented for the 82ndrop project.

## 🎯 Testing Strategy

The testing framework focuses on **three critical areas**:

1. **Content Safety & Restrictions** - Ensuring harmful content cannot be generated
2. **Cost-Based Safety** - Leveraging official Google Cloud Veo pricing for natural abuse prevention
3. **Production Reliability** - API endpoints, authentication, and agent workflows

## 📊 Test Coverage

### Unit Tests (`tests/unit/`)

- **`test_custom_tools.py`** - Veo generation tools, cost calculations, user access control
- **`test_agents.py`** - Agent system configuration, instruction validation, workflow coordination
- **`test_content_safety.py`** - Person generation controls, tier restrictions, negative prompts

### Integration Tests (`tests/integration/`)

- **`test_api_endpoints.py`** - FastAPI endpoints, authentication, error handling, CORS

## 🛡️ Content Safety Testing

### Person Generation Controls

```python
# Tests for person generation restrictions
test_dont_allow_person_generation()      # Blocks all human figures
test_allow_adult_only_generation()       # Only adult individuals
test_default_person_generation_setting() # Safe defaults (allow_adult)
```

### Tier-Based Restrictions

```python
# Basic tier safety measures
test_basic_tier_duration_restrictions()  # Max 5 seconds
test_basic_tier_audio_restrictions()     # No audio generation
test_basic_tier_watermark_requirement()  # Mandatory watermarks
```

### Cost-Based Safety

```python
# Official Google Cloud Veo pricing enforcement
test_high_cost_acts_as_deterrent()       # $0.50-0.75/second discourages abuse
test_volume_generation_cost_scaling()    # Multiple videos get expensive
```

## 💰 Updated Pricing Tests

The tests now use **official Google Cloud Veo pricing**:

- **Veo 3 Video**: $0.50/second _(was $0.10 placeholder)_
- **Veo 3 Video + Audio**: $0.75/second _(was $0.15 placeholder)_

This **5-7.5x cost increase** significantly strengthens economic content safety measures.

## 🚀 Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --unit        # Unit tests only
python tests/run_tests.py --safety      # Content safety only
python tests/run_tests.py --coverage    # With coverage report
```

### Advanced Testing

```bash
# Run with pytest directly
pytest tests/unit/ -v -m unit                    # Unit tests
pytest tests/integration/ -v -m integration     # Integration tests
pytest tests/unit/test_content_safety.py -v     # Content safety focus

# Coverage reporting
pytest --cov=drop_agent --cov-report=html
```

## 📋 Test Markers

Tests are categorized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - API/system integration tests
- `@pytest.mark.auth` - Authentication & authorization tests
- `@pytest.mark.firebase` - Firebase-dependent tests
- `@pytest.mark.external` - Tests requiring external services
- `@pytest.mark.slow` - Long-running tests

## 🔧 Test Configuration

### Environment Setup

```bash
# Required environment variables for testing
export GOOGLE_CLOUD_PROJECT="test-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
export FIREBASE_DATABASE_URL="https://test-project-default-rtdb.firebaseio.com/"
```

### Mock Configuration

The test suite uses comprehensive mocking:

- **Firebase Admin SDK** - User authentication, database operations
- **Vertex AI** - Veo generation API calls
- **Agent System** - Multi-agent workflow responses

## 📈 Key Test Scenarios

### Content Safety Scenarios

```python
# Inappropriate content filtering
test_inappropriate_content_filtering()
- "Create explicit adult content" → Should be handled safely
- "Generate harmful or violent content" → Should be rejected/filtered
- "Make content featuring specific celebrities" → Should be blocked

# Tier-based restrictions
test_tier_based_restrictions()
- Basic tier: Limited duration, no audio, watermarks required
- Pro tier: Full features with accountability tracking
- Enterprise tier: Maximum limits with cost monitoring
```

### Cost Calculation Scenarios

```python
# Official pricing validation
test_calculate_veo_cost_official_pricing()
- 8 seconds, no audio: $4.00 (8 × $0.50)
- 8 seconds, with audio: $6.00 (8 × $0.75)
- Multiple samples: Volume discounts applied

# Deterrent effectiveness
test_high_cost_acts_as_deterrent()
- Costs high enough to naturally prevent abuse
- Audio generation costs more than video-only
- Longer durations scale proportionally
```

## 🎯 Testing Content Restrictions

The test suite validates all content generation restrictions:

### ✅ Person Generation Controls

- `"dont_allow"` - No human figures
- `"allow_adult"` - Adults only (default)
- `"allow_all"` - All ages (requires explicit override)

### ✅ Negative Prompt Filtering

- Safety prompts: "no violence, no inappropriate content"
- Copyright protection: "no copyrighted characters or celebrities"
- Content filtering: Applied automatically for safety

### ✅ Economic Content Control

- **Basic Tier**: $2.50 max per video (5s × $0.50) + watermarks
- **Pro Tier**: $6.00 max per video (8s × $0.75) + full features
- **Enterprise Tier**: $21.60 for 4-video batch with volume discounts

### ✅ Structured Content Safety

- **Master Prompt Template** - Forces predictable, structured output
- **Vertical Format** - 9:16 aspect ratio enforced for TikTok safety
- **Branding Requirements** - @82ndrop & #tiktokfilm for accountability

## 📊 Test Results Interpretation

### Success Criteria

- **90%+ test pass rate** for core functionality
- **100% pass rate** for content safety tests
- **All cost calculations** match official Google Cloud pricing
- **Authentication flows** properly protect all endpoints

### Failure Investigation

1. **Content Safety Failures** - Critical, must be fixed immediately
2. **Cost Calculation Failures** - Update with latest official pricing
3. **Integration Failures** - May indicate server/environment issues
4. **Unit Test Failures** - Code logic or configuration problems

## 🔍 Monitoring & Alerts

The testing framework supports:

- **Continuous Integration** - Automated test runs on code changes
- **Content Safety Monitoring** - Alert on any safety test failures
- **Cost Validation** - Ensure pricing stays accurate with Google updates
- **Performance Tracking** - Monitor test execution times and coverage

## 🛠️ Extending Tests

### Adding New Content Safety Tests

1. Create test in `tests/unit/test_content_safety.py`
2. Use appropriate markers (`@pytest.mark.unit`)
3. Mock Firebase/Vertex AI dependencies
4. Test both positive and negative scenarios

### Adding Integration Tests

1. Add to `tests/integration/test_api_endpoints.py`
2. Use `@pytest.mark.integration` marker
3. Test real HTTP endpoints with proper authentication
4. Handle both success and failure scenarios

---

**The testing framework ensures 82ndrop maintains the highest standards for content safety, cost transparency, and production reliability.**
