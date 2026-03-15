import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(
    page_title="Vue d'ensemble",
    layout="wide"
)

sidebar("Vue")

st.markdown('<div class="title">Vue d’ensemble</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Indicateurs clés et aperçu global des données</div>',
    unsafe_allow_html=True
)