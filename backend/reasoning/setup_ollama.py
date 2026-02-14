"""
Ollama Setup Script
===================
Pulls the required models for the 3-tier fallback system.

Models:
- T1: phi4-mini (3.8B, 2.5GB) - Best reasoning
- T2: qwen2.5:3b (3.1B, 1.9GB) - Balanced
- T3: qwen2.5:0.5b (0.5B, 398MB) - Fast fallback

Run: python -m backend.reasoning.setup_ollama
"""

import asyncio
import sys


async def main():
    from .ollama_client import OllamaClient, ModelTier, TIER_CONFIG
    
    print("=" * 60)
    print("SYNAPSIS - Ollama Model Setup")
    print("=" * 60)
    print()
    
    client = OllamaClient()
    
    # Check Ollama is running
    print("Checking Ollama server...")
    if not await client.check_health():
        print("ERROR: Ollama server not running!")
        print("Start it with: ollama serve")
        print("Or install from: https://ollama.ai")
        return 1
    
    print("✓ Ollama server is running")
    print()
    
    # List current models
    print("Current models:")
    models = await client.list_models()
    if models:
        for m in models:
            print(f"  - {m}")
    else:
        print("  (none)")
    print()
    
    # Pull required models
    print("Pulling required models (this may take a while)...")
    print()
    
    results = await client.ensure_models_available()
    
    print()
    print("=" * 60)
    print("SETUP RESULTS")
    print("=" * 60)
    
    all_good = True
    for tier, available in results.items():
        config = TIER_CONFIG[tier]
        status = "✓" if available else "✗"
        print(f"{status} {tier.name}: {config['model']} - {config['description']}")
        if not available:
            all_good = False
    
    print()
    
    if all_good:
        print("All models ready! You can now run Synapsis.")
    else:
        print("WARNING: Some models failed to download.")
        print("The system will use available models with fallback.")
    
    await client.close()
    return 0 if all_good else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
