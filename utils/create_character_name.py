import streamlit as st
from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def create_character_name(description: str) -> str:
    """
    モンスターの特徴説明を基に、かっこいい名前を生成する関数。
    """
    prompt = f"""
    あなたはファンタジーゲームのキャラクターデザイナーです。
    以下の特徴を持つモンスターに、かっこいい名前を付けてください。

    特徴: {description}

    条件:
    - 神話的で詩的な響き
    - 出力は名前のみ
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()
