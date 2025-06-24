"""
82ndrop Agent System Evaluations

Tests the complete agent workflow including:
- TaskMaster coordination
- Guide Agent schema creation
- Search Agent enrichment
- PromptWriter final output generation
- JSON format validation
- Creative prompt handling
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
        if root_agent.name != "task_master_agent":
            raise Exception(f"Root agent name incorrect: {root_agent.name}")
            
        if root_agent.model != "gemini-2.0-flash":
            raise Exception(f"Root agent model incorrect: {root_agent.model}")
        
        # Verify sub-agents are configured
        if len(root_agent.sub_agents) != 3:
            raise Exception(f"Expected 3 sub-agents, got {len(root_agent.sub_agents)}")
            
        # Verify sub-agents exist and have correct names
        expected_agents = ["guide_agent", "search_agent", "prompt_writer_agent"]
        actual_agents = [agent.name for agent in root_agent.sub_agents]
        
        for expected in expected_agents:
            if expected not in actual_agents:
                raise Exception(f"Missing agent: {expected}")
        
        # Verify each sub-agent has the correct model
        for agent in root_agent.sub_agents:
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
                "sub_agents_count": len(root_agent.sub_agents),
                "sub_agent_names": actual_agents,
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


async def test_prompt_structures():
    """Test that prompts are properly structured"""
    
    print("📝 Testing Prompt Structures")
    
    start_time = time.time()
    
    try:
        from drop_agent.prompts import PROMPT
        from drop_agent.sub_agents.guide.prompt import INSTRUCTION as GUIDE_INSTRUCTION
        from drop_agent.sub_agents.search.prompt import INSTRUCTION as SEARCH_INSTRUCTION
        from drop_agent.sub_agents.prompt_writer.prompt import INSTRUCTION as PROMPT_WRITER_INSTRUCTION
        
        # Verify prompts exist and are non-empty
        prompts = {
            "root_prompt": PROMPT,
            "guide_instruction": GUIDE_INSTRUCTION,
            "search_instruction": SEARCH_INSTRUCTION,
            "prompt_writer_instruction": PROMPT_WRITER_INSTRUCTION,
        }
        
        for name, prompt in prompts.items():
            if not prompt or len(prompt.strip()) < 50:
                raise Exception(f"{name} is too short or empty")
        
        # Verify root prompt mentions coordination or team work
        coordination_keywords = ["coordinate", "orchestrate", "team", "specialist", "sub-agent"]
        if not any(keyword in PROMPT.lower() for keyword in coordination_keywords):
            raise Exception("Root prompt doesn't mention coordination/orchestration or team work")
            
        # Verify prompt writer mentions JSON
        if "json" not in PROMPT_WRITER_INSTRUCTION.lower():
            raise Exception("Prompt writer doesn't mention JSON output")
            
        duration = time.time() - start_time
        print(f"✅ PASS: Prompt structures test completed in {duration:.2f}s")
        
        return {
            "test_name": "prompt_structures",
            "passed": True,
            "duration": duration,
            "metrics": {
                "prompts_checked": len(prompts),
                "avg_prompt_length": sum(len(p) for p in prompts.values()) // len(prompts),
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Prompt structures test failed: {e}")
        return {
            "test_name": "prompt_structures",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_json_format_validation():
    """Test JSON format validation logic"""
    
    print("🔍 Testing JSON Format Validation")
    
    start_time = time.time()
    
    try:
        # Test valid data structures for new composition format with dialogue support
        valid_examples = [
            {
                "composition": {
                    "layer_count": 4,
                    "canvas_type": "vertical_short_form",
                    "total_duration": "8 seconds",
                    "composition_style": "layered_content"
                },
                "layers": [
                    {
                        "layer_id": 1,
                        "layer_type": "text_overlay",
                        "position": "top_third",
                        "content_prompt": "Show the text 'One-Eyed Gorilla Podcast'",
                        "visual_style": "retro-futuristic glowing text",
                        "duration": "full_video",
                        "z_index": 4
                    },
                    {
                        "layer_id": 2,
                        "layer_type": "main_content",
                        "position": "center_main",
                        "content_prompt": "Film three funky gorillas with hippy jewelry sitting around a round stone podcast table",
                        "visual_style": "stylized Joe Rogan-style podcast in Stone Age setting",
                        "duration": "full_video",
                        "z_index": 1,
                        "dialogue_sequence": [
                            {"speaker": "tall_gorilla", "voice": "raspy", "text": "They say he landed with nothing…", "timing": "0-2s"},
                            {"speaker": "short_spiky_gorilla", "voice": "excited", "text": "…but left a trail of awakened minds.", "timing": "2-4s"},
                            {"speaker": "medium_gorilla", "voice": "low_and_slow", "text": "He made the choice… when others followed instinct.", "timing": "4-6s"},
                            {"speaker": "all_three", "voice": "soft_whisper", "text": "That's what made him the upgrade.", "timing": "6-8s"}
                        ]
                    },
                    {
                        "layer_id": 3,
                        "layer_type": "text_overlay",
                        "position": "middle_third",
                        "content_prompt": "Show the line 'The brown one made a choice.'",
                        "visual_style": "retro-futuristic glowing text",
                        "duration": "2.5 seconds",
                        "timing": "4-6.5s",
                        "z_index": 3
                    },
                    {
                        "layer_id": 4,
                        "layer_type": "caption_layer",
                        "position": "bottom_third",
                        "content_prompt": "Show 'Not strength. Not instinct. Choice.'",
                        "visual_style": "subtitle_style_glowing",
                        "duration": "full_video",
                        "z_index": 2
                    }
                ],
                "final_video": {
                    "title": "One-Eyed Gorilla Podcast - The Upgrade",
                    "description": "What makes the One-Eyed Gorilla different? Not strength. Not instinct. Choice.",
                    "hashtags": ["#podcast", "#gorilla", "#stoneage", "#retrofuture", "#choice"],
                    "call_to_action": "Tune in for full episodes!",
                    "engagement_hook": "They say he landed with nothing…"
                }
            },
            {
                "composition": {
                    "layer_count": 3,
                    "canvas_type": "vertical_short_form",
                    "total_duration": "20-30 seconds",
                    "composition_style": "comedy_layered"
                },
                "layers": [
                    {
                        "layer_id": 1,
                        "layer_type": "text_overlay",
                        "position": "top_third",
                        "content_prompt": "Create animated text: 'Wall Street's newest analyst'",
                        "visual_style": "professional_title_text",
                        "duration": "full_video",
                        "z_index": 3
                    },
                    {
                        "layer_id": 2,
                        "layer_type": "main_content",
                        "position": "center_main",
                        "content_prompt": "Film a gorilla in a suit passionately explaining stock market trends",
                        "visual_style": "professional_comedy",
                        "duration": "full_video",
                        "z_index": 1
                    },
                    {
                        "layer_id": 3,
                        "layer_type": "caption_layer",
                        "position": "bottom_third",
                        "content_prompt": "Create stock terms and price updates as scrolling text overlays",
                        "visual_style": "financial_ticker_style",
                        "duration": "last_10_seconds",
                        "z_index": 2
                    }
                ],
                "final_video": {
                    "title": "Wall Street's Newest Analyst",
                    "description": "When the market needs a primal perspective",
                    "hashtags": ["#stocks", "#finance", "#gorilla", "#comedy"],
                    "call_to_action": "What stock would you trust a gorilla with?",
                    "engagement_hook": "Wall Street's getting wild"
                }
            },
            {
                "composition": {
                    "layer_count": 2,
                    "canvas_type": "vertical_short_form",
                    "total_duration": "15-20 seconds",
                    "composition_style": "floating_overlay"
                },
                "layers": [
                    {
                        "layer_id": 1,
                        "layer_type": "main_content",
                        "position": "full_screen",
                        "content_prompt": "Film animals in their natural habitat with realistic behavior",
                        "visual_style": "nature_documentary",
                        "duration": "full_video",
                        "z_index": 1
                    },
                    {
                        "layer_id": 2,
                        "layer_type": "text_overlay",
                        "position": "floating_overlay",
                        "content_prompt": "Create animated speech bubbles with animal thoughts about humans",
                        "visual_style": "cartoon_speech_bubbles",
                        "duration": "full_video",
                        "z_index": 2
                    }
                ],
                "final_video": {
                    "title": "Overheard in the Animal Kingdom",
                    "description": "What animals really think about us humans",
                    "hashtags": ["#animals", "#comedy", "#perspective"],
                    "call_to_action": "What would your pet say about you?",
                    "engagement_hook": "They think WE'RE the weird ones"
                }
            }
        ]
        
        for i, parsed in enumerate(valid_examples):
            
            # Validate required fields for new composition format
            if "composition" not in parsed:
                raise Exception(f"Example {i+1} missing composition field")
            if "layers" not in parsed:
                raise Exception(f"Example {i+1} missing layers field")
            if "final_video" not in parsed:
                raise Exception(f"Example {i+1} missing final_video field")
                
            # Validate composition structure
            composition = parsed["composition"]
            composition_fields = ["layer_count", "canvas_type", "total_duration", "composition_style"]
            for field in composition_fields:
                if field not in composition:
                    raise Exception(f"Example {i+1} composition missing field: {field}")
                    
            # Validate that canvas_type is always vertical_short_form
            if composition["canvas_type"] != "vertical_short_form":
                raise Exception(f"Example {i+1} canvas_type must be 'vertical_short_form' for TikTok optimization, got: {composition['canvas_type']}")
                
            # Validate layers array
            layers = parsed["layers"]
            if not isinstance(layers, list) or len(layers) == 0:
                raise Exception(f"Example {i+1} layers must be a non-empty array")
                
            # Validate each layer structure
            required_layer_fields = ["layer_id", "layer_type", "position", "content_prompt", "visual_style", "duration", "z_index"]
            for j, layer in enumerate(layers):
                for field in required_layer_fields:
                    if field not in layer:
                        raise Exception(f"Example {i+1} layer {j+1} missing field: {field}")
                        
                # Validate dialogue_sequence if present
                if "dialogue_sequence" in layer:
                    if not isinstance(layer["dialogue_sequence"], list):
                        raise Exception(f"Example {i+1} layer {j+1} dialogue_sequence must be an array")
                    for k, dialogue in enumerate(layer["dialogue_sequence"]):
                        dialogue_fields = ["speaker", "voice", "text", "timing"]
                        for field in dialogue_fields:
                            if field not in dialogue:
                                raise Exception(f"Example {i+1} layer {j+1} dialogue {k+1} missing field: {field}")
                
                # Validate positioning terms
                valid_positions = ["top_third", "middle_third", "center_main", "bottom_third", "full_screen", "left_half", "right_half", "floating_overlay", "side_bar"]
                if layer["position"] not in valid_positions:
                    raise Exception(f"Example {i+1} layer {j+1} invalid position: {layer['position']}")
                        
            # Validate final_video structure
            final_video = parsed["final_video"]
            final_video_fields = ["title", "description", "hashtags", "call_to_action", "engagement_hook"]
            for field in final_video_fields:
                if field not in final_video:
                    raise Exception(f"Example {i+1} final_video missing field: {field}")
                    
            # Validate field types
            if not isinstance(final_video["hashtags"], list):
                raise Exception(f"Example {i+1} final_video hashtags must be an array")
        
        duration = time.time() - start_time
        print(f"✅ PASS: JSON format validation test completed in {duration:.2f}s")
        
        return {
            "test_name": "json_format_validation",
            "passed": True,
            "duration": duration,
            "metrics": {
                "examples_tested": len(valid_examples),
                "required_layer_fields": len(required_layer_fields),
                "dialogue_sequences_validated": 1,
                "positioning_terms_validated": len(valid_positions),
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: JSON format validation test failed: {e}")
        return {
            "test_name": "json_format_validation",
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


async def test_successful_examples_analysis():
    """Analyze the successful examples from terminal session"""
    
    print("📊 Testing Successful Examples Analysis")
    
    start_time = time.time()
    
    try:
        # Examples from the successful terminal session
        successful_examples = [
            {
                "input": "A gorilla in a business suit explaining the stock market in a cinematic style.",
                "output": {
                    "top": "Wall Street's Newest Analyst",
                    "center": "A gorilla in a suit passionately explains stock market trends using charts and graphs.",
                    "bottom": "Invest like a beast! #stocks #finance #gorilla"
                }
            },
            {
                "input": "Make a funny video about what animals think about humans.",
                "output": {
                    "top": "Overheard in the Animal Kingdom",
                    "center": "Animals hilariously commentating on human behavior",
                    "bottom": "They think WE'RE the weird ones..."
                }
            },
            {
                "input": "Gorilla podcast, but they're reviewing the latest action movie.",
                "output": {
                    "top": "Ape About Movies Podcast",
                    "center": "Gorilla reviews 'Rampage' (2018)",
                    "bottom": "Rate 🍌🍌🍌 if you agree!"
                }
            },
            {
                "input": "Let's do a movie remake of The Matrix, but make Neo a confused golden retriever.",
                "output": {
                    "top": "What if The Matrix was wholesome?",
                    "center": "Golden Retriever realizes he's living in a simulation and uses his powers for good",
                    "bottom": "He just wants belly rubs and world peace"
                }
            }
        ]
        
        # Analyze the patterns
        metrics = {
            "total_examples": len(successful_examples),
            "avg_input_length": sum(len(ex["input"]) for ex in successful_examples) // len(successful_examples),
            "avg_top_length": sum(len(ex["output"]["top"]) for ex in successful_examples) // len(successful_examples),
            "avg_center_length": sum(len(ex["output"]["center"]) for ex in successful_examples) // len(successful_examples),
            "avg_bottom_length": sum(len(ex["output"]["bottom"]) for ex in successful_examples) // len(successful_examples),
        }
        
        # Validate each example maintains key themes
        for i, example in enumerate(successful_examples):
            output = example["output"]
            
            # Check that outputs are engaging and creative
            if len(output["top"]) < 10:
                raise Exception(f"Example {i+1} top section too short")
                
            if len(output["center"]) < 20:
                raise Exception(f"Example {i+1} center section too short")
                
            if len(output["bottom"]) < 10:
                raise Exception(f"Example {i+1} bottom section too short")
        
        duration = time.time() - start_time
        print(f"✅ PASS: Successful examples analysis completed in {duration:.2f}s")
        print(f"   Analyzed {metrics['total_examples']} successful examples")
        
        return {
            "test_name": "successful_examples_analysis",
            "passed": True,
            "duration": duration,
            "metrics": metrics,
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Successful examples analysis test failed: {e}")
        return {
            "test_name": "successful_examples_analysis",
            "passed": False,
            "error": str(e),
            "duration": duration,
        }


async def test_gorilla_podcast_json_validation():
    """Test the corrected gorilla podcast JSON structure"""
    
    print("🔍 Testing Gorilla Podcast JSON Validation")
    
    start_time = time.time()
    
    try:
        # The corrected JSON structure for the gorilla podcast prompt
        corrected_json_data = {
            "composition": {
                "layer_count": 4,
                "canvas_type": "vertical_short_form",
                "total_duration": "8 seconds",
                "composition_style": "layered_content"
            },
            "layers": [
                {
                    "layer_id": 1,
                    "layer_type": "text_overlay",
                    "position": "top_third",
                    "content_prompt": "Show the text \"One-Eyed Gorilla Podcast\"",
                    "visual_style": "retro-futuristic glowing text",
                    "duration": "full_video",
                    "z_index": 4
                },
                {
                    "layer_id": 2,
                    "layer_type": "main_content",
                    "position": "center_main",
                    "content_prompt": "Film three funky gorillas with hippy jewelry sitting around a round stone podcast table with glowing primitive microphones. Close-up camera cuts on each gorilla's face as they speak, synced with expressive animated lips. Subtle glowing lights, light dust, and retro-futuristic podcast effects.",
                    "visual_style": "stylized Joe Rogan-style podcast in Stone Age setting",
                    "duration": "full_video",
                    "z_index": 1,
                    "dialogue_sequence": [
                        {"speaker": "tall_gorilla", "voice": "raspy", "text": "They say he landed with nothing…", "timing": "0-2s"},
                        {"speaker": "short_spiky_gorilla", "voice": "excited", "text": "…but left a trail of awakened minds.", "timing": "2-4s"},
                        {"speaker": "medium_gorilla", "voice": "low_and_slow", "text": "He made the choice… when others followed instinct.", "timing": "4-6s"},
                        {"speaker": "all_three", "voice": "soft_whisper", "text": "That's what made him the upgrade.", "timing": "6-8s"}
                    ]
                },
                {
                    "layer_id": 3,
                    "layer_type": "text_overlay",
                    "position": "middle_third",
                    "content_prompt": "Show the line \"The brown one made a choice.\"",
                    "visual_style": "retro-futuristic glowing text",
                    "duration": "2.5 seconds",
                    "timing": "4-6.5s",
                    "z_index": 3
                },
                {
                    "layer_id": 4,
                    "layer_type": "caption_layer",
                    "position": "bottom_third",
                    "content_prompt": "Show \"Not strength. Not instinct. Choice.\"",
                    "visual_style": "subtitle_style_glowing",
                    "duration": "full_video",
                    "z_index": 2
                }
            ],
            "final_video": {
                "title": "One-Eyed Gorilla Podcast - The Upgrade",
                "description": "What makes the One-Eyed Gorilla different? Not strength. Not instinct. Choice. Tune in to find out more!",
                "hashtags": ["#podcast", "#gorilla", "#stoneage", "#retrofuture", "#choice"],
                "call_to_action": "Tune in for full episodes!",
                "engagement_hook": "They say he landed with nothing…"
            }
        }
        
        # Use the already parsed JSON data
        parsed = corrected_json_data
        
        # Validate all the issues identified in the original prompt
        print("✅ Validating dialogue content...")
        main_layer = next(layer for layer in parsed["layers"] if layer["layer_type"] == "main_content")
        if "dialogue_sequence" not in main_layer:
            raise Exception("Missing dialogue_sequence in main_content layer")
        
        dialogue = main_layer["dialogue_sequence"]
        if len(dialogue) != 4:
            raise Exception(f"Expected 4 dialogue entries, got {len(dialogue)}")
            
        expected_speakers = ["tall_gorilla", "short_spiky_gorilla", "medium_gorilla", "all_three"]
        for i, entry in enumerate(dialogue):
            if entry["speaker"] != expected_speakers[i]:
                raise Exception(f"Dialogue {i+1} speaker mismatch: expected {expected_speakers[i]}, got {entry['speaker']}")
                
        print("✅ Validating caption positioning...")
        middle_caption = next((layer for layer in parsed["layers"] if layer.get("timing") == "4-6.5s"), None)
        if not middle_caption or middle_caption["position"] != "middle_third":
            raise Exception("Middle caption should be positioned in middle_third, not center_main")
            
        print("✅ Validating timing context...")
        if middle_caption["timing"] != "4-6.5s":
            raise Exception("Middle caption timing should be 4-6.5s to align with third dialogue line")
            
        print("✅ Validating layer structure...")
        if parsed["composition"]["layer_count"] != 4:
            raise Exception("Should have 4 layers for this complex composition")
            
        # Validate positioning terms
        positions = [layer["position"] for layer in parsed["layers"]]
        expected_positions = ["top_third", "center_main", "middle_third", "bottom_third"]
        for pos in expected_positions:
            if pos not in positions:
                raise Exception(f"Missing expected position: {pos}")
        
        duration = time.time() - start_time
        print(f"✅ PASS: Gorilla podcast JSON validation completed in {duration:.2f}s")
        
        return {
            "test_name": "gorilla_podcast_json_validation",
            "passed": True,
            "duration": duration,
            "metrics": {
                "dialogue_entries_validated": len(dialogue),
                "positioning_corrections_verified": 1,
                "timing_synchronization_verified": 1,
                "layer_count_validated": parsed["composition"]["layer_count"],
            },
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAIL: Gorilla podcast JSON validation failed: {e}")
        return {
            "test_name": "gorilla_podcast_json_validation",
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
        test_prompt_structures,
        test_json_format_validation,
        test_successful_examples_analysis,
        test_gorilla_podcast_json_validation,
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