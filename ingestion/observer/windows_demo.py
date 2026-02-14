"""
Windows demo — Create files in watched directories and see them get detected.

Run from the project root:
    python -m ingestion.observer.windows_demo
"""

import os
import sys
import time
from pathlib import Path


# Map extensions to human-readable categories
EXT_CATEGORIES = {
    ".pdf": "PDF document",
    ".txt": "Text file",
    ".md": "Markdown",
    ".docx": "Word document",
    ".jpg": "JPEG image",
    ".jpeg": "JPEG image",
    ".png": "PNG image",
    ".wav": "WAV audio",
    ".mp3": "MP3 audio",
    ".json": "JSON data",
}


def main():
    # Add project root to path (only within main, not at import time)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from ingestion.observer import SynapsisWatcher, save_config, _setup_logging
    from ingestion.observer.constants import SUPPORTED_EXTENSIONS, DEFAULT_CONFIG

    _setup_logging()

    # Watch the real production directories from constants.py
    watched = DEFAULT_CONFIG["watched_directories"]
    config = {
        "watched_directories": watched,
        "exclude_patterns": DEFAULT_CONFIG["exclude_patterns"],
        "max_file_size_mb": DEFAULT_CONFIG["max_file_size_mb"],
        "rate_limit_files_per_minute": 60,  # faster for testing
    }
    save_config(config)

    # Sort extensions for display
    sorted_exts = sorted(SUPPORTED_EXTENSIONS)

    print("\n" + "=" * 70)
    print("  Synapsis Observer - Windows Demo")
    print("=" * 70)

    print(f"\n  Watched directories ({len(watched)}):")
    for d in watched:
        resolved = Path(os.path.expanduser(d)).resolve()
        status = "OK" if resolved.is_dir() else "MISSING"
        print(f"    [{status:7s}] {d}  ->  {resolved}")

    print(f"\n  Supported extensions ({len(SUPPORTED_EXTENSIONS)}):")
    for ext in sorted_exts:
        label = EXT_CATEGORIES.get(ext, "")
        print(f"    {ext:8s} {label}")

    print(f"\n  Exclude patterns:")
    for pat in config["exclude_patterns"]:
        print(f"    {pat}")

    print(f"\n  Max file size: {config['max_file_size_mb']} MB")

    # Start watcher — live watch starts instantly, initial scan runs in background
    print("\n  Starting watcher (live watch starts immediately)...")
    print("  Background scan of existing files will run in parallel.")
    watcher = SynapsisWatcher()
    if not watcher.start():
        print("  ERROR: Watcher failed to start. Check your configuration.")
        return

    print("\n" + "-" * 70)
    print("  The watcher is LIVE. Try any of these in a NEW CMD window:")
    print("-" * 70)
    print()

    # Show commands for common directories
    print("  In Documents:")
    print('    echo hello > "%USERPROFILE%\\Documents\\test.txt"')
    print()
    print("  In Desktop:")
    print('    echo hello > "%USERPROFILE%\\Desktop\\test.txt"')
    print()
    print("  In Downloads:")
    print('    echo hello > "%USERPROFILE%\\Downloads\\test.txt"')
    print()
    print("  Or any subdirectory:")
    print('    echo hello > "%USERPROFILE%\\Documents\\subfolder\\test.txt"')

    print(f"\n  Unsupported extensions are IGNORED:")
    print(f"    echo x > test.py   (not in supported list)")
    print(f"    echo x > temp.tmp  (excluded)")
    print(f"\n  Or just drag/drop/save/delete files in Explorer!")
    print("\n  Watch this window for [PROCESS] logs.")
    print("\n  Press Ctrl+C to stop.")
    print("-" * 70 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        watcher.stop()
        print(f"\n  Done.  Config: {Path.home() / '.synapsis' / 'config.json'}\n")


if __name__ == "__main__":
    main()
