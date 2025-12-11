import streamlit as st
import pandas as pd
from supabase import create_client, Client
from update_evolution import update_evolution
from generate_monster_prompt import generate_monster_prompt
from upload_monster_image import upload_monster_image
from create_monster_fig import create_monster_fig
from convert_status_to_japanese import convert_status_to_japanese
from create_character_name import create_character_name

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
user_id_text = "test_user_osugi"

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
    <div style="position:relative; width:600px; height:600px; margin:auto; overflow:hidden;">
        <img src="{frame_url}" style="width:100%; height:100%; position:absolute; top:0; left:0; z-index:2;">
        <img src="{monster_url}" style="width:80%; height:80%; object-fit:cover; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); z-index:2;">
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
        # 1. revolution値を減らす
        updated_row = update_evolution(row, decrement=1000)
        if updated_row:
            # st.success("evolution値を更新しました！")

            # ステータスを日本語表現に変換
            description = convert_status_to_japanese(updated_row)
            # st.write(description)

            prompt_image, prompt_name = generate_monster_prompt(filtered_row, mapping_rows, description)
            # st.write("生成プロンプト:", prompt_image)

            character_name = create_character_name(prompt_name)
            # st.write("生成された名前:", character_name)

            supabase.table("character").update({"character_name": character_name}).eq("user_id_text", updated_row["user_id_text"]).execute()

            image_url, image_stream = create_monster_fig(prompt_image, character_name)

            # ファイル保存（Supabaseアップロード用）
            evolution_count = updated_row.get("evolution_count", 0)
            file_name = f"{updated_row['user_id_text']}_{evolution_count}.png"
            with open(file_name, "wb") as f:
                f.write(image_stream.getbuffer())

            # 画像アップロード＆URL更新
            new_url = upload_monster_image(file_name, updated_row["user_id_text"], evolution_count)
            # st.write("新しい画像URL:", new_url)

            st.rerun()

st.markdown(
    """
    <div style='width:100%; height:8px;'></div>
    """,
    unsafe_allow_html=True
)

if row:    
    # その下にテーブル表示
    filtered_row = {label_map[k]: row.get(k, None) for k in keys_to_show}
    df = pd.DataFrame({
        "項目": list(filtered_row.keys()),
        "値": list(filtered_row.values())
    }).set_index("項目")

#    st.success("キャラクターパラメータ")
    st.dataframe(df, use_container_width=True)

st.markdown(
    """
    <style>
    .tight-table td, .tight-table th {
        padding: 4px 8px;
        font-size: 0.9rem;
    }
    </style>
    <table class="tight-table" style="margin:auto;">
        <tr><th>項目</th><th>値</th></tr>
        <tr><td>攻撃</td><td>1</td></tr>
        <tr><td>防御</td><td>1</td></tr>
        <tr><td>素早さ</td><td>1</td></tr>
        <tr><td>魅力</td><td>1</td></tr>
        <tr><td>知力</td><td>1</td></tr>
        <tr><td>集中</td><td>1</td></tr>
        <tr><td>魔力</td><td>1</td></tr>
        <tr><td>閃き</td><td>1</td></tr>
        <tr><td>愛情</td><td>1</td></tr>
        <tr><td>運</td><td>1</td></tr>
    </table>
    """,
    unsafe_allow_html=True
)


import plotly.graph_objects as go

labels = [label_map[k] for k in keys_to_show]
values = [row.get(k, 0) for k in keys_to_show]

# labels = ["攻撃","防御","素早さ","魅力","知力","集中","魔力","閃き","愛情","運"]
# values = [3,5,2,7,4,6,1,8,5,9]


# 最大値を動的に決定（例：次の10単位に丸める）
max_val = max(values)
axis_max = ((max_val // 10) + 1) * 10

fig = go.Figure(
    data=go.Scatterpolar(
        r=values + [values[0]],   # 最初に戻る
        theta=labels + [labels[0]],
        fill='toself',
        line=dict(color="#b08d57")
    )
)

fig.update_layout(
    width=700,
    height=700,
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(
            visible=True,
            range=[0, axis_max],
            tickvals=list(range(0, axis_max+1, 2)),
            ticktext=[str(v) for v in range(0, axis_max+1, 2)],
            tickfont=dict(size=14, color="black")
        ),
        angularaxis=dict(
            tickfont=dict(size=16, color="black")
        )
    ),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)