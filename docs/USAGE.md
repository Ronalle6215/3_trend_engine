# Hướng Dẫn Sử Dụng — Trend Engine v2

## Mục Lục

- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt](#cài-đặt)
- [Cấu Hình](#cấu-hình)
- [Cách Sử Dụng](#cách-sử-dụng)
- [Đọc Kết Quả](#đọc-kết-quả)
- [Chạy Tự Động](#chạy-tự-động)
- [Tùy Chỉnh Nâng Cao](#tùy-chỉnh-nâng-cao)
- [Xử Lý Lỗi](#xử-lý-lỗi)

---

## Yêu Cầu Hệ Thống

- Python 3.10+
- macOS / Linux / Windows
- API Keys (xem phần Cấu Hình)

## Cài Đặt

```bash
# Clone repo
git clone https://github.com/Ronalle6215/3_trend_engine.git
cd 3_trend_engine

# Cài dependencies
pip install -r requirements.txt
```

## Cấu Hình

### 1. API Keys (`.env`)

```bash
cp .env.example .env
```

Mở file `.env` và điền API keys:

| Key | Nguồn | Cách lấy | Chi phí |
|-----|-------|----------|---------|
| `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) | Đăng ký → Dashboard → API Keys | Free 1000 crawls/tháng |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) | Create API Key | Free tier |

> **Google Trends** và **TikTok** không cần API key (free).

### 2. Seed Keywords (`sources.yaml`)

Mở `src/trend_engine/config/sources.yaml` để tùy chỉnh keywords theo ngành:

```yaml
seed_keywords:
  - ai              # Công nghệ
  - giáo dục        # Education
  - fnb             # F&B
  - đồ uống         # Beverages
  - bán lẻ          # Retail
  - vending         # Vending machines
```

### 3. Bật/Tắt nguồn dữ liệu

```yaml
sources:
  google_trends: true     # Bật
  news_firecrawl: true    # Bật
  tiktok: true            # Bật
  ecommerce:              # Chưa implement
    shopee: true
    lazada: true
```

## Cách Sử Dụng

### Chạy Full Pipeline (khuyến nghị)

```bash
PYTHONPATH=src python3 -m trend_engine.cli.main all --window 24h
```

Lệnh này sẽ:
1. **Collect** — Thu thập dữ liệu từ Google Trends, News, TikTok
2. **Detect** — Phân tích, clustering, scoring, AI enrichment
3. **Export** — Xuất file JSON

### Chạy Từng Bước

```bash
# Chỉ thu thập
PYTHONPATH=src python3 -m trend_engine.cli.main collect --window 24h

# Chỉ phân tích (tự động collect trước)
PYTHONPATH=src python3 -m trend_engine.cli.main detect --window 24h

# Chỉ export (tự động collect + detect trước)
PYTHONPATH=src python3 -m trend_engine.cli.main export
```

### Tham Số

| Tham số | Mô tả | Giá trị | Mặc định |
|---------|-------|---------|----------|
| `command` | Lệnh chạy | `collect`, `detect`, `export`, `all`, `schedule` | — |
| `--window` | Khung thời gian | `6h`, `24h`, `72h` | `24h` |
| `--top` | Số trends tối đa | Số nguyên | `20` |
| `--interval` | Khoảng cách schedule | `30m`, `1h`, `6h`, `1d` | `6h` |

## Đọc Kết Quả

### File Output

| File | Vị trí | Mô tả |
|------|--------|-------|
| `trends_latest.json` | `data/` | Trends mới nhất (ghi đè mỗi lần) |
| `trends_YYYYMMDD_HHMMSS.json` | `data/` | Bản archive theo thời gian |
| `trend_engine.db` | `data/` | Database lịch sử (SQLite) |

### Cấu Trúc Mỗi Trend

```json
{
  "trend_id": "trend_cluster_003",
  "topic": "ai agents",
  "trend_type": "cross_platform",
  "trend_score": 78.5,
  "confidence": 1.0,
  "why_trending": [
    "Xu hướng AI agent bùng nổ tại VN...",
    "Appears across 3 platforms"
  ],
  "sources": ["google_trends", "news_firecrawl", "tiktok"],
  "suggested_actions": {
    "content_marketing": [
      "Viết bài blog về AI Agent",
      "Tạo video TikTok hướng dẫn AI tools"
    ]
  }
}
```

### Giải Thích Các Trường

| Trường | Ý nghĩa |
|--------|---------|
| `trend_score` | Điểm xu hướng (0-100), càng cao càng hot |
| `confidence` | Độ tin cậy (0-1.0), dựa trên số nguồn xác nhận |
| `trend_type` | `viral` / `cross_platform` / `rising` / `emerging` |
| `why_trending` | Giải thích tại sao trending (Gemini AI + data-driven) |
| `suggested_actions` | Gợi ý hành động cho content/marketing team |

## Chạy Tự Động

### Dùng Built-in Scheduler

```bash
# Chạy mỗi 6h (mặc định)
PYTHONPATH=src python3 -m trend_engine.cli.main schedule

# Chạy mỗi 30 phút
PYTHONPATH=src python3 -m trend_engine.cli.main schedule --interval 30m

# Chạy mỗi ngày
PYTHONPATH=src python3 -m trend_engine.cli.main schedule --interval 1d
```

Nhấn `Ctrl+C` để dừng.

### Dùng Cron (Linux/macOS)

```bash
# Mở crontab
crontab -e

# Thêm dòng (chạy mỗi 6h)
0 */6 * * * cd /path/to/3_trend_engine && PYTHONPATH=src python3 -m trend_engine.cli.main all --window 24h
```

## Tùy Chỉnh Nâng Cao

### Chỉnh Scoring Weights

Mở `src/trend_engine/scoring/weights.py`:

```python
DEFAULT_WEIGHTS = {
    "volume": 0.30,     # Trọng số cho lượng tìm kiếm/view
    "diversity": 0.25,  # Trọng số cho đa nền tảng
    "mentions": 0.25,   # Trọng số cho số lần xuất hiện
    "recency": 0.20,    # Trọng số cho độ mới
}
```

### Thêm Collector Mới

1. Tạo file trong `src/trend_engine/collectors/`
2. Kế thừa `BaseCollector`, implement `collect(window) -> RawSignal`
3. Đăng ký trong `collect_pipeline.py` `_COLLECTOR_MAP`
4. Bật trong `sources.yaml`

### Xem Lịch Sử Trends (SQLite)

```bash
# Mở database
sqlite3 data/trend_engine.db

# Xem runs gần nhất
SELECT * FROM runs ORDER BY started_at DESC LIMIT 5;

# Xem trends hot nhất
SELECT topic, trend_score, trend_type FROM trends ORDER BY trend_score DESC LIMIT 10;

# Lịch sử 1 topic
SELECT detected_at, trend_score FROM trends WHERE topic LIKE '%ai%' ORDER BY detected_at;
```

## Xử Lý Lỗi

| Lỗi | Nguyên nhân | Cách sửa |
|-----|-------------|----------|
| `CollectorError: FIRECRAWL_API_KEY not set` | Chưa cấu hình `.env` | Tạo file `.env` từ `.env.example` |
| `CollectorError: pytrends not installed` | Thiếu dependency | `pip install -r requirements.txt` |
| `Google Trends trending_searches failed` | Rate limit / network | Thử lại sau vài phút |
| `TikTok Creative Center scraping failed` | TikTok đổi HTML | Tự động fallback sang Gemini |
| `Gemini enrichment failed` | API key hết quota | Vẫn chạy, chỉ thiếu AI explanations |
