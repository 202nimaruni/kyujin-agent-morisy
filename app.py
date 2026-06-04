from __future__ import annotations

import base64
from io import BytesIO
from typing import Any, Dict, List

import streamlit as st

from prompts import DEFAULT_TONES, to_job_posting_markdown
from questions import QUESTIONS, Question
from thumbnail import generate_thumbnail_candidates
from ui import inject_styles, progress_bar, render_header


def _init_state() -> None:
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "answers" not in st.session_state:
        st.session_state.answers: Dict[str, Any] = {}
    if "tone_index" not in st.session_state:
        st.session_state.tone_index = 0
    if "generated" not in st.session_state:
        st.session_state.generated = ""
    if "thumb_candidates" not in st.session_state:
        st.session_state.thumb_candidates: List[Dict[str, Any]] = []
    if "thumb_selected" not in st.session_state:
        st.session_state.thumb_selected = 0


def _parse_bullets(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _render_field(q: Question) -> Any:
    current = st.session_state.answers.get(q.key)
    if q.field_type == "text":
        return st.text_input(q.label, value=current or "", placeholder=q.hint or None)
    if q.field_type == "textarea":
        return st.text_area(q.label, value=current or "", height=140, placeholder=q.hint or None)
    if q.field_type == "select":
        options = list(q.presets)
        idx = options.index(current) if current in options else 0
        return st.selectbox(q.label, options, index=idx)
    if q.field_type == "bullets":
        default = "\n".join(current) if isinstance(current, list) else (current or "")
        text = st.text_area(q.label, value=default, height=120, placeholder=q.hint or None)
        presets = st.multiselect("よく使う項目から追加", list(q.presets), default=[])
        merged = _parse_bullets(text)
        for p in presets:
            if p not in merged:
                merged.append(p)
        return merged
    return st.text_input(q.label, value=current or "")


def _validate(q: Question, value: Any) -> bool:
    if not q.required:
        return True
    if q.field_type == "bullets":
        return bool(value)
    return bool(str(value).strip())


def _payload() -> Dict[str, Any]:
    a = st.session_state.answers
    return {
        "company_name": a.get("company_name"),
        "position_title": a.get("position_title"),
        "employment_type": a.get("employment_type"),
        "location": a.get("location"),
        "salary_range": a.get("salary_range"),
        "remote_policy": a.get("remote_policy"),
        "background": a.get("background"),
        "work_description": a.get("work_description"),
        "requirements_must": a.get("requirements_must") or [],
        "requirements_nice": a.get("requirements_nice") or [],
        "persona": a.get("persona"),
        "environment": a.get("environment"),
        "working_hours": a.get("working_hours"),
        "holidays": a.get("holidays"),
        "selection_flow": a.get("selection_flow"),
        "apply_method": a.get("apply_method"),
    }


def _question_step() -> None:
    total = len(QUESTIONS) + 1  # + tone
    step = st.session_state.step
    progress_bar(step, total)

    if step < len(QUESTIONS):
        q = QUESTIONS[step]
        st.markdown('<div class="morisy-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="morisy-step">質問</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="morisy-label">{q.label}</div>', unsafe_allow_html=True)
        if q.hint:
            st.markdown(f'<div class="morisy-hint">{q.hint}</div>', unsafe_allow_html=True)

        value = _render_field(q)
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("戻る", disabled=step == 0):
                st.session_state.step -= 1
                st.rerun()
        with c2:
            if st.button("次へ", type="primary"):
                if not _validate(q, value):
                    st.error("入力してください。")
                else:
                    st.session_state.answers[q.key] = value
                    st.session_state.step += 1
                    st.rerun()
        return

    # tone step
    st.markdown('<div class="morisy-card">', unsafe_allow_html=True)
    st.markdown('<div class="morisy-label">トーン&マナー</div>', unsafe_allow_html=True)
    tone_names = [t.name for t in DEFAULT_TONES]
    idx = st.radio(
        "文体を選択",
        range(len(tone_names)),
        format_func=lambda i: tone_names[i],
        index=st.session_state.tone_index,
    )
    st.session_state.tone_index = idx
    tone = DEFAULT_TONES[idx]
    st.info(tone.description)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("戻る"):
            st.session_state.step -= 1
            st.rerun()
    with c2:
        if st.button("求人を生成", type="primary"):
            st.session_state.generated = to_job_posting_markdown(_payload(), tone)
            st.session_state.step = len(QUESTIONS) + 1
            st.rerun()


def _result_step() -> None:
    st.success("求人文を生成しました。内容を確認し、コピーしてご利用ください。")
    st.markdown(st.session_state.generated)
    st.download_button(
        "Markdownをダウンロード",
        data=st.session_state.generated,
        file_name="job_posting.md",
        mime="text/markdown",
    )
    st.markdown("---")
    st.subheader("求人サムネイル（美容医療向け広告品質）")
    st.caption("日本語テキストは画像生成AIに描画させず、背景生成後にアプリ側で合成します。")

    api_key = st.text_input("OpenAI APIキー", type="password", key="openai_api_key")
    feedback = st.text_area(
        "サムネイル追加要望（任意）",
        value="",
        height=80,
        placeholder="例: もっと華やかに、ピンクベージュを強めに、人物の切れを抑えてください",
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        generate = st.button("サムネイルを生成", type="primary")
    with c2:
        regenerate = st.button("要望を反映して再生成")

    if generate or regenerate:
        if not api_key.strip():
            st.error("APIキーを入力してください。")
        else:
            with st.spinner("背景生成→デザイン合成→品質評価中です..."):
                try:
                    candidates, analysis, copy = generate_thumbnail_candidates(
                        payload=_payload(),
                        final_text=st.session_state.generated,
                        api_key=api_key.strip(),
                        feedback=feedback if regenerate else "",
                        n=3,
                    )
                    encoded: List[Dict[str, Any]] = []
                    for c in candidates:
                        encoded.append(
                            {
                                "png_b64": base64.b64encode(c.image_bytes).decode("ascii"),
                                "score": c.score,
                                "metrics": c.metrics,
                            }
                        )
                    st.session_state.thumb_candidates = encoded
                    st.session_state.thumb_selected = 0
                    st.success("サムネイル候補を生成しました。")
                    st.caption(f"テンプレート判定: {analysis.get('template_type', 'default')}")
                    st.caption(f"コピー案: {copy.get('main_copy', '')} / {copy.get('sub_copy', '')}")
                except Exception as e:
                    st.error(f"サムネイル生成に失敗しました: {e}")

    if st.session_state.thumb_candidates:
        options = [f"候補 {i + 1}" for i in range(len(st.session_state.thumb_candidates))]
        st.session_state.thumb_selected = st.radio(
            "候補を選択",
            options=range(len(options)),
            format_func=lambda i: options[i],
            index=min(st.session_state.thumb_selected, len(options) - 1),
            horizontal=True,
        )

        cols = st.columns(len(st.session_state.thumb_candidates))
        for i, cand in enumerate(st.session_state.thumb_candidates):
            with cols[i]:
                png = base64.b64decode(cand["png_b64"])
                st.image(png, caption=f"候補{i+1} / score {cand.get('score', 0)}", use_container_width=True)
                m = cand.get("metrics", {})
                st.caption(
                    f"design={m.get('design_quality', '-')}, luxury={m.get('luxury_feminine_feel', '-')}, "
                    f"deco={m.get('decorative_richness', '-')}"
                )

        selected = st.session_state.thumb_candidates[st.session_state.thumb_selected]
        selected_png = base64.b64decode(selected["png_b64"])
        st.download_button(
            "選択中サムネイルをダウンロード",
            data=BytesIO(selected_png).getvalue(),
            file_name="job_thumbnail.png",
            mime="image/png",
        )

    if st.button("最初から作り直す"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.generated = ""
        st.session_state.thumb_candidates = []
        st.session_state.thumb_selected = 0
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="求人作成エージェント モリシー",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()
    _init_state()
    render_header()

    if st.session_state.step > len(QUESTIONS):
        _result_step()
    else:
        _question_step()


if __name__ == "__main__":
    main()
