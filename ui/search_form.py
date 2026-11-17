import asyncio
import html

import httpx
import streamlit as st

from scraper import get_search_task_specs, load_stores, process_search_results


PANEL_CSS = """
<style>
  .scan-panel {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: linear-gradient(160deg, #0d1117 0%, #111827 55%, #0b1220 100%);
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 16px 18px 14px 18px;
    margin-bottom: 14px;
    color: #e6edf3;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
  }
  .scan-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
  }
  .scan-title {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.2px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .scan-query {
    font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace;
    background: #1f6feb22;
    color: #58a6ff;
    border: 1px solid #1f6feb55;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.82rem;
  }
  .scan-meta {
    font-size: 0.78rem;
    color: #8b949e;
    white-space: nowrap;
  }
  .scan-bar-wrap {
    height: 8px;
    border-radius: 999px;
    background: #161b22;
    border: 1px solid #21262d;
    overflow: hidden;
    margin-bottom: 12px;
  }
  .scan-bar {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #00b4d8, #1f6feb 55%, #7c3aed);
    background-size: 200% 100%;
    animation: bar-shift 2.2s linear infinite;
    transition: width 0.35s ease;
  }
  @keyframes bar-shift {
    0% { background-position: 0% 0; }
    100% { background-position: 200% 0; }
  }
  .scan-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
    gap: 8px;
  }
  .scan-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #161b2266;
    border: 1px solid #21262d;
    border-radius: 9px;
    padding: 7px 10px;
    font-size: 0.78rem;
    min-width: 0;
    transition: border-color 0.2s ease, background 0.2s ease;
  }
  .scan-chip .name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 600;
  }
  .scan-chip .count {
    font-size: 0.72rem;
    color: #8b949e;
    white-space: nowrap;
  }
  .scan-chip.pending .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #30363d; flex: 0 0 9px;
  }
  .scan-chip.running {
    border-color: #1f6feb88;
    background: #1f6feb1a;
  }
  .scan-chip.running .dot {
    width: 12px; height: 12px; border-radius: 50%;
    border: 2px solid #1f6feb44;
    border-top-color: #58a6ff;
    animation: spin 0.8s linear infinite;
    flex: 0 0 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .scan-chip.done { border-color: #23863688; background: #2386361f; }
  .scan-chip.done .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #3fb950; flex: 0 0 9px;
    box-shadow: 0 0 8px #3fb950aa;
  }
  .scan-chip.done .count { color: #3fb950; font-weight: 700; }
  .scan-chip.empty { border-color: #d2992288; background: #d299221a; }
  .scan-chip.empty .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #d29922; flex: 0 0 9px;
  }
  .scan-chip.empty .count { color: #d29922; font-weight: 700; }
  .scan-chip.empty .name { color: #b8945a; }
  .scan-chip.error { border-color: #da363388; background: #da36331f; }
  .scan-chip.error .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #f85149; flex: 0 0 9px;
  }
  .scan-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-top: 10px;
    font-size: 0.74rem;
    color: #8b949e;
  }
  .scan-live {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #58a6ff;
  }
  .scan-live .pulse {
    width: 7px; height: 7px; border-radius: 50%;
    background: #58a6ff;
    box-shadow: 0 0 0 0 #58a6ffcc;
    animation: pulse 1.4s ease-out infinite;
  }
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 #58a6ffcc; }
    100% { box-shadow: 0 0 0 8px #58a6ff00; }
  }
</style>
"""


def _render_panel(placeholder, query, store_names, state):
  total = len(store_names) or 1
  done = sum(1 for n in store_names if state.get(n, {}).get("status") == "done")
  errors = sum(1 for n in store_names if state.get(n, {}).get("status") == "error")
  running = [
      n for n in store_names if state.get(n, {}).get("status") == "running"
  ]
  finished = done + errors
  percent = int(round(finished / total * 100))
  total_found = sum(
      state.get(n, {}).get("count", 0) for n in store_names
  )

  chips = []
  for name in store_names:
    info = state.get(name, {"status": "pending", "count": 0})
    status = info.get("status", "pending")
    count = info.get("count", 0)
    safe_name = html.escape(str(name))
    if status == "done" and count == 0:
      chip_class = "empty"
      count_html = '<span class="count">0 prod.</span>'
    elif status == "done":
      chip_class = "done"
      count_html = f'<span class="count">{count} prod.</span>'
    elif status == "running":
      chip_class = "running"
      count_html = '<span class="count">scanare…</span>'
    elif status == "error":
      chip_class = "error"
      count_html = '<span class="count">eroare</span>'
    else:
      chip_class = "pending"
      count_html = '<span class="count">în așteptare</span>'
    chips.append(
        f'<div class="scan-chip {chip_class}">'
        f'<span class="dot"></span>'
        f'<span class="name">{safe_name}</span>{count_html}</div>'
    )

  live_text = (
      f"Se scanează: {', '.join(html.escape(n) for n in running[:3])}"
      + (" +" + str(len(running) - 3) if len(running) > 3 else "")
      if running
      else "Se pregătesc magazinele…"
  )
  if not running and finished >= len(store_names):
    live_text = (
        "Scanare finalizată — niciun produs găsit"
        if total_found == 0
        else "Scanare finalizată"
    )

  safe_query = html.escape(query)
  panel_html = (
      PANEL_CSS
      + '<div class="scan-panel">'
      + '<div class="scan-head">'
      + '<div class="scan-title">⚡ Scanare magazine '
      + f'<span class="scan-query">{safe_query}</span></div>'
      + f'<div class="scan-meta">{finished}/{len(store_names)} · '
      + f"{total_found} produse găsite</div>"
      + "</div>"
      + '<div class="scan-bar-wrap"><div class="scan-bar" '
      + f'style="width:{percent}%"></div></div>'
      + f'<div class="scan-grid">{"".join(chips)}</div>'
      + '<div class="scan-foot">'
      + f'<span class="scan-live"><span class="pulse"></span>{live_text}</span>'
      + f'<span>{percent}% complet</span>'
      + "</div></div>"
  )
  placeholder.markdown(panel_html, unsafe_allow_html=True)


async def _run_search_with_progress(query: str):
  stores = [s["name"] for s in load_stores()]
  state = {name: {"status": "pending", "count": 0} for name in stores}

  placeholder = st.empty()
  _render_panel(placeholder, query, stores, state)

  aggregated_results = []

  async with httpx.AsyncClient() as client:
    specs = get_search_task_specs(query, client)
    for store_name, _ in specs:
      if store_name not in state:
        state[store_name] = {"status": "pending", "count": 0}
        stores.append(store_name)

    if not specs:
      for name in stores:
        state[name] = {"status": "done", "count": 0}
      _render_panel(placeholder, query, stores, state)
      return []

    async def run_one(store_name, coro):
      state[store_name]["status"] = "running"
      _render_panel(placeholder, query, stores, state)
      try:
        results = await coro
        if not isinstance(results, list):
          results = []
      except Exception as e:
        print(f"Eroare la {store_name}: {e}")
        state[store_name]["status"] = "error"
        state[store_name]["count"] = 0
        _render_panel(placeholder, query, stores, state)
        return store_name, []

      state[store_name]["status"] = "done"
      state[store_name]["count"] = len(results)
      _render_panel(placeholder, query, stores, state)
      return store_name, results

    tasks = [
        asyncio.create_task(run_one(store_name, coro))
        for store_name, coro in specs
    ]

    for task in asyncio.as_completed(tasks):
      store_name, results = await task
      aggregated_results.extend(results)

  _render_panel(placeholder, query, stores, state)
  return process_search_results(aggregated_results, query)


def render_search_form():
  # Când căutarea e pornită dintr-un device, câmpul e pre-completat o dată.
  prefill = st.session_state.pop("search_prefill", "")
  input_token = st.session_state.get("search_input_token", 0)
  with st.form(key="search_form"):
    col1, col2 = st.columns([5, 1])
    with col1:
      part_input = st.text_input(
          "Introdu Part Number sau produs:",
          value=prefill,
          placeholder="ex: G502, FX607VU, Memorie Corsair...",
          label_visibility="collapsed",
          key=f"search_q_{input_token}",
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
    # Resetăm filtrele vechi (magazine/categorii debifate într-o sesiune
    # anterioară sau înainte de navigarea în alt modul), altfel noile
    # rezultate pot rămâne complet ascunse și par că „nu apar".
    # Nu modificăm direct cheile aici: sidebarul a instanțiat deja
    # checkbox-urile în această rundă, iar Streamlit ar refuza scrierea.
    # Amânăm resetul la începutul rundei următoare, în app.py.
    st.session_state["_pending_filter_reset"] = True
    st.rerun()
