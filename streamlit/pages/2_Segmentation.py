import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(page_title="Segmentation RFM", layout="wide")

sidebar("RFM")

st.markdown('<div class="title">Segmentation RFM</div>', unsafe_allow_html=True)