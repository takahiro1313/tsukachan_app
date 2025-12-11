import streamlit as st
import pandas as pd
from parameter_update import apply_parameter_update
from supabase import create_client, Client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

label_map = {
    "attack": "攻撃",
    "defense": "防御",
    "agility": "素早さ",
    "charm": "魅力",
    "intelligence": "知力",
    "concentration": "集中",
    "magic": "魔力",
    "dexterity": "器用さ",
    "love": "愛情",
    "luck": "運"
}

keys_to_show = list(label_map.keys())

st.title("キャラクター補正シミュレーション")

user_id_text = st.text_input("ユーザーID", "test_user_osugi")

# ジャンル番号は1つだけ、選択肢を0〜3に変更
genre_index = st.selectbox("ジャンル番号", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], index=1)

# ステータスは前後をインデックスで選択
prev_status = st.selectbox("前ステータス", [0, 1, 2, 3], index=0)
new_status = st.selectbox("新ステータス", [0, 1, 2, 3], index=2)

pages = st.number_input("ページ数", min_value=1, max_value=2000, value=236)

#進化バー表示、進化可能回数を表示
st.write("進化ゲージ")
col1, col2 = st.columns([4, 1])
with col1:
    progress_bar = st.progress(0)         # 初期バー（0/1000）
with col2:
    level_text_ph = st.empty()            # 右のテキスト枠
    level_text_ph.write("進化レベル: 0")  # 初期表示

# Supabaseからユーザーのキャラクター画像URLを取得
response = supabase.table("character").select("image_URL").eq("user_id_text", user_id_text).execute()
if response.data and len(response.data) > 0:
    monster_url = response.data[0]["image_URL"]
else:
    # デフォルト画像（該当ユーザーに画像がない場合）
    monster_url = "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/default_monster.png"

frame_url = "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/monster_flame.png"

st.markdown(
    f"""
    <div style="position:relative; width:400px; height:400px; margin:auto;">
    <!-- モンスター画像（中央に小さめで配置） -->
    <img src="{monster_url}" style="width:250px; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); z-index:2;">

    <!-- 額縁画像（背景） -->
    <img src="{frame_url}" style="width:100%; height:100%; position:absolute; top:0; left:0; z-index:1;">
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("補正を適用"):
    # apply_parameter_updateを新しい引数仕様で呼び出し
    before, after = apply_parameter_update(
        user_id_text,
        genre_index,   # ジャンル番号は1つだけ
        prev_status,
        new_status,
        pages
    )

    # 必要なキーだけ抽出して日本語ラベルに変換
    filtered_before = {label_map[k]: before.get(k, None) for k in keys_to_show}
    filtered_after = {label_map[k]: after.get(k, None) for k in keys_to_show}

    # DataFrameにまとめて表示
    df = pd.DataFrame({
        "項目": list(filtered_before.keys()),
        "変更前": list(filtered_before.values()),
        "変更後": list(filtered_after.values())
    }).set_index("項目")

    st.success("補正前後キャラパラメータ")
    st.table(df)

    evolution_value = after.get("evolution", 0)

    progress_bar.progress(min(evolution_value / 1000, 1.0))  # 既存バーを更新
    level_text_ph.write(f"進化可能数: {evolution_value // 1000}")
