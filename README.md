# Trend Engine v2

A modular **Trend Intelligence Engine** that collects signals from multiple sources, detects rising trends, and generates actionable insights for the **Vietnamese market**.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         CLI / Scheduler                       │
├───────────────┬───────────────┬───────────────┬───────────────┤
│   Collect     │    Detect     │    Export      │   Schedule    │
│   Pipeline    │    Pipeline   │    Pipeline    │   (APScheduler)│
├───────────────┼───────────────┴───────────────┴───────────────┤
│  Collectors   │           Processing & Scoring                │
│ ┌───────────┐ │ ┌───────────┐ ┌───────────┐ ┌──────────────┐ │
│ │Google     │ │ │Normalizer │ │Clustering │ │Trend Scorer  │ │
│ │Trends     │ │ │           │ │(fuzzy)    │ │(features +   │ │
│ │(pytrends) │ │ ├───────────┤ ├───────────┤ │ weights +    │ │
│ ├───────────┤ │ │Keyword    │ │Deduplicator│ │ Gemini)      │ │
│ │Firecrawl  │ │ │Extractor  │ │           │ └──────────────┘ │
│ │News       │ │ │(Gemini)   │ └───────────┘                  │
│ ├───────────┤ │ └───────────┘                                 │
│ │TikTok     │ │                                               │
│ │Creative   │ │                                               │
│ │Center     │ │                                               │
│ └───────────┘ │                                               │
├───────────────┴───────────────────────────────────────────────┤
│                    Storage Layer                              │
│              JSON (local) + SQLite (history)                  │
└───────────────────────────────────────────────────────────────┘
```

## Data Sources

| Source | Method | Cost | API Key? |
|--------|--------|------|----------|
| **Google Trends** | `pytrends` library | Free | No |
| **News** | Firecrawl API `/search` | Free tier (1000/mo) | Yes |
| **TikTok** | Creative Center scraping | Free | No |
| **AI Processing** | Gemini API | Free tier | Yes |

## Quick Start

### 1. Install

```bash
cd /Users/macos/VScode/3_trend_engine
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys:
#   FIRECRAWL_API_KEY=fc-xxx
#   GEMINI_API_KEY=xxx
```

### 3. Run

```bash
# Full pipeline (collect → detect → export)
PYTHONPATH=src python -m trend_engine.cli.main all --window 24h

# Individual steps
PYTHONPATH=src python -m trend_engine.cli.main collect --window 24h
PYTHONPATH=src python -m trend_engine.cli.main detect --window 24h
PYTHONPATH=src python -m trend_engine.cli.main export

# Auto-schedule (every 6 hours by default)
PYTHONPATH=src python -m trend_engine.cli.main schedule

# Custom interval
PYTHONPATH=src python -m trend_engine.cli.main schedule --interval 30m
```

### 4. Output

- **Latest trends**: `data/trends_latest.json`
- **Archived trends**: `data/trends_YYYYMMDD_HHMMSS.json`
- **History database**: `data/trend_engine.db`

## Configuration

### `src/trend_engine/config/sources.yaml`

```yaml
language: vi

seed_keywords:
  - ai
  - giáo dục
  - fnb
  - đồ uống
  - bán lẻ
  - vending

sources:
  google_trends: true
  news_firecrawl: true
  tiktok: true

ranking:
  top_n: 20
```

### `.env`

```
FIRECRAWL_API_KEY=fc-your-key
GEMINI_API_KEY=your-gemini-key
SCHEDULE_INTERVAL_HOURS=6
```

## Output Format

Each trend in `trends_latest.json`:

```json
{
  "trend_id": "trend_cluster_001",
  "topic": "ai agents",
  "trend_type": "cross_platform",
  "trend_score": 78.5,
  "confidence": 1.0,
  "time_window": "24h",
  "why_trending": [
    "Xu hướng AI agent đang bùng nổ tại Việt Nam...",
    "Appears across 3 platforms (google_trends, news_firecrawl, tiktok)",
    "High signal volume (5,100)"
  ],
  "sources": ["google_trends", "news_firecrawl", "tiktok"],
  "evidence": [
    {"source": "google_trends", "text": "ai agents", "volume": 100},
    {"source": "tiktok", "text": "ai", "volume": 5000000}
  ],
  "suggested_actions": {
    "content_marketing": [
      "Viết bài blog về ứng dụng AI Agent trong kinh doanh",
      "Tạo video TikTok hướng dẫn sử dụng AI tools"
    ]
  }
}
```

## Testing

```bash
PYTHONPATH=src pytest tests/ -v
```

## Project Structure

```
3_trend_engine/
├── src/trend_engine/
│   ├── cli/main.py              # CLI entrypoint
│   ├── collectors/              # Data source collectors
│   │   ├── base.py              # Abstract interface
│   │   ├── google_trends_collector.py
│   │   ├── firecrawl_news_collector.py
│   │   └── tiktok_collector.py
│   ├── config/
│   │   ├── settings.py          # Settings (dotenv + YAML)
│   │   └── sources.yaml         # Source config
│   ├── core/
│   │   ├── models.py            # Data contracts
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── logging.py           # Logger config
│   │   └── time_window.py       # Window validation
│   ├── processing/
│   │   ├── normalizer.py        # Signal normalization
│   │   ├── keyword_extractor.py # Gemini keyword extraction
│   │   ├── clustering.py        # Fuzzy topic clustering
│   │   └── deduplicator.py      # Normalize → cluster pipeline
│   ├── scoring/
│   │   ├── trend_features.py    # Feature extractors
│   │   ├── weights.py           # Configurable weights
│   │   └── trend_scorer.py      # Weighted scoring + Gemini
│   ├── storage/
│   │   ├── base_store.py        # Abstract interface
│   │   ├── local_files_store.py # JSON storage
│   │   └── sqlite_store.py      # SQLite history
│   ├── pipelines/
│   │   ├── collect_pipeline.py  # Config-driven collection
│   │   ├── detect_pipeline.py   # Dedup → score
│   │   └── export_pipeline.py   # JSON + archive export
│   ├── scheduler.py             # APScheduler auto-run
│   └── utils/
│       ├── http.py              # Retry + rate limiting
│       └── text.py              # Vietnamese text utils
├── data/                        # Output directory
├── tests/
│   ├── test_collectors.py
│   ├── test_processing.py
│   └── test_pipeline_integration.py
├── requirements.txt
└── .env.example
```
