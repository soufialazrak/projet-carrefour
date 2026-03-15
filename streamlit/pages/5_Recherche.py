import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(page_title="Recherche", layout="wide")

sidebar("Recherche")

st.markdown('<div class="title">Recherche</div>', unsafe_allow_html=True)