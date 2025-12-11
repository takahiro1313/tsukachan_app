import streamlit as st
from parameter_update import apply_parameter_update

def test_apply_parameter_update():
    # ダミーの入力値を用意
    user_id_text = "test_user_osugi"
    genre_name = "文学"        # parameter テーブルに存在するジャンル名を指定
    prev_status = 0            # 未登録
    new_status = 1             # 登録済
    pages = 200                # ページ数

    # 関数呼び出し
    char, updated, msg = apply_parameter_update(
        user_id_text=user_id_text,
        genre_name=genre_name,
        prev_status=prev_status,
        new_status=new_status,
        pages=pages
    )

    # 結果を表示
    st.write("char:", char)
    st.write("updated:", updated)
    st.info(msg)

# 実行
if __name__ == "__main__":
    test_apply_parameter_update()