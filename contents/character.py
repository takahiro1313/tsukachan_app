import streamlit as st
import pandas as pd

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from supabase import create_client, Client
from utils.update_evolution import update_evolution
from utils.generate_monster_prompt import generate_monster_prompt
from utils.upload_monster_image import upload_monster_image
from utils.create_monster_fig import create_monster_fig
from utils.convert_status_to_japanese import convert_status_to_japanese
from utils.create_character_name import create_character_name

# Supabase設定
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 英語キーを日本語に変換する辞書
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

# ユーザーID入力
user_id_text = st.session_state["username"]

bg_url = "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/character_background_7.PNG"
st.markdown(f"""
<style>
.stApp {{
    background-image: url("{bg_url}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
</style>
""", unsafe_allow_html=True)

# Supabaseからユーザーのキャラクターデータを取得
response = supabase.table("character").select("*").eq("user_id_text", user_id_text).execute()

if response.data and len(response.data) > 0:
    row = response.data[0]
    # キャラクター名を取得
    character_name = row.get("character_name", "はじまりの卵")

    st.markdown(
        f"""
        <h1 style='text-align: center; font-size: 2.2rem; line-height: 1.2; margin-bottom: 0.5em;'>
            {character_name}
        </h1>
        """,
    unsafe_allow_html=True
    )
    # 画像URL
    monster_url = row.get(
        "image_URL",
        "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/default_monster.png"
    )
else:
    st.error("該当ユーザーが見つかりません")
    row = {}
    monster_url = "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/default_monster.png"

frame_url = "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/monster_flame.png"


# 画像表示
st.markdown(
    f"""
    <div style="position:relative; width:100%; max-width:600px; aspect-ratio:1/1; margin:auto; overflow:hidden;">
        <img src="{frame_url}" style="width:100%; height:100%; position:absolute; top:0; left:0; z-index:2;">
        <img src="{monster_url}" style="width:80%; height:80%; object-fit:contain; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); z-index:3;">
    </div>
    """,
    unsafe_allow_html=True
)

evolution_value = row.get("evolution", 0)

st.markdown(
    f"<h5 style='text-align: center; font-size: 1.6rem;'>進化可能数: {evolution_value // 1000}</h5>",
    unsafe_allow_html=True
    )

progress_ratio = min(evolution_value / 1000, 1.0) * 100

# 画像の直後に進化ゲージを表示
st.markdown(
    f"""
    <style>
    @keyframes shine {{
        0% {{ background-position: -200px 0; }}
        100% {{ background-position: 200px 0; }}
    }}
    .glow-bar {{
        background: #ddd;
        width: 400px;
        height: 30px;
        border-radius: 5px;
        margin: auto;
        overflow: hidden;
    }}
    .glow-fill {{
        background: linear-gradient(
            90deg,
            #4CAF50 25%,
            #8BC34A 50%,
            #4CAF50 75%
        );
        background-size: 200px 100%;
        animation: shine 2s linear infinite;
        height: 30px;
        border-radius: 5px;
    }}
    </style>
    <div class="glow-bar">
        <div class="glow-fill" style="width:{progress_ratio}%"></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='width:100%; height:16px;'></div>
    """,
    unsafe_allow_html=True
)

# CSSでボタンを中央＆金色に
st.markdown(
    """
    <style>
    div.stButton > button:first-child {
        display: block;       /* ブロック要素にする */
        margin: 0 auto;       /* 左右の余白を自動にして中央寄せ */
        background-color: #b8860b; /* dark goldenrod */
        box-shadow: 0 0 5px #b8860b;
        background: linear-gradient(
        90deg,
        #cfa94f 25%,
        #e0c170 50%,
        #cfa94f 75%
        );
        color: black;
        font-weight: bold;
        border-radius: 8px;
        font-size: 1.6rem;
        padding: 10px 20px;
        border: none;
    }
    div.stButton > button:first-child:disabled {
        background: #ccc !important;   /* ← グラデーションを完全に上書き */
        color: #666 !important;
        cursor: not-allowed;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# generate_monster_promptの前処理。label_mapに対応するキーだけ抽出
status_keys = list(label_map.keys())
filtered_row = {k: row.get(k, 0) for k in status_keys}

# species_mappingは別途取得しておく
mapping_rows = supabase.table("species_mapping").select("*").execute().data

# 3列に分けて真ん中にボタンを置く
col1, col2, col3 = st.columns([4, 2, 4])
with col2:
    disabled_flag = evolution_value < 1000

    if st.button("進化する", disabled=disabled_flag):
        st.session_state["show_overlay"] = True
        st.session_state["generating"] = True
        st.rerun()
# overlay 表示
if st.session_state.get("show_overlay", False):
    st.markdown("""
    <style>
    .overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.8);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .overlay video {
        max-width: 80%;
        max-height: 80%;
        border: 3px solid gold;
        box-shadow: 0 0 20px gold;
    }
    </style>
    <div class="overlay">
        <video autoplay muted loop>
            <source src="https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/summon_1_compressed.webm" type="video/webm">
        </video>
    </div>
    """, unsafe_allow_html=True)

    # 生成処理を overlay 中に実行
    if st.session_state.get("generating", False):
        updated_row = update_evolution(row, decrement=1000)
        if updated_row:
            description = convert_status_to_japanese(updated_row)
            prompt_image, prompt_name = generate_monster_prompt(filtered_row, mapping_rows, description)
            character_name = create_character_name(prompt_name)

            supabase.table("character").update(
                {"character_name": character_name}
            ).eq("user_id_text", updated_row["user_id_text"]).execute()

            image_url, image_stream = create_monster_fig(prompt_image, character_name)

            evolution_count = updated_row.get("evolution_count", 0)
            file_name = f"{updated_row['user_id_text']}_{evolution_count}.jpg"
            new_url = upload_monster_image(image_stream, updated_row["user_id_text"], evolution_count)

            # 完了したら overlay を消す
            st.session_state["show_overlay"] = False
            st.session_state["generating"] = False
            st.rerun()

st.markdown(
    """
    <div style='width:100%; height:8px;'></div>
    """,
    unsafe_allow_html=True
)
 
st.markdown(
    """
    <div style='width:100%; height:8px;'></div>
    """,
    unsafe_allow_html=True
)


import plotly.graph_objects as go
import streamlit as st

labels = [label_map[k] for k in keys_to_show]
values = [row.get(k, 0) for k in keys_to_show]

# 最大値を動的に決定（例：次の10単位に丸める）
max_val = max(values)
axis_max = ((max_val // 10) + 1) * 10

# レーダーチャート
fig = go.Figure(
    data=go.Scatterpolar(
        r=values + [values[0]],   # 最初に戻る
        theta=labels + [labels[0]],
        mode="none",              # 線やマーカーなしで塗りつぶしのみ
        fill='toself',
        fillcolor="rgba(197,145,14,0.75)"  # 魔法陣風の濃い光
    )
)

# レイアウト調整（レスポンシブ対応）
fig.update_layout(
    autosize=True,                # 自動サイズ調整
    margin=dict(l=20, r=20, t=40, b=20),  # 余白を小さめに
    paper_bgcolor="rgba(0,0,0,0)",   # 背景透過
    plot_bgcolor="rgba(0,0,0,0)",    # プロット領域も透過
    polar=dict(
        bgcolor="rgba(93,83,83,0.1)",  # 石板風の背景
        radialaxis=dict(
            visible=True,
            range=[0, axis_max],
            tickvals=list(range(0, axis_max+1, 2)),
            ticktext=[str(v) for v in range(0, axis_max+1, 2)],
            tickfont=dict(size=16, color="#a67c52", family="serif"),  # 少し小さめに
            showline=True,
            linecolor="#9E8060",   # 軸線を金属色に
            gridcolor="rgba(70,51,23,0.5)"  # グリッドを濃いめの金色に
        ),
        angularaxis=dict(
            tickfont=dict(size=16, color="#3D250A", family="serif")  # ラベルも羊皮紙風
        )
    ),
    showlegend=False
)

# Streamlitに表示（レスポンシブ）
st.plotly_chart(fig, width="stretch")

# フォントサイズを画面幅に応じて調整（CSSメディアクエリ）
st.markdown("""
<style>
@media (max-width: 600px) {
    .js-plotly-plot .xtick text,
    .js-plotly-plot .ytick text {
        font-size: 12px !important;
    }
}
</style>
""", unsafe_allow_html=True)

if st.session_state.get("show_overlay", False):
    st.markdown("""
    <style>
    .overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.8); /* 黒半透明 */
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .overlay video {
        max-width: 80%;
        max-height: 80%;
        border: 3px solid gold;
        box-shadow: 0 0 20px gold;
    }
    </style>
    <div class="overlay">
        <video autoplay muted>
            <source src="https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/summon_5.mp4" type="video/mp4">
        </video>
    </div>
    """, unsafe_allow_html=True)
