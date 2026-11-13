import streamlit as st
from utils import get_product_tag


def render_sidebar(stores, data):
  # Stil CSS cu padding redus și eliminarea oricărei scurtări de text
  st.sidebar.markdown(
      """
        <style>
            section[data-testid="stSidebar"] div.stButton > button {
                background-color: #21262d !important;
                color: #c9d1d9 !important;
                border: 1px solid #30363d !important;
                border-radius: 4px !important;
                font-size: 11px !important;
                font-weight: 500 !important;
                padding: 2px 2px !important;
                min-height: 24px !important;
                width: 100% !important;
                box-shadow: none !important;
                white-space: nowrap !important;
                transition: all 0.15s ease-in-out;
            }
            section[data-testid="stSidebar"] div.stButton > button:hover {
                background-color: #30363d !important;
                color: #ffffff !important;
                border-color: #8b949e !important;
            }
            section[data-testid="stSidebar"] div.stButton > button:active {
                background-color: #1f6feb !important;
                color: #ffffff !important;
                border-color: #388bfd !important;
            }
        </style>
    """,
      unsafe_allow_html=True,
  )

  # --- MAGAZINE ACTIVE ---
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

  # Proporții optimizate: titlul primește mai puțin, butoanele primesc spațiu generos
  c1, c2, c3 = st.sidebar.columns([1.3, 1.3, 1.4])
  with c1:
    st.markdown(
        "<p"
        ' style="font-weight: 600; font-size: 13px; margin-top: 4px;'
        ' color: #e6edf3;">🗂️ Magazine</p>',
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
    store_checkboxes[store] = st.sidebar.checkbox(
        label, value=True, key=f"store_{store}"
    )

  st.sidebar.markdown("---")

  # --- CATEGORII / TAGURI ---
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

  all_tags = [
      "💻 Laptopuri",
      "🖨️ Consumabile",
      "⚡ Încărcătoare",
      "❄️ Coolere",
      "🔌 Mufe & Conectori",
      "🖼️ Ramă Display",
      "🧠 Memorie RAM",
      "💾 Stocare",
      "🔋 Baterie",
      "⌨️ Tastatură",
      "🖥️ Display",
      "🔧 Piese / Altele",
  ]

  c4, c5, c6 = st.sidebar.columns([1.3, 1.3, 1.4])
  with c4:
    st.markdown(
        "<p"
        ' style="font-weight: 600; font-size: 13px; margin-top: 4px;'
        ' color: #e6edf3;">🏷️ Categorii</p>',
        unsafe_allow_html=True,
    )
  with c5:
    if st.button("Toate", key="btn_all_tags"):
      for t in all_tags:
        st.session_state[f"tag_{t}"] = True
      st.rerun()
  with c6:
    if st.button("Niciunul", key="btn_none_tags"):
      for t in all_tags:
        st.session_state[f"tag_{t}"] = False
      st.rerun()

  tag_checkboxes = {}
  for tag in all_tags:
    count = tag_counts.get(tag, 0)
    tag_checkboxes[tag] = st.sidebar.checkbox(
        f"{tag} — {count}", value=True, key=f"tag_{tag}"
    )

  return store_checkboxes, tag_checkboxes