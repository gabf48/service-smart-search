import streamlit as st
from utils import get_product_tag

# Cheile sunt exact valorile întoarse de classify_category (fără emoji).
# Emoji-ul se folosește doar la afișarea etichetei în sidebar.
TAG_ICONS = {
    "Laptopuri": "💻",
    "Consumabile Imprimante": "🖨️",
    "Consumabile": "🧪",
    "Încărcătoare": "⚡",
    "Coolere": "❄️",
    "Mufe & Conectori": "🔌",
    "Ramă Display": "🖼️",
    "Memorie RAM": "🧠",
    "Stocare": "💾",
    "Baterie": "🔋",
    "Tastatură": "⌨️",
    "Display": "🖥️",
    "Piese / Altele": "🔧",
}


def render_sidebar(stores, data):
  # 1. Gestionarea stării temei în session_state
  if "theme" not in st.session_state:
    st.session_state.theme = "dark"

  # 2. Palete de culori pentru Dark și Light
  themes = {
      "dark": {
          "bg_color": "#0d1117",
          "card_bg": "#161b22",
          "text_color": "#c9d1d9",
          "text_muted": "#8b949e",
          "border_color": "#30363d",
          "btn_bg": "#21262d",
          "btn_hover": "#30363d",
          "card_hover": "#1f242c",
      },
      "light": {
          "bg_color": "#ffffff",
          "card_bg": "#f6f8fa",
          "text_color": "#24292f",
          "text_muted": "#57606a",
          "border_color": "#d0d7de",
          "btn_bg": "#f3f4f6",
          "btn_hover": "#ebf0f4",
          "card_hover": "#eaeef2",
      },
  }

  t = themes[st.session_state.theme]

  # 3. Injectarea dinamică a stilurilor CSS
  st.sidebar.markdown(
      f"""
        <style>
            .stApp {{
                background-color: {t["bg_color"]} !important;
                color: {t["text_color"]} !important;
            }}
            section[data-testid="stSidebar"] div.stButton > button {{
                background-color: {t["btn_bg"]} !important;
                color: {t["text_color"]} !important;
                border: 1px solid {t["border_color"]} !important;
                border-radius: 4px !important;
                font-size: 12px !important;
                font-weight: 500 !important;
                padding: 4px 8px !important;
                min-height: 28px !important;
                width: 100% !important;
                box-shadow: none !important;
                transition: all 0.15s ease-in-out;
            }}
            section[data-testid="stSidebar"] div.stButton > button:hover {{
                background-color: {t["btn_hover"]} !important;
                border-color: {t["text_muted"]} !important;
            }}
            .result-card {{
                background-color: {t["card_bg"]} !important;
                border: 1px solid {t["border_color"]} !important;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                transition: transform 0.15s ease, border-color 0.15s ease;
            }}
            .result-card:hover {{
                border-color: #1f6feb !important;
            }}
        </style>
    """,
      unsafe_allow_html=True,
  )

  # --- HEADER SIDEBAR & BUTON TEMĂ ---
  st.sidebar.markdown(
      f'<p style="font-weight: 700; font-size: 16px; margin-bottom: 8px;'
      f' color: {t["text_color"]};">⚙️ Meniu Service</p>',
      unsafe_allow_html=True,
  )

  theme_label = (
      "☀️ Schimbă pe Modul Light"
      if st.session_state.theme == "dark"
      else "🌙 Schimbă pe Modul Dark"
  )
  if st.sidebar.button(theme_label, key="btn_toggle_theme"):
    st.session_state.theme = (
        "light" if st.session_state.theme == "dark" else "dark"
    )
    st.rerun()

  st.sidebar.markdown("---")

  # --- SECȚIUNEA 1: MAGAZINE ACTIVE ---
  store_domains = {s["name"]: s.get("domain", "") for s in stores}
  store_counts = {}
  if data:
    for item in data:
      s_name = item["Magazin"]
      store_counts[s_name] = store_counts.get(s_name, 0) + 1

  available_stores = (
      sorted(list(set(item["Magazin"] for item in data)))
      if data
      else [s["name"] for s in stores]
  )

  c1, c2, c3 = st.sidebar.columns([1.3, 1.3, 1.4])
  with c1:
    st.markdown(
        f'<p style="font-weight: 600; font-size: 13px; margin-top: 4px;'
        f' color: {t["text_color"]};">🗂️ Magazine</p>',
        unsafe_allow_html=True,
    )
  with c2:
    if st.button("Toate", key="btn_all_stores"):
      for s in available_stores:
        st.session_state[f"store_{s}"] = True
      st.rerun()
  with c3:
    if st.button("Niciunul", key="btn_none_stores"):
      for s in available_stores:
        st.session_state[f"store_{s}"] = False
      st.rerun()

  store_checkboxes = {}
  for store in available_stores:
    count = store_counts.get(store, 0)
    domain = store_domains.get(store, "")
    label = (
        f"🌐 {store} ({domain}) — {count}"
        if domain
        else f"🌐 {store} — {count}"
    )

    # Inițializăm starea în session_state dacă nu există, fără a pasa value= în checkbox
    key_name = f"store_{store}"
    if key_name not in st.session_state:
      st.session_state[key_name] = True

    store_checkboxes[store] = st.sidebar.checkbox(label, key=key_name)

  st.sidebar.markdown("---")

  # --- SECȚIUNEA 2: CATEGORII / TAGURI ---
  active_store_data = (
      [item for item in data if store_checkboxes.get(item["Magazin"], True)]
      if data
      else []
  )

  tag_counts = {}
  if active_store_data:
    for item in active_store_data:
      tag = get_product_tag(item["Produs"])
      tag_counts[tag] = tag_counts.get(tag, 0) + 1

  all_tags = list(TAG_ICONS)

  c4, c5, c6 = st.sidebar.columns([1.3, 1.3, 1.4])
  with c4:
    st.markdown(
        f'<p style="font-weight: 600; font-size: 13px; margin-top: 4px;'
        f' color: {t["text_color"]};">🏷️ Categorii</p>',
        unsafe_allow_html=True,
    )
  with c5:
    if st.button("Toate", key="btn_all_tags"):
      for t_item in all_tags:
        st.session_state[f"tag_{t_item}"] = True
      st.rerun()
  with c6:
    if st.button("Niciunul", key="btn_none_tags"):
      for t_item in all_tags:
        st.session_state[f"tag_{t_item}"] = False
      st.rerun()

  tag_checkboxes = {}
  for tag in all_tags:
    count = tag_counts.get(tag, 0)
    key_name = f"tag_{tag}"
    if key_name not in st.session_state:
      st.session_state[key_name] = True

    tag_checkboxes[tag] = st.sidebar.checkbox(
        f"{TAG_ICONS[tag]} {tag} — {count}", key=key_name
    )

  return store_checkboxes, tag_checkboxes