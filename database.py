"""SQLite persistence for the service/client module.

The database lives in a local ``data/`` folder next to the application, so no
external server or extra dependency is needed (``sqlite3`` is in the standard
library).
"""

import os
import sqlite3
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "service.db")

ALLOWED_PHOTO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

DEFAULT_STATUSES = [
    ("Nou", "#1f6feb", 0),
    ("În diagnostic", "#d29922", 1),
    ("Așteaptă piese", "#a371f7", 2),
    ("În reparare", "#f0883e", 3),
    ("Gata de ridicare", "#3fb950", 4),
    ("Finalizat", "#238636", 5),
    ("Anulat", "#f85149", 6),
]

DEFAULT_PART_STATUSES = [
    ("De comandat", "#d29922", 0),
    ("Comandată", "#1f6feb", 1),
    ("Primată", "#a371f7", 2),
    ("Montată", "#238636", 3),
    ("Anulată", "#f85149", 4),
]

FIELD_LABELS = {
    "name": "Nume",
    "phone": "Telefon",
    "problem": "Problemă",
    "notes": "Observații",
    "status_id": "Status",
}


def get_connection():
  os.makedirs(DATA_DIR, exist_ok=True)
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA foreign_keys = ON")
  conn.execute("PRAGMA journal_mode = WAL")
  return conn


def _log(conn, client_id, action, details=""):
  conn.execute(
      "INSERT INTO client_history (client_id, action, details) VALUES (?, ?, ?)",
      (client_id, action, details or ""),
  )


def _status_name(conn, status_id):
  if status_id is None:
    return "—"
  row = conn.execute("SELECT name FROM statuses WHERE id = ?", (status_id,)).fetchone()
  return row["name"] if row else "—"


def init_db():
  os.makedirs(UPLOAD_DIR, exist_ok=True)
  with get_connection() as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#1f6feb',
            sort_order INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            device TEXT NOT NULL DEFAULT '',
            problem TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            status_id INTEGER REFERENCES statuses(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            model TEXT NOT NULL,
            mtm TEXT NOT NULL DEFAULT '',
            serial_number TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS client_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS client_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            action TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS part_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#1f6feb',
            sort_order INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS device_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            product_name TEXT NOT NULL,
            price TEXT NOT NULL DEFAULT '',
            store TEXT NOT NULL DEFAULT '',
            link TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            part_number TEXT NOT NULL DEFAULT '',
            quantity INTEGER NOT NULL DEFAULT 1,
            notes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'De comandat',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    # Migrare pentru baze create înainte de adăugarea dispozitivelor multiple.
    photo_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(client_photos)")
    }
    if "device_id" not in photo_columns:
      conn.execute(
          "ALTER TABLE client_photos ADD COLUMN device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL"
      )

    # Migrare pentru baze create înainte de adăugarea câmpului MTM.
    device_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(devices)")
    }
    if "mtm" not in device_columns:
      conn.execute("ALTER TABLE devices ADD COLUMN mtm TEXT NOT NULL DEFAULT ''")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_photos_client ON client_photos(client_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_devices_client ON devices(client_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_client ON client_history(client_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_offers_device ON device_offers(device_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_offers_client ON device_offers(client_id)"
    )

    count = conn.execute("SELECT COUNT(*) FROM statuses").fetchone()[0]
    if count == 0:
      conn.executemany(
          "INSERT INTO statuses (name, color, sort_order) VALUES (?, ?, ?)",
          DEFAULT_STATUSES,
      )

    part_count = conn.execute("SELECT COUNT(*) FROM part_statuses").fetchone()[0]
    if part_count == 0:
      conn.executemany(
          "INSERT INTO part_statuses (name, color, sort_order) VALUES (?, ?, ?)",
          DEFAULT_PART_STATUSES,
      )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    # Mută device-ul vechi (un singur text) în tabela de dispozitive — O DATĂ.
    # Fără flag, init_db() ar re-insera device-ul după fiecare editare/ștergere.
    already_migrated = conn.execute(
        "SELECT value FROM schema_meta WHERE key = 'legacy_devices_migrated'"
    ).fetchone()
    if not already_migrated:
      legacy = conn.execute(
          "SELECT id, device FROM clients WHERE device IS NOT NULL AND device != ''"
      ).fetchall()
      for row in legacy:
        exists = conn.execute(
            "SELECT 1 FROM devices WHERE client_id = ? AND model = ?",
            (row["id"], row["device"]),
        ).fetchone()
        if not exists:
          conn.execute(
              "INSERT INTO devices (client_id, model) VALUES (?, ?)",
              (row["id"], row["device"]),
          )
      # Câmpul denormalizat rămâne gol: sursa de adevăr e tabela devices.
      conn.execute(
          "UPDATE clients SET device = '' WHERE device IS NOT NULL AND device != ''"
      )
      conn.execute(
          "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
          ("legacy_devices_migrated", "1"),
      )


# --- Statusuri -------------------------------------------------------------


def get_statuses():
  with get_connection() as conn:
    rows = conn.execute(
        "SELECT id, name, color, sort_order FROM statuses ORDER BY sort_order, id"
    ).fetchall()
  return [dict(row) for row in rows]


def add_status(name, color="#1f6feb"):
  clean_name = (name or "").strip()
  if not clean_name:
    return None
  with get_connection() as conn:
    existing = conn.execute(
        "SELECT id FROM statuses WHERE LOWER(name) = LOWER(?)", (clean_name,)
    ).fetchone()
    if existing:
      return None
    sort_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM statuses"
    ).fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO statuses (name, color, sort_order) VALUES (?, ?, ?)",
        (clean_name, color or "#1f6feb", sort_order),
    )
    return cursor.lastrowid


def delete_status(status_id):
  with get_connection() as conn:
    in_use = conn.execute(
        "SELECT COUNT(*) FROM clients WHERE status_id = ?", (status_id,)
    ).fetchone()[0]
    if in_use:
      return False
    conn.execute("DELETE FROM statuses WHERE id = ?", (status_id,))
    return True


def get_status_counts():
  with get_connection() as conn:
    rows = conn.execute(
        """
        SELECT s.name, COUNT(c.id) AS count
        FROM statuses s LEFT JOIN clients c ON c.status_id = s.id
        GROUP BY s.id, s.name ORDER BY s.sort_order, s.id
        """
    ).fetchall()
  return {row["name"]: row["count"] for row in rows}


# --- Clienți ---------------------------------------------------------------


def _save_photos(conn, client_id, uploaded_files, device_id=None):
  os.makedirs(UPLOAD_DIR, exist_ok=True)
  saved = 0
  for uploaded in uploaded_files or []:
    extension = os.path.splitext(uploaded.name)[1].lower()
    if extension not in ALLOWED_PHOTO_EXTENSIONS:
      extension = ".bin"
    filename = f"{client_id}_{uuid.uuid4().hex}{extension}"
    destination = os.path.join(UPLOAD_DIR, filename)
    with open(destination, "wb") as output:
      output.write(uploaded.getbuffer())
    relative_path = os.path.join("uploads", filename).replace("\\", "/")
    conn.execute(
        "INSERT INTO client_photos (client_id, device_id, file_path) VALUES (?, ?, ?)",
        (client_id, device_id, relative_path),
    )
    saved += 1
  return saved


def add_client(name, phone, device="", problem="", notes="", status_id=None,
               uploaded_files=None):
  with get_connection() as conn:
    if status_id is None:
      status_id = conn.execute(
          "SELECT id FROM statuses ORDER BY sort_order, id LIMIT 1"
      ).fetchone()[0]
    cursor = conn.execute(
        """
        INSERT INTO clients (name, phone, device, problem, notes, status_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            (name or "").strip(),
            (phone or "").strip(),
            (device or "").strip(),
            (problem or "").strip(),
            (notes or "").strip(),
            status_id,
        ),
    )
    client_id = cursor.lastrowid
    if (device or "").strip():
      conn.execute(
          "INSERT INTO devices (client_id, model) VALUES (?, ?)",
          (client_id, (device or "").strip()),
      )
    saved = _save_photos(conn, client_id, uploaded_files)
    _log(
        conn,
        client_id,
        "Client creat",
        f"Status: {_status_name(conn, status_id)}"
        + (f" · Dispozitiv: {device.strip()}" if (device or "").strip() else ""),
    )
    if saved:
      _log(conn, client_id, "Poze adăugate", f"{saved} poză/poze")
    return client_id


def update_client(client_id, **fields):
  allowed = {"name", "phone", "problem", "notes", "status_id"}
  updates = {k: v for k, v in fields.items() if k in allowed}
  if not updates:
    return
  with get_connection() as conn:
    old = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if not old:
      return

    changes = []
    changed_values = []
    for key, value in updates.items():
      if old[key] == value:
        continue
      if key == "status_id":
        changes.append(
            f"Status: {_status_name(conn, old[key])} → {_status_name(conn, value)}"
        )
      else:
        changes.append(f"{FIELD_LABELS.get(key, key)}: {old[key] or '—'} → {value or '—'}")
      changed_values.append((key, value))
    if not changes:
      return

    assignments = [f"{key} = ?" for key, _ in changed_values]
    values = [value for _, value in changed_values]
    values.append(client_id)
    conn.execute(
        f"UPDATE clients SET {', '.join(assignments)}, "
        "updated_at = datetime('now', 'localtime') WHERE id = ?",
        values,
    )
    _log(conn, client_id, "Client actualizat", "; ".join(changes))


def set_client_status(client_id, status_id):
  update_client(client_id, status_id=status_id)


def list_clients(search="", status_names=None):
  query = """
      SELECT c.id, c.name, c.phone, c.problem, c.notes,
             c.created_at, c.updated_at,
             s.id AS status_id, s.name AS status_name, s.color AS status_color,
             (SELECT COUNT(*) FROM client_photos p WHERE p.client_id = c.id) AS photo_count,
             (SELECT GROUP_CONCAT(d.model, ', ') FROM devices d WHERE d.client_id = c.id) AS devices,
             (SELECT COUNT(*) FROM devices d WHERE d.client_id = c.id) AS device_count
      FROM clients c
      LEFT JOIN statuses s ON s.id = c.status_id
      WHERE 1 = 1
  """
  params = []
  if search:
    query += """
        AND (LOWER(c.name) LIKE ? OR LOWER(c.phone) LIKE ?
             OR LOWER(c.device) LIKE ?
             OR EXISTS (SELECT 1 FROM devices d
                        WHERE d.client_id = c.id
                           AND (LOWER(d.model) LIKE ? OR LOWER(d.mtm) LIKE ?)))
    """
    like = f"%{search.lower()}%"
    params.extend([like, like, like, like, like])
  if status_names:
    placeholders = ", ".join("?" for _ in status_names)
    query += f" AND s.name IN ({placeholders})"
    params.extend(status_names)
  query += " ORDER BY c.id DESC"

  with get_connection() as conn:
    rows = conn.execute(query, params).fetchall()
  return [dict(row) for row in rows]


def get_client(client_id):
  with get_connection() as conn:
    row = conn.execute(
        """
        SELECT c.*, s.name AS status_name, s.color AS status_color
        FROM clients c LEFT JOIN statuses s ON s.id = c.status_id
        WHERE c.id = ?
        """,
        (client_id,),
    ).fetchone()
  return dict(row) if row else None


# --- Dispozitive -----------------------------------------------------------


def get_client_devices(client_id):
  with get_connection() as conn:
    rows = conn.execute(
        "SELECT id, model, mtm, serial_number, notes, created_at "
        "FROM devices WHERE client_id = ? ORDER BY id",
        (client_id,),
    ).fetchall()
  return [dict(row) for row in rows]


def add_device(client_id, model, mtm="", serial_number="", notes=""):
  clean_model = (model or "").strip()
  if not clean_model:
    return None
  clean_mtm = (mtm or "").strip()
  with get_connection() as conn:
    cursor = conn.execute(
        "INSERT INTO devices (client_id, model, mtm, serial_number, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            client_id,
            clean_model,
            clean_mtm,
            (serial_number or "").strip(),
            (notes or "").strip(),
        ),
    )
    device_id = cursor.lastrowid
    _log(
        conn,
        client_id,
        "Dispozitiv adăugat",
        clean_model + (f" · MTM: {clean_mtm}" if clean_mtm else ""),
    )
    return device_id


def update_device(device_id, **fields):
  allowed = {"model", "mtm", "serial_number", "notes"}
  updates = {k: v for k, v in fields.items() if k in allowed}
  if not updates:
    return
  with get_connection() as conn:
    old = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    if not old:
      return
    changes = [
        f"{k}: {old[k] or '—'} → {v or '—'}"
        for k, v in updates.items()
        if old[k] != v
    ]
    if not changes:
      return
    assignments = [f"{k} = ?" for k in updates]
    values = list(updates.values()) + [device_id]
    conn.execute(
        f"UPDATE devices SET {', '.join(assignments)} WHERE id = ?", values
    )
    _log(conn, old["client_id"], "Dispozitiv actualizat", "; ".join(changes))


def delete_device(device_id):
  with get_connection() as conn:
    old = conn.execute(
        "SELECT client_id, model FROM devices WHERE id = ?", (device_id,)
    ).fetchone()
    if not old:
      return
    conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    _log(conn, old["client_id"], "Dispozitiv șters", old["model"])


# --- Poze ------------------------------------------------------------------


def get_client_photos(client_id):
  with get_connection() as conn:
    rows = conn.execute(
        """
        SELECT p.id, p.file_path, p.device_id, p.uploaded_at, d.model AS device_model
        FROM client_photos p LEFT JOIN devices d ON d.id = p.device_id
        WHERE p.client_id = ? ORDER BY p.id
        """,
        (client_id,),
    ).fetchall()
  return [dict(row) for row in rows]


def add_photos(client_id, uploaded_files, device_id=None):
  with get_connection() as conn:
    saved = _save_photos(conn, client_id, uploaded_files, device_id)
    if saved:
      _log(conn, client_id, "Poze adăugate", f"{saved} poză/poze")
    return saved


def photo_full_path(file_path):
  return os.path.join(DATA_DIR, file_path.replace("/", os.sep))


def delete_photo(photo_id):
  with get_connection() as conn:
    row = conn.execute(
        "SELECT client_id, file_path FROM client_photos WHERE id = ?", (photo_id,)
    ).fetchone()
    if not row:
      return
    full_path = photo_full_path(row["file_path"])
    conn.execute("DELETE FROM client_photos WHERE id = ?", (photo_id,))
    _log(conn, row["client_id"], "Poză ștearsă", "")
  if os.path.exists(full_path):
    os.remove(full_path)


# --- Istoric ---------------------------------------------------------------


def get_client_history(client_id, limit=200):
  with get_connection() as conn:
    rows = conn.execute(
        """
        SELECT id, action, details, created_at
        FROM client_history WHERE client_id = ?
        ORDER BY id DESC LIMIT ?
        """,
        (client_id, limit),
    ).fetchall()
  return [dict(row) for row in rows]


def add_intervention(client_id, details):
  clean = (details or "").strip()
  if not clean:
    return
  with get_connection() as conn:
    _log(conn, client_id, "Intervenție", clean)


def delete_client(client_id):
  photos = get_client_photos(client_id)
  with get_connection() as conn:
    conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
  for photo in photos:
    full_path = photo_full_path(photo["file_path"])
    if os.path.exists(full_path):
      os.remove(full_path)


# --- Oferte de piese (corelare căutare ↔ device) ---------------------------


OFFER_FIELD_LABELS = {
    "product_name": "Piesă",
    "price": "Preț",
    "store": "Magazin",
    "link": "Link",
    "quantity": "Cantitate",
    "notes": "Notițe",
    "status": "Status piesă",
}


def get_part_statuses():
  with get_connection() as conn:
    rows = conn.execute(
        "SELECT name, color FROM part_statuses ORDER BY sort_order, id"
    ).fetchall()
  return [dict(row) for row in rows]


def get_device_owner(device_id):
  with get_connection() as conn:
    row = conn.execute(
        """
        SELECT d.id AS device_id, d.model, d.mtm, d.serial_number,
               d.client_id, c.name AS client_name
        FROM devices d JOIN clients c ON c.id = d.client_id
        WHERE d.id = ?
        """,
        (device_id,),
    ).fetchone()
  return dict(row) if row else None


def get_device_offers(device_id):
  with get_connection() as conn:
    rows = conn.execute(
        "SELECT * FROM device_offers WHERE device_id = ? ORDER BY id DESC",
        (device_id,),
    ).fetchall()
  return [dict(row) for row in rows]


def get_client_offers(client_id):
  with get_connection() as conn:
    rows = conn.execute(
        """
        SELECT o.*, d.model AS device_model
        FROM device_offers o LEFT JOIN devices d ON d.id = o.device_id
        WHERE o.client_id = ? ORDER BY o.device_id, o.id DESC
        """,
        (client_id,),
    ).fetchall()
  return [dict(row) for row in rows]


def get_offer_counts_by_device(client_id):
  with get_connection() as conn:
    rows = conn.execute(
        "SELECT device_id, COUNT(*) AS count FROM device_offers "
        "WHERE client_id = ? GROUP BY device_id",
        (client_id,),
    ).fetchall()
  return {row["device_id"]: row["count"] for row in rows}


def get_offer(offer_id):
  with get_connection() as conn:
    row = conn.execute(
        "SELECT * FROM device_offers WHERE id = ?", (offer_id,)
    ).fetchone()
  return dict(row) if row else None


def add_offer(device_id, product, part_number="", status=None, quantity=1, notes=""):
  """Salvează o ofertă din rezultatele căutării, legată de un device."""
  with get_connection() as conn:
    device = conn.execute(
        "SELECT d.model, d.client_id FROM devices d WHERE d.id = ?", (device_id,)
    ).fetchone()
    if not device:
      return None
    if not status:
      first = conn.execute(
          "SELECT name FROM part_statuses ORDER BY sort_order, id LIMIT 1"
      ).fetchone()
      status = first["name"] if first else DEFAULT_PART_STATUSES[0][0]
    cursor = conn.execute(
        """
        INSERT INTO device_offers
            (device_id, client_id, product_name, price, store, link,
             image_url, category, part_number, quantity, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            device_id,
            device["client_id"],
            str(product.get("Produs") or "").strip(),
            str(product.get("Preț") or "").strip(),
            str(product.get("Magazin") or "").strip(),
            str(product.get("Sursă / Link") or "").strip(),
            str(product.get("Imagine") or "").strip(),
            str(product.get("Categorie") or "").strip(),
            str(part_number or "").strip(),
            max(1, int(quantity or 1)),
            (notes or "").strip(),
            status,
        ),
    )
    offer_id = cursor.lastrowid
    _log(
        conn,
        device["client_id"],
        "Ofertă salvată",
        f"{str(product.get('Produs') or '')[:70]} · {device['model']} · {status}",
    )
    return offer_id


def update_offer(offer_id, **fields):
  allowed = {"product_name", "price", "store", "link", "quantity", "notes", "status"}
  updates = {k: v for k, v in fields.items() if k in allowed}
  if not updates:
    return
  with get_connection() as conn:
    old = conn.execute(
        "SELECT * FROM device_offers WHERE id = ?", (offer_id,)
    ).fetchone()
    if not old:
      return

    changes = []
    changed_values = []
    for key, value in updates.items():
      if key == "quantity":
        value = max(1, int(value or 1))
      elif isinstance(value, str):
        value = value.strip()
      if old[key] == value:
        continue
      changes.append(
          f"{OFFER_FIELD_LABELS.get(key, key)}: {old[key] or '—'} → {value or '—'}"
      )
      changed_values.append((key, value))
    if not changes:
      return

    assignments = [f"{key} = ?" for key, _ in changed_values]
    assignments.append("updated_at = datetime('now', 'localtime')")
    values = [value for _, value in changed_values] + [offer_id]
    conn.execute(
        f"UPDATE device_offers SET {', '.join(assignments)} WHERE id = ?", values
    )
    _log(conn, old["client_id"], "Ofertă actualizată", "; ".join(changes))


def delete_offer(offer_id):
  with get_connection() as conn:
    old = conn.execute(
        "SELECT client_id, product_name FROM device_offers WHERE id = ?", (offer_id,)
    ).fetchone()
    if not old:
      return
    conn.execute("DELETE FROM device_offers WHERE id = ?", (offer_id,))
    _log(conn, old["client_id"], "Ofertă ștearsă", old["product_name"])
