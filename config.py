import streamlit as st


def setup_page():
  st.set_page_config(
      page_title="Service Smart | Motor Global Piese",
      page_icon="⚡",
      layout="wide",
  )
  st.markdown(
      """
    <style>
    .main { background-color: #0e1117; }
    .stTextInput input { background-color: #1a1c23; color: #ffffff; border: 1px solid #2d3748; border-radius: 10px; padding: 12px; font-size: 1.1rem; }
    .stNumberInput input { background-color: #1a1c23; color: #ffffff; border: 1px solid #2d3748; border-radius: 8px; }
    .stButton button { background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%); color: white; font-weight: bold; border: none; border-radius: 10px; padding: 0.7rem 1.5rem; width: 100%; font-size: 1.05rem; }
    .result-card { background-color: #161b22; border: 1px solid #30363d; padding: 18px; border-radius: 10px; margin-bottom: 12px; transition: border-color 0.2s; }
    .result-card:hover { border-color: #58a6ff; }
    div[data-testid="stForm"] small, div[data-testid="input-instruction"], .stTextInput small { display: none !important; }
    </style>
    """,
      unsafe_allow_html=True,
  )