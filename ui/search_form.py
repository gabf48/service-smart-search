import asyncio

import httpx
import streamlit as st

from scraper import get_search_task_specs, load_stores, process_search_results


async def _run_search_with_progress(query: str):
  stores = [s["name"] for s in load_stores()]
  status_placeholders = {}
  state = {name: {"status": "pending", "count": 0} for name in stores}

  progress_container = st.container()
  with progress_container:
    st.markdown(f"**Scanare magazine pentru:** `{query}`")
    cols = st.columns(min(len(stores), 4) or 1)
    for idx, name in enumerate(stores):
      with cols[idx % len(cols)]:
        status_placeholders[name] = st.empty()

  def render_status(name: str):
    ph = status_placeholders.get(name)
    if not ph:
      return
    info = state[name]
    if info["status"] == "pending":
      ph.info(f"⏳ {name}\n\nÎn așteptare...")
    elif info["status"] == "running":
      ph.warning(f"🔄 {name}\n\nScanare... ({info['count']} produse)")
    elif info["status"] == "done":
      ph.success(f"✅ {name}\n\nFinalizat: {info['count']} produse")
    elif info["status"] == "error":
      ph.error(f"⚠️ {name}\n\nEroare la scanare")

  for name in stores:
    render_status(name)

  aggregated_results = []

  async with httpx.AsyncClient() as client:
    specs = get_search_task_specs(query, client)
    # Include eventuale magazine noi din specs care nu sunt în websites.json
    for store_name, _ in specs:
      if store_name not in state:
        state[store_name] = {"status": "pending", "count": 0}
        status_placeholders[store_name] = st.empty()
        render_status(store_name)

    if not specs:
      for name in stores:
        state[name]["status"] = "done"
        state[name]["count"] = 0
        render_status(name)
      return []

    async def run_one(store_name, coro):
      state[store_name]["status"] = "running"
      render_status(store_name)
      try:
        results = await coro
        if not isinstance(results, list):
          results = []
      except Exception as e:
        print(f"Eroare la {store_name}: {e}")
        state[store_name]["status"] = "error"
        state[store_name]["count"] = 0
        render_status(store_name)
        return store_name, []

      state[store_name]["status"] = "done"
      state[store_name]["count"] = len(results)
      render_status(store_name)
      return store_name, results

    task_map = {
        asyncio.create_task(run_one(store_name, coro)): store_name
        for store_name, coro in specs
    }

    for task in asyncio.as_completed(list(task_map.keys())):
      store_name, results = await task
      aggregated_results.extend(results)

  return process_search_results(aggregated_results, query)


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
    try:
      results = asyncio.run(_run_search_with_progress(st.session_state.last_query))
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      results = loop.run_until_complete(
          _run_search_with_progress(st.session_state.last_query)
      )
    st.session_state.search_results = results
    st.rerun()