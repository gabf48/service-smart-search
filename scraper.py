import asyncio
import importlib
import json
import os
import re

import httpx

from utils.filters import (
    is_irrelevant_product,
    normalize_price_display,
    parse_price_for_sorting,
)
from utils.tags import classify_category  # <--- Importul clasificatorului global de categorii


# Magazinele active sunt definite în websites.json. `module` e fișierul din
# scrapers/ care știe să caute în magazinul respectiv.
DEFAULT_STORES = [
    {"name": "Powerlaptop", "domain": "powerlaptop.ro", "module": "powerlaptop", "enabled": True},
    {"name": "eMAG", "domain": "emag.ro", "module": "emag", "enabled": True},
    {"name": "Piese-Laptop", "domain": "piese-laptop.ro", "module": "piese_laptop", "enabled": True},
    {"name": "OnLaptop", "domain": "onlaptop.ro", "module": "onlaptop", "enabled": True},
    {"name": "PC Garage", "domain": "pcgarage.ro", "module": "pc_garage", "enabled": True},
    {"name": "Interlink", "domain": "interlink.ro", "module": "interlink", "enabled": True},
]


def _module_from_name(name: str) -> str:
  return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(name).lower())).strip("_")


def load_stores(enabled_only: bool = True):
  """Citește magazinele din websites.json (cu fallback la lista implicită)."""
  stores = DEFAULT_STORES
  if os.path.exists("websites.json"):
    try:
      with open("websites.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        loaded = data.get("stores")
        if isinstance(loaded, list) and loaded:
          stores = loaded
    except Exception as e:
      print(f"Eroare la citirea websites.json: {e}")

  normalized = []
  for store in stores:
    if not isinstance(store, dict) or not store.get("name"):
      continue
    item = dict(store)
    item.setdefault("enabled", True)
    if not item.get("module"):
      item["module"] = _module_from_name(item["name"])
    normalized.append(item)

  if enabled_only:
    normalized = [store for store in normalized if store["enabled"]]
  return normalized


async def _run_store(scrape_fn, client, part_number: str, store_name: str):
  """Rulează un scraper și forțează numele magazinului pe fiecare rezultat."""
  results = await scrape_fn(client, part_number)
  if not isinstance(results, list):
    return []
  for item in results:
    if isinstance(item, dict):
      item["Magazin"] = store_name
  return results


def get_search_task_specs(part_number: str, client: httpx.AsyncClient):
  """Construiește sarcinile de căutare pentru toate magazinele active."""
  specs = []
  seen_modules = set()

  for store in load_stores(enabled_only=True):
    module_name = store["module"]
    if module_name in seen_modules:
      continue
    seen_modules.add(module_name)

    try:
      scraper_module = importlib.import_module(f"scrapers.{module_name}")
      scrape_fn = getattr(scraper_module, "scrape")
      specs.append((
          store["name"],
          _run_store(scrape_fn, client, part_number, store["name"]),
      ))
    except Exception as e:
      print(f"Eroare la încărcarea scraperului {module_name}: {e}")

  return specs


def process_search_results(all_results, part_number: str):
  filtered_results = []
  # Un magazin poate returna același produs de mai multe ori (paginare / reluări).
  # Între magazine păstrăm toate ofertele, ca să rămână comparația de preț.
  seen = {}
  for item in all_results:
    title = item.get("Produs", "")

    # 1. Dacă produsul este irelevant (telefon, tabletă, casnic, etc.), îl tăiem din start
    if is_irrelevant_product(title, part_number):
      continue

    # 2. Suprascriem categoria global pe baza titlului, asigurând consecvența între magazine
    item["Categorie"] = classify_category(title)
    item["Preț"] = normalize_price_display(item.get("Preț", "N/A"))

    key = (
        str(item.get("Magazin", "")).strip().lower(),
        re.sub(r"\s+", " ", str(title).strip().lower()),
    )
    if key in seen:
      idx = seen[key]
      old_price = parse_price_for_sorting(filtered_results[idx].get("Preț"))
      new_price = parse_price_for_sorting(item.get("Preț"))
      if new_price < old_price:
        filtered_results[idx] = item
    else:
      seen[key] = len(filtered_results)
      filtered_results.append(item)

  return filtered_results


async def search_parts(part_number: str):
  async with httpx.AsyncClient() as client:
    specs = get_search_task_specs(part_number, client)
    if not specs:
      return []

    tasks = [coro for _, coro in specs]
    responses = await asyncio.gather(*tasks)

    all_results = []
    for store_res in responses:
      all_results.extend(store_res)

    # 🛡️ FILTRARE GLOBALĂ & CLASIFICARE GLOBALĂ UNITARĂ
    return process_search_results(all_results, part_number)
