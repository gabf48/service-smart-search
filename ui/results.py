import html
import re
import textwrap

import streamlit as st
from ui.sidebar import TAG_ICONS
from utils import get_product_tag
from utils.filters import parse_price_for_sorting


def _render_card(item, current_query, is_cheapest):
  raw_title = item.get("Produs", "")
  tag_text = item.get("Categorie") or get_product_tag(raw_title)

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
        f"<style>"
        f".thumb-wrap .img-preview{{display:none;}}"
        f".thumb-wrap:hover .img-preview{{display:block;}}"
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


def render_results(filtered_data, sort_option="Fără sortare"):
  # Preluăm query-ul curent din session_state pentru a ști ce să evidențiem
  current_query = st.session_state.get("last_query", "")

  # Grupăm produsele pe categorii și determinăm prețul minim pe fiecare categorie
  groups = {}
  for item in filtered_data:
    category = item.get("Categorie") or get_product_tag(item.get("Produs", ""))
    groups.setdefault(category, []).append(item)

  category_min = {}
  for category, items in groups.items():
    prices = [
        parse_price_for_sorting(item.get("Preț"))
        for item in items
    ]
    finite_prices = [p for p in prices if p != float("inf")]
    category_min[category] = min(finite_prices) if finite_prices else None

  desc = sort_option == "Preț descrescător 📉"

  def _group_sort_key(category):
    value = category_min.get(category)
    if value is None:
      return (1, 0.0)
    return (0, -value if desc else value)

  ordered_categories = sorted(groups.keys(), key=_group_sort_key)

  st.caption(
      "📦 Rezultate grupate pe categorii — cel mai ieftin produs apare primul;"
      " folosește săgeata pentru restul produselor din categorie."
  )

  for category in ordered_categories:
    items = groups[category]
    icon = TAG_ICONS.get(category, "🔧")
    min_price = category_min.get(category)
    if min_price is None:
      min_price_text = "fără preț"
    else:
      min_price_text = (
          f"{int(min_price)}"
          if float(min_price).is_integer()
          else f"{min_price:.2f}".rstrip("0").rstrip(".")
      ) + " Lei"
    items_word = "produs" if len(items) == 1 else "produse"

    header_html = (
        '<div style="display:flex;justify-content:space-between;align-items:baseline;'
        'gap:10px;margin:14px 0 8px 0;border-bottom:1px solid #21262d;padding-bottom:6px;">'
        f'<span style="font-size:1.02rem;font-weight:700;color:#c9d1d9;">{icon} {html.escape(str(category))}</span>'
        f'<span style="font-size:0.76rem;color:#8b949e;">{len(items)} {items_word} · de la {min_price_text}</span>'
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Cel mai ieftin produs din categorie — afișat mereu, primul
    cheapest_idx = 0
    best_price = float("inf")
    for idx, item in enumerate(items):
      price_val = parse_price_for_sorting(item.get("Preț"))
      if price_val < best_price:
        best_price = price_val
        cheapest_idx = idx

    cheapest_item = items[cheapest_idx]
    rest_items = items[:cheapest_idx] + items[cheapest_idx + 1:]

    _render_card(cheapest_item, current_query, is_cheapest=True)

    # Restul produselor din categorie — ascunse by default sub o săgeată
    if rest_items:
      rest_word = "produs" if len(rest_items) == 1 else "produse"
      label = f"🔽 Vezi restul ({len(rest_items)} {rest_word}) din {category}"
      with st.expander(label, expanded=False):
        for item in rest_items:
          price_val = parse_price_for_sorting(item.get("Preț"))
          _render_card(
              item,
              current_query,
              is_cheapest=price_val != float("inf") and price_val == best_price,
          )
