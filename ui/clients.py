"""Streamlit UI for client/service management (SQLite backed)."""

import html
import os

import pandas as pd
import streamlit as st

import database as db
from utils import format_money


def _badge(name, color):
  safe_name = html.escape(str(name or "Fără status"))
  safe_color = html.escape(str(color or "#8b949e"), quote=True)
  return (
      f'<span style="display:inline-block;background:{safe_color};color:#fff;'
      f'padding:2px 9px;border-radius:999px;font-size:0.75rem;font-weight:700;">'
      f"{safe_name}</span>"
  )


def _start_search_for_device(device_id, query):
  """Trece pe modulul Căutare cu deviceul ca țintă și query pre-completat."""
  st.session_state["search_target_device_id"] = device_id
  st.session_state["search_prefill"] = query
  st.session_state["search_input_token"] = st.session_state.get("search_input_token", 0) + 1
  st.session_state["pending_app_module"] = "🔍 Căutare piese"
  st.rerun()


# --- Client nou ------------------------------------------------------------


def _render_add_client():
  statuses = db.get_statuses()
  status_names = [s["name"] for s in statuses]
  name_to_id = {s["name"]: s["id"] for s in statuses}

  uploader_key = f"new_client_photos_{st.session_state.get('new_photo_key', 0)}"
  uploaded_files = st.file_uploader(
      "📷 Poze (opțional, se pot selecta mai multe)",
      accept_multiple_files=True,
      type=["png", "jpg", "jpeg", "webp", "gif"],
      key=uploader_key,
  )

  with st.form("add_client_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      name = st.text_input("Nume client *", placeholder="ex. Popescu Ion")
      device = st.text_input("Device / model", placeholder="ex. HP 250 G7, iPhone 12")
    with col2:
      phone = st.text_input("Nr. telefon *", placeholder="ex. 0712 345 678")
      status_name = st.selectbox("Status", status_names) if status_names else None

    problem = st.text_area("Problemă raportată", height=90)
    notes = st.text_area("Observații interne", height=70)
    submitted = st.form_submit_button("💾 Salvează client", use_container_width=True)

  if submitted:
    if not (name or "").strip() or not (phone or "").strip():
      st.warning("Completează numele clientului și numărul de telefon.")
      return
    client_id = db.add_client(
        name=name,
        phone=phone,
        device=device,
        problem=problem,
        notes=notes,
        status_id=name_to_id.get(status_name),
        uploaded_files=uploaded_files,
    )
    st.success(f"Clientul a fost salvat (ID #{client_id}).")
    st.session_state["new_photo_key"] = st.session_state.get("new_photo_key", 0) + 1
    st.rerun()


# --- Editare client --------------------------------------------------------


def _render_edit_client(client):
  statuses = db.get_statuses()
  status_names = [s["name"] for s in statuses]
  name_to_id = {s["name"]: s["id"] for s in statuses}
  current_status = client["status_name"] or ""

  with st.form(f"edit_client_{client['id']}"):
    col1, col2 = st.columns(2)
    with col1:
      name = st.text_input("Nume client", value=client["name"])
      phone = st.text_input("Nr. telefon", value=client["phone"])
    with col2:
      index = status_names.index(current_status) if current_status in status_names else 0
      status_name = st.selectbox("Status", status_names, index=index)
      st.caption(f"Creat: {client['created_at']} · Actualizat: {client['updated_at']}")

    problem = st.text_area("Problemă raportată", value=client["problem"] or "", height=90)
    notes = st.text_area("Observații interne", value=client["notes"] or "", height=70)
    save = st.form_submit_button("💾 Salvează modificările", use_container_width=True)

  if save:
    db.update_client(
        client["id"],
        name=name,
        phone=phone,
        problem=problem,
        notes=notes,
        status_id=name_to_id.get(status_name),
    )
    st.success("Modificările au fost salvate în istoric.")
    st.rerun()

  st.markdown("---")
  if st.checkbox("Confirmă ștergerea clientului", key=f"confirm_del_{client['id']}"):
    if st.button("🗑️ Șterge clientul definitiv", key=f"del_client_{client['id']}"):
      db.delete_client(client["id"])
      st.success("Clientul și toate datele lui au fost șterse.")
      st.rerun()


# --- Dispozitive -----------------------------------------------------------


def _render_devices_tab(client):
  st.markdown("Un client poate avea unul sau mai multe dispozitive.")

  devices = db.get_client_devices(client["id"])
  offer_counts = db.get_offer_counts_by_device(client["id"])
  if not devices:
    st.info("Acest client nu are încă niciun dispozitiv adăugat.")

  for device in devices:
    saved = offer_counts.get(device["id"], 0)
    suffix = f" · 🔩 {saved} {'ofertă' if saved == 1 else 'oferte'}" if saved else ""
    mtm_hint = f" · MTM: {device['mtm']}" if device.get("mtm") else ""
    st_hint = f" · ST: {device['service_tag']}" if device.get("service_tag") else ""
    with st.expander(f"📱 {device['model']}{mtm_hint}{st_hint}{suffix}", expanded=False):
      if st.button(
          "🔍 Caută piese pentru acest device",
          key=f"search_for_dev_{device['id']}",
          use_container_width=True,
      ):
        _start_search_for_device(device["id"], device["model"])

      with st.form(f"edit_device_{device['id']}"):
        model = st.text_input("Model Name / model", value=device["model"])
        mtm = st.text_input(
            "MTM (Machine Type Model)",
            value=device.get("mtm") or "",
            placeholder="ex. 20R1000MRT",
        )
        serial = st.text_input("S/N (număr de serie)", value=device["serial_number"] or "")
        extra1, extra2, extra3 = st.columns(3)
        with extra1:
          mfg_yr = st.text_input(
              "MFG YR", value=device.get("mfg_yr") or "", placeholder="ex. 2023"
          )
        with extra2:
          service_tag = st.text_input(
              "Service Tag (ST)", value=device.get("service_tag") or "", placeholder="ex. ABC1234"
          )
        with extra3:
          express_code = st.text_input(
              "Express Service Code (EX)",
              value=device.get("express_service_code") or "",
              placeholder="ex. 12345678901",
          )
        notes = st.text_area("Observații dispozitiv", value=device["notes"] or "", height=70)
        save = st.form_submit_button("💾 Salvează dispozitivul")
      if save:
        db.update_device(
            device["id"],
            model=model,
            mtm=mtm,
            serial_number=serial,
            mfg_yr=mfg_yr,
            service_tag=service_tag,
            express_service_code=express_code,
            notes=notes,
        )
        st.success("Dispozitivul a fost actualizat.")
        st.rerun()

      if st.checkbox("Șterge dispozitivul", key=f"confirm_del_dev_{device['id']}"):
        if st.button("Confirmă ștergerea", key=f"del_dev_{device['id']}"):
          db.delete_device(device["id"])
          st.success("Dispozitivul a fost șters.")
          st.rerun()

  st.markdown("---")
  st.subheader("➕ Dispozitiv nou")
  with st.form(f"add_device_{client['id']}"):
    model = st.text_input("Model Name / model *", placeholder="ex. Lenovo IdeaPad 3")
    mtm = st.text_input("MTM (Machine Type Model)", placeholder="ex. 20R1000MRT")
    serial = st.text_input("S/N (număr de serie)")
    extra1, extra2, extra3 = st.columns(3)
    with extra1:
      mfg_yr = st.text_input("MFG YR", placeholder="ex. 2023")
    with extra2:
      service_tag = st.text_input("Service Tag (ST)", placeholder="ex. ABC1234")
    with extra3:
      express_code = st.text_input("Express Service Code (EX)", placeholder="ex. 12345678901")
    notes = st.text_area("Observații", height=60)
    add = st.form_submit_button("Adaugă dispozitiv", use_container_width=True)
  if add:
    if not (model or "").strip():
      st.warning("Introdu modelul dispozitivului.")
    else:
      db.add_device(
          client["id"],
          model,
          mtm=mtm,
          serial_number=serial,
          mfg_yr=mfg_yr,
          service_tag=service_tag,
          express_service_code=express_code,
          notes=notes,
      )
      st.success("Dispozitivul a fost adăugat.")
      st.rerun()


# --- Poze ------------------------------------------------------------------


def _render_photos_tab(client):
  devices = db.get_client_devices(client["id"])
  device_options = {d["id"]: f"📱 {d['model']}" for d in devices}
  device_labels = ["Fără device"] + list(device_options.values())
  selected_label = st.selectbox(
      "Asociază pozele la dispozitiv",
      device_labels,
      key=f"photo_device_{client['id']}",
  )
  selected_device_id = None
  for device_id, label in device_options.items():
    if label == selected_label:
      selected_device_id = device_id
      break

  uploaded_files = st.file_uploader(
      "📷 Adaugă poze",
      accept_multiple_files=True,
      type=["png", "jpg", "jpeg", "webp", "gif"],
      key=f"detail_photos_{client['id']}",
  )
  if st.button("⬆️ Salvează pozele", use_container_width=True):
    if not uploaded_files:
      st.warning("Selectează cel puțin o poză.")
    else:
      count = db.add_photos(client["id"], uploaded_files, selected_device_id)
      st.success(f"Au fost salvate {count} poze.")
      st.rerun()

  st.markdown("---")
  photos = db.get_client_photos(client["id"])
  if not photos:
    st.info("Nu există poze pentru acest client.")
    return

  columns = st.columns(4)
  for idx, photo in enumerate(photos):
    with columns[idx % 4]:
      full_path = db.photo_full_path(photo["file_path"])
      if os.path.exists(full_path):
        st.image(full_path, use_container_width=True)
      else:
        st.caption("Fișier lipsă")
      st.caption(photo["device_model"] or "Fără device")
      if st.button("🗑️ Șterge", key=f"del_photo_{photo['id']}"):
        db.delete_photo(photo["id"])
        st.rerun()


# --- Oferte de piese -------------------------------------------------------


def _render_offers_tab(client):
  st.markdown(
      "Piesele găsite în căutare și salvate aici sunt legate de dispozitivul "
      "clientului. Schimbările de status se salvează în istoric."
  )
  offers = db.get_client_offers(client["id"])
  if not offers:
    st.info(
        "Nu există încă oferte salvate. Pornește o căutare dintr-un device sau"
        " folosește butonul „Salvează la client” din rezultatele căutării."
    )
    return

  status_colors = {s["name"]: s["color"] for s in db.get_part_statuses()}
  statuses = list(status_colors.keys()) or ["De comandat"]

  grouped = {}
  for offer in offers:
    grouped.setdefault(offer["device_id"], []).append(offer)

  for device_id, items in grouped.items():
    device_label = items[0]["device_model"] or f"Device #{device_id}"
    with st.expander(f"📱 {device_label} · 🔩 {len(items)} oferte", expanded=True):
      for offer in items:
        with st.container(border=True):
          title = html.escape(str(offer["product_name"] or "Piesă"))
          link = str(offer["link"] or "").strip()
          if link.startswith(("http://", "https://")):
            title = f'<a href="{html.escape(link, quote=True)}" target="_blank">{title}</a>'
          st.markdown(
              f"**{title}**  "
              + _badge(offer["status"], status_colors.get(offer["status"])),
              unsafe_allow_html=True,
          )
          col1, col2 = st.columns([2, 2])
          with col1:
            st.caption(f"💰 {offer['price'] or '—'} · 🏬 {offer['store'] or '—'}")
          with col2:
            st.caption(
                f"Cantitate: {offer['quantity']} · Salvată: {offer['created_at']}"
            )
          if offer["part_number"]:
            st.caption(f"Căutare: `{offer['part_number']}`")
          if offer["notes"]:
            st.caption(f"📝 {offer['notes']}")

          with st.expander("✏️ Editează oferta", expanded=False):
            with st.form(f"edit_offer_{offer['id']}"):
              idx = statuses.index(offer["status"]) if offer["status"] in statuses else 0
              new_status = st.selectbox("Status piesă", statuses, index=idx)
              new_qty = st.number_input(
                  "Cantitate", min_value=1, value=int(offer["quantity"] or 1), step=1
              )
              new_notes = st.text_area(
                  "Notițe", value=offer["notes"] or "", height=70
              )
              save = st.form_submit_button("💾 Salvează", use_container_width=True)
            if save:
              db.update_offer(
                  offer["id"],
                  status=new_status,
                  quantity=new_qty,
                  notes=new_notes,
              )
              st.success("Oferta a fost actualizată.")
              st.rerun()
            if st.checkbox("Șterge oferta", key=f"confirm_del_offer_{offer['id']}"):
              if st.button("Confirmă ștergerea", key=f"del_offer_{offer['id']}"):
                db.delete_offer(offer["id"])
                st.success("Oferta a fost ștearsă.")
                st.rerun()


# --- Financiar -------------------------------------------------------------


def _render_financial_tab(client):
  st.markdown(
      "Înregistrează banii primiți de la client și cheltuielile făcute pentru "
      "repararea lui. Profitul se calculează automat: **Încasat − Cheltuit**."
  )

  summary = db.get_client_financial_summary(client["id"])
  profit = summary["profit"]
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("💵 Încasat", format_money(summary["total_income"]))
  with col2:
    st.metric("💸 Cheltuit", format_money(summary["total_expense"]))
  with col3:
    st.metric("📈 Profit", format_money(profit))

  color = "#3fb950" if profit >= 0 else "#f85149"
  st.markdown(
      f'<span style="color:{color};font-size:0.82rem;font-weight:600;">'
      f"{summary['transaction_count']} tranzacție/tranzacții înregistrate"
      "</span>",
      unsafe_allow_html=True,
  )

  st.markdown("---")
  st.subheader("➕ Tranzacție nouă")
  with st.form(f"add_transaction_{client['id']}"):
    type_col, category_col = st.columns(2)
    with type_col:
      tx_type = st.selectbox("Tip", list(db.TRANSACTION_TYPES))
    with category_col:
      category = st.selectbox("Categorie", list(db.TRANSACTION_CATEGORIES))
    amount_col, desc_col = st.columns([1, 3])
    with amount_col:
      amount = st.number_input(
          "Sumă (Lei)", min_value=0.01, value=1.0, step=10.0, format="%.2f"
      )
    with desc_col:
      description = st.text_input(
          "Descriere",
          placeholder="ex. Tastatură HP 250 G7 — plătită furnizor",
      )
    add = st.form_submit_button("💾 Adaugă tranzacția", use_container_width=True)
  if add:
    transaction_id = db.add_transaction(
        client["id"],
        tx_type,
        amount,
        category=category,
        description=description,
    )
    if transaction_id is None:
      st.warning("Introdu o sumă pozitivă pentru tranzacție.")
    else:
      st.success("Tranzacția a fost adăugată în istoric.")
      st.rerun()

  st.markdown("---")
  st.subheader("🧾 Tranzacții")
  transactions = db.get_client_transactions(client["id"])
  if not transactions:
    st.info("Nu există tranzacții înregistrate pentru acest client.")
    return

  for tx in transactions:
    is_income = tx["type"] == "Încasare"
    icon = "➕" if is_income else "➖"
    tx_color = "#3fb950" if is_income else "#f85149"
    with st.container(border=True):
      st.markdown(
          f"{icon} **{html.escape(tx['type'])}** · "
          f"<span style='color:{tx_color};font-weight:700;'>"
          f"{format_money(tx['amount'])}</span> · `{html.escape(tx['category'])}`",
          unsafe_allow_html=True,
      )
      details = tx["created_at"]
      if tx["description"]:
        details += f" · {html.escape(tx['description'])}"
      st.caption(details)

      with st.expander("✏️ Editează tranzacția", expanded=False):
        type_index = (
            db.TRANSACTION_TYPES.index(tx["type"])
            if tx["type"] in db.TRANSACTION_TYPES
            else 0
        )
        category_index = (
            db.TRANSACTION_CATEGORIES.index(tx["category"])
            if tx["category"] in db.TRANSACTION_CATEGORIES
            else 0
        )
        with st.form(f"edit_transaction_{tx['id']}"):
          e_type = st.selectbox(
              "Tip", list(db.TRANSACTION_TYPES), index=type_index,
              key=f"edit_tx_type_{tx['id']}",
          )
          e_category = st.selectbox(
              "Categorie", list(db.TRANSACTION_CATEGORIES), index=category_index,
              key=f"edit_tx_category_{tx['id']}",
          )
          e_amount = st.number_input(
              "Sumă (Lei)",
              min_value=0.01,
              value=float(tx["amount"]),
              step=10.0,
              format="%.2f",
              key=f"edit_tx_amount_{tx['id']}",
          )
          e_description = st.text_input(
              "Descriere", value=tx["description"] or "",
              key=f"edit_tx_description_{tx['id']}",
          )
          save = st.form_submit_button("💾 Salvează", use_container_width=True)
        if save:
          db.update_transaction(
              tx["id"],
              type=e_type,
              amount=e_amount,
              category=e_category,
              description=e_description,
          )
          st.success("Tranzacția a fost actualizată.")
          st.rerun()
        if st.checkbox("Șterge tranzacția", key=f"confirm_del_tx_{tx['id']}"):
          if st.button("Confirmă ștergerea", key=f"del_tx_{tx['id']}"):
            db.delete_transaction(tx["id"])
            st.success("Tranzacția a fost ștearsă.")
            st.rerun()


# --- Istoric ---------------------------------------------------------------


def _render_history_tab(client):
  st.markdown("Fiecare modificare este salvată automat cu dată și oră.")

  with st.form(f"add_intervention_{client['id']}"):
    details = st.text_area(
        "Descriere intervenție",
        placeholder="ex. Verificat sursa, înlocuit condensatorul C12...",
        height=80,
    )
    add = st.form_submit_button("➕ Adaugă intervenție în istoric", use_container_width=True)
  if add:
    db.add_intervention(client["id"], details)
    st.success("Intervenția a fost adăugată.")
    st.rerun()

  st.markdown("---")
  entries = db.get_client_history(client["id"])
  if not entries:
    st.info("Încă nu există evenimente în istoric.")
    return

  for entry in entries:
    with st.container(border=True):
      st.markdown(f"**{entry['created_at']}** · {html.escape(entry['action'])}")
      if entry["details"]:
        st.caption(entry["details"])


# --- Workspace client selectat ---------------------------------------------


def _render_client_workspace(client_id):
  client = db.get_client(client_id)
  if not client:
    st.warning("Clientul selectat nu mai există.")
    return

  st.markdown("---")
  st.markdown(
      f"## {html.escape(client['name'])} "
      + _badge(client["status_name"], client["status_color"]),
      unsafe_allow_html=True,
  )
  st.caption(f"ID #{client['id']} · Telefon: {client['phone']}")

  tabs = st.tabs(
      [
          "✏️ Editare", "📱 Dispozitive", "🔩 Piese/Oferte",
          "💰 Financiar", "📷 Poze", "🕘 Istoric",
      ]
  )
  with tabs[0]:
    _render_edit_client(client)
  with tabs[1]:
    _render_devices_tab(client)
  with tabs[2]:
    _render_offers_tab(client)
  with tabs[3]:
    _render_financial_tab(client)
  with tabs[4]:
    _render_photos_tab(client)
  with tabs[5]:
    _render_history_tab(client)


# --- Lista clienți (tabel) -------------------------------------------------


def _render_client_list():
  statuses = db.get_statuses()
  status_names = [s["name"] for s in statuses]
  counts = db.get_status_counts()

  metric_cols = st.columns(min(len(counts), 6) or 1)
  for idx, (status_name, count) in enumerate(counts.items()):
    with metric_cols[idx % len(metric_cols)]:
      st.metric(status_name, count)

  st.markdown("---")
  col1, col2 = st.columns([2, 2])
  with col1:
    search = st.text_input(
        "🔎 Caută client (nume / telefon / device)", key="clients_search"
    )
  with col2:
    selected_statuses = st.multiselect(
        "Filtrează după status", status_names, key="clients_status_filter"
    )

  clients = db.list_clients(search=search or "", status_names=selected_statuses)
  st.caption(f"{len(clients)} client/clienti găsiți · selectează un rând pentru detalii")

  if not clients:
    st.info("Nu există clienți care să corespundă filtrelor.")
    return

  table_data = [
      {
          "Nume client": c["name"],
          "Status": c["status_name"] or "Fără status",
          "Nr. telefon": c["phone"],
          "Dispozitive": c["devices"] or "—",
          "Încasat": round(c["total_income"], 2),
          "Cheltuit": round(c["total_expense"], 2),
          "Profit": round(c["profit"], 2),
          "Creat": c["created_at"],
          "Ultimul update": c["updated_at"],
      }
      for c in clients
  ]
  df = pd.DataFrame(table_data, index=[c["id"] for c in clients])

  def _profit_style(value):
    if value > 0:
      return "color: #3fb950; font-weight: 700"
    if value < 0:
      return "color: #f85149; font-weight: 700"
    return ""

  # Styler se folosește doar pentru culori; formatarea numerelor e în column_config.
  styled_df = df.style.map(_profit_style, subset=["Profit"])

  event = st.dataframe(
      styled_df,
      hide_index=True,
      width="stretch",
      column_config={
          "Încasat": st.column_config.NumberColumn("Încasat", format="%.2f Lei"),
          "Cheltuit": st.column_config.NumberColumn("Cheltuit", format="%.2f Lei"),
          "Profit": st.column_config.NumberColumn("Profit", format="%.2f Lei"),
      },
      selection_mode="single-row",
      on_select="rerun",
      key="clients_table",
  )
  selected_rows = event.selection.rows
  if selected_rows:
    selected_id = int(df.index[selected_rows[0]])
    _render_client_workspace(selected_id)


# --- Statusuri -------------------------------------------------------------


def _render_statuses():
  st.markdown(
      "Statusurile pot fi extinse oricând și sunt folosite în tabelul de clienți și în filtre."
  )
  counts = db.get_status_counts()
  statuses = db.get_statuses()

  for status in statuses:
    cols = st.columns([3, 1, 1])
    with cols[0]:
      st.markdown(
          _badge(status["name"], status["color"])
          + f" <span style='color:#8b949e;font-size:0.78rem;'>"
          f"({counts.get(status['name'], 0)} clienți)</span>",
          unsafe_allow_html=True,
      )
    with cols[2]:
      confirm_key = f"confirm_delete_status_{status['id']}"
      if st.checkbox("Șterge", key=confirm_key):
        if st.button("Confirmă", key=f"del_status_{status['id']}"):
          if db.delete_status(status["id"]):
            st.success("Statusul a fost șters.")
          else:
            st.warning("Statusul este folosit de cel puțin un client.")
          st.rerun()

  st.markdown("---")
  st.subheader("➕ Status nou")
  col1, col2 = st.columns([2, 1])
  with col1:
    new_name = st.text_input("Nume status", placeholder="ex. În așteptare client")
  with col2:
    new_color = st.color_picker("Culoare", value="#1f6feb")
  if st.button("Adaugă status", use_container_width=True):
    if not (new_name or "").strip():
      st.warning("Introdu un nume pentru status.")
    elif db.add_status(new_name, new_color) is None:
      st.warning("Există deja un status cu acest nume.")
    else:
      st.success("Statusul a fost adăugat.")
      st.rerun()


def render_clients_page():
  db.init_db()
  st.title("🧾 Clienți & Service")
  st.markdown("Evidența clienților, a dispozitivelor și a intervențiilor de reparare.")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Client nou", "📋 Listă clienți", "🏷️ Statusuri"]
  )
  with tab1:
    _render_add_client()
  with tab2:
    _render_client_list()
  with tab3:
    _render_statuses()
