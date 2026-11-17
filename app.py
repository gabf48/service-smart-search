from config import setup_page
from filtering import filter_and_sort_data
from scraper import load_stores
import streamlit as st
from ui.filters import render_filters_and_sort
from ui.results import render_results
from ui.search_form import render_search_form
from ui.sidebar import render_sidebar
from utils.filters import is_irrelevant_product, parse_price_for_sorting
from utils.formatting import highlight_search_terms
from utils.tags import get_product_tag

setup_page()

app_module = st.sidebar.radio(
    "Modul aplicație",
    ["🔍 Căutare piese", "🧾 Clienți & Service"],
    horizontal=True,
)

if app_module == "🧾 Clienți & Service":
  from ui.clients import render_clients_page

  render_clients_page()
  st.stop()

if "search_results" not in st.session_state:
  st.session_state.search_results = None
if "last_query" not in st.session_state:
  st.session_state.last_query = ""

raw_data = st.session_state.search_results
cleaned_data = (
    [item for item in raw_data if not is_irrelevant_product(item["Produs"])]
    if raw_data
    else raw_data
)

stores = load_stores()
store_checkboxes, tag_checkboxes = render_sidebar(stores, cleaned_data)

st.title("⚡ Motor Global de Căutare Piese")
st.markdown(
    "Interogare simultană în timp real în stocurile magazinelor partenere."
)
st.markdown("")

render_search_form()

st.markdown("---")

data = cleaned_data
query = st.session_state.last_query

if data is not None:
  if data:
    sort_option, min_price, max_price = render_filters_and_sort()

    filtered_data, hidden_by_store, hidden_by_tag = filter_and_sort_data(
        data,
        store_checkboxes,
        tag_checkboxes,
        sort_option,
        min_price,
        max_price,
    )

    st.success(
        f"S-au găsit **{len(filtered_data)}** oferte afișate (din {len(data)}"
        f" totale) pentru `{query}`."
    )

    info_msgs = []
    if hidden_by_store > 0:
      info_msgs.append(f"{hidden_by_store} oferte ascunse (magazin debifat)")
    if hidden_by_tag > 0:
      info_msgs.append(f"{hidden_by_tag} oferte ascunse (categorie debifată)")

    if info_msgs:
      st.info("ℹ️ " + " | ".join(info_msgs))

    st.markdown("---")

    if filtered_data:
      render_results(filtered_data, sort_option)
    else:
      st.warning(
          "⚠️ Niciun produs nu corespunde filtrelor de preț, magazin și"
          " categorii selectate."
      )
  else:
    st.warning(
        f"⚠️ Niciun magazin din listă nu a returnat un produs valid pentru"
        f" `{query}`."
    )
else:
  st.info(
      "💡 Introdu codul piesei sau denumirea în bara centrală de căutare de"
      " mai sus și apasă **Enter** sau butonul **Caută**."
  )