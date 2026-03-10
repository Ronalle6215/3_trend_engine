"""
Gemini-powered content generator for marketing
"""

import json
import re

from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings

logger = get_logger(__name__)


def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_blog_draft(topic: str, why_trending: list[str], sources: list[str]) -> str:
    context = "\n".join(f"- {w}" for w in why_trending[:3])
    src_list = ", ".join(sources)
    prompt = (
        f"Viết một bài blog tiếng Việt khoảng 500-700 từ về xu hướng: \"{topic}\"\n\n"
        f"Bối cảnh trending:\n{context}\n"
        f"Nguồn dữ liệu: {src_list}\n\n"
        f"Yêu cầu:\n"
        f"- Tiêu đề hấp dẫn (H1)\n"
        f"- Giới thiệu xu hướng và tại sao nó đang hot\n"
        f"- Phân tích 2-3 điểm chính\n"
        f"- Ứng dụng thực tế cho doanh nghiệp Việt Nam\n"
        f"- Kết luận + kêu gọi hành động\n"
        f"- Output dạng Markdown"
    )
    try:
        return _call_gemini(prompt)
    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        return f"⚠️ Không thể tạo bài viết: {e}"


def generate_facebook_post(topic: str, why_trending: list[str]) -> str:
    context = "\n".join(f"- {w}" for w in why_trending[:3])
    prompt = (
        f"Viết một bài đăng Facebook tiếng Việt hấp dẫn về xu hướng: \"{topic}\"\n\n"
        f"Bối cảnh:\n{context}\n\n"
        f"Yêu cầu:\n"
        f"- Ngắn gọn 3-5 dòng, dễ đọc trên mobile\n"
        f"- Mở đầu bằng emoji bắt mắt\n"
        f"- Kèm câu hỏi tương tác cho người đọc\n"
        f"- Thêm 5-8 hashtags tiếng Việt + tiếng Anh ở cuối\n"
        f"- Tone: chuyên nghiệp nhưng gần gũi"
    )
    try:
        return _call_gemini(prompt)
    except Exception as e:
        logger.error(f"FB post generation failed: {e}")
        return f"⚠️ Không thể tạo Facebook post: {e}"


def generate_tiktok_hashtags(topic: str) -> str:
    prompt = (
        f"Tạo danh sách 15-20 hashtags cho TikTok video về chủ đề: \"{topic}\" tại thị trường Việt Nam.\n\n"
        f"Yêu cầu:\n"
        f"- Mix tiếng Việt + tiếng Anh\n"
        f"- Bao gồm hashtags phổ biến (ví dụ #xuhuong, #viral, #fyp)\n"
        f"- Bao gồm hashtags chuyên ngành liên quan\n"
        f"- Mỗi hashtag trên 1 dòng, bắt đầu bằng #\n"
        f"- Thêm gợi ý ý tưởng video ngắn (2-3 ý tưởng)"
    )
    try:
        return _call_gemini(prompt)
    except Exception as e:
        logger.error(f"TikTok hashtags generation failed: {e}")
        return f"⚠️ Không thể tạo hashtags: {e}"
