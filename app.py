import asyncio
import re
from scraper import load_stores, search_parts
import streamlit as st

st.set_page_config(
    page_title="Service Smart | Motor Global Piese", page_icon="⚡", layout="wide"
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


def parse_price_for_sorting(price_str):
  if not price_str or "N/A" in price_str:
    return float("inf")
  clean = (
      price_str.lower()
      .replace("de la", "")
      .replace("lei", "")
      .replace("ron", "")
      .strip()
  )
  clean = clean.replace(".", "").replace(",", ".")
  match = re.search(r"(\d+(\.\d+)?)", clean)
  if match:
    try:
      return float(match.group(1))
    except ValueError:
      pass
  return float("inf")


stores = load_stores()

# --- SIDEBAR: Magazine Active cu Checkbox-uri ---
with st.sidebar:
  st.title("⚡ Service Smart")
  st.markdown("### 📂 Magazine Active")

  store_checkboxes = {}
  for s in stores:
    # Fiecare magazin are un checkbox bifat by default (value=True)
    store_checkboxes[s["name"]] = st.checkbox(
        f"🌐 {s['name']} ({s['domain']})", value=True, key=f"chk_{s['name']}"
    )

  st.divider()
  st.info("Poți adăuga magazine noi direct în `websites.json`.")

# --- CONȚINUT PRINCIPAL: Motorul Global de Căutare (CENTRAL) ---
st.title("⚡ Motor Global de Căutare Piese")
st.markdown(
    "Interogare simultană în timp real în stocurile magazinelor partenere."
)
st.markdown("")

if "search_results" not in st.session_state:
  st.session_state.search_results = None
if "last_query" not in st.session_state:
  st.session_state.last_query = ""

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

st.markdown("---")

data = st.session_state.search_results
query = st.session_state.last_query

if data is not None:
  if data:
    with st.expander(
        "🎛️ Filtre avansate și Sortare după Preț", expanded=True
    ):
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

   # 1. Aplicăm filtrele de magazin (bifat/debifat) și preț
    filtered_data = []
    hidden_by_store = 0

    for item in data:
      # Verificăm dacă magazinul este bifat în sidebar
      if not store_checkboxes.get(item["Magazin"], True):
        hidden_by_store += 1
        continue

      p_val = parse_price_for_sorting(item["Preț"])
      if p_val == float("inf"):
        filtered_data.append(item)
        continue

      if min_price > 0 and p_val < min_price:
        continue
      if max_price > 0 and p_val > max_price:
        continue
      filtered_data.append(item)

    # 2. Aplicăm sortarea
    if sort_option == "Preț crescător 📈":
      filtered_data = sorted(
          filtered_data, key=lambda x: parse_price_for_sorting(x["Preț"])
      )
    elif sort_option == "Preț descrescător 📉":
      filtered_data = sorted(
          filtered_data,
          key=lambda x: parse_price_for_sorting(x["Preț"]),
          reverse=True,
      )

    st.success(
        f"S-au găsit **{len(filtered_data)}** oferte afișate (din {len(data)}"
        f" totale) pentru `{query}`."
    )
    if hidden_by_store > 0:
      st.info(
          f"ℹ️ Alte **{hidden_by_store}** oferte au fost ascunse deoarece"
          " magazinul corespunzător este debifat în sidebar."
      )
    st.markdown("---")

    if filtered_data:
      for item in filtered_data:
        card_html = f"""
                <div class="result-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="background: #1f6feb; color: white; padding: 3px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">{item["Magazin"]}</span>
                        <span style="font-size: 1.25rem; font-weight: 700; color: #3fb950;">{item["Preț"]}</span>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 600; margin-bottom: 6px;">
                        <a href="{item["Sursă / Link"]}" target="_blank" style="color: #f0f6fc; text-decoration: none;" onMouseOver="this.style.color='#58a6ff'" onMouseOut="this.style.color='#f0f6fc'">{item["Produs"]}</a>
                    </div>
                    <div style="font-size: 0.82rem;">
                        <a href="{item["Sursă / Link"]}" target="_blank" style="color: #8b949e; text-decoration: none;" onMouseOver="this.style.color='#58a6ff'" onMouseOut="this.style.color='#8b949e'">🔗 Deschide pagina produsului în magazin</a>
                    </div>
                </div>
                """
        st.markdown(card_html, unsafe_allow_html=True)
    else:
      st.warning(
          "⚠️ Niciun produs nu corespunde filtrelor de preț și magazine"
          " selectate."
      )
  else:
    st.warning(
        f"⚠️ Niciun magazin din listă nu a returnat un produs pentru `{query}`."
    )
else:
  st.info(
      "💡 Introdu codul piesei sau denumirea în bara centrală de căutare de"
      " mai sus și apasă **Enter** sau butonul **Caută**."
  )