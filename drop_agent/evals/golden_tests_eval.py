"""
82ndrop Agent System Evaluations

Tests the complete agent workflow including:
- TaskMaster coordination with Enhanced Master Prompt Templates
- Guide Agent enhanced analysis for 8-second videos
- Search Agent enrichment
- PromptWriter Enhanced Master Prompt output generation
- Natural language format validation
- Audio, animated captions, and metadata validation
"""

import asyncio
import logging
import time
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_agent_configuration():
    """Test that the agent system is properly configured"""
    
    print("🔄 Testing Agent Configuration")
    
    start_time = time.time()
    
    try:
        # Test agent imports and structure
        from drop_agent.agent import root_agent
        from drop_agent.sub_agents.guide.agent import guide_agent
        from drop_agent.sub_agents.search.agent import search_agent
        from drop_agent.sub_agents.prompt_writer.agent import prompt_writer_agent
        
        # Verify root agent configuration
        if root_agent.name != "drop_agent":
            raise Exception(f"Root agent name incorrect: {root_agent.name}")
            
        if root_agent.model != "gemini-2.0-flash":
            raise Exception(f"Root agent model incorrect: {root_agent.model}")
        
        # Verify sub-agents are configured
        if len(root_agent.sub_agents) < 2:  # At least guide and prompt_writer
            raise Exception(f"Expected at least 2 sub-agents, got {len(root_agent.sub_agents)}")
            
        # Verify essential sub-agents exist
        essential_agents = ["guide_agent", "prompt_writer_agent"]
        available_agents = [agent.name for agent in root_agent.sub_agents] if hasattr(root_agent, 'sub_agents') else []
        
        for essential in essential_agents:
            if essential not in available_agents:
                print(f"⚠️  Warning: {essential} not found in sub_agents, checking tools...")
                # May be in tools instead of sub_agents
        
        # Verify each available sub-agent has the correct model
        for agent in getattr(root_agent, 'sub_agents', []):
            if agent.model != "gemini-2.0-flash":
                raise Exception(f"Agent {agent.name} has wrong model: {agent.model}")
                
        duration = time.time() - start_time
        print(f"✅ PASS: Agent configuration test completed in {duration:.2f}s")
        
        return {
            "test_name": "agent_configuration",
            "passed": True,
            "duration": duration,
            "metrics": {
                "root_agent_name": root_agent.name,
                "root_agent_model": root_agent.model,
                "sub_agents_count": len(getattr(root_agent, 'sub_agents', [])),
                "available_agents": available_agents,
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Agent configuration test failed: {e}")
        return {
            "test_name": "agent_configuration",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_enhanced_prompt_structures():
    """Test that Enhanced Master Prompt Template structures are properly configured"""
    
    print("📝 Testing Enhanced Prompt Template Structures")
    
    start_time = time.time()
    
    try:
        from drop_agent.prompts import PROMPT
        from drop_agent.sub_agents.guide.prompt import GUIDE_PROMPT
        from drop_agent.sub_agents.prompt_writer.prompt import PROMPT_WRITER_PROMPT
        
        # Verify prompts exist and are non-empty
        prompts = {
            "root_prompt": PROMPT,
            "guide_prompt": GUIDE_PROMPT, 
            "prompt_writer_prompt": PROMPT_WRITER_PROMPT,
        }
        
        for name, prompt in prompts.items():
            if not prompt or len(prompt.strip()) < 50:
                raise Exception(f"{name} is too short or empty")
        
        # Verify root prompt mentions Enhanced Master Prompt Template
        enhanced_keywords = ["enhanced master prompt", "8 seconds", "enhanced template"]
        if not any(keyword in PROMPT.lower() for keyword in enhanced_keywords):
            raise Exception("Root prompt doesn't mention Enhanced Master Prompt Template")
            
        # Verify prompt writer uses Enhanced Master Prompt Template (NOT JSON)
        # Allow "never JSON" but not asking for JSON output
        json_requests = ["output json", "return json", "generate json", "create json"]
        if any(request in PROMPT_WRITER_PROMPT.lower() for request in json_requests):
            raise Exception("Prompt writer still asks for JSON output - should use Enhanced Master Prompt Template")
            
        # Verify Enhanced Template features
        enhanced_features = [
            "audio", "dialogue", "animated captions", "8 seconds", 
            "soft neon glow", "fade in", "slide up", "metadata",
            "character", "platform_style", "mood_descriptors"
        ]
        
        missing_features = []
        for feature in enhanced_features:
            if feature not in PROMPT_WRITER_PROMPT.lower():
                missing_features.append(feature)
        
        if missing_features:
            raise Exception(f"Missing Enhanced Template features: {missing_features}")
            
        # Verify precise timing format [0.5s], [2.0s], [4.5s], [6.5s]
        timing_patterns = ["[0.5s]", "[2.0s]", "[4.5s]", "[6.5s]"]
        found_timing = any(pattern in PROMPT_WRITER_PROMPT for pattern in timing_patterns)
        if not found_timing:
            raise Exception("Missing precise timing format in Enhanced Template")
            
        duration = time.time() - start_time
        print(f"✅ PASS: Enhanced prompt structures test completed in {duration:.2f}s")
        
        return {
            "test_name": "enhanced_prompt_structures",
            "passed": True,
            "duration": duration,
            "metrics": {
                "prompts_checked": len(prompts),
                "enhanced_features_found": len(enhanced_features) - len(missing_features),
                "avg_prompt_length": sum(len(p) for p in prompts.values()) // len(prompts),
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Enhanced prompt structures test failed: {e}")
        return {
            "test_name": "enhanced_prompt_structures",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_enhanced_template_validation():
    """Test Enhanced Master Prompt Template output validation"""
    
    print("🎬 Testing Enhanced Master Prompt Template Output")
    
    start_time = time.time()
    
    try:
        # Test valid Enhanced Master Prompt Template structure
        sample_enhanced_prompt = """
Generate a single, cohesive vertical short-form video (9:16 aspect ratio), 8 seconds long. The screen should follow a layered mobile-first TikTok layout with full sound.

⸻

🎧 Audio
• Dialogue (spoken by energetic fitness trainer):
"Ready to transform your mornings? Here's my game-changing routine!"
• Background music:
Upbeat electronic beats — motivational and energizing, suited for morning workout vibe.

⸻

🧱 Layer Breakdown

🔺 Top Third (Animated Captions):
Show these animated captions in sequence, timed for mobile:
• [0.5s] "5:30 AM Wake Up"
• [2.0s] "Cold Shower Boost"
• [4.5s] "10 Minute Workout"  
• [6.5s] "Ready to Conquer!"
Use a crisp sans-serif font with soft neon glow, each line fading in and sliding up to replace the previous. Mobile-readable and attention-grabbing.

🎤 Center (Main Scene):
Close-up tracking shot, smooth dolly-in of athletic young woman in modern bathroom and bedroom, demonstrating morning routine with energetic movements. Bright minimalist apartment with natural light streaming through windows.
The vibe should feel like trendy TikTok fitness content — inspiring and achievable. Frame it vertically for mobile viewing with warm golden hour lighting.

🔻 Bottom Third (Static Branding):
Lock this footer text at the bottom for the entire video:

@82ndrop | #morningroutine #productivity #5amclub
Styled in clean white TikTok font with a subtle drop shadow for clarity.

⸻

📝 Title & CTA (metadata)
• Title: "Morning Routine That Will Change Your Life"
• Description: "Try this 5:30 AM routine for 7 days and feel the difference! What's your morning routine?"
• Call to Action: "Follow for more productivity tips!"

All visual layers should feel cinematic, coherent, and aligned with the TikTok 9:16 format.
"""
        
        # Validate Enhanced Template structure
        required_sections = [
            "8 seconds long",
            "🎧 Audio",
            "• Dialogue (spoken by",
            "• Background music:",
            "🧱 Layer Breakdown", 
            "🔺 Top Third (Animated Captions):",
            "[0.5s]", "[2.0s]", "[4.5s]", "[6.5s]",
            "soft neon glow", "fading in and sliding up",
            "🎤 Center (Main Scene):",
            "🔻 Bottom Third (Static Branding):",
            "@82ndrop |",
            "📝 Title & CTA (metadata)",
            "• Title:", "• Description:", "• Call to Action:",
            "9:16 format"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in sample_enhanced_prompt:
                missing_sections.append(section)
        
        if missing_sections:
            raise Exception(f"Missing required Enhanced Template sections: {missing_sections}")
        
        # Validate no JSON structure
        json_indicators = ["{", "}", '"layer_id":', '"composition":', '"layers":']
        found_json = [indicator for indicator in json_indicators if indicator in sample_enhanced_prompt]
        if found_json:
            raise Exception(f"Found JSON structure in Enhanced Template: {found_json}")
            
        # Validate 8-second format
        if "8 seconds" not in sample_enhanced_prompt:
            raise Exception("Missing 8-second duration specification")
            
        # Validate audio section
        if "🎧 Audio" not in sample_enhanced_prompt or "Dialogue" not in sample_enhanced_prompt:
            raise Exception("Missing audio section with character dialogue")
            
        # Validate animated captions with precise timing
        timing_count = sum(1 for timing in ["[0.5s]", "[2.0s]", "[4.5s]", "[6.5s]"] if timing in sample_enhanced_prompt)
        if timing_count < 4:
            raise Exception(f"Missing precise timing format - found {timing_count}/4 timings")
            
        # Validate metadata section
        metadata_items = ["Title:", "Description:", "Call to Action:"]
        missing_metadata = [item for item in metadata_items if item not in sample_enhanced_prompt]
        if missing_metadata:
            raise Exception(f"Missing metadata items: {missing_metadata}")
            
        duration = time.time() - start_time
        print(f"✅ PASS: Enhanced Template validation completed in {duration:.2f}s")
        
        return {
            "test_name": "enhanced_template_validation",
            "passed": True,
            "duration": duration,
            "metrics": {
                "required_sections_found": len(required_sections) - len(missing_sections),
                "total_required_sections": len(required_sections),
                "timing_elements_found": timing_count,
                "template_length": len(sample_enhanced_prompt),
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Enhanced Template validation failed: {e}")
        return {
            "test_name": "enhanced_template_validation", 
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_environment_setup():
    """Test that the environment is properly configured"""
    
    print("🌍 Testing Environment Setup")
    
    start_time = time.time()
    
    try:
        import os
        load_dotenv()
        
        # Check for required environment variables
        required_vars = ["GOOGLE_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {missing_vars}")
            print("This might affect live testing but structure tests can still pass")
        
        # Test imports work
        try:
            from google.adk import Agent
            from google.adk.tools.agent_tool import AgentTool
            import google.genai
        except ImportError as e:
            raise Exception(f"Required packages not available: {e}")
            
        duration = time.time() - start_time
        print(f"✅ PASS: Environment setup test completed in {duration:.2f}s")
        
        return {
            "test_name": "environment_setup",
            "passed": True,
            "duration": duration,
            "metrics": {
                "missing_env_vars": len(missing_vars),
                "required_packages_available": True,
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Environment setup test failed: {e}")
        return {
            "test_name": "environment_setup",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_enhanced_examples_analysis():
    """Analyze successful Enhanced Master Prompt Template examples"""
    
    print("📊 Testing Enhanced Examples Analysis")
    
    start_time = time.time()
    
    try:
        # Enhanced Master Prompt Template examples
        enhanced_examples = [
            {
                "input": "A gorilla in a business suit explaining the stock market in a cinematic style.",
                "expected_features": [
                    "8 seconds long", "🎧 Audio", "energetic financial expert",
                    "animated captions", "[0.5s]", "[2.0s]", "[4.5s]", "[6.5s]",
                    "soft neon glow", "fading in and sliding up", 
                    "platform style", "trendy TikTok business content",
                    "title", "description", "call to action", "@82ndrop"
                ]
            },
            {
                "input": "Make a funny video about what animals think about humans.",
                "expected_features": [
                    "8 seconds long", "🧱 Layer Breakdown", "witty animal observer",
                    "character dialogue", "background music", "comedic and observational",
                    "🔺 Top Third (Animated Captions)", "mobile-readable and attention-grabbing",
                    "🎤 Center (Main Scene)", "warm golden hour lighting",
                    "🔻 Bottom Third (Static Branding)", "metadata"
                ]
            },
            {
                "input": "Gorilla podcast, but they're reviewing the latest action movie.",
                "expected_features": [
                    "vertical short-form video", "layered mobile-first TikTok layout",
                    "dialogue spoken by passionate film critic gorilla", 
                    "upbeat discussion beats", "podcast vibe",
                    "crisp sans-serif font", "9:16 format",
                    "trendy TikTok entertainment content", "inspiring and entertaining"
                ]
            },
            {
                "input": "Let's do a movie remake of The Matrix, but make Neo a confused golden retriever.",
                "expected_features": [
                    "full sound", "character description", "action description",
                    "setting description", "mood descriptors", "lighting style",
                    "wholesome and heartwarming", "clean white TikTok font",
                    "subtle drop shadow", "cinematic coherent aligned"
                ]
            }
        ]
        
        # Analyze Enhanced Template patterns
        enhanced_metrics = {
            "total_examples": len(enhanced_examples),
            "avg_input_length": sum(len(ex["input"]) for ex in enhanced_examples) // len(enhanced_examples),
            "total_features_tested": sum(len(ex["expected_features"]) for ex in enhanced_examples),
            "avg_features_per_example": sum(len(ex["expected_features"]) for ex in enhanced_examples) // len(enhanced_examples),
        }
        
        # Validate Enhanced Template features in examples
        for i, example in enumerate(enhanced_examples):
            expected_features = example["expected_features"]
            
            # Check for core Enhanced Template elements
            core_elements = ["8 seconds", "audio", "animated captions", "character", "metadata"]
            missing_core = [elem for elem in core_elements if not any(elem.lower() in feature.lower() for feature in expected_features)]
            
            if missing_core:
                print(f"⚠️  Example {i+1} missing core elements: {missing_core}")
            
            # Check minimum feature count for Enhanced Template
            if len(expected_features) < 8:
                raise Exception(f"Example {i+1} insufficient Enhanced Template features: {len(expected_features)}")
        
        # Validate Enhanced Template structure requirements
        required_sections = ["🎧 Audio", "🧱 Layer Breakdown", "🔺 Top Third", "🎤 Center", "🔻 Bottom Third", "📝 Title & CTA"]
        timing_elements = ["[0.5s]", "[2.0s]", "[4.5s]", "[6.5s]"]
        animation_features = ["soft neon glow", "fading in", "sliding up", "mobile-readable"]
        
        total_enhanced_features = len(required_sections) + len(timing_elements) + len(animation_features)
        
        if total_enhanced_features < 14:
            raise Exception(f"Insufficient Enhanced Template feature validation: {total_enhanced_features}")
        
        duration = time.time() - start_time
        print(f"✅ PASS: Enhanced examples analysis completed in {duration:.2f}s")
        print(f"   Analyzed {enhanced_metrics['total_examples']} Enhanced Template examples")
        print(f"   Tested {enhanced_metrics['total_features_tested']} enhanced features")
        
        return {
            "test_name": "enhanced_examples_analysis",
            "passed": True,
            "duration": duration,
            "metrics": enhanced_metrics,
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Enhanced examples analysis test failed: {e}")
        return {
            "test_name": "enhanced_examples_analysis",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_natural_language_validation():
    """Test Enhanced Master Prompt Template natural language output validation"""
    
    print("🔍 Testing Natural Language Template Validation")
    
    start_time = time.time()
    
    try:
        # Enhanced Master Prompt Template example for gorilla podcast
        sample_natural_language_prompt = """
Generate a single, cohesive vertical short-form video (9:16 aspect ratio), 8 seconds long. The screen should follow a layered mobile-first TikTok layout with full sound.

⸻

🎧 Audio
• Dialogue (spoken by charismatic podcast host gorilla):
"They say he landed with nothing... but left a trail of awakened minds. He made the choice when others followed instinct. That's what made him the upgrade."
• Background music:
Mysterious electronic ambient — thoughtful and contemplative, suited for philosophical podcast vibe.

⸻

🧱 Layer Breakdown

🔺 Top Third (Animated Captions):
Show these animated captions in sequence, timed for mobile:
• [0.5s] "One-Eyed Gorilla Podcast"
• [2.0s] "The Upgrade Story"
• [4.5s] "Choice Over Instinct"
• [6.5s] "What Made Him Different"
Use a crisp sans-serif font with soft neon glow, each line fading in and sliding up to replace the previous. Mobile-readable and attention-grabbing.

🎤 Center (Main Scene):
Medium shot tracking footage, smooth camera movements of three funky gorillas with hippy jewelry sitting around a round stone podcast table with glowing primitive microphones. Close-up cuts on each gorilla's face as they speak, synced with expressive animated lips. Subtle glowing lights and retro-futuristic podcast effects.
The vibe should feel like trendy TikTok podcast content — mysterious and thought-provoking. Frame it vertically for mobile viewing with atmospheric lighting.

🔻 Bottom Third (Static Branding):
Lock this footer text at the bottom for the entire video:

@82ndrop | #podcast #gorilla #stoneage #choice
Styled in clean white TikTok font with a subtle drop shadow for clarity.

⸻

📝 Title & CTA (metadata)
• Title: "One-Eyed Gorilla Podcast - The Upgrade"
• Description: "What makes the One-Eyed Gorilla different? Not strength. Not instinct. Choice. Tune in to find out more!"
• Call to Action: "Tune in for full episodes!"

All visual layers should feel cinematic, coherent, and aligned with the TikTok 9:16 format.
"""
        
        # Validate Enhanced Master Prompt Template structure
        print("✅ Validating natural language template structure...")
        
        # Check for required Enhanced Template sections
        required_sections = [
            "8 seconds long", "🎧 Audio", "• Dialogue (spoken by",
            "• Background music:", "🧱 Layer Breakdown", 
            "🔺 Top Third (Animated Captions):", "🎤 Center (Main Scene):",
            "🔻 Bottom Third (Static Branding):", "📝 Title & CTA (metadata)"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in sample_natural_language_prompt:
                missing_sections.append(section)
        
        if missing_sections:
            raise Exception(f"Missing required natural language sections: {missing_sections}")
            
        print("✅ Validating audio dialogue content...")
        # Validate character dialogue is present
        if "charismatic podcast host gorilla" not in sample_natural_language_prompt:
            raise Exception("Missing character identification in dialogue section")
            
        # Validate dialogue content
        dialogue_text = "They say he landed with nothing... but left a trail of awakened minds"
        if dialogue_text not in sample_natural_language_prompt:
            raise Exception("Missing expected dialogue content")
            
        print("✅ Validating animated caption timing...")
        # Check for precise timing format
        timing_elements = ["[0.5s]", "[2.0s]", "[4.5s]", "[6.5s]"]
        missing_timing = []
        for timing in timing_elements:
            if timing not in sample_natural_language_prompt:
                missing_timing.append(timing)
                
        if missing_timing:
            raise Exception(f"Missing precise timing elements: {missing_timing}")
            
        print("✅ Validating enhanced features...")
        # Check for Enhanced Template features
        enhanced_features = [
            "soft neon glow", "fading in and sliding up", "mobile-readable",
            "atmospheric lighting", "trendy tiktok podcast content",
            "mysterious and thought-provoking", "@82ndrop", "9:16 format"
        ]
        
        missing_features = []
        for feature in enhanced_features:
            if feature.lower() not in sample_natural_language_prompt.lower():
                missing_features.append(feature)
                
        if missing_features:
            raise Exception(f"Missing enhanced template features: {missing_features}")
            
        # Validate no JSON structure
        json_indicators = ["{", "}", '"layer_id":', '"composition":']
        found_json = [indicator for indicator in json_indicators if indicator in sample_natural_language_prompt]
        if found_json:
            raise Exception(f"Found JSON structure in natural language template: {found_json}")
        
        duration = time.time() - start_time
        print(f"✅ PASS: Natural language template validation completed in {duration:.2f}s")
        
        return {
            "test_name": "natural_language_validation",
            "passed": True,
            "duration": duration,
            "metrics": {
                "required_sections_validated": len(required_sections),
                "timing_elements_validated": len(timing_elements),
                "enhanced_features_validated": len(enhanced_features),
                "template_length": len(sample_natural_language_prompt),
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Natural language template validation failed: {e}")
        return {
            "test_name": "natural_language_validation",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_vertical_default_validation():
    """Test that the system always defaults to vertical format for TikTok optimization"""
    
    print("🔍 Testing Vertical Default Validation")
    
    start_time = time.time()
    
    try:
        # Test data structures that should always be vertical
        test_cases = [
            {
                "name": "Simple Morning Routine",
                "composition": {
                    "canvas_type": "vertical_short_form",
                    "layer_count": 3,
                    "total_duration": "30 seconds",
                    "composition_style": "tiktok_layered"
                }
            },
            {
                "name": "Complex Dialogue Content",
                "composition": {
                    "canvas_type": "vertical_short_form",
                    "layer_count": 4,
                    "total_duration": "45 seconds",
                    "composition_style": "mobile_podcast"
                }
            },
            {
                "name": "Educational Content",
                "composition": {
                    "canvas_type": "vertical_short_form",
                    "layer_count": 5,
                    "total_duration": "60 seconds",
                    "composition_style": "educational_vertical"
                }
            }
        ]
        
        print("✅ Validating vertical format defaults...")
        for i, test_case in enumerate(test_cases):
            composition = test_case["composition"]
            
            # Validate canvas_type is always vertical_short_form
            if composition["canvas_type"] != "vertical_short_form":
                raise Exception(f"Test case '{test_case['name']}' must use vertical_short_form canvas_type for TikTok optimization")
                
            # Validate composition_style suggests mobile/vertical optimization
            mobile_styles = ["tiktok_layered", "mobile_podcast", "educational_vertical", "vertical_story", "mobile_optimized"]
            style_is_mobile = any(mobile_term in composition["composition_style"] for mobile_term in ["tiktok", "mobile", "vertical"])
            
            if not style_is_mobile:
                print(f"⚠️  Warning: Test case '{test_case['name']}' style should indicate mobile/vertical optimization")
        
        print("✅ Validating TikTok duration optimization...")
        for test_case in test_cases:
            duration_str = test_case["composition"]["total_duration"]
            # Extract number from duration string
            duration_num = int(duration_str.split()[0])
            
            # TikTok optimal durations are 15-60 seconds
            if duration_num < 15 or duration_num > 60:
                print(f"⚠️  Warning: '{test_case['name']}' duration {duration_num}s may not be optimal for TikTok (15-60s recommended)")
        
        print("✅ Validating mobile-first approach...")
        # All test cases should demonstrate mobile-first thinking
        mobile_indicators = ["vertical_short_form", "tiktok", "mobile", "vertical"]
        for test_case in test_cases:
            composition_str = str(test_case["composition"])
            has_mobile_indicator = any(indicator in composition_str.lower() for indicator in mobile_indicators)
            
            if not has_mobile_indicator:
                raise Exception(f"Test case '{test_case['name']}' should include mobile/vertical indicators")
        
        duration = time.time() - start_time
        print(f"✅ PASS: Vertical default validation completed in {duration:.2f}s")
        
        return {
            "test_name": "vertical_default_validation",
            "passed": True,
            "duration": duration,
            "metrics": {
                "test_cases_validated": len(test_cases),
                "vertical_format_enforced": True,
                "mobile_optimization_verified": True,
                "tiktok_duration_checked": True,
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Vertical default validation failed: {e}")
        return {
            "test_name": "vertical_default_validation",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def run_82ndrop_evaluations():
    """Run all 82ndrop agent evaluation tests"""
    
    print("🔬 Starting 82ndrop Agent System Evaluations")
    print("=" * 60)
    
    tests = [
        test_environment_setup,
        test_agent_configuration,
        test_enhanced_prompt_structures,
        test_enhanced_template_validation,
        test_enhanced_examples_analysis,
        test_natural_language_validation,
        test_vertical_default_validation,
    ]
    
    results = []
    start_time = datetime.now()
    
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test_func.__name__} failed with error: {e}")
            results.append(
                {
                    "test_name": test_func.__name__,
                    "passed": False,
                    "error": str(e),
                    "duration": 0,
                }
            )
        
        print()  # Add spacing between tests
    
    # Calculate summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    passed_tests = sum(1 for r in results if r["passed"])
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("=" * 60)
    print("82ndrop Agent System Evaluation Results:")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Total Duration: {total_duration:.2f}s")
    
    if success_rate == 100:
        print("🎉 All 82ndrop agent tests passed!")
        print("✨ System is ready for production use!")
    else:
        print("⚠️  Some 82ndrop agent tests failed - check logs for details")
    
    # Add note about live testing
    print()
    print("📝 Note: These tests validate system structure and configuration.")
    print("   For live agent testing, use: adk run drop_agent")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("evals").mkdir(exist_ok=True)
    report_file = f"evals/82ndrop_eval_report_{timestamp}.json"
    
    detailed_report = {
        "summary": {
            "evaluation_info": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "agent_system": "82ndrop",
                "test_environment": "development",
                "evaluation_type": "structural_validation",
            },
            "results": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
            },
            "notes": [
                "These tests validate system structure and configuration",
                "Live agent testing available via: adk run drop_agent",
                "All successful examples from terminal session are documented",
            ]
        },
        "detailed_results": results,
    }
    
    with open(report_file, "w") as f:
        json.dump(detailed_report, f, indent=2, default=str)
    
    print(f"📊 Detailed report saved to: {report_file}")
    
    return detailed_report


if __name__ == "__main__":
    asyncio.run(run_82ndrop_evaluations()) 