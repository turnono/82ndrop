#!/usr/bin/env python3
"""
Test runner for 82ndrop project
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=Path(__file__).parent.parent)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e}")
        return False

def main():
    """Run the test suite"""
    print("🧪 82ndrop Test Suite Runner")
    print("=" * 60)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    success_count = 0
    total_tests = 0
    
    # Test commands to run
    test_commands = [
        {
            "cmd": "python -m pytest tests/unit/ -v -m unit",
            "description": "Unit Tests",
            "required": True
        },
        {
            "cmd": "python -m pytest tests/unit/test_content_safety.py -v",
            "description": "Content Safety Tests",
            "required": True
        },
        {
            "cmd": "python -m pytest tests/unit/test_custom_tools.py -v",
            "description": "Custom Tools Tests",
            "required": True
        },
        {
            "cmd": "python -m pytest tests/unit/test_agents.py -v",
            "description": "Agent System Tests",
            "required": True
        },
        {
            "cmd": "python -m pytest tests/integration/ -v -m integration --maxfail=3",
            "description": "Integration Tests",
            "required": False  # May fail if server isn't running
        },
        {
            "cmd": "python -m pytest --cov=drop_agent --cov-report=term-missing",
            "description": "Coverage Report",
            "required": False
        },
        {
            "cmd": "python -m pytest tests/ -m 'unit or integration' --tb=short",
            "description": "All Core Tests",
            "required": True
        }
    ]
    
    print(f"📋 Running {len(test_commands)} test suites...\n")
    
    for test in test_commands:
        total_tests += 1
        if run_command(test["cmd"], test["description"]):
            success_count += 1
        elif test["required"]:
            print(f"\n💥 Required test failed: {test['description']}")
            print("❌ Test suite execution stopped due to critical failure")
            sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 ALL TESTS PASSED! The 82ndrop project is ready for deployment.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - success_count} test suite(s) failed.")
        print("🔧 Please review the failures above and fix any issues.")
        sys.exit(1)

def run_specific_tests():
    """Run specific test categories"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run specific 82ndrop tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--safety", action="store_true", help="Run content safety tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (no external dependencies)")
    
    args = parser.parse_args()
    
    if args.unit:
        run_command("python -m pytest tests/unit/ -v", "Unit Tests Only")
    elif args.integration:
        run_command("python -m pytest tests/integration/ -v", "Integration Tests Only")
    elif args.safety:
        run_command("python -m pytest tests/unit/test_content_safety.py -v", "Content Safety Tests Only")
    elif args.coverage:
        run_command("python -m pytest --cov=drop_agent --cov-report=html", "Coverage Report")
    elif args.fast:
        run_command("python -m pytest -m 'unit and not external' -v", "Fast Tests Only")
    else:
        main()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_specific_tests()
    else:
        main() 