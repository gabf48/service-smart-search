import asyncio
from scraper import search_parts
import streamlit as st


def render_search_form():
  with st.form(key="search_form"):
    col1, col2 = st.columns([5, 1])
    with col1:
      part_input = st.text_input(
          "Introdu Part Number sau produs:",
          placeholder="ex: G502, FX607VU, Memorie Corsair...",
          label_visibility="collapsed",
      )
    with col2:
      search_button = st.form_submit_button(
          "🔍 Caută", use_container_width=True
      )

  if search_button and part_input:
    st.session_state.last_query = part_input.strip()
    with st.spinner(
        f"Se interogează stocurile pentru `{st.session_state.last_query}`..."
    ):
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      st.session_state.search_results = loop.run_until_complete(
          search_parts(st.session_state.last_query)
      )
    st.rerun()