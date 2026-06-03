from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ToneAndManner:
    name: str
    description: str
    style_rules: List[str]


DEFAULT_TONES: List[ToneAndManner] = [
    ToneAndManner(
        name="誠実・端的（ビジネス）",
        description="落ち着いた敬体。冗長にせず、要点を明確に。",
        style_rules=[
            "敬体（です・ます）で統一する",
            "結論→理由→補足の順で書く",
            "誇大表現は避け、事実ベースで書く",
            "専門用語は必要最小限。初出は補足する",
        ],
    ),
    ToneAndManner(
        name="フレンドリー（応募導線重視）",
        description="親しみやすく、応募ハードルを下げる。読みやすさ最優先。",
        style_rules=[
            "柔らかい語尾で統一する（〜です/〜できます）",
            "箇条書きを多用し、1文を短くする",
            "応募手順や選考フローを明確にする",
        ],
    ),
    ToneAndManner(
        name="ハイレベル（エンジニア向け）",
        description="技術者に刺さる情報密度。スコープ・裁量・技術スタックを具体化。",
        style_rules=[
            "技術スタック・開発プロセス・裁量の情報を厚めに",
            "期待値と評価軸を明確に",
            "抽象語を避け、具体例で示す",
        ],
    ),
]


HIDDEN_GUIDELINES: List[str] = [
    "差別的表現や年齢・性別等の不適切な要件は書かない",
    "給与や条件は誤認を招かない範囲で書く。レンジを提示できるなら提示する",
    "応募者に必要な情報（勤務地/雇用形態/勤務時間/休日/試用期間/選考フロー）を欠かさない",
    "会社の自慢だけで終わらず、仕事内容・期待成果・支援体制も書く",
    "『アットホーム』『根性』などの曖昧語は具体化する",
]


SECTION_ORDER = [
    "職種・募集背景",
    "仕事内容",
    "必須要件",
    "歓迎要件",
    "求める人物像",
    "働く環境・チーム",
    "勤務条件",
    "選考フロー",
    "応募方法",
]


def to_job_posting_markdown(payload: Dict[str, Any], tone: ToneAndManner) -> str:
    company = payload.get("company_name") or "貴社"
    position = payload.get("position_title") or "募集職種"
    employment = payload.get("employment_type") or "雇用形態"
    location = payload.get("location") or "勤務地"
    salary = payload.get("salary_range") or "給与"

    must = payload.get("requirements_must") or []
    nice = payload.get("requirements_nice") or []
    persona = payload.get("persona") or ""
    work = payload.get("work_description") or ""
    background = payload.get("background") or ""
    environment = payload.get("environment") or ""
    hours = payload.get("working_hours") or ""
    holidays = payload.get("holidays") or ""
    selection = payload.get("selection_flow") or ""
    apply = payload.get("apply_method") or ""

    def bullets(items: List[str]) -> str:
        if not items:
            return "- （入力してください）"
        return "\n".join([f"- {x}" for x in items])

    lines: List[str] = []
    lines.append(f"# {position}（{employment}）｜{company}")
    lines.append("")
    lines.append(f"- **勤務地**: {location}")
    lines.append(f"- **給与**: {salary}")
    if payload.get("remote_policy"):
        lines.append(f"- **リモート**: {payload.get('remote_policy')}")
    if payload.get("work_style"):
        lines.append(f"- **勤務スタイル**: {payload.get('work_style')}")
    lines.append("")

    # Sections
    lines.append("## 職種・募集背景")
    lines.append(background or "（募集背景を入力してください）")
    lines.append("")

    lines.append("## 仕事内容")
    lines.append(work or "（仕事内容を入力してください）")
    if payload.get("responsibilities"):
        lines.append("")
        lines.append("**主な業務**")
        lines.append(bullets(payload.get("responsibilities") or []))
    if payload.get("tech_stack"):
        lines.append("")
        lines.append("**技術スタック**")
        lines.append(bullets(payload.get("tech_stack") or []))
    lines.append("")

    lines.append("## 必須要件")
    lines.append(bullets(must))
    lines.append("")

    lines.append("## 歓迎要件")
    lines.append(bullets(nice))
    lines.append("")

    lines.append("## 求める人物像")
    lines.append(persona or "（求める人物像を入力してください）")
    lines.append("")

    lines.append("## 働く環境・チーム")
    lines.append(environment or "（チーム/環境を入力してください）")
    if payload.get("benefits"):
        lines.append("")
        lines.append("**制度・福利厚生**")
        lines.append(bullets(payload.get("benefits") or []))
    lines.append("")

    lines.append("## 勤務条件")
    if hours:
        lines.append(f"- **勤務時間**: {hours}")
    else:
        lines.append("- **勤務時間**: （入力してください）")
    if holidays:
        lines.append(f"- **休日休暇**: {holidays}")
    else:
        lines.append("- **休日休暇**: （入力してください）")
    if payload.get("trial_period"):
        lines.append(f"- **試用期間**: {payload.get('trial_period')}")
    lines.append("")

    lines.append("## 選考フロー")
    lines.append(selection or "（選考フローを入力してください。例：書類→面接2回→内定）")
    lines.append("")

    lines.append("## 応募方法")
    lines.append(apply or "（応募方法を入力してください。例：フォームよりご応募ください）")
    lines.append("")

    # Tone rules + hidden guidelines are applied as a “post-checklist” section (non-visible in final by default)
    if payload.get("_include_internal_checklist"):
        lines.append("---")
        lines.append("## （内部チェック）トーン&注意点")
        lines.append("")
        lines.append("**トーン**")
        lines.append(bullets([f"{tone.name}: {tone.description}"] + tone.style_rules))
        lines.append("")
        lines.append("**注意点**")
        lines.append(bullets(HIDDEN_GUIDELINES))
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def openai_compatible_generate(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout_s: int = 45,
) -> str:
    """
    OpenAI互換の /chat/completions を叩く最小実装。
    例: OpenAI, Azure OpenAI互換ゲートウェイ, ローカルLLMの互換サーバーなど。
    """
    import requests

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()

