"""
Gemini-powered content generator — Full Content Studio + Image Generation
"""

import base64
import json
import time
from pathlib import Path

from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings

logger = get_logger(__name__)

BRAND_KIT_DIR = settings.project_root / "data" / "brand_kit"
BRAND_KIT_DIR.mkdir(parents=True, exist_ok=True)

IMAGES_DIR = settings.project_root / "src" / "trend_engine" / "web" / "static" / "images" / "generated"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

TONE_PRESETS = {
    "professional": "Chuyên nghiệp, đáng tin cậy, dùng số liệu cụ thể",
    "friendly": "Thân thiện, gần gũi, dễ hiểu, như đang nói chuyện với bạn",
    "genz": "Gen-Z, năng động, dùng từ lóng phổ biến, emoji nhiều, ngắn gọn",
    "humorous": "Hài hước, dí dỏm, có ví dụ vui, giữ sự chuyên nghiệp",
    "academic": "Học thuật, nghiên cứu, phân tích sâu, có trích dẫn",
    "sales": "Bán hàng, persuasive, tạo urgency, CTA mạnh",
}

TEMPLATES = {
    "blog_seo": {
        "name": "📝 Blog SEO",
        "content_type": "blog",
        "tone": "professional",
        "word_count": 700,
        "desc": "Bài blog chuẩn SEO, có H2/H3, keyword density phù hợp",
    },
    "fb_engagement": {
        "name": "📘 FB Engagement",
        "content_type": "facebook",
        "tone": "friendly",
        "word_count": 150,
        "desc": "Bài FB tối ưu engagement, có câu hỏi tương tác",
    },
    "tiktok_viral": {
        "name": "🎵 TikTok Viral",
        "content_type": "tiktok",
        "tone": "genz",
        "word_count": 100,
        "desc": "Hashtags + script ngắn cho video TikTok",
    },
    "linkedin_pro": {
        "name": "💼 LinkedIn Pro",
        "content_type": "blog",
        "tone": "professional",
        "word_count": 400,
        "desc": "Thought leadership, insight ngành, professional tone",
    },
    "email_mkt": {
        "name": "📧 Email Marketing",
        "content_type": "blog",
        "tone": "sales",
        "word_count": 300,
        "desc": "Email marketing với subject line, CTA, và urgency",
    },
}

# Text generation models
TEXT_MODELS = [
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (nhanh, miễn phí)", "type": "text"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (chất lượng cao)", "type": "text"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite (nhẹ nhất)", "type": "text"},
]

# All models including image
AVAILABLE_MODELS = TEXT_MODELS + [
    {"id": "imagen-3.0-generate-002", "name": "🖼️ Imagen 3.0 (tạo hình ảnh)", "type": "image"},
]


def _call_gemini(prompt: str, model_id: str = "gemini-2.5-flash") -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(model_id)
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_image(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """Generate image using Imagen 3.0 via Gemini API."""
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)

        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
            ),
        )

        if response.generated_images:
            image_data = response.generated_images[0].image.image_bytes
            filename = f"gen_{int(time.time())}.png"
            filepath = IMAGES_DIR / filename
            filepath.write_bytes(image_data)

            return {
                "success": True,
                "filename": filename,
                "url": f"/static/images/generated/{filename}",
            }
        return {"success": False, "error": "Không tạo được hình ảnh"}

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {"success": False, "error": str(e)}


def get_generated_images() -> list[dict]:
    """List all generated images."""
    images = []
    if IMAGES_DIR.exists():
        for f in sorted(IMAGES_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix in (".png", ".jpg", ".jpeg", ".webp"):
                size = f.stat().st_size
                images.append({
                    "name": f.name,
                    "url": f"/static/images/generated/{f.name}",
                    "size": f"{size / 1024:.1f} KB",
                })
    return images[:20]


def save_uploaded_image(filename: str, content: bytes) -> dict:
    """Save user-uploaded image."""
    safe_name = f"upload_{int(time.time())}_{filename}"
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-").strip()
    path = IMAGES_DIR / safe_name
    path.write_bytes(content)
    return {
        "filename": safe_name,
        "url": f"/static/images/generated/{safe_name}",
    }


def _load_brand_kit() -> str:
    """Load all brand kit files as context string."""
    texts = []
    if BRAND_KIT_DIR.exists():
        for f in sorted(BRAND_KIT_DIR.iterdir()):
            if f.suffix in (".txt", ".md"):
                try:
                    content = f.read_text(encoding="utf-8")[:3000]
                    texts.append(f"--- {f.name} ---\n{content}")
                except Exception:
                    pass
    return "\n\n".join(texts)


def _build_brand_context(brand_text: str) -> str:
    if not brand_text:
        return ""
    return (
        f"\n\n--- TÀI LIỆU THƯƠNG HIỆU (Brand Kit) ---\n"
        f"Hãy tuân theo tone, style, và thông tin thương hiệu dưới đây:\n{brand_text}\n"
        f"--- HẾT TÀI LIỆU ---\n"
    )


def generate_content(
    topic: str,
    why_trending: list[str],
    sources: list[str],
    content_type: str = "blog",
    tone: str = "professional",
    word_count: int = 500,
    model_id: str = "gemini-2.5-flash",
    custom_notes: str = "",
    use_brand_kit: bool = True,
) -> str:
    """Universal content generator."""
    tone_desc = TONE_PRESETS.get(tone, tone)
    context = "\n".join(f"- {w}" for w in why_trending[:3])
    src_list = ", ".join(sources) if sources else "N/A"

    brand_ctx = ""
    if use_brand_kit:
        brand_text = _load_brand_kit()
        brand_ctx = _build_brand_context(brand_text)

    custom_section = f"\nYêu cầu bổ sung từ người dùng: {custom_notes}\n" if custom_notes else ""

    if content_type == "facebook":
        prompt = _build_fb_prompt(topic, context, tone_desc, word_count, brand_ctx, custom_section)
    elif content_type == "tiktok":
        prompt = _build_tiktok_prompt(topic, tone_desc, brand_ctx, custom_section)
    else:
        prompt = _build_blog_prompt(topic, context, src_list, tone_desc, word_count, brand_ctx, custom_section)

    try:
        return _call_gemini(prompt, model_id)
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        return f"⚠️ Không thể tạo content: {e}"


def _build_blog_prompt(topic, context, sources, tone_desc, word_count, brand_ctx, custom):
    return (
        f"Viết một bài blog tiếng Việt khoảng {word_count} từ về xu hướng: \"{topic}\"\n\n"
        f"Bối cảnh trending:\n{context}\n"
        f"Nguồn dữ liệu: {sources}\n\n"
        f"Văn phong: {tone_desc}\n"
        f"Yêu cầu:\n"
        f"- Tiêu đề hấp dẫn (H1)\n"
        f"- Giới thiệu xu hướng\n"
        f"- Phân tích 2-3 điểm chính\n"
        f"- Ứng dụng thực tế cho doanh nghiệp Việt Nam\n"
        f"- Kết luận + kêu gọi hành động\n"
        f"- Output dạng Markdown\n"
        f"- Tối đa {word_count} từ\n"
        f"{brand_ctx}{custom}"
    )


def _build_fb_prompt(topic, context, tone_desc, word_count, brand_ctx, custom):
    return (
        f"Viết một bài đăng Facebook tiếng Việt về xu hướng: \"{topic}\"\n\n"
        f"Bối cảnh:\n{context}\n\n"
        f"Văn phong: {tone_desc}\n"
        f"Yêu cầu:\n"
        f"- Tối đa {word_count} từ\n"
        f"- Mở đầu bằng emoji bắt mắt\n"
        f"- Kèm câu hỏi tương tác\n"
        f"- Thêm 5-8 hashtags tiếng Việt + tiếng Anh\n"
        f"{brand_ctx}{custom}"
    )


def _build_tiktok_prompt(topic, tone_desc, brand_ctx, custom):
    return (
        f"Tạo nội dung TikTok cho chủ đề: \"{topic}\" tại thị trường Việt Nam.\n\n"
        f"Văn phong: {tone_desc}\n"
        f"Yêu cầu:\n"
        f"- 15-20 hashtags (mix Việt + Anh)\n"
        f"- 2-3 ý tưởng video ngắn\n"
        f"- Script mẫu cho 1 video (30-60 giây)\n"
        f"{brand_ctx}{custom}"
    )


def get_brand_kit_files() -> list[dict]:
    """List uploaded brand kit files."""
    files = []
    if BRAND_KIT_DIR.exists():
        for f in sorted(BRAND_KIT_DIR.iterdir()):
            if f.suffix in (".txt", ".md"):
                size = f.stat().st_size
                files.append({"name": f.name, "size": f"{size / 1024:.1f} KB"})
    return files


def save_brand_kit_file(filename: str, content: bytes) -> str:
    """Save uploaded file to brand kit directory."""
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
    path = BRAND_KIT_DIR / safe_name
    path.write_bytes(content)
    return safe_name


def delete_brand_kit_file(filename: str) -> bool:
    """Delete a file from brand kit."""
    path = BRAND_KIT_DIR / filename
    if path.exists() and path.parent == BRAND_KIT_DIR:
        path.unlink()
        return True
    return False
