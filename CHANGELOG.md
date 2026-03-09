# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-03-09

### 🚀 Major Rewrite — From Scaffold to Full Pipeline

**Before:** 90% scaffold/stub with hardcoded mock data, broken imports, and empty files.
**After:** Fully functional trend intelligence engine with real data sources, AI processing, and auto-scheduling.

### Added
- **Real Google Trends collector** — `pytrends` library, fetches VN trending searches, seed keyword interest, related queries (free, no API key)
- **Real Firecrawl News collector** — searches news per seed keyword with Vietnamese context
- **Real TikTok collector** — Creative Center scraping (free) + Gemini AI fallback
- **Signal normalizer** — unified schema for heterogeneous data sources
- **Gemini-powered keyword extractor** — AI extraction with naive fallback
- **Fuzzy topic clustering** — groups similar signals via string similarity
- **Feature-based trend scoring** — volume, source diversity, mentions, recency (0-100 scale with configurable weights)
- **Gemini trend enrichment** — AI-generated `why_trending` explanations and `suggested_actions` in Vietnamese
- **SQLite storage** — persistent history with `runs`, `signals`, `trends` tables + indexed queries
- **APScheduler integration** — `schedule` CLI command, configurable interval, SIGINT graceful shutdown
- **HTTP utilities** — shared session with retry, rate limiting, User-Agent rotation
- **Vietnamese text utilities** — stop words, text cleaning, diacritics removal, fuzzy similarity
- **Config-driven pipeline** — collectors loaded dynamically from `sources.yaml`
- **Timestamped archive exports** — `trends_YYYYMMDD_HHMMSS.json` alongside `trends_latest.json`
- **Custom exceptions** — `CollectorError`, `ProcessingError`, `StorageError`, `ConfigError`
- **21 unit + integration tests** — collectors (mocked), processing, full pipeline, SQLite persistence
- **Complete README** — architecture diagram, setup guide, output format, project structure

### Fixed
- **`pydantic` not in requirements** — replaced with `dataclass` + `python-dotenv`
- **Relative export path** — now uses project-root-based absolute path
- **CLI standalone `detect`/`export`** — was crashing due to undefined variables
- **`sources.yaml` never loaded** — now parsed at startup via `Settings`

### Changed
- `settings.py` — pydantic `BaseSettings` → `dataclass` + `dotenv` + YAML loader
- `collect_pipeline.py` — hardcoded collector list → config-driven dynamic loading
- `detect_pipeline.py` — accepts `top_n` parameter
- `export_pipeline.py` — uses `settings.data_dir` + adds archive copy
- `cli/main.py` — refactored into helper functions, added `schedule` command

---

## [1.0.0] - 2026-02-xx

### Added
- Initial project scaffold with modular architecture
- Data models: `RawSignal`, `TopicCluster`, `TrendResult`
- Mock collectors: Google Trends, Firecrawl News, TikTok
- Basic CLI with `collect`, `detect`, `export`, `all` commands
- Local JSON file storage
- 2 basic unit tests
