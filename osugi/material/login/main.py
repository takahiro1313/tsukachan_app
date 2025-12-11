import streamlit as st
import new_regi  # ← ファイル名に合わせて修正

users = {"osugi": "tes"}

# --- セッション初期化 ---
if "logincheck" not in st.session_state:
    st.session_state.logincheck = 0  # 0=未ログイン, 1=成功
if "page_state" not in st.session_state:
    st.session_state.page_state = "login"  # login or new_regi

# --- ログインページ ---
if st.session_state.page_state == "login":
    st.title("ログインページ")

    if st.session_state.logincheck == 0:
        user_id = st.text_input("ユーザーID")
        password = st.text_input("パスワード", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("ログイン"):
                if user_id in users and users[user_id] == password:
                    st.session_state.logincheck = 1
                    st.success("ログイン成功！")
                    st.rerun()
                else:
                    st.error("ユーザーIDまたはパスワードが違います")
        with col2:
            if st.button("新規登録へ"):
                st.session_state.page_state = "new_regi"
                st.rerun()

# --- 新規登録ページ ---
elif st.session_state.page_state == "new_regi":
    new_regi.show()
#    if st.button("ログインページへ戻る"):
#        st.session_state.page_state = "login"
#        st.rerun()

# --- ログイン後のメニュー ---
if st.session_state.logincheck == 1 and st.session_state.page_state == "login":
    st.sidebar.title("メニュー")
    page = st.sidebar.selectbox("ページ選択", ["ホーム", "キャラクター", "本の登録", "ログアウト"])

    if page == "ホーム":
        st.write("ログイン成功です。")
    elif page == "キャラクター":
        import character
        character.show()
    elif page == "本の登録":
        import book_registore
        book_registore.show()
    elif page == "ログアウト":
        st.session_state.logincheck = 0
        st.warning("ログアウトしました。")
        st.rerun()