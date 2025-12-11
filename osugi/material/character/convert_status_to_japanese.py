import streamlit as st
from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def convert_status_to_japanese(updated_row: dict) -> str:
    """
    updated_row の中の status_text を日本語の特徴表現に変換する関数。
    例: "HP: 120, Attack: 80" → "高い体力と強い攻撃力を持つ"
    """
    status_text = updated_row.get("status_text", "")

    prompt = f"""
    あなたはゲームデザイナーです。
    以下の能力値を日本語の特徴表現に変換してください。
    数値は直接使わず、「高い体力」「俊敏」「防御が堅い」「魅力的」などの言葉にしてください。

    能力値: {status_text}

    出力は日本語の特徴表現のみ。
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()
