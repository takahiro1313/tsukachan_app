import streamlit as st
from supabase import create_client, Client
import time

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bucket_name = "material"

def upload_monster_image(file_name: str, user_id_text: str, evolution_count: int) -> str:
    """
    画像をSupabase Storageにアップロードし、公開URLをcharacterテーブルに保存する関数。
    ファイル名は user_id_text と進化回数でユニーク化。
    """
    # ユニークなファイル名を生成
    unique_file_name = f"{user_id_text}_{evolution_count}.png"

    # 画像アップロード（存在すれば上書き、なければ新規作成）
    with open(file_name, "rb") as f:
        supabase.storage.from_(bucket_name).update(unique_file_name, f)

    # 公開URL取得
    public_url = supabase.storage.from_(bucket_name).get_public_url(unique_file_name)

    # characterテーブル更新
    supabase.table("character").update({"image_URL": public_url}).eq("user_id_text", user_id_text).execute()

    return public_url