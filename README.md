# 求人作成エージェント モリシー

質問形式で情報を入力し、求人文を生成する Streamlit Web アプリ（準備中）。

## ローカル起動

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## デプロイ（Streamlit Community Cloud）

1. このリポジトリを GitHub に push
2. https://share.streamlit.io で GitHub 連携
3. Main file: `app.py` を指定して Deploy
