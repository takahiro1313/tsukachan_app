import requests
import cv2
import re
import xmltodict
import numpy as np
import streamlit as st
import base64
from openai import OpenAI


# OpenAI Vision APIを使ってISBNをOCRで読み取る関数
def extract_isbn_by_ocr(image_bytes: bytes) -> str | None:
    """
    画像からOpenAI Vision APIを使ってISBNテキストを抽出する。
    ISBN-13（978または979で始まる13桁）を返す。見つからなければNone。
    """
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # 画像をBase64エンコード
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 安価で高速なモデル
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """この画像から書籍のISBNコードを読み取ってください。

ISBNは通常「ISBN978-」や「ISBN979-」で始まる13桁の数字です。
ハイフンを除いた13桁の数字のみを返してください。

例: ISBN978-4-8443-6517-4 → 9784844365174

ISBNが見つからない場合は「NOT_FOUND」と返してください。
数字のみを返し、他の説明は不要です。"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"  # 高解像度で読み取り
                        }
                    }
                ]
            }
        ],
        max_tokens=50
    )

    result = response.choices[0].message.content.strip()

    # ISBNとして有効か確認（13桁で978または979で始まる）
    if result and result != "NOT_FOUND":
        # 数字以外を除去
        isbn = re.sub(r'\D', '', result)
        if len(isbn) == 13 and isbn.startswith(('978', '979')):
            return isbn

    return None


# 本のバーコードを読取って、ISBNコードを返す関数
# cv2.VideoCapture(0) を使う方法はデプロイ時に動かないため、Streamlitのカメラ入力コンポーネントを使用する方法に変更
def barcode_scanner(placeholder):
    img_file_buffer = st.camera_input("カメラでバーコードを読み取ってください", key="camera_input")

    if img_file_buffer is None:
        # 撮影していない
        return None

    # 撮影済み → OpenCVで処理
    bytes_data = img_file_buffer.getvalue()
    np_array = np.frombuffer(bytes_data, np.uint8)
    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 撮影画像を表示
    placeholder.image(frame_rgb, channels="RGB")

    # --- Step 1: OpenCVでバーコード検出を試みる ---
    barcode_reader = cv2.barcode.BarcodeDetector()

    try:
        ok, decoded_info, decoded_type, corners = barcode_reader.detectAndDecode(frame_rgb)
    except ValueError:
        decoded_info, decoded_type, corners = barcode_reader.detectAndDecode(frame_rgb)
        ok = bool(decoded_info)

    st.write(f"検出されたバーコード: {decoded_info}")

    isbn_code = None
    if decoded_info:
        # decoded_info が文字列ならリストに変換
        if isinstance(decoded_info, str):
            decoded_info = [decoded_info]

        for code in decoded_info:
            if code.startswith(('978', '979')):
                isbn_code = code
                break

    # バーコードからISBNが取得できた場合はそれを返す
    if isbn_code:
        return isbn_code

    # --- Step 2: バーコード検出失敗 → OpenAI Vision OCRにフォールバック ---
    st.info("バーコードからISBNを検出できませんでした。OCRで読み取りを試みています...")

    try:
        ocr_isbn = extract_isbn_by_ocr(bytes_data)
        if ocr_isbn:
            st.success(f"OCRでISBNを検出しました: {ocr_isbn}")
            return ocr_isbn
        else:
            st.warning("OCRでもISBNを検出できませんでした。")
    except Exception as e:
        st.error(f"OCR処理中にエラーが発生しました: {e}")

    # 撮影したがISBNが見つからなかった場合は "" を返す
    return ""


# def barcode_scanner(placeholder):

#     # カメラデバイスに接続（0は内蔵カメラ）
#     cap = cv2.VideoCapture(0)
#     # 解像度を高めに設定（1280x720）
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#     # バーコードリーダーを作成
#     barcode_reader = cv2.barcode.BarcodeDetector()

#     # 検出されたバーコード情報を格納する集合
#     detected_codes = set()
#     isbn_code = None

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         # 表示用（カラー） OpenCVはBGRフォーマットなので、RGBに変換
#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#         # 検出用（グレースケール）
#         frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#         # バーコード情報を取得
#         try:
#             # バーコード検出（グレースケールで処理）
#             ok, decoded_info, decoded_type, corners = barcode_reader.detectAndDecode(frame_gray) # type: ignore
#         except ValueError:
#             decoded_info, decoded_type, corners = barcode_reader.detectAndDecode(frame_gray)
#             ok = bool(decoded_info)

#         if len(decoded_info) > 2:
#             detected_codes.add(f'{decoded_info}')

#         # プレースホルダーに画像を表示（カラー映像）
#         placeholder.image(frame_rgb, channels="RGB")

#         # バーコードが検出されたらループを終了
#         if len(detected_codes) >= 2:
#             for code in detected_codes:
#                 if code.startswith(('978', '979')):  # ISBNは978 または 979 で始まる
#                     isbn_code = code
#                     break

#             # カメラ映像を消す
#             placeholder.empty()
#             break

#     cap.release()

#     return isbn_code


# 著者名を成形する関数
def clean_creator(creator):
    # creator が文字列の場合
    if isinstance(creator, str):
        creators = [creator]
    # 複数著者の場合はリストで渡される
    elif isinstance(creator, list):
        creators = creator
    else:
        return ""

    cleaned = []
    for c in creators:
        # 姓と名の間のカンマを削除（例: "山田, 太郎" → "山田 太郎"）
        name = c.replace(",", "")

        # 誕生年の除去（例: "山田 太郎 1972-" → "山田 太郎"）
        name = re.sub(r"\s*\d{4}-", "", name)

        # 前後の余分な空白を削除
        name = name.strip()

        cleaned.append(name)

    # 複数著者はカンマ区切りで結合
    return ", ".join(cleaned)


# NDC10の請求記号から第一次区分を取得する関数
def ndc10_first_level(call_number):
    # NDC10 第一次区分
    ndc10_lv1 = {
        "0": "総記",
        "1": "哲学",
        "2": "歴史",
        "3": "社会科学",
        "4": "自然科学",
        "5": "技術.工学",
        "6": "産業",
        "7": "芸術.美術",
        "8": "言語",
        "9": "文学",
    }

    # 先頭が数字かどうか確認。レスポンスにデータが無ければNoneの場合もある。
    if not call_number or not call_number[0].isdigit():
        return "不明"

    # 対応表にある区分を返す
    first_digit = call_number[0] #文字列の1桁目
    return ndc10_lv1.get(first_digit, "不明")


# ISBNを使って国立国会図書館検索APIから書誌情報を取得
# 参考：https://qiita.com/yknm1989/items/f77d22e1c7f1347d79b0
def get_api_book_info(isbn):
    # NDLサーチAPIのエンドポイントURL
    base_url = "https://iss.ndl.go.jp/api/opensearch"

    # APIリクエストのパラメータ
    params = {
        'isbn': isbn,
        'format': 'xml'
    }

    # リクエストを取得
    response = requests.get(base_url, params=params)

    # XMLを辞書型に変換
    book_info = xmltodict.parse(response.text)

    # call_number（請求記号）としてNDC10分類コードを取得
    subject = book_info['rss']['channel']['item']['dc:subject'] # 複数の分類区分の情報を含む
    # 優先順位リスト 本によってはNDC10が無い場合もあるため、NDC9, NDC8も順に確認
    ndc_priority = ["dcndl:NDC10", "dcndl:NDC9", "dcndl:NDC8"]

    call_number = None
    for ndc_type in ndc_priority:
        for item in subject:
            if isinstance(item, dict) and item.get('@xsi:type') == ndc_type:
                call_number = item.get('#text')
                break
        if call_number:
            break

    # publsiherは1社の場合は文字列、複数の場合は文字列のリストなので、辞書作成時に三項演算子で処理できるように事前定義
    publisher = book_info['rss']['channel']['item']['dc:publisher']

    # 入れ子になった辞書型を整理し、必要な情報のみ取得
    dict_api_book_info = {
    "isbn": isbn, # ISBN
    "title": book_info['rss']['channel']['item']['dc:title'], #タイトル
    "title_kana": book_info['rss']['channel']['item']['dcndl:titleTranscription'], #タイトルカナ表記
    "author": clean_creator(book_info['rss']['channel']['item']['dc:creator']), # 作者
    "author_kana": clean_creator(book_info['rss']['channel']['item']['dcndl:creatorTranscription']), # 作者カナ表記
    "pages": int(book_info['rss']['channel']['item']['dc:extent'].rstrip("p").split(",")[-1]), # ページ数：末尾の'p'を除いて数値に変換
    # ページ数：前書き・目次と本編のページ数が2つ記載されているケース（'28,386p'）があったので、カンマで分割して最期の数字を取得。常に最後を取得でいいかは保障無し。
    "call_number": call_number, # 請求記号のうちNDC10分類コード
    "genre": ndc10_first_level(call_number), # NDC10 第一次区分
    "publisher": ", ".join(publisher) if isinstance(publisher, list) else publisher, # 出版社
    }

    return dict_api_book_info
