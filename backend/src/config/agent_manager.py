"""
Agent configuration manager for Perplexity OSS.

Handles automatic agent creation and ID storage to reduce setup friction.
Priority order: ENV vars → config file → auto-create agents
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import httpx

# Import fcntl only on Unix systems
if sys.platform != "win32":
    import fcntl

# Import agent configurations
from llm.agent_config import (
    ANSWER_GENERATION_AGENT,
    QUERY_PLANNING_AGENT,
    QUERY_REPHRASE_AGENT,
    SEARCH_QUERY_AGENT,
    RELATED_QUESTIONS_AGENT,
    AGENT_VERSION,
)

# Config file location (Docker volume mount point)
CONFIG_DIR = Path(os.getenv("AGENT_CONFIG_DIR", "/app/config"))
CONFIG_FILE = CONFIG_DIR / "agents.json"

# Agent role mapping
AGENT_CONFIGS = {
    "answer_generation": ANSWER_GENERATION_AGENT,
    "query_planning": QUERY_PLANNING_AGENT,
    "query_rephrase": QUERY_REPHRASE_AGENT,
    "search_query": SEARCH_QUERY_AGENT,
    "related_questions": RELATED_QUESTIONS_AGENT,
}

# Environment variable mapping
ENV_VAR_MAP = {
    "answer_generation": "LYZR_ANSWER_GENERATION_AGENT_ID",
    "query_planning": "LYZR_QUERY_PLANNING_AGENT_ID",
    "query_rephrase": "LYZR_QUERY_REPHRASE_AGENT_ID",
    "search_query": "LYZR_SEARCH_QUERY_AGENT_ID",
    "related_questions": "LYZR_RELATED_QUESTIONS_AGENT_ID",
}


class AgentConfigManager:
    """Manages agent configuration with auto-creation support."""

    def __init__(self, api_key: str = None, api_base: str = None):
        self.api_key = api_key or os.getenv("LYZR_API_KEY")
        self.api_base = api_base or os.getenv(
            "LYZR_API_BASE", "https://agent-prod.studio.lyzr.ai"
        )

        if not self.api_key:
            raise ValueError("LYZR_API_KEY is required for agent management")

        # Ensure config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def load_from_env(self) -> Optional[Dict[str, str]]:
        """
        Load agent IDs from environment variables.
        Returns None if any required agent ID is missing.
        """
        agent_ids = {}
        for role, env_var in ENV_VAR_MAP.items():
            agent_id = os.getenv(env_var, "").strip()
            # Skip if empty, None, or placeholder value
            if not agent_id or agent_id.startswith("your_") or agent_id == "":
                # Missing or placeholder value - need to check all before returning None
                return None
            agent_ids[role] = agent_id

        print("✓ Loaded agent IDs from environment variables")
        return agent_ids

    def load_from_file(self) -> Optional[Dict[str, str]]:
        """Load agent IDs from config file if it exists."""
        if not CONFIG_FILE.exists():
            return None

        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            agent_ids = config.get("agent_ids", {})

            # Validate we have all required agents
            if set(agent_ids.keys()) >= set(ENV_VAR_MAP.keys()):
                print(f"✓ Loaded agent IDs from config file: {CONFIG_FILE}")
                return agent_ids
            else:
                print(f"⚠ Config file incomplete, missing agents")
                return None

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠ Error reading config file: {e}")
            return None

    def get_stored_version(self) -> Optional[str]:
        """Get the version of agents stored in config file."""
        if not CONFIG_FILE.exists():
            return None

        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            return config.get("version")
        except Exception as e:
            print(f"⚠ Error reading version from config: {e}")
            return None

    def needs_update(self, agents_exist: bool = True) -> bool:
        """
        Check if agents need to be updated based on version.
        
        Args:
            agents_exist: If True, agents already exist (from config/env), so missing version means update needed.
                         If False, agents don't exist yet, so missing version means creation needed (not update).
        
        Returns:
            True if agents need updating, False otherwise
        """
        import os
        stored_version = self.get_stored_version()
        # Read version directly from environment to ensure we get the latest value
        # Fallback to module constant if env var not set
        current_version = os.getenv("AGENT_VERSION", AGENT_VERSION)
        
        if not stored_version:
            if agents_exist:
                # No version stored but agents exist (backwards compatibility case)
                # This means agents were created before version tracking was added
                # We should update them to ensure they have the latest configuration
                print(f"📦 No version field found in config file (backwards compatibility)")
                print(f"   Agents exist but version is missing - will update to version {current_version}")
                print(f"   This ensures agents have the latest configuration")
                return True
            else:
                # No version stored and agents don't exist - need creation not update
                return False

        if stored_version != current_version:
            print(f"📦 Agent version changed: {stored_version} -> {current_version}")
            print(f"   Agents will be updated")
            return True

        print(f"✓ Agent version matches: {current_version} (no update needed)")
        return False

    def save_to_file(self, agent_ids: Dict[str, str], version: str = None) -> None:
        """
        Save agent IDs to config file with atomic write.
        Uses file locking to prevent race conditions.
        """
        config_data = {
            "agent_ids": agent_ids,
            "version": version or AGENT_VERSION,
            "created_at": datetime.utcnow().isoformat(),
            "api_base": self.api_base,
            "note": "Auto-generated by Perplexity OSS. Do not edit manually unless necessary.",
        }

        # Write to temporary file first
        temp_file = CONFIG_FILE.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                # Lock file during write (Unix only, Windows doesn't need this)
                if sys.platform != "win32":
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)

                json.dump(config_data, f, indent=2)

                if sys.platform != "win32":
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Atomic replace
            temp_file.replace(CONFIG_FILE)
            print(f"✓ Saved agent IDs to {CONFIG_FILE}")

        except Exception as e:
            print(f"✗ Error saving config file: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    async def create_agent(
        self, role: str, config: Dict, retry_count: int = 3
    ) -> str:
        """
        Create a single agent via Lyzr API.
        Returns the agent ID.
        """
        url = f"{self.api_base}/v3/agents/"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

        # Build payload from config
        # Note: agent_config.py uses different keys than API expects
        payload = {
            "name": config["name"],
            "description": config["description"],
            "agent_role": config.get("agent_role", ""),
            "agent_goal": config.get("agent_goal", ""),
            "agent_instructions": config["agent_instructions"],
            "provider_id": config["provider_id"],
            "model": config["model"],
            "temperature": float(config["temperature"]),
            "top_p": float(config["top_p"]),
            "llm_credential_id": config["llm_credential_id"],
            "features": config.get("features", []),
            "response_format": config.get("response_format", {}),
            "store_messages": config.get("store_messages", True),
            "file_output": config.get("file_output", False),
        }

        print(f"Creating {role} agent: {config['name']}...")

        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()

                    result = response.json()
                    print(f"API Response for {role}: {result}")

                    # Handle different response structures
                    if "id" in result:
                        agent_id = str(result["id"])
                    elif "agent_id" in result:
                        agent_id = str(result["agent_id"])
                    elif isinstance(result, dict) and "data" in result and "id" in result["data"]:
                        agent_id = str(result["data"]["id"])
                    else:
                        raise Exception(f"Could not find agent ID in response: {result}")

                    print(f"✓ Created {role} agent with ID: {agent_id}")
                    return agent_id

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < retry_count - 1:
                    # Rate limited, retry with backoff
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limited, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"✗ Error creating {role} agent: {e.response.text}")
                    raise

            except Exception as e:
                print(f"✗ Error creating {role} agent: {e}")
                raise

        raise Exception(f"Failed to create {role} agent after {retry_count} attempts")

    async def update_agent(
        self, role: str, agent_id: str, config: Dict, retry_count: int = 3
    ) -> str:
        """
        Update an existing agent via Lyzr API using PUT.
        Returns the agent ID.
        """
        # Update endpoint works WITHOUT trailing slash (405 error with trailing slash)
        url = f"{self.api_base}/v3/agents/{agent_id}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }
        
        print(f"   Updating {role} agent (ID: {agent_id})...")
        print(f"   URL: {url}")
        print(f"   Method: PUT")

        # Build payload from config (same as create)
        payload = {
            "name": config["name"],
            "description": config["description"],
            "agent_role": config.get("agent_role", ""),
            "agent_goal": config.get("agent_goal", ""),
            "agent_instructions": config["agent_instructions"],
            "provider_id": config["provider_id"],
            "model": config["model"],
            "temperature": float(config["temperature"]),
            "top_p": float(config["top_p"]),
            "llm_credential_id": config["llm_credential_id"],
            "features": config.get("features", []),
            "response_format": config.get("response_format", {}),
            "store_messages": config.get("store_messages", True),
            "file_output": config.get("file_output", False),
        }

        print(f"Updating {role} agent (ID: {agent_id}): {config['name']}...")

        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.put(url, headers=headers, json=payload)
                    response.raise_for_status()

                    result = response.json()
                    print(f"✓ Updated {role} agent successfully")
                    return agent_id

            except httpx.HTTPStatusError as e:
                error_text = e.response.text if hasattr(e.response, 'text') else str(e.response.content)
                print(f"✗ HTTP Error {e.response.status_code} updating {role} agent:")
                print(f"   Response: {error_text}")
                
                if e.response.status_code == 429 and attempt < retry_count - 1:
                    # Rate limited, retry with backoff
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limited, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise

            except Exception as e:
                print(f"✗ Error updating {role} agent: {e}")
                raise

        raise Exception(f"Failed to update {role} agent after {retry_count} attempts")

    async def update_all_agents(self, agent_ids: Dict[str, str]) -> Dict[str, str]:
        """
        Update all agents via Lyzr API.
        Returns the same dict (IDs don't change, only config updates).
        """
        print("\n" + "=" * 60)
        print("🔄 Updating Lyzr agents to new version...")
        print("=" * 60 + "\n")

        for role, agent_id in agent_ids.items():
            try:
                config = AGENT_CONFIGS[role]
                await self.update_agent(role, agent_id, config)
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            except Exception as e:
                print(f"✗ Failed to update {role} agent: {e}")
                print(f"   Continuing with other agents...")

        print("\n" + "=" * 60)
        print("✓ Agent update completed!")
        print("=" * 60 + "\n")

        return agent_ids

    async def create_all_agents(self) -> Dict[str, str]:
        """
        Create all required agents via Lyzr API.
        Returns a dict mapping role -> agent_id.
        """
        print("\n" + "=" * 60)
        print("🤖 Auto-creating Lyzr agents for Perplexity OSS...")
        print("=" * 60 + "\n")

        agent_ids = {}

        for role, config in AGENT_CONFIGS.items():
            try:
                agent_id = await self.create_agent(role, config)
                agent_ids[role] = agent_id
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            except Exception as e:
                print(f"✗ Failed to create {role} agent: {e}")
                # Clean up any agents we created
                print("Rolling back agent creation...")
                # TODO: Could add cleanup logic here if needed
                raise Exception(
                    f"Agent creation failed for {role}. Please check your API key and try again."
                )

        print("\n" + "=" * 60)
        print("✓ All agents created successfully!")
        print("=" * 60 + "\n")

        return agent_ids

    async def ensure_agents_exist(self) -> Dict[str, str]:
        """
        Ensure all required agents exist and are up-to-date.
        Priority: ENV vars → config file (check version) → auto-create

        Returns a dict mapping role -> agent_id.
        """
        # Import here to ensure env vars are loaded
        import os
        env_version = os.getenv("AGENT_VERSION", "NOT SET IN ENV")
        # Use env version if available, otherwise fallback to module constant
        effective_version = env_version if env_version != "NOT SET IN ENV" else AGENT_VERSION
        
        print(f"\n{'='*70}")
        print(f"🔍 AGENT UPDATE CHECK - NEW CODE VERSION")
        print(f"{'='*70}")
        print(f"   AGENT_VERSION from code constant: {AGENT_VERSION}")
        print(f"   AGENT_VERSION from environment: {env_version}")
        print(f"   Effective version (will be used): {effective_version}")
        print(f"   Config file path: {CONFIG_FILE}")
        print(f"   Config file exists: {CONFIG_FILE.exists()}")
        
        # 1. Check environment variables first
        agent_ids_from_env = self.load_from_env()
        if agent_ids_from_env:
            print("✓ Agent IDs loaded from environment variables")
            print(f"   Found {len(agent_ids_from_env)} agents in environment")
            # Check if version changed and update if needed
            # agents_exist=True because we have agent IDs from env vars
            print(f"   Checking if update is needed...")
            if self.needs_update(agents_exist=True):
                try:
                    print("📦 Updating agents with new configuration...")
                    agent_ids = await self.update_all_agents(agent_ids_from_env)
                    # Save updated version and IDs to config file
                    self.save_to_file(agent_ids, AGENT_VERSION)
                    print("✅ Agents updated successfully with new version")
                    return agent_ids
                except Exception as e:
                    print(f"⚠️ Failed to update agents: {e}")
                    print(f"   Continuing with existing agents from environment")
                    import traceback
                    traceback.print_exc()
            else:
                # Version matches, no update needed, but save to config if not exists
                if not CONFIG_FILE.exists():
                    print("💾 Saving agent configuration to file...")
                    self.save_to_file(agent_ids_from_env, AGENT_VERSION)
            return agent_ids_from_env

        # 2. Check config file
        agent_ids = self.load_from_file()
        if agent_ids:
            print("✓ Agent IDs loaded from config file")
            print(f"   Found {len(agent_ids)} agents in config file")
            # Check if version changed and update if needed
            # agents_exist=True because we loaded agent IDs from config file
            print(f"   Checking if update is needed...")
            if self.needs_update(agents_exist=True):
                try:
                    print("📦 Updating agents with new configuration...")
                    agent_ids = await self.update_all_agents(agent_ids)
                    # Save updated version
                    self.save_to_file(agent_ids, AGENT_VERSION)
                    print("✅ Agents updated successfully with new version")
                except Exception as e:
                    print(f"⚠️ Failed to update agents: {e}")
                    print(f"   Continuing with existing agents")
                    import traceback
                    traceback.print_exc()
            return agent_ids

        # 3. Auto-create agents (with lock to prevent duplicates)
        lock_file = CONFIG_DIR / "agents.lock"

        try:
            # Create lock file
            with open(lock_file, "w") as lock:
                if sys.platform != "win32":
                    # Try to acquire exclusive lock (non-blocking)
                    try:
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        # Another process is creating agents, wait for it
                        print("⏳ Another process is creating agents, waiting...")
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)  # Blocking

                        # Check if config was created while we waited
                        agent_ids = self.load_from_file()
                        if agent_ids:
                            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                            return agent_ids

                # Double-check config doesn't exist (race condition)
                agent_ids = self.load_from_file()
                if agent_ids:
                    if sys.platform != "win32":
                        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                    return agent_ids

                # Create agents
                agent_ids = await self.create_all_agents()

                # Save to file
                self.save_to_file(agent_ids)

                if sys.platform != "win32":
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

                return agent_ids

        finally:
            # Clean up lock file
            if lock_file.exists():
                try:
                    lock_file.unlink()
                except:
                    pass

    def get_agent_id(self, role: str, agent_ids: Dict[str, str]) -> str:
        """Get a specific agent ID from the config."""
        agent_id = agent_ids.get(role)
        if not agent_id:
            raise ValueError(f"Agent ID for {role} not found in configuration")
        return agent_id


# Synchronous loading (without auto-creation)
def load_agent_config_sync(api_key: str = None, api_base: str = None) -> Optional[Dict[str, str]]:
    """
    Synchronously load agent configuration from env or file.
    Does NOT auto-create agents (use ensure_agents_exist_async for that).
    Returns None if agents need to be created.
    """
    manager = AgentConfigManager(api_key, api_base)

    # Try environment variables first
    agent_ids = manager.load_from_env()
    if agent_ids:
        return agent_ids

    # Try config file
    agent_ids = manager.load_from_file()
    if agent_ids:
        return agent_ids

    # No agents found - caller should create them
    return None


# Async function for auto-creation
async def ensure_agents_exist_async(api_key: str = None, api_base: str = None) -> Dict[str, str]:
    """
    Async function to ensure agents exist (will auto-create if needed).
    Use this at app startup or in async contexts.
    """
    manager = AgentConfigManager(api_key, api_base)
    return await manager.ensure_agents_exist()
