import streamlit as st

def show():
    st.title("新規登録ページ")
    st.write("ここでユーザー登録を行います")

    # 入力フォーム
    user_id = st.text_input("ユーザーID")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")

    # 登録ボタン
    if st.button("登録", key="regi"):
        if user_id and email and password:
            # 本来はここで Supabase に insert する処理を入れる
            st.success(f"ユーザー {user_id} を登録しました！（仮）")

            # 登録成功後はログインページへ戻す
            st.session_state.logincheck = 0
            st.session_state.page_state = "login"
            st.rerun()
        else:
            st.error("すべての項目を入力してください")

    # ログインページへ戻るボタン（常設）
    if st.button("ログインページへ戻る", key="login"):
        st.session_state.page_state = "login"
        st.rerun()