"""
Generate route — Content Studio with AI model selection, tone, templates, brand kit, images
"""

import json

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pathlib import Path

from trend_engine.storage.sqlite_store import SQLiteStore
from trend_engine.services.content_generator import (
    generate_content,
    generate_image,
    optimize_image_prompt,
    get_brand_kit_files,
    get_generated_images,
    save_brand_kit_file,
    save_uploaded_image,
    delete_brand_kit_file,
    TONE_PRESETS,
    TEMPLATES,
    AVAILABLE_MODELS,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

REF_IMAGES_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "references"
REF_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _get_trends():
    db = SQLiteStore()
    trends = db.get_latest_trends(limit=20)
    for t in trends:
        if isinstance(t.get("why_trending_json"), str):
            try:
                t["why_trending"] = json.loads(t["why_trending_json"])
            except Exception:
                t["why_trending"] = []
    return trends


def _base_ctx(request, **extra):
    # List reference images
    ref_images = []
    if REF_IMAGES_DIR.exists():
        for f in sorted(REF_IMAGES_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix in (".png", ".jpg", ".jpeg", ".webp"):
                ref_images.append({
                    "name": f.name,
                    "url": f"/static/images/references/{f.name}",
                })
    return {
        "request": request,
        "page": "generate",
        "trends": _get_trends(),
        "content": None,
        "content_type": None,
        "tone_presets": TONE_PRESETS,
        "template_presets": TEMPLATES,
        "models": AVAILABLE_MODELS,
        "brand_files": get_brand_kit_files(),
        "generated_images": get_generated_images(),
        "ref_images": ref_images,
        "image_result": None,
        "optimized_prompt": None,
        **extra,
    }


@router.get("/", response_class=HTMLResponse)
async def generate_form(request: Request, msg: str = ""):
    return templates.TemplateResponse("generate.html", _base_ctx(request, msg=msg))


@router.post("/", response_class=HTMLResponse)
async def generate_content_route(
    request: Request,
    topic: str = Form(...),
    content_type: str = Form("blog"),
    tone: str = Form("professional"),
    word_count: int = Form(500),
    model_id: str = Form("gemini-2.5-flash"),
    custom_notes: str = Form(""),
    use_brand_kit: bool = Form(False),
):
    trends = _get_trends()

    why_trending = []
    sources = []
    for t in trends:
        if t.get("topic") == topic:
            why_trending = t.get("why_trending", [])
            try:
                sources = json.loads(t.get("sources_json", "[]"))
            except Exception:
                sources = []

    content = generate_content(
        topic=topic,
        why_trending=why_trending,
        sources=sources,
        content_type=content_type,
        tone=tone,
        word_count=word_count,
        model_id=model_id,
        custom_notes=custom_notes,
        use_brand_kit=use_brand_kit,
    )

    return templates.TemplateResponse("generate.html", _base_ctx(
        request,
        trends=trends,
        content=content,
        content_type=content_type,
        selected_topic=topic,
        selected_tone=tone,
        selected_model=model_id,
        word_count=word_count,
        custom_notes=custom_notes,
    ))


# ─── Image endpoints ───────────────────────────────────────

@router.post("/optimize-prompt", response_class=JSONResponse)
async def optimize_prompt_route(
    request: Request,
    image_prompt: str = Form(...),
    brand_text: str = Form(""),
    reference_desc: str = Form(""),
):
    """Step 1: Optimize user prompt → return optimized version for review."""
    optimized = optimize_image_prompt(
        user_prompt=image_prompt,
        brand_text=brand_text,
        reference_desc=reference_desc,
    )
    return {"optimized_prompt": optimized}


@router.post("/generate-image", response_class=HTMLResponse)
async def generate_image_route(
    request: Request,
    image_prompt: str = Form(...),
    aspect_ratio: str = Form("16:9"),
    image_model: str = Form("imagen-4.0-generate-001"),
):
    """Step 2: Generate image using the confirmed (optimized) prompt."""
    result = generate_image(image_prompt, aspect_ratio, model_id=image_model)
    return templates.TemplateResponse("generate.html", _base_ctx(
        request,
        image_result=result,
        image_prompt=image_prompt,
    ))


@router.post("/upload-reference", response_class=HTMLResponse)
async def upload_reference(
    request: Request,
    ref_image: UploadFile = File(...),
):
    """Upload reference image (person, product) for image generation context."""
    if ref_image.filename:
        data = await ref_image.read()
        if len(data) > 5 * 1024 * 1024:
            return RedirectResponse(url="/generate?msg=File+quá+lớn+(max+5MB)", status_code=303)
        import time
        safe = f"ref_{int(time.time())}_{ref_image.filename}"
        safe = "".join(c for c in safe if c.isalnum() or c in "._-").strip()
        (REF_IMAGES_DIR / safe).write_bytes(data)
    return RedirectResponse(url="/generate?msg=Reference+uploaded!", status_code=303)


@router.post("/upload-image", response_class=HTMLResponse)
async def upload_image(
    request: Request,
    content_image: UploadFile = File(...),
):
    if content_image.filename:
        data = await content_image.read()
        if len(data) > 5 * 1024 * 1024:
            return RedirectResponse(url="/generate?msg=File+quá+lớn+(max+5MB)", status_code=303)
        save_uploaded_image(content_image.filename, data)
    return RedirectResponse(url="/generate?msg=Hình+đã+upload!", status_code=303)


@router.post("/upload-brand", response_class=HTMLResponse)
async def upload_brand_file(
    request: Request,
    brand_file: UploadFile = File(...),
):
    if brand_file.filename:
        content = await brand_file.read()
        save_brand_kit_file(brand_file.filename, content)
    return RedirectResponse(url="/generate?msg=File+uploaded!", status_code=303)


@router.post("/delete-brand", response_class=HTMLResponse)
async def delete_brand(request: Request, filename: str = Form(...)):
    delete_brand_kit_file(filename)
    return RedirectResponse(url="/generate?msg=File+deleted!", status_code=303)
