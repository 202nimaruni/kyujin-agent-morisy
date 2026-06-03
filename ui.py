from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent


def inject_styles() -> None:
    st.markdown(
        """
<style>
  #MainMenu, footer, header {visibility: hidden;}
  .block-container {padding-top: 1.2rem; max-width: 920px;}
  .morisy-hero {
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 55%, #ffffff 100%);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.2rem 1.4rem 1rem;
    margin-bottom: 1rem;
  }
  .morisy-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.2rem 1.3rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
  }
  .morisy-step {
    color: #64748b;
    font-size: 0.85rem;
    margin-bottom: 0.35rem;
  }
  .morisy-label {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }
  .morisy-hint {
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 0.8rem;
  }
  div.stButton > button[kind="primary"] {
    background: #2563eb;
    border: none;
    border-radius: 10px;
    font-weight: 700;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    logo_path = ROOT / "assets" / "logo.svg"
    col1, col2 = st.columns([1.2, 2.8])
    with col1:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
    with col2:
        st.markdown(
            """
<div class="morisy-hero">
  <div style="font-size:1.35rem;font-weight:800;color:#0f172a;">求人を、迷わず作る。</div>
  <div style="color:#475569;margin-top:.35rem;">
    質問に答えるだけで、トーン&マナーを反映した求人文を生成します。
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )


def progress_bar(step: int, total: int) -> None:
    st.progress(min(step / max(total, 1), 1.0))
    st.caption(f"ステップ {step + 1} / {total}")
