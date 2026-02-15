# Observer Testing Guide (Windows & Docker)

## Quick Start

### 0. **Docker** (recommended for production)

The observer runs inside the Docker image alongside the backend. Files placed in
mounted volumes are automatically detected.

```bash
# Build and start everything (Qdrant + backend with observer)
docker-compose up --build -d

# Check logs — look for "ingestion.watcher_started"
docker logs -f synapsis-backend
```

**Mount your own directories** — edit `docker-compose.yml` volumes:

```yaml
volumes:
  - ./data:/app/data
  - ./config:/app/config
  # Add your host directories here:
  - C:/Users/YourName/Documents:/app/watched/Documents
  - C:/Users/YourName/Desktop:/app/watched/Desktop
  - C:/Users/YourName/Downloads:/app/watched/Downloads
```

Then set the env var so the backend watches them:

```yaml
environment:
  - SYNAPSIS_WATCHED_DIRECTORIES=["/app/watched/Documents","/app/watched/Desktop","/app/watched/Downloads"]
```

**Test inside Docker:**

```bash
# Copy a file into a watched volume
docker cp my_notes.txt synapsis-backend:/app/watched/sample_knowledge/

# Or write directly
docker exec synapsis-backend sh -c 'echo "hello world" > /app/watched/sample_knowledge/test.txt'

# Watch the logs for [PROCESS] events
docker logs -f synapsis-backend
```

---

### 1. **Interactive Demo** (full watcher, native)

```cmd
cd C:\Users\Asus\Desktop\AI_Minds
python -m ingestion.observer.windows_demo
```

The watcher will start monitoring your default directories (Documents, Desktop, Downloads, etc.). You'll see the watched directory paths in the output.

**Test in a new terminal:**

```cmd
REM Create a text file in a watched directory - should be detected
echo test content > "%USERPROFILE%\Documents\notes.txt"

REM Modify it - should detect change
echo more content >> "%USERPROFILE%\Documents\notes.txt"

REM Create a temp file - should be IGNORED
echo temp > "%USERPROFILE%\Documents\temp.tmp"

REM Copy an image - should be detected
copy C:\path\to\image.jpg test.jpg

REM Delete - should detect deletion
del "%USERPROFILE%\Documents\notes.txt"
```

Watch the first terminal for `[PROCESS]` logs. Press `Ctrl+C` to stop.

---

### 2. **Watch Real Directories**

**Option A: Use defaults (Documents/Desktop/Downloads/Pictures/Music)**

```cmd
cd C:\Users\Asus\Desktop\AI_Minds
python -m ingestion.observer.watcher
```

**Option B: Watch specific folder**

```cmd
cd C:\Users\Asus\Desktop\AI_Minds

REM In CMD, use double backslashes
python -c "from ingestion.observer import save_config; save_config({'watched_directories': ['C:\\\\Users\\\\Asus\\\\Desktop\\\\test_folder'], 'rate_limit_files_per_minute': 60})"

REM In PowerShell, Python still needs escaped backslashes
python -c "from ingestion.observer import save_config; save_config({'watched_directories': ['C:\\Users\\Asus\\Desktop\\test_folder'], 'rate_limit_files_per_minute': 60})"

python -m ingestion.observer.watcher
```

**Option C: Python script**
Create `test_watcher.py`:

```python
from ingestion.observer import SynapsisWatcher

watcher = SynapsisWatcher()
watcher.start()

print("Watcher running. Create/modify files in watched directories.")
print("Press Enter to stop...")
input()

watcher.stop()
print("Done!")
```

Run: `python test_watcher.py`

---

## Expected Behavior

### Log Output

```
2026-02-14 21:16:15 [INFO] synapsis.observer: Config loaded from C:\Users\Asus\.synapsis\config.json
2026-02-14 21:16:15 [INFO] synapsis.observer: Watching 2 director(ies): [WindowsPath('C:/Users/Asus/Desktop'), ...]
2026-02-14 21:16:15 [INFO] synapsis.observer: Initial scan complete — 5 event(s) queued
2026-02-14 21:16:15 [INFO] synapsis.observer: Live filesystem watcher started.
2026-02-14 21:16:17 [INFO] synapsis.observer: Queued FileEvent(created, C:\Users\Asus\Desktop\test.txt)
2026-02-14 21:16:17 [INFO] synapsis.observer: [PROCESS] CREATED | C:\Users\Asus\Desktop\test.txt | 2026-02-14T...
```

### File Operations Test Matrix

| Windows Command                           | Expected Result            |
| ----------------------------------------- | -------------------------- |
| `echo test > notes.txt`                   | ✓ `[PROCESS] CREATED`      |
| `echo test >> notes.txt` (no new content) | ✗ Skipped (checksum match) |
| `echo new text >> notes.txt`              | ✓ `[PROCESS] MODIFIED`     |
| `del notes.txt`                           | ✓ `[PROCESS] DELETED`      |
| `echo test > script.py`                   | ✗ Ignored (unsupported)    |
| `echo test > temp.tmp`                    | ✗ Ignored (excluded)       |
| Word creates `~$document.docx`            | ✗ Ignored (temp file)      |
| Create file in `node_modules\`            | ✗ Ignored (excluded)       |
| Create 100MB file                         | ✗ Ignored (size limit)     |

---

## Configuration (Windows)

### Config File Location

```
C:\Users\Asus\.synapsis\config.json
```

### Edit Config

```cmd
REM Open in Notepad
notepad %USERPROFILE%\.synapsis\config.json

REM Or use Python
python
>>> from ingestion.observer import load_config, save_config
>>> config = load_config()
>>> config["watched_directories"]
>>> config["rate_limit_files_per_minute"] = 60
>>> save_config(config)
>>> exit()
```

### Example Config

```json
{
  "watched_directories": [
    "C:\\Users\\Asus\\Documents",
    "C:\\Users\\Asus\\Desktop",
    "C:\\Users\\Asus\\Downloads"
  ],
  "exclude_patterns": [
    "node_modules/**",
    ".git/**",
    "__pycache__/**",
    "*.tmp",
    "*.exe",
    "*.dll",
    "~$*"
  ],
  "max_file_size_mb": 50,
  "rate_limit_files_per_minute": 10
}
```

---

## Troubleshooting

### "Directory does not exist" warning

- Config uses Unix paths (`~/Documents`) but Windows needs full paths
- Fix: Use `C:\Users\Asus\Documents` instead

### "ModuleNotFoundError: No module named 'watchdog'"

- Check which Python: `where python`
- Should be: `C:\Users\Asus\anaconda3\python.exe`
- Install to correct Python: `python -m pip install watchdog`

### No events detected

1. Check directory exists: `dir "C:\path\to\folder"`
2. Check file extension is supported: `.pdf .txt .md .docx .jpg .jpeg .png .wav .mp3 .json`
3. Check config: `type %USERPROFILE%\.synapsis\config.json`
4. Check exclusions don't match your file

### Events are slow

- Default rate limit is 10 files/minute
- Increase: edit config or use `{'rate_limit_files_per_minute': 60}`

### Duplicate events

- Normal for Windows (saves trigger multiple events)
- Checksum dedup prevents duplicate processing

---

## Supported File Types

| Extension               | Parser          | Status  |
| ----------------------- | --------------- | ------- |
| `.pdf`                  | PyMuPDF         | ✓ Ready |
| `.txt`                  | Built-in        | ✓ Ready |
| `.md`                   | Built-in        | ✓ Ready |
| `.docx`                 | python-docx     | ⌛ TODO |
| `.jpg`, `.jpeg`, `.png` | pytesseract OCR | ⌛ TODO |
| `.wav`, `.mp3`          | faster-whisper  | ⌛ TODO |
| `.json`                 | Built-in        | ✓ Ready |

---

## Integration Next Steps

The observer is working. Now connect it to the processing pipeline:

1. **Replace the TODO in processor.py** (line 23-29):

   ```python
   # Current: just logs
   logger.info("[PROCESS] %s | %s", fe.event_type, fe.src_path)

   # Replace with:
   intake_orchestrator.process(fe)
   ```

2. **Create the intake orchestrator** → routes files to parsers by extension

3. **Build the parser router** → PDF, image OCR, audio transcription, etc.

4. **Connect to enrichment** → entity extraction, embedding, graph building

The watcher is production-ready and tested. Ready to build on top! 🚀
