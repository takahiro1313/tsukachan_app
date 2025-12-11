# import os
# from dotenv import load_dotenv

# 環境変数読み込み
# load_dotenv()
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

from supabase import create_client, Client
import streamlit as st

from supabase import create_client, Client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def apply_parameter_update(
    user_id_text: str,
    genre_name: str,
    prev_status: int,
    new_status: int,
    pages: int
) -> tuple[dict, dict, str]:
    """
    キャラクターのパラメータにジャンル補正を加算する関数
    - user_id_text: ユーザーID文字列
    - genre_name: ジャンル名
    - prev_status: 以前の読書ステータス (0:未登録, 1:登録済, 2:読了, 3:レビュー済)
    - new_status: 新しい読書ステータス (0:未登録, 1:登録済, 2:読了, 3:レビュー済)
    - pages: 本のページ数
    """

    # ステータスが後退している場合は処理しない
    if prev_status >= new_status:
        return {}, {}, f"処理スキップ: prev_status({prev_status}) > new_status({new_status}) のため更新しません。"

    # 1. キャラクター取得
    res_char = supabase.table("character").select("*").eq("user_id_text", user_id_text).execute()
    if not res_char.data:
        return {}, {}, f"エラー: user_id_text={user_id_text} のキャラクターが存在しません。"

    char = res_char.data[0]

    # 2. ジャンル補正値取得
    res_param = supabase.table("parameter").select("*").eq("genre_name", genre_name).execute()
    param = res_param.data[0] if res_param.data else {}

    # ステータス係数
    def get_status_coefficient(prev_status: int, new_status: int) -> float:
        transition_map = {
            (0, 1): 0.25,
            (0, 2): 1.25,
            (0, 3): 1.75,
            (1, 2): 1.0,
            (1, 3): 1.5,
            (2, 3): 0.5,
        }
        return transition_map.get((prev_status, new_status), 0.0)

    # ページ数係数
    def get_page_coefficient(p: int) -> float:
        if p < 140:
            return 1.0
        elif 140 <= p < 250:
            return 1.2
        elif 250 <= p < 360:
            return 1.4
        elif 360 <= p < 500:
            return 1.8
        else:
            return 2.4

    status_coef = get_status_coefficient(prev_status, new_status)
    page_coef = get_page_coefficient(pages)

    updated = {}
    for key, value in char.items():
        if key in param and isinstance(value, (int, float)) and isinstance(param[key], (int, float)):
            add_value = int(round(param[key] * status_coef * page_coef))
            updated[key] = value + add_value
        else:
            updated[key] = value

    # evolution更新
    if "evolution" in char and isinstance(char["evolution"], (int, float)):
        updated["evolution"] = char["evolution"] + pages
    else:
        updated["evolution"] = pages

    # 新しいステータスを更新
    updated["status"] = new_status

    # DB更新
    supabase.table("character").update(updated).eq("user_id_text", user_id_text).execute()

    return char, updated, "キャラクターを更新しました。"
