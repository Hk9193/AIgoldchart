import streamlit as st

def apply_theme():
    st.markdown("""
        <style>
        body { background-color: #0e0e0e; color: #ffffff; }
        .stButton>button {
            background-color: #00FFD1;
            color: black;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)
