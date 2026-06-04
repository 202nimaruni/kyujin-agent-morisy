from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont


@dataclass
class ThumbnailCandidate:
    image_bytes: bytes
    score: int
    metrics: Dict[str, Any]
    prompt: str


TEMPLATE_STYLES: Dict[str, Dict[str, str]] = {
    "beauty_recruit": {
        "accent": "#b04773",
        "accent2": "#f6dfe9",
        "ribbon": "#c78d55",
        "bg": "#fff7fb",
        "stroke": "#e7c797",
        "sub": "#4d3c3c",
    },
    "default": {
        "accent": "#1f6fa1",
        "accent2": "#d8efff",
        "ribbon": "#1f6fa1",
        "bg": "#f7fbff",
        "stroke": "#9ecded",
        "sub": "#1f3f66",
    },
}


def _safe_json_from_content(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return {}
    return {}


def _chat_json(api_key: str, prompt: str, model: str = "gpt-4.1-mini", timeout_s: int = 45) -> Dict[str, Any]:
    res = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout_s,
    )
    res.raise_for_status()
    content = (res.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
    return _safe_json_from_content(content)


def _normalize_template(analysis: Dict[str, Any]) -> str:
    text = " ".join(
        [
            str(analysis.get("template_type", "")),
            str(analysis.get("industry", "")),
            str(analysis.get("job_type", "")),
            str(analysis.get("visual_direction", "")),
        ]
    )
    if any(k in text.lower() for k in ["beauty", "cosmetic", "aesthetic"]) or any(
        k in text for k in ["美容", "クリニック", "美容医療"]
    ):
        return "beauty_recruit"
    return "default"


def _analyze(payload: Dict[str, Any], final_text: str, feedback: str, api_key: str) -> Dict[str, Any]:
    prompt = f"""
求人原稿を解析し、JSONのみ返してください。
{{
  "industry":"",
  "job_type":"",
  "target":"",
  "main_message":"",
  "sub_message":"",
  "appeal_points":[],
  "template_type":"",
  "visual_direction":""
}}
template_typeは beauty_recruit または default のみ。
美容医療・美容クリニック・美容皮膚科・美容外科・サロン系は beauty_recruit を優先。

求人情報:
職種={payload.get("position_title","")}
勤務地={payload.get("location","")}
給与={payload.get("salary_range","")}
雇用形態={payload.get("employment_type","")}

完成原稿:
{final_text}

追加フィードバック:
{feedback}
"""
    data = _chat_json(api_key, prompt)
    if not isinstance(data, dict):
        data = {}
    data["template_type"] = _normalize_template(data)
    return data


def _build_copy(analysis: Dict[str, Any], payload: Dict[str, Any], final_text: str, api_key: str) -> Dict[str, Any]:
    fallback_title = str(payload.get("position_title", "") or "スタッフ募集")
    prompt = f"""
求人バナー用の短いコピーをJSONのみで返してください。
{{
  "main_copy":"",
  "sub_copy":"",
  "badges":["","","",""],
  "bottom_copy":""
}}
ルール:
- 日本語で作成
- main_copy: 18文字以内
- sub_copy: 30文字以内
- badges: 3〜4個、各14文字以内
- bottom_copy: 34文字以内
- 美容医療テンプレート時は上品・華やか・女性向けの語感

分析:
{json.dumps(analysis, ensure_ascii=False)}

求人タイトル:
{fallback_title}

本文:
{final_text}
"""
    parsed = _chat_json(api_key, prompt)
    badges = parsed.get("badges") if isinstance(parsed.get("badges"), list) else []
    badges = [str(x)[:14] for x in badges if str(x).strip()][:4]
    return {
        "main_copy": str(parsed.get("main_copy") or fallback_title)[:18],
        "sub_copy": str(parsed.get("sub_copy") or "求人募集中")[:30],
        "badges": badges or ["正社員募集", "研修制度あり", "残業ほぼなし"],
        "bottom_copy": str(parsed.get("bottom_copy") or "まずはお気軽にご応募ください")[:34],
    }


def _beauty_background_prompt(analysis: Dict[str, Any], copy: Dict[str, Any], variant: int) -> str:
    return f"""A luxurious Japanese beauty clinic recruitment banner background.
A clean and elegant cosmetic clinic interior with soft warm lighting, white marble, beige and pink accents, gold details, blurred shelves and reception counter in the background.
On the right side, a Japanese woman in her late 20s wearing elegant white clinic-style attire, holding a smartphone or tablet, looking down naturally with a soft smile.
Professional, feminine, premium, clean, bright, warm, beauty medical industry, SNS marketing job atmosphere.
Leave wide clean space on the left side for Japanese text overlay.
Soft pink beige and white color palette with subtle gold accents.
High-end cosmetic clinic advertising style.
Modern Japanese recruitment banner design.
Aspect ratio 4:3, 1200x900 composition.
Right 40%: person. Left 60%: empty for text.
Face, hands, smartphone should be naturally visible.
Background should have elegant blur and depth.
Avoid overexposure.
Style variation seed hint: {variant}.
No text.
No typography.
No logo.
No words.
No Japanese characters.
No signage.
No banner text."""


def _default_background_prompt(analysis: Dict[str, Any], variant: int) -> str:
    return f"""A photorealistic Japanese recruitment banner background.
Industry: {analysis.get("industry","general business")}.
Job type: {analysis.get("job_type","staff")}.
Composition: right side person, left side clean space for text.
Bright and clean ad-photo style. Variation: {variant}.
No text.
No typography.
No logo.
No words.
No Japanese characters.
No signage."""


def _generate_background(api_key: str, prompt: str, timeout_s: int = 120) -> Image.Image:
    res = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1536x1024",
        },
        timeout=timeout_s,
    )
    res.raise_for_status()
    data = res.json()
    item = (data.get("data") or [None])[0] or {}
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    if item.get("url"):
        img_res = requests.get(item["url"], timeout=timeout_s)
        img_res.raise_for_status()
        return Image.open(io.BytesIO(img_res.content)).convert("RGBA")
    raise RuntimeError("画像生成結果が取得できませんでした。")


def _fit_cover_right_anchor(src: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    tw, th = target_size
    sw, sh = src.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, nw - tw)
    top = max(0, (nh - th) // 2)
    return resized.crop((left, top, left + tw, top + th))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc" if bold else "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_round_rect(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int], radius: int, fill: str, outline: Optional[str] = None, width: int = 1) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _text(draw: ImageDraw.ImageDraw, pos: Tuple[int, int], text: str, fill: str, font: ImageFont.ImageFont) -> None:
    draw.text(pos, text, fill=fill, font=font)


def _compose_beauty(background: Image.Image, copy: Dict[str, Any]) -> Image.Image:
    canvas = _fit_cover_right_anchor(background, (1200, 900)).convert("RGBA")

    tint = Image.new("RGBA", canvas.size, (255, 246, 248, 95))
    canvas.alpha_composite(tint)

    draw = ImageDraw.Draw(canvas)
    left_w = 720

    panel = Image.new("RGBA", (left_w - 36, 690), (255, 255, 255, 0))
    pd = ImageDraw.Draw(panel)
    _draw_round_rect(pd, (0, 0, panel.width - 1, panel.height - 1), 28, fill=(255, 246, 250, 225), outline=(231, 199, 151, 200), width=2)
    panel = panel.filter(ImageFilter.GaussianBlur(0.5))
    canvas.alpha_composite(panel, (24, 20))

    # top ribbon
    _draw_round_rect(draw, (56, 44, 390, 98), 24, fill="#fff2ea", outline="#c89664", width=2)
    _text(draw, (76, 60), "美容医療業界で活躍！", "#b56a8f", _load_font(24, bold=True))

    _text(draw, (56, 132), str(copy.get("main_copy", "")), "#b04773", _load_font(60, bold=True))
    _text(draw, (58, 222), str(copy.get("sub_copy", "")), "#4d3c3c", _load_font(32))

    draw.line((56, 288, left_w - 74, 288), fill="#c78d55", width=2)

    badges = (copy.get("badges") or [])[:4]
    for i, badge in enumerate(badges):
        y = 316 + i * 88
        _draw_round_rect(draw, (56, y, left_w - 78, y + 64), 18, fill="#fffdfd", outline="#c78d55", width=2)
        draw.ellipse((72, y + 19, 98, y + 45), fill="#f4e3cf", outline="#c78d55", width=1)
        _text(draw, (112, y + 17), str(badge), "#6a4b42", _load_font(28, bold=True))

    # bottom CTA
    cta = Image.new("RGBA", (1148, 104), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cta)
    _draw_round_rect(cd, (0, 0, 1148, 104), 28, fill="#d887a9", outline="#c78d55", width=2)
    canvas.alpha_composite(cta, (26, 790))
    _text(draw, (52, 822), str(copy.get("bottom_copy", "")), "#ffffff", _load_font(34, bold=True))

    # tiny decorative sparkles
    for x, y in [(632, 82), (1092, 136), (1030, 744)]:
        draw.ellipse((x, y, x + 7, y + 7), fill=(255, 255, 255, 210))
        draw.ellipse((x + 11, y + 6, x + 16, y + 11), fill=(255, 255, 255, 190))

    return canvas


def _compose_default(background: Image.Image, copy: Dict[str, Any]) -> Image.Image:
    canvas = _fit_cover_right_anchor(background, (1200, 900)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    left_w = 720
    draw.rectangle((0, 0, left_w, 900), fill="#f7fbff")
    _text(draw, (52, 92), str(copy.get("main_copy", "")), "#173861", _load_font(56, bold=True))
    _text(draw, (56, 220), str(copy.get("sub_copy", "")), "#1f6fa1", _load_font(30, bold=True))
    badges = (copy.get("badges") or [])[:4]
    for i, b in enumerate(badges):
        y = 330 + i * 92
        _draw_round_rect(draw, (48, y, left_w - 46, y + 66), 18, fill="#ffffff", outline="#9ecded", width=2)
        _text(draw, (74, y + 18), str(b), "#1b3c66", _load_font(26, bold=True))
    draw.rectangle((0, 804, 1200, 900), fill="#1f6fa1")
    _text(draw, (36, 832), str(copy.get("bottom_copy", "")), "#ffffff", _load_font(30, bold=True))
    return canvas


def _to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _score_candidate(image_bytes: bytes, api_key: str, beauty_mode: bool = False) -> Dict[str, Any]:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = """
あなたは求人バナー品質審査員です。JSONのみ返してください。
{
  "readability":0-10,
  "design_quality":0-10,
  "professional_score":0-10,
  "right_crop_risk":true/false,
  "clinic_background_feel":0-10,
  "blue_tone_dominant":true/false,
  "decorative_richness":0-10,
  "luxury_feminine_feel":0-10
}
"""
    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4.1-mini",
                "temperature": 0,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }
                ],
            },
            timeout=40,
        )
        res.raise_for_status()
        content = (res.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
        parsed = _safe_json_from_content(content)
    except Exception:
        parsed = {}

    readability = int(parsed.get("readability", 6) or 6)
    design_quality = int(parsed.get("design_quality", 6) or 6)
    professional = int(parsed.get("professional_score", 6) or 6)
    clinic = int(parsed.get("clinic_background_feel", 7 if beauty_mode else 6) or (7 if beauty_mode else 6))
    deco = int(parsed.get("decorative_richness", 7 if beauty_mode else 6) or (7 if beauty_mode else 6))
    luxury = int(parsed.get("luxury_feminine_feel", 7 if beauty_mode else 6) or (7 if beauty_mode else 6))
    right_crop = bool(parsed.get("right_crop_risk", False))
    blue_dom = bool(parsed.get("blue_tone_dominant", False))
    base = (readability + design_quality + professional + clinic + deco + luxury) / 6 * 10
    penalty = (8 if right_crop else 0) + (8 if blue_dom and beauty_mode else 0)
    score = max(0, min(100, int(round(base - penalty))))
    return {
        "readability": readability,
        "design_quality": design_quality,
        "professional_score": professional,
        "clinic_background_feel": clinic,
        "decorative_richness": deco,
        "luxury_feminine_feel": luxury,
        "right_crop_risk": right_crop,
        "blue_tone_dominant": blue_dom,
        "score": score,
    }


def generate_thumbnail_candidates(
    *,
    payload: Dict[str, Any],
    final_text: str,
    api_key: str,
    feedback: str = "",
    n: int = 3,
) -> Tuple[List[ThumbnailCandidate], Dict[str, Any], Dict[str, Any]]:
    if not api_key:
        raise ValueError("OpenAI APIキーが未設定です。")
    analysis = _analyze(payload, final_text, feedback, api_key)
    copy = _build_copy(analysis, payload, final_text, api_key)
    template = _normalize_template(analysis)
    beauty_mode = template == "beauty_recruit"

    candidates: List[ThumbnailCandidate] = []
    for i in range(n):
        prompt = _beauty_background_prompt(analysis, copy, i) if beauty_mode else _default_background_prompt(analysis, i)
        bg = _generate_background(api_key, prompt)
        composed = _compose_beauty(bg, copy) if beauty_mode else _compose_default(bg, copy)
        png = _to_png_bytes(composed)
        metrics = _score_candidate(png, api_key, beauty_mode=beauty_mode)
        candidates.append(ThumbnailCandidate(image_bytes=png, score=int(metrics.get("score", 0)), metrics=metrics, prompt=prompt))

    candidates.sort(key=lambda c: c.score, reverse=True)
    best = candidates[0] if candidates else None
    need_retry = False
    if best:
        m = best.metrics
        need_retry = (
            int(m.get("design_quality", 0)) < 8
            or int(m.get("professional_score", 0)) < 8
            or bool(m.get("right_crop_risk", False))
            or (beauty_mode and bool(m.get("blue_tone_dominant", False)))
            or (beauty_mode and int(m.get("luxury_feminine_feel", 0)) < 8)
            or (beauty_mode and int(m.get("decorative_richness", 0)) < 7)
        )
    if need_retry:
        for i in range(n):
            prompt = _beauty_background_prompt(analysis, copy, i + 10) if beauty_mode else _default_background_prompt(analysis, i + 10)
            bg = _generate_background(api_key, prompt)
            composed = _compose_beauty(bg, copy) if beauty_mode else _compose_default(bg, copy)
            png = _to_png_bytes(composed)
            metrics = _score_candidate(png, api_key, beauty_mode=beauty_mode)
            candidates.append(ThumbnailCandidate(image_bytes=png, score=int(metrics.get("score", 0)), metrics=metrics, prompt=prompt))
        candidates.sort(key=lambda c: c.score, reverse=True)

    return candidates[:3], analysis, copy
