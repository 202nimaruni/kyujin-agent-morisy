from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from prompts import DEFAULT_TONES, to_job_posting_markdown
from questions import QUESTIONS, Question
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
    if st.button("最初から作り直す"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.generated = ""
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
