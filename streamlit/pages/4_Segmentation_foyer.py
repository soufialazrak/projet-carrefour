import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(page_title="Segmentation foyer", layout="wide")

sidebar("Foyer")

st.markdown('<div class="title">Segmentation foyer</div>', unsafe_allow_html=True)