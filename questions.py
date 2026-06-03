from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence


@dataclass(frozen=True)
class Question:
    key: str
    label: str
    hint: str
    field_type: str  # text | textarea | select | multiselect | bullets
    presets: Sequence[str] = ()
    required: bool = True


QUESTIONS: List[Question] = [
    Question("company_name", "会社名", "正式名称またはサービス名", "text"),
    Question("position_title", "募集職種名", "例：カスタマーサクセス", "text"),
    Question(
        "employment_type",
        "雇用形態",
        "",
        "select",
        ("正社員", "契約社員", "業務委託", "アルバイト・パート", "インターン"),
    ),
    Question("location", "勤務地", "例：東京都渋谷区 / フルリモート", "text"),
    Question("salary_range", "給与", "例：月給30万円〜45万円", "text"),
    Question(
        "remote_policy",
        "リモート",
        "",
        "select",
        ("フルリモート", "ハイブリッド", "出社", "応相談"),
        required=False,
    ),
    Question("background", "募集背景", "なぜ今、この職種を募集するのか", "textarea"),
    Question("work_description", "仕事内容", "具体的な業務・期待する成果", "textarea"),
    Question(
        "requirements_must",
        "必須要件",
        "1行につき1項目（改行区切り）",
        "bullets",
        (
            "社会人経験2年以上",
            "ビジネスレベルのコミュニケーション力",
            "基本的なPCスキル",
        ),
    ),
    Question(
        "requirements_nice",
        "歓迎要件",
        "1行につき1項目",
        "bullets",
        ("業界経験", "マネジメント経験", "英語力"),
        required=False,
    ),
    Question("persona", "求める人物像", "価値観・スタンス・働き方", "textarea"),
    Question("environment", "働く環境・チーム", "体制・雰囲気・支援", "textarea"),
    Question("working_hours", "勤務時間", "例：9:00-18:00（休憩1h）", "text"),
    Question("holidays", "休日休暇", "例：週休2日制、祝日、年末年始", "text"),
    Question(
        "selection_flow",
        "選考フロー",
        "",
        "select",
        (
            "書類選考 → 面接1回 → 内定",
            "書類選考 → 面接2回 → 内定",
            "カジュアル面談 → 書類 → 面接 → 内定",
        ),
    ),
    Question(
        "apply_method",
        "応募方法",
        "",
        "select",
        ("応募フォームよりご応募ください", "メールでのご応募", "採用ページよりご応募ください"),
    ),
]
