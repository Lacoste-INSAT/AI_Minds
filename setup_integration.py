#!/usr/bin/env python3
"""
Synapsis + Rowboat Integration Setup
=====================================
Sets up the local environment for running Rowboat with Synapsis backend
instead of cloud APIs.

This script:
1. Creates the rowboat config directory (~/.rowboat/config)
2. Copies the Synapsis OpenAI-compatible config to rowboat
3. Verifies Ollama is running and models are available
4. Tests the connection to Synapsis backend

Usage:
    python setup_integration.py
    
    # Or run directly:
    python -m setup_integration
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Config paths
SCRIPT_DIR = Path(__file__).parent
SYNAPSIS_CONFIG = SCRIPT_DIR / "config" / "rowboat-models.json"
ROWBOAT_CONFIG_DIR = Path.home() / ".rowboat" / "config"
ROWBOAT_MODELS_CONFIG = ROWBOAT_CONFIG_DIR / "models.json"


def print_header(text: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def print_status(status: str, message: str):
    """Print a status message."""
    icons = {"ok": "✓", "error": "✗", "warn": "⚠", "info": "→"}
    icon = icons.get(status, "•")
    print(f"  {icon} {message}")


def check_python_deps():
    """Check if required Python packages are available."""
    print_header("Checking Python Dependencies")
    
    required = ["fastapi", "httpx", "structlog", "pydantic"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            print_status("ok", f"{pkg} installed")
        except ImportError:
            missing.append(pkg)
            print_status("error", f"{pkg} NOT installed")
    
    if missing:
        print_status("warn", f"Install missing: pip install {' '.join(missing)}")
        return False
    return True


def check_ollama():
    """Check if Ollama is running and has required models."""
    print_header("Checking Ollama")
    
    try:
        import httpx
        
        # Check if Ollama is running
        try:
            resp = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5.0)
            if resp.status_code != 200:
                print_status("error", "Ollama not responding")
                return False
            print_status("ok", "Ollama is running")
        except Exception:
            print_status("error", "Ollama not reachable at localhost:11434")
            print_status("info", "Start Ollama: ollama serve")
            return False
        
        # Check for required models
        data = resp.json()
        available = {m["name"].split(":")[0] for m in data.get("models", [])}
        
        required_models = ["phi4-mini", "qwen2.5"]
        has_model = False
        
        for model in required_models:
            if model in available or any(model in m for m in available):
                print_status("ok", f"Model '{model}' available")
                has_model = True
            else:
                print_status("warn", f"Model '{model}' not found")
        
        if not has_model:
            print_status("info", "Pull a model: ollama pull phi4-mini")
            return False
        
        return True
        
    except ImportError:
        print_status("error", "httpx not installed (pip install httpx)")
        return False


def check_backend():
    """Check if Synapsis backend is running."""
    print_header("Checking Synapsis Backend")
    
    try:
        import httpx
        
        try:
            resp = httpx.get("http://127.0.0.1:8000/health", timeout=5.0)
            if resp.status_code == 200:
                print_status("ok", "Synapsis backend is running")
                
                # Check OpenAI-compat endpoint
                resp2 = httpx.get("http://127.0.0.1:8000/v1/models", timeout=5.0)
                if resp2.status_code == 200:
                    print_status("ok", "OpenAI-compatible API available")
                    models = resp2.json().get("data", [])
                    for m in models[:3]:
                        print_status("info", f"  Model: {m['id']}")
                return True
            else:
                print_status("error", "Backend returned non-200 status")
                return False
        except Exception as e:
            print_status("error", f"Backend not reachable: {e}")
            print_status("info", "Start backend: cd backend && python -m uvicorn main:app")
            return False
            
    except ImportError:
        print_status("error", "httpx not installed")
        return False


def setup_rowboat_config():
    """Create rowboat config directory and copy config."""
    print_header("Setting Up Rowboat Configuration")
    
    # Create config directory
    ROWBOAT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    print_status("ok", f"Config directory: {ROWBOAT_CONFIG_DIR}")
    
    # Check if config already exists
    if ROWBOAT_MODELS_CONFIG.exists():
        print_status("warn", "Existing models.json found")
        
        # Backup existing config
        backup = ROWBOAT_MODELS_CONFIG.with_suffix(".json.backup")
        shutil.copy(ROWBOAT_MODELS_CONFIG, backup)
        print_status("info", f"Backed up to: {backup}")
    
    # Copy our config
    if SYNAPSIS_CONFIG.exists():
        shutil.copy(SYNAPSIS_CONFIG, ROWBOAT_MODELS_CONFIG)
        print_status("ok", f"Copied Synapsis config to {ROWBOAT_MODELS_CONFIG}")
    else:
        # Create config inline
        config = {
            "provider": {
                "flavor": "openai-compatible",
                "baseURL": "http://127.0.0.1:8000/v1",
                "headers": {"X-Client": "rowboat-synapsis"}
            },
            "model": "phi4-mini"
        }
        with open(ROWBOAT_MODELS_CONFIG, "w") as f:
            json.dump(config, f, indent=2)
        print_status("ok", f"Created config at {ROWBOAT_MODELS_CONFIG}")
    
    # Verify config
    try:
        with open(ROWBOAT_MODELS_CONFIG) as f:
            config = json.load(f)
        print_status("info", f"  Provider: {config['provider']['flavor']}")
        print_status("info", f"  Base URL: {config['provider']['baseURL']}")
        print_status("info", f"  Model: {config['model']}")
        return True
    except Exception as e:
        print_status("error", f"Config validation failed: {e}")
        return False


def print_summary(results: dict):
    """Print final summary."""
    print_header("Setup Summary")
    
    all_ok = all(results.values())
    
    for check, passed in results.items():
        status = "ok" if passed else "error"
        print_status(status, check)
    
    print()
    if all_ok:
        print("  🎉 All checks passed! Rowboat is ready to use Synapsis backend.")
        print()
        print("  Next steps:")
        print("    1. Start the Rowboat Electron app: cd rowboat/apps/x && npm run dev")
        print("    2. The app will use local Ollama via Synapsis backend")
        print("    3. No API keys required — fully air-gapped!")
    else:
        print("  ⚠️  Some checks failed. Fix the issues above and run again.")
        print()
        print("  Quick fix commands:")
        print("    - Start Ollama: ollama serve")
        print("    - Pull model: ollama pull phi4-mini")
        print("    - Start backend: cd backend && uvicorn main:app --reload")


def main():
    """Run all setup checks."""
    print("\n" + "="*60)
    print(" Synapsis + Rowboat Integration Setup")
    print(" Air-gapped local AI — Zero cloud dependencies")
    print("="*60)
    
    results = {}
    
    # Run checks
    results["Python dependencies"] = check_python_deps()
    results["Ollama service"] = check_ollama()
    results["Synapsis backend"] = check_backend()
    results["Rowboat config"] = setup_rowboat_config()
    
    # Print summary
    print_summary(results)
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
