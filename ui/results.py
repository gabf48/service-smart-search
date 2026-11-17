import html
import re
import textwrap

import streamlit as st

import database as db
from ui.sidebar import TAG_ICONS
from utils import get_product_tag
from utils.filters import parse_price_for_sorting


@st.dialog("➕ Salvează oferta la client")
def _save_offer_dialog(item, query):
  db.init_db()
  clients = db.list_clients()
  if not clients:
    st.warning(
        "Nu există clienți în baza de date. Adaugă mai întâi un client din"
        " modulul „Clienți & Service”."
    )
    return

  target_id = st.session_state.get("search_target_device_id")
  target = db.get_device_owner(target_id) if target_id else None

  client_ids = [c["id"] for c in clients]
  client_by_id = {c["id"]: c for c in clients}
  client_index = 0
  if target:
    for idx, cid in enumerate(client_ids):
      if cid == target["client_id"]:
        client_index = idx
        break
  client_id = st.selectbox(
      "Client",
      client_ids,
      index=client_index,
      format_func=lambda cid: (
          f"{client_by_id[cid]['name']} · {client_by_id[cid]['phone']}"
      ),
      key="offer_client_select",
  )

  devices = db.get_client_devices(client_id)
  if not devices:
    st.warning(
        "Clientul selectat nu are încă niciun dispozitiv. Adaugă unul din fișa clientului."
    )
    return

  device_ids = [d["id"] for d in devices]
  device_by_id = {d["id"]: d for d in devices}
  device_index = 0
  if target and target["device_id"] in device_ids:
    device_index = device_ids.index(target["device_id"])
  device_id = st.selectbox(
      "Dispozitiv",
      device_ids,
      index=device_index,
      format_func=lambda did: (
          f"📱 {device_by_id[did]['model']}"
          + (f" · MTM {device_by_id[did]['mtm']}" if device_by_id[did].get("mtm") else "")
          + (f" · ST {device_by_id[did]['service_tag']}" if device_by_id[did].get("service_tag") else "")
          + (f" · S/N {device_by_id[did]['serial_number']}" if device_by_id[did]["serial_number"] else "")
      ),
      key="offer_device_select",
  )

  statuses = [s["name"] for s in db.get_part_statuses()]
  col1, col2 = st.columns([2, 1])
  with col1:
    status = st.selectbox("Status piesă", statuses, key="offer_status_select")
  with col2:
    quantity = st.number_input("Cantitate", min_value=1, value=1, step=1, key="offer_qty_input")
  notes = st.text_area("Notițe", height=70, key="offer_notes_input")

  st.markdown("---")
  st.markdown(f"**{html.escape(str(item.get('Produs', '')))}**")
  st.caption(
      f"{html.escape(str(item.get('Magazin', '')))} · "
      f"{html.escape(str(item.get('Preț', '')))}"
  )

  if st.button("💾 Salvează oferta", type="primary", use_container_width=True):
    db.add_offer(
        device_id,
        item,
        part_number=query,
        status=status,
        quantity=quantity,
        notes=notes,
    )
    st.success("Oferta a fost salvată în fișa clientului.")
    st.rerun()


def _render_card(item, current_query, is_cheapest, card_key):
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

  # Cardul e un container nativ cu bordură, ca butonul de salvare să facă
  # parte din el, nu să fie randat separat sub un bloc HTML.
  card_html = f"""
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
"""
  rendered_html = textwrap.dedent(card_html).strip()

  with st.container(border=True):
    if hasattr(st, "html"):
      st.html(rendered_html)
    else:
      st.markdown(rendered_html, unsafe_allow_html=True)

    with st.container(horizontal=True, horizontal_alignment="right"):
      if st.button(
          "Salvează la client",
          icon=":material/bookmark_add:",
          key=f"save_offer_{card_key}",
      ):
        _save_offer_dialog(item, current_query)


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
  card_seq = 0

  st.caption(
      "📦 Rezultate grupate pe categorii — cel mai ieftin produs apare primul,"
      " urmat de restul ofertelor din categorie."
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

    card_seq += 1
    _render_card(cheapest_item, current_query, is_cheapest=True, card_key=card_seq)

    # Restul produselor din categorie — ascunse by default sub o săgeată
    if rest_items:
      rest_word = "produs" if len(rest_items) == 1 else "produse"
      label = f"🔽 Vezi restul ({len(rest_items)} {rest_word}) din {category}"
      with st.expander(label, expanded=True):
        for item in rest_items:
          price_val = parse_price_for_sorting(item.get("Preț"))
          card_seq += 1
          _render_card(
              item,
              current_query,
              is_cheapest=price_val != float("inf") and price_val == best_price,
              card_key=card_seq,
          )
