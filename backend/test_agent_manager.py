#!/usr/bin/env python3
"""
Test script for agent_manager functionality.
Run this to validate that agents can be created/loaded correctly.

Usage:
    python test_agent_manager.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_agent_manager():
    """Test the agent manager functionality"""
    from src.config.agent_manager import AgentConfigManager

    print("\n" + "=" * 70)
    print("Testing Agent Manager")
    print("=" * 70 + "\n")

    # Check if API key is set
    api_key = os.getenv("LYZR_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("❌ LYZR_API_KEY not set or is a placeholder")
        print("Please set LYZR_API_KEY environment variable to test")
        return False

    print(f"✓ API Key found: {api_key[:10]}...")

    # Initialize manager
    try:
        manager = AgentConfigManager(api_key=api_key)
        print("✓ AgentConfigManager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AgentConfigManager: {e}")
        return False

    # Test loading from environment
    print("\n--- Testing Environment Variable Loading ---")
    env_ids = manager.load_from_env()
    if env_ids:
        print("✓ Loaded agent IDs from environment variables:")
        for role, agent_id in env_ids.items():
            print(f"  - {role}: {agent_id}")
    else:
        print("⚠ No complete set of agent IDs in environment variables")

    # Test loading from file
    print("\n--- Testing Config File Loading ---")
    file_ids = manager.load_from_file()
    if file_ids:
        print("✓ Loaded agent IDs from config file:")
        for role, agent_id in file_ids.items():
            print(f"  - {role}: {agent_id}")
    else:
        print("⚠ No config file found or incomplete")

    # Test ensure_agents_exist (main function)
    print("\n--- Testing ensure_agents_exist() ---")
    try:
        agent_ids = await manager.ensure_agents_exist()
        print("✓ Agents loaded/created successfully:")
        for role, agent_id in agent_ids.items():
            print(f"  - {role}: {agent_id}")

        # Verify all required agents are present
        required_roles = [
            "query_rephrase",
            "answer_generation",
            "related_questions",
            "query_planning",
            "search_query",
        ]
        missing = [r for r in required_roles if r not in agent_ids]
        if missing:
            print(f"❌ Missing required agents: {missing}")
            return False

        print("✓ All required agents present")

    except Exception as e:
        print(f"❌ Failed to ensure agents exist: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test LyzrSpecializedAgents integration
    print("\n--- Testing LyzrSpecializedAgents Integration ---")
    try:
        from src.llm.lyzr_agent import LyzrSpecializedAgents

        specialized = LyzrSpecializedAgents(api_key=api_key)
        print("✓ LyzrSpecializedAgents initialized")

        # Check if agents can be retrieved
        agents_to_test = [
            ("query_rephrase", specialized.get_query_rephrase_agent),
            ("answer_generation", specialized.get_answer_generation_agent),
            ("related_questions", specialized.get_related_questions_agent),
            ("query_planning", specialized.get_query_planning_agent),
            ("search_query", specialized.get_search_query_agent),
        ]

        for name, getter in agents_to_test:
            try:
                agent = getter()
                print(f"✓ Retrieved {name} agent: {agent.agent_id}")
            except Exception as e:
                print(f"❌ Failed to retrieve {name} agent: {e}")
                return False

    except Exception as e:
        print(f"❌ Failed to test LyzrSpecializedAgents: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Run tests
    success = asyncio.run(test_agent_manager())
    sys.exit(0 if success else 1)
