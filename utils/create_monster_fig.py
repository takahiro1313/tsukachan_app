from PIL import Image
import requests
import io
import streamlit as st
from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

dalle_model = "dall-e-3"

def create_monster_fig(prompt_image: str, monster_name: str) -> tuple[str, io.BytesIO]:
    """
    モンスター名と画像生成用プロンプトを組み合わせて画像を生成し、
    メモリ上に保持した画像データを返す関数。
    返却値は (image_url, BytesIO) のタプル。
    """

    # 名前を組み込んだ最終プロンプト
    final_prompt = f"""
{prompt_image}

このモンスターの名前は「{monster_name}」で、その雰囲気をデザインに反映してください。

"""

    # 画像生成
    illust = client.images.generate(
        model=dalle_model,
        prompt=final_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    # 生成された画像URLを取得
    image_url = illust.data[0].url

    # 画像をダウンロードしてメモリ上に保持
    response = requests.get(image_url)
    image_stream = io.BytesIO(response.content)

    # Pillowで開いて 512x512 に縮小
    img = Image.open(image_stream)
    img_resized = img.resize((512, 512))

    # JPEG形式で圧縮保存
    compressed_stream = io.BytesIO()
    img_resized.save(compressed_stream, format="JPEG", quality=85)
    compressed_stream.seek(0)

    return image_url, compressed_stream
