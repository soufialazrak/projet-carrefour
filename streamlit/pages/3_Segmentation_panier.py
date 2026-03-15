import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(page_title="Segmentation panier", layout="wide")

sidebar("Panier")

st.markdown('<div class="title">Segmentation panier</div>', unsafe_allow_html=True)