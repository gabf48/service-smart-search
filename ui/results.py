import html
import re
import textwrap

import streamlit as st
from utils import get_product_tag
from utils.filters import parse_price_for_sorting


def render_results(filtered_data):
  # Preluăm query-ul curent din session_state pentru a ști ce să evidențiem
  current_query = st.session_state.get("last_query", "")

  # Determinăm cel mai mic preț pe fiecare categorie (din rezultatele afișate)
  min_price_by_category = {}
  for item in filtered_data:
    category = item.get("Categorie") or get_product_tag(item.get("Produs", ""))
    price_val = parse_price_for_sorting(item.get("Preț"))
    if price_val == float("inf"):
      continue
    current_min = min_price_by_category.get(category)
    if current_min is None or price_val < current_min:
      min_price_by_category[category] = price_val

  for item in filtered_data:
    raw_title = item.get("Produs", "")
    tag_text = item.get("Categorie") or get_product_tag(raw_title)
    price_val = parse_price_for_sorting(item.get("Preț"))
    is_cheapest = (
        price_val != float("inf")
        and min_price_by_category.get(tag_text) == price_val
    )

    # Evidențiere sigură în HTML (escape + <mark>)
    safe_title = html.escape(raw_title)
    query = (current_query or "").strip()
    if query:
      try:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlighted_title = pattern.sub(
            lambda m: f"<mark style='background:#facc15;color:#111827;padding:0 2px;border-radius:2px;'>{m.group(0)}</mark>",
            safe_title,
        )
      except re.error:
        highlighted_title = safe_title
    else:
      highlighted_title = safe_title

    cheapest_badge = (
        '<span style="background: #f59e0b; color: #111827; padding: 3px 10px; '
        'border-radius: 5px; font-size: 0.8rem; font-weight: bold; margin-left: 8px;">'
        '🏷️ Cel mai ieftin</span>'
        if is_cheapest
        else ""
    )

    magazin = html.escape(str(item.get("Magazin", "")))
    safe_tag = html.escape(str(tag_text))
    pret = html.escape(str(item.get("Preț", "N/A")))
    link = html.escape(str(item.get("Sursă / Link", "#")), quote=True)
    image_url = str(item.get("Imagine", "") or "").strip()
    image_html = ""
    if image_url.startswith(("http://", "https://")):
      safe_image = html.escape(image_url, quote=True)
      safe_alt = html.escape(raw_title, quote=True)
      image_html = (
          f'<style>'
          f'.thumb-wrap .img-preview{{display:none;}}'
          f'.thumb-wrap:hover .img-preview{{display:block;}}'
          f"</style>"
          f'<div class="thumb-wrap" style="position:relative;flex:0 0 72px;width:72px;height:72px;">'
          f'<a href="{link}" target="_blank">'
          f'<img src="{safe_image}" alt="{safe_alt}" '
          f'style="width:72px;height:72px;object-fit:contain;border-radius:6px;'
          f'background:#ffffff;padding:4px;border:1px solid #30363d;" loading="lazy" />'
          f"</a>"
          f'<div class="img-preview" style="position:absolute;left:80px;top:-20px;z-index:9999;'
          f'padding:6px;background:#0d1117;border:1px solid #30363d;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.45);">'
          f'<img src="{safe_image}" alt="{safe_alt}" '
          f'style="width:280px;max-width:40vw;height:auto;max-height:320px;object-fit:contain;display:block;background:#fff;border-radius:4px;" loading="lazy" />'
          f"</div></div>"
      )

    card_html = f"""
<div class="result-card">
  <div style="display: flex; gap: 12px; align-items: flex-start;">
    {image_html}
    <div style="flex: 1; min-width: 0;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px;">
        <div>
          <span style="background: #1f6feb; color: white; padding: 3px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">{magazin}</span>
          <span style="background: #238636; color: white; padding: 3px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; margin-left: 8px;">{safe_tag}</span>
          {cheapest_badge}
        </div>
        <span style="font-size: 1.25rem; font-weight: 700; color: #3fb950; white-space: nowrap;">{pret}</span>
      </div>
      <div style="font-size: 1.05rem; font-weight: 600; margin-bottom: 6px;">
        <a href="{link}" target="_blank" style="color: #f0f6fc; text-decoration: none;" onMouseOver="this.style.color='#58a6ff'" onMouseOut="this.style.color='#f0f6fc'">{highlighted_title}</a>
      </div>
      <div style="font-size: 0.82rem;">
        <a href="{link}" target="_blank" style="color: #8b949e; text-decoration: none;" onMouseOver="this.style.color='#58a6ff'" onMouseOut="this.style.color='#8b949e'">🔗 Deschide pagina produsului în magazin</a>
      </div>
    </div>
  </div>
</div>
"""
    rendered_html = textwrap.dedent(card_html).strip()
    if hasattr(st, "html"):
      st.html(rendered_html)
    else:
      st.markdown(rendered_html, unsafe_allow_html=True)