import streamlit as st

from prompts import DEFAULT_TONES

st.set_page_config(page_title="求人作成エージェント モリシー", page_icon="📝", layout="wide")

st.title("求人作成エージェント モリシー")
st.caption("質問形式で情報を入力し、求人文を生成するツール（準備中）")

st.info(
    "媒体フォーマット・質問項目・非表示プロンプトは、指示いただいてから反映します。"
    " 現時点ではローカル環境の起動確認用の画面です。"
)

with st.expander("利用可能なトーン&マナー（プレビュー）"):
    for tone in DEFAULT_TONES:
        st.subheader(tone.name)
        st.write(tone.description)
        for rule in tone.style_rules:
            st.markdown(f"- {rule}")
