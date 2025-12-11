import os
import streamlit as st
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

# =====================================================
# ページ設定（最初に実行・例外が出ない構成）
# =====================================================
st.set_page_config(page_title="新規ユーザー登録")

# =====================================================
# 背景画像（失敗しても落ちない）
# =====================================================
bg_url = "https://wmcppeiutkzrxrgwguvm.supabase.co/storage/v1/object/public/material/character_background_5.png"

try:
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
except:
    pass

# =====================================================
# CSS（常に安全）
# =====================================================
st.markdown("""
<style>
div.stButton > button:first-child {
    display: block;
    margin: 0 auto;
    background-color: #b8860b;
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
    background: #ccc !important;
    color: #666 !important;
    cursor: not-allowed;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* 🔽 Streamlit Authenticator のログインボタン専用CSS */
div[data-testid="stForm"] button {
    background-color: #b8860b !important;
    background: linear-gradient(
        90deg,
        #cfa94f 25%,
        #e0c170 50%,
        #cfa94f 75%
    ) !important;
    color: black !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    font-size: 1.6rem !important;
    padding: 10px 20px !important;
    border: none !important;
    box-shadow: 0 0 5px #b8860b !important;
}
</style>
""", unsafe_allow_html=True)

st.title("新規ユーザー登録")

# =====================================================
# Supabase 接続（失敗してもページは落とさない）
# =====================================================
supabase = None
try:
    from supabase import create_client
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    supabase = None

# =====================================================
# フォーム
# =====================================================
with st.form("register_form"):
    new_username = st.text_input("ユーザーID")
    new_name = st.text_input("表示名")
    new_email = st.text_input("メールアドレス")
    new_password = st.text_input("パスワード", type="password")
    submitted = st.form_submit_button("登録")

# =====================================================
# 登録処理（ボタン押下時のみ）
# =====================================================
if submitted:
    if not new_username or not new_password:
        st.error("ユーザーIDとパスワードは必須です")
    else:
        # config.yaml の場所
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
        except:
            CONFIG_PATH = None

        # config 読み込み
        if not CONFIG_PATH or not os.path.exists(CONFIG_PATH):
            st.error("config.yaml が見つかりません")
        else:
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                    config = yaml.load(file, Loader=SafeLoader)
            except:
                st.error("config.yaml の読み込みに失敗しました")
                config = None

            # バリデーション
            if config:
                if "credentials" not in config:
                    config["credentials"] = {"usernames": {}}
                if "usernames" not in config["credentials"]:
                    config["credentials"]["usernames"] = {}

                # 重複チェック
                if new_username in config["credentials"]["usernames"]:
                    st.error("このユーザーIDはすでに使われています")
                else:
                    # パスワードをハッシュ化
                    try:
                        hashed_password = stauth.utilities.hasher.Hasher.hash(new_password)
                    except:
                        st.error("パスワードの暗号化に失敗しました")
                        hashed_password = None

                    if hashed_password:
                        # ユーザー登録
                        config["credentials"]["usernames"][new_username] = {
                            "name": new_name,
                            "email": new_email,
                            "password": hashed_password
                        }

                        # 保存
                        try:
                            with open(CONFIG_PATH, "w", encoding="utf-8") as file:
                                yaml.dump(config, file, allow_unicode=True)
                        except:
                            st.error("config.yaml の書き込みに失敗しました")

                        # セッション
                        st.session_state["user_id"] = new_username

                        # Supabase 登録
                        if supabase:
                            try:
                                supabase.table("character").insert({
                                    "user_id_text": new_username
                                }).execute()
                            except Exception as e:
                                st.warning(f"Supabase登録スキップ: {e}")

                        st.success("登録できました！ログイン画面からログインしてください。")

# =====================================================
# 戻るボタン
# =====================================================
if st.button("ログイン画面へ戻る"):
    st.session_state["page"] = "main"
    st.rerun()