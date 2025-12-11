import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ⚠️ 修正箇所: ハードコードされた接続情報を削除 ----------------------------------

# secrets.tomlから情報を読み込む
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError:
    # 接続情報が見つからない場合のエラー処理
    st.error("エラー: .streamlit/secrets.toml に Supabase の接続情報が記述されていません。ファイルを確認してください。")
    st.stop() 

@st.cache_resource
def init_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase_client()

# =================================================================
# データベース操作関数
# =================================================================

def update_read_status(book_id: str, new_status: str):
    """
    指定されたbook_idの書籍の read_status を更新する。
    """
    try:
        supabase.table("book") \
            .update({"read_status": new_status}) \
            .eq("book_id", book_id) \
            .execute()
        
        st.success(f"✅ 読了ステータスを '{new_status}' に更新しました。")
        # 更新後、セッションステートのキャッシュをクリアして再取得させる
        if 'detail_data' in st.session_state:
            del st.session_state['detail_data']
            st.rerun() # ページを再実行して最新のデータを表示
            return

    except Exception as e:
        st.error(f"データベースの更新中にエラーが発生しました: {e}")


def fetch_book_detail(book_id: str):
    """
    指定されたbook_idの書籍の詳細データを取得する。
    """
    # 詳細表示に必要な全ての項目を取得
    columns_to_select = "book_id, user_id, isbn, title, author, pages, publisher, purchase_or_library, paper_or_digital, read_status"
    
    try:
        response = supabase.table("book") \
            .select(columns_to_select) \
            .eq("book_id", book_id) \
            .execute()
        
        if response.data:
            return response.data[0] 
        else:
            return None
            
    except Exception as e:
        st.error(f"詳細データの取得中にエラーが発生しました: {e}")
        return None

# =================================================================
# Streamlit UI
# =================================================================

st.set_page_config(layout="wide")
st.title("📖 書籍詳細と編集")

# 1. book_id のチェック
if 'selected_book_id' not in st.session_state or not st.session_state['selected_book_id']:
    st.warning("詳細を表示する書籍が選択されていません。")
    if st.button("一覧に戻る"):
        st.switch_page("book_ichiran.py") 
    st.stop()

book_id = st.session_state['selected_book_id']

# 2. 詳細データを取得 (データキャッシュがない場合のみ)
if 'detail_data' not in st.session_state:
    st.session_state['detail_data'] = fetch_book_detail(book_id)

detail = st.session_state['detail_data']

if detail:
    st.subheader(f"『{detail['title']}』の詳細情報")

    # 3. 詳細データの表形式表示
    # 辞書をデータフレームに変換し、転置して詳細表を作成
    df = pd.DataFrame.from_dict(detail, orient='index', columns=['値'])
    df = df.rename(index={
        'book_id': 'ブックID',
        'user_id': 'ユーザーID',
        'isbn': 'ISBN',
        'title': 'タイトル',
        'author': '著者',
        'pages': 'ページ数',
        'publisher': '出版社',
        'purchase_or_library': '購入/図書館',
        'paper_or_digital': '紙/デジタル',
        'read_status': '読了ステータス (現状)'
    })
    
    # read_status の行をハイライトするためのスタイル設定
    def highlight_status(val):
        color = 'background-color: #ffcccc' if val == '未読' else 'background-color: #ccffcc'
        return color

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=False
    )
    
    st.divider()

    # 4. 編集機能: read_status
    st.header("📝 読了ステータスの編集")
    
    READ_OPTIONS = ["未読", "読了"]
    
    current_status = detail.get('read_status', READ_OPTIONS[0]) # データがない場合は未読をデフォルトに
    
    # SelectBox で新しいステータスを選択
    new_status = st.selectbox(
        "新しいステータスを選択:",
        options=READ_OPTIONS,
        # 現在のステータスを選択肢のデフォルトとして設定
        index=READ_OPTIONS.index(current_status) if current_status in READ_OPTIONS else 0
    )

    if st.button("ステータスを更新"):
        if new_status != current_status:
            update_read_status(book_id, new_status)
        else:
            st.warning("ステータスは変更されていません。")

else:
    st.error(f"ブックID: {book_id} の詳細情報が見つかりませんでした。")
    
# 一覧ページに戻るボタン
#st.button("↩️ 一覧に戻る", on_click=st.switch_page, args=["book_ichiran.py"])
# pages/detail_edit.py の末尾付近のボタン処理を以下に置き換える

# 警告の原因となる on_click/args の形式を避け、シンプルな if st.button で遷移させる

if st.button("↩️ 一覧に戻る"):
    # book_ichiran.py はメインページ（アプリの実行起点）なので、ファイル名を直接指定
    st.switch_page("book_ichiran.py")