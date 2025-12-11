import streamlit as st
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client
from streamlit_webrtc import webrtc_streamer

from utils.register_by_barcode_func import barcode_scanner, get_api_book_info
from utils.parameter_update import apply_parameter_update

# Supabase呼び出し
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# JSTタイムゾーンを定義
JST = timezone(timedelta(hours=9))

# user_idの取得（セッションステートから取得する想定）
user_id = st.session_state["username"]
# user_id = "test_user_01" # テスト用固定値

# 背景画像設定
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

st.title('本のバーコードから登録・編集')

if "isbn_code" not in st.session_state:
    camera_placeholder = st.empty()
    isbn_code = barcode_scanner(camera_placeholder)

    if isbn_code is None:
        # まだ撮影していない → 何も表示しない
        pass
    elif isbn_code == "":
        # 撮影したが失敗
        st.warning("ISBNを読み取れませんでした。")
        # 手入力用テキストボックスを表示
        manual_isbn = st.text_input("ISBNコードを手入力してください")
        # 入力があればそれを利用
        if manual_isbn:
            st.session_state["isbn_code"] = manual_isbn
            st.success(f'登録する本のISBN: {manual_isbn}')
    else:
        # 成功
        st.session_state["isbn_code"] = isbn_code
        st.success(f'登録する本のISBN: {isbn_code}')

# ISBNが取得できていれば書誌情報を取得（初回のみ）
if "isbn_code" in st.session_state and "dict_book_info_before" not in st.session_state:
    # Supabaseに登録済みの本か確認。Supabaseからuser_idとISBNで検索
    same_isbn_book = supabase.table("book").select("*").eq("user_id", user_id).eq("isbn", st.session_state["isbn_code"]).execute()

    if same_isbn_book.data and len(same_isbn_book.data) > 0: # 登録済みの本の場合
        # 既存レコードを編集対象にする
        dict_book_info_before = same_isbn_book.data[0]
        st.info("既存データを取得しました。編集して更新できます。")
    else: # 未登録の本の場合
        # 別ファイルで定義しているget_api_book_info関数を呼び出して、APIからISBNコードを使って書誌情報を新規取得
        dict_book_info_before = get_api_book_info(st.session_state["isbn_code"])
        st.info("APIから新規データを取得しました。")

    st.session_state["dict_book_info_before"] = dict_book_info_before

# 書誌情報がある場合は編集フォームを表示
if "dict_book_info_before" in st.session_state:
    dict_book_info_before = st.session_state["dict_book_info_before"]

    # dict_book_info_before をベースに dict_book_info_after を作成
    dict_book_info_after = dict_book_info_before.copy()

    # 編集不要なキー
    fixed_keys = ['isbn', 'pages', 'call_number', 'genre', 'book_id', 'user_id', 'created_at', 'updated_at']
    # 表示用ラベル
    dict_book_info_label = {
        "title": "タイトル",
        "title_kana": "タイトルカナ表記",
        "author": "著者",
        "author_kana": "著者カナ表記",
        "publisher": "出版社",
    }

    # 編集可能なキーだけ text_input に展開
    for key, value in dict_book_info_before.items():
        if key in dict_book_info_label: # text_inputで上書き編集可能にする
            dict_book_info_after[key] = st.text_input(
                label=dict_book_info_label[key],
                value=str(value) if value is not None else "",
            )

    # APIで取得できない追加情報を入力フォームで追加。既存データがあれば初期値に設定。
    dict_book_info_after["label"] = st.text_input("レーベル", value=dict_book_info_before.get("label", ""))
    dict_book_info_after["purchase_or_library"] = st.radio("購入/図書館", ["購入", "図書館"],
                                                            index=["購入", "図書館"].index(dict_book_info_before.get("purchase_or_library", "購入")))
    dict_book_info_after["paper_or_digital"] = st.radio("紙/電子書籍", ["紙", "電子書籍"],
                                                        index=["紙", "電子書籍"].index(dict_book_info_before.get("paper_or_digital", "紙")))
    dict_book_info_after["read_status"] = st.radio("読書状況", ["未読", "読書中", "読了"],
                                                    index=["未読", "読書中", "読了"].index(dict_book_info_before.get("read_status", "未読")))

    # 読み始めた日　st.date_input では空欄にできないので「入力する」選択肢を追加
    started_at_val = dict_book_info_before.get("started_at")
    completed_flag_start = st.checkbox("読み始めた日を入力する", value=started_at_val is not None)
    if completed_flag_start:
        dict_book_info_after["started_at"] = st.date_input(
            "読み始めた日",
            value=datetime.fromisoformat(started_at_val) if started_at_val else datetime.now(JST)
        ).isoformat()
    else:
        dict_book_info_after["started_at"] = None

    # 読了日　st.date_input では空欄にできないので「入力する」選択肢を追加
    completed_at_val = dict_book_info_before.get("completed_at")
    completed_flag_complete = st.checkbox("読了日を入力する", value=completed_at_val is not None)
    if completed_flag_complete:
        dict_book_info_after["completed_at"] = st.date_input(
            "読了日",
            value=datetime.fromisoformat(completed_at_val) if completed_at_val else datetime.now(JST)
        ).isoformat()
    else:
        dict_book_info_after["completed_at"] = None

    # レビュー
    dict_book_info_after["review"] = st.text_area("レビュー", value=dict_book_info_before.get("review", ""))
    # 選択肢が「公開する」なら True、そうでなければ False
    dict_book_info_after["review_published"] = (st.radio("レビュー公開設定", ["公開する", "公開しない"],
                                                index=0 if dict_book_info_before.get("review_published", False) else 1
                                                ) == "公開する"                                                )

    # 確認用（完成品では消す）
    # st.write("登録内容（完成時は消す）:", dict_book_info_after)

    # 登録ボタン
    if st.button("登録"):
        dict_book_info_after['user_id'] = user_id
        same_isbn_book_id = supabase.table("book").select("book_id").eq("user_id", user_id).eq("isbn", dict_book_info_after["isbn"]).execute()
        # 既存レコードがある場合
        if same_isbn_book_id.data and len(same_isbn_book_id.data) > 0:
            # 更新処理
            dict_book_info_after['updated_at'] = datetime.now(JST).isoformat()
            dict_book_info_after["prev_status"] = dict_book_info_before["new_status"]
            status_map = {"未読": 1, "読書中": 2, "読了": 3}
            dict_book_info_after["new_status"] = status_map[dict_book_info_after["read_status"]]
            book_id = same_isbn_book_id.data[0]["book_id"]
            supabase.table("book").update(dict_book_info_after).eq("book_id", book_id).execute()
            st.success("更新しました！")
        else:
            # 新規登録
            dict_book_info_after["prev_status"] = 0
            status_map = {"未読": 1, "読書中": 2, "読了": 3}
            dict_book_info_after["new_status"] = status_map[dict_book_info_after["read_status"]]
            dict_book_info_after['created_at'] = datetime.now(JST).isoformat()
            supabase.table("book").insert(dict_book_info_after).execute()
            st.success("登録しました！")

    # --- キャラクター更新処理（呼び出し） ---
        char, updated, msg = apply_parameter_update(
            user_id_text=user_id,
            genre_name=dict_book_info_after.get("genre", ""),
            prev_status=dict_book_info_after["prev_status"],
            new_status=dict_book_info_after["new_status"],
            pages=dict_book_info_after.get("pages", 0)
        )
        st.info(msg)

        st.session_state["registered"] = True

    # 登録成功後だけ「別の本を登録する」ボタンを表示
    if st.session_state.get("registered"):
        if st.button("別の本を登録する"):
            # user_id を保持したまま他のキーを削除
            for key in list(st.session_state.keys()):
                if key not in ["user_id"]:
                    st.session_state.pop(key)
            st.rerun()


