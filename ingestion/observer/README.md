ingestion/observer/
├── __init__.py        → public API + logging setup
├── constants.py       → extensions, default config, paths
├── config.py          → load / save config, resolve directories
├── checksum.py        → SHA-256 compute + persistent ChecksumStore
├── filters.py         → extension, exclusion, size limit checks
├── events.py          → FileEvent DTO + RateLimiter
├── handler.py         → watchdog callback (filter → dedup → enqueue)
├── scanner.py         → initial directory scan on startup
├── processor.py       → background queue consumer
├── watcher.py         → SynapsisWatcher controller + CLI main()
└── windows_demo.py    → interactive Windows demo script