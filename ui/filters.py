import streamlit as st


def render_filters_and_sort():
  with st.expander("🎛️ Filtre avansate și Sortare după Preț", expanded=True):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
      sort_option = st.selectbox(
          "Ordonare preț",
          ["Fără sortare", "Preț crescător 📈", "Preț descrescător 📉"],
      )
    with f_col2:
      min_price = st.number_input(
          "Preț minim (Lei)", min_value=0.0, value=0.0, step=50.0
      )
    with f_col3:
      max_price = st.number_input(
          "Preț maxim (Lei)",
          min_value=0.0,
          value=0.0,
          max_value=200000.0,
          step=100.0,
          help="Lăsați 0.0 pentru fără limită maximă",
      )
  return sort_option, min_price, max_price