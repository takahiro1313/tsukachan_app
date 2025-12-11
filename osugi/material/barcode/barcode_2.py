# ブラウザでもうごくverとしてcopilotが提案したもの
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO

st.title("Webcam Barcode Reader (camera_input版)")

# ブラウザからカメラ入力
img_file = st.camera_input("カメラから撮影してください")

if img_file is not None:
    # PIL → NumPy(OpenCV形式) に変換
    img = Image.open(img_file)
    frame = np.array(img)

    # バーコード検出器
    barcode_reader = cv2.barcode.BarcodeDetector()
    try:
        result = barcode_reader.detectAndDecode(frame)
        if len(result) == 4:
            ok, decoded_info, decoded_type, corners = result
        else:
            decoded_info, decoded_type, corners = result
            ok = bool(decoded_info)
    except Exception as e:
        st.write(f"バーコード検出エラー: {e}")
        decoded_info, decoded_type, corners = [], [], []
        ok = False

    # 撮影画像を表示
    st.image(frame, channels="RGB")

    # バーコードが検出された場合
    if decoded_info:
        st.header("検出されたバーコード")
        for code in decoded_info:
            st.write(code)

            # ISBNコードっぽいものがあれば画像取得
            if "9784" in code:
                url = f"https://ndlsearch.ndl.go.jp/thumbnail/{code}.jpg"
                res = requests.get(url)
                if res.status_code == 200:
                    image = Image.open(BytesIO(res.content))
                    st.image(image, caption="取得した画像")
