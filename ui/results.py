import streamlit as st
from utils import get_product_tag, highlight_search_terms


def render_results(filtered_data):
  # Preluăm query-ul curent din session_state pentru a ști ce să evidențiem
  current_query = st.session_state.get("last_query", "")

  for item in filtered_data:
    tag_text = get_product_tag(item["Produs"])

    # Aplicăm highlight-ul pe titlul produsului bazat pe termenul căutat
    highlighted_title = highlight_search_terms(item["Produs"], current_query)

    card_html = f"""
        <div class="result-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>
                    <span style="background: #1f6feb; color: white; padding: 3px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">{item["Magazin"]}</span>
                    <span style="background: #238636; color: white; padding: 3px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; margin-left: 8px;">{tag_text}</span>
                </div>
                <span style="font-size: 1.25rem; font-weight: 700; color: #3fb950;">{item["Preț"]}</span>
            </div>
            <div style="font-size: 1.05rem; font-weight: 600; margin-bottom: 6px;">
                <a href="{item["Sursă / Link"]}" target="_blank" style="color: #f0f6fc; text-decoration: none;" onMouseOver="this.style.color='#58a6ff'" onMouseOut="this.style.color='#f0f6fc'">{highlighted_title}</a>
            </div>
            <div style="font-size: 0.82rem;">
                <a href="{item["Sursă / Link"]}" target="_blank" style="color: #8b949e; text-decoration: none;" onMouseOver="this.style.color='#58a6ff'" onMouseOut="this.style.color='#8b949e'">🔗 Deschide pagina produsului în magazin</a>
            </div>
        </div>
        """
    st.markdown(card_html, unsafe_allow_html=True)