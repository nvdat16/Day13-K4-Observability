"""
Prompt Versioning Script - Create and manage prompts on Langfuse
Run: python scripts/prompt_versioning.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

from langfuse import Langfuse

# Prompt configuration
PROMPT_NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
PROMPT_VERSION_1 = """You are an AI assistant for a VinAI observability lab.

Feature={{feature}}
Docs={{docs}}
Question={{message}}

Please provide a helpful, accurate response based on the provided documentation."""

PROMPT_VERSION_2 = """[SYSTEM] Observability AI Assistant - VinAI Lab

**Task**: Answer user questions using provided RAG documentation.

**Context**:
- Feature: {{feature}}
- Retrieved Docs: {{docs}}

**User Query**:
{{message}}

**Response Guidelines**:
1. Base your answer on the retrieved documentation
2. Be concise but complete
3. If information is not in docs, say so clearly"""


def get_langfuse_client() -> Langfuse:
    """Initialize Langfuse client with credentials from environment."""
    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
    )


def create_prompt_v1(client: Langfuse) -> dict:
    """Create prompt version 1 with baseline and production labels."""
    print("\n[1] Creating Prompt Version 1...")

    try:
        # Create/update prompt with version 1
        prompt = client.create_prompt(
            name=PROMPT_NAME,
            prompt=PROMPT_VERSION_1,
            labels=["baseline", "production"],
            type="text",
        )
        print(f"    Created prompt '{PROMPT_NAME}'")
        print(f"    Version: {prompt.version}")
        print(f"    Labels: baseline, production")
        return {"version": prompt.version, "labels": ["baseline", "production"]}
    except Exception as e:
        print(f"    Error: {e}")
        return {"error": str(e)}


def create_prompt_v2(client: Langfuse) -> dict:
    """Create prompt version 2 with candidate label."""
    print("\n[2] Creating Prompt Version 2...")

    try:
        # Create new version with candidate label
        prompt = client.create_prompt(
            name=PROMPT_NAME,
            prompt=PROMPT_VERSION_2,
            labels=["candidate"],
            type="text",
        )
        print(f"    Created prompt '{PROMPT_NAME}'")
        print(f"    Version: {prompt.version}")
        print(f"    Labels: candidate")
        return {"version": prompt.version, "labels": ["candidate"]}
    except Exception as e:
        print(f"    Error: {e}")
        return {"error": str(e)}


def list_prompts(client: Langfuse) -> list[dict]:
    """List all versions of the prompt."""
    print("\n[3] Listing prompt versions...")

    try:
        prompts = client.get_prompt(name=PROMPT_NAME)
        print(f"    Current prompt: {prompts.name}")
        print(f"    Current version: {prompts.version}")
        print(f"    Labels: {prompts.labels}")
        return [{"version": prompts.version, "labels": prompts.labels}]
    except Exception as e:
        print(f"    Error: {e}")
        return []


def update_production_label(client: Langfuse, version: int) -> bool:
    """Update production label to a specific version."""
    print(f"\n[4] Updating production label to version {version}...")

    try:
        # Get the specific version and update its labels
        prompt = client.create_prompt(
            name=PROMPT_NAME,
            prompt=PROMPT_VERSION_2 if version == 2 else PROMPT_VERSION_1,
            labels=["production"],
            type="text",
        )
        print(f"    Production label now points to version: {prompt.version}")
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


def rollback_production(client: Langfuse) -> bool:
    """Rollback production label to version 1."""
    print("\n[5] Rolling back production to version 1...")

    try:
        prompt = client.create_prompt(
            name=PROMPT_NAME,
            prompt=PROMPT_VERSION_1,
            labels=["production"],
            type="text",
        )
        print(f"    Production label rolled back to version: {prompt.version}")
        print("    NOTE: For manual rollback, go to Langfuse dashboard:")
        print(f"          1. Open https://us.cloud.langfuse.com")
        print(f"          2. Navigate to Prompts > {PROMPT_NAME}")
        print(f"          3. Change 'production' label to version 1")
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    """Main function to run prompt versioning workflow."""
    print("=" * 60)
    print("Langfuse Prompt Versioning Script")
    print("=" * 60)

    # Check credentials
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        print("\nERROR: Langfuse credentials not found!")
        print("Please set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        return 1

    client = get_langfuse_client()

    print("\nThis script will:")
    print("  1. Create Prompt Version 1 (labels: baseline, production)")
    print("  2. Create Prompt Version 2 (label: candidate)")
    print("  3. List current prompt versions")
    print("\nManual steps after running this script:")
    print("  - Go to Langfuse dashboard to view traces")
    print("  - Change 'production' label between versions")
    print("  - Take screenshots for evidence")

    try:
        # Step 1: Create version 1
        v1 = create_prompt_v1(client)
        if "error" in v1:
            print("\nFailed to create prompt v1, trying to update existing...")
            client.create_prompt(
                name=PROMPT_NAME,
                prompt=PROMPT_VERSION_1,
                labels=["baseline", "production"],
                type="text",
            )

        # Step 2: Create version 2
        v2 = create_prompt_v2(client)
        if "error" in v2:
            print("\nFailed to create prompt v2, trying to update existing...")
            client.create_prompt(
                name=PROMPT_NAME,
                prompt=PROMPT_VERSION_2,
                labels=["candidate"],
                type="text",
            )

        # Step 3: List versions
        list_prompts(client)

        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print(f"1. Go to Langfuse dashboard: https://us.cloud.langfuse.com")
        print(f"2. Navigate to Prompts section")
        print(f"3. View '{PROMPT_NAME}' prompt with v1 and v2")
        print(f"4. Run load test: python scripts/load_test.py")
        print(f"5. Take screenshots of traces with different labels")
        print(f"6. For rollback: change 'production' label to v1 manually")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
