import streamlit as st
from supabase import create_client, Client
import time
import io
import tempfile

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bucket_name = "material"

def upload_monster_image(image_stream: io.BytesIO, user_id_text: str, evolution_count: int) -> str:
    """
    BytesIOを一時ファイルに保存してSupabase Storageにアップロードし、
    公開URLをcharacterテーブルに保存する関数。
    """
    unique_file_name = f"{user_id_text}_{evolution_count}.jpg"  # JPEGに統一

    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_stream.getbuffer())
        tmp_path = tmp.name

    # Supabaseにアップロード（存在すれば上書き）
    supabase.storage.from_(bucket_name).update(unique_file_name, tmp_path)

    # 公開URL取得
    public_url = supabase.storage.from_(bucket_name).get_public_url(unique_file_name)

    # characterテーブル更新
    supabase.table("character").update({"image_URL": public_url}).eq("user_id_text", user_id_text).execute()

    return public_url