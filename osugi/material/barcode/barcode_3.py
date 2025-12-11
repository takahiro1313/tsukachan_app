from pyzbar.pyzbar import decode
import cv2
import streamlit as st
from PIL import Image
import numpy as np

st.title("Barcode Reader (pyzbar版)")

img_file = st.camera_input("バーコードを撮影してください")

if img_file is not None:
    img = Image.open(img_file)
    frame = np.array(img)

    decoded_objects = decode(frame)
    st.image(frame, channels="RGB")

    if decoded_objects:
        for obj in decoded_objects:
            st.write("バーコード:", obj.data.decode("utf-8"))
    else:
        st.write("バーコードが検出できませんでした")
