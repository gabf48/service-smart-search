import asyncio
import importlib
import json
import os
import re
from scrapers import emag, onlaptop, piese_laptop, powerlaptop
import httpx
from utils.filters import (
    is_irrelevant_product,
    normalize_price_display,
    parse_price_for_sorting,
)
from utils.tags import classify_category  # <--- Importul clasificatorului global de categorii


def load_stores():
  if os.path.exists("websites.json"):
    try:
      with open("websites.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("stores", [])
    except Exception:
      pass
  return [
      {"name": "Powerlaptop", "domain": "powerlaptop.ro"},
      {"name": "eMAG", "domain": "emag.ro"},
      {"name": "Piese-Laptop", "domain": "piese-laptop.ro"},
      {"name": "OnLaptop", "domain": "onlaptop.ro"},
  ]


async def _run_store_scrape(store_name, scrape_coro):
  try:
    results = await scrape_coro
    if not isinstance(results, list):
      return store_name, []
    return store_name, results
  except Exception as e:
    print(f"Eroare la {store_name}: {e}")
    return store_name, []


def get_search_task_specs(part_number: str, client: httpx.AsyncClient):
  specs = []

  try:
    importlib.reload(piese_laptop)
    specs.append(("Piese-Laptop", piese_laptop.scrape(client, part_number)))
  except Exception as e:
    print(f"Eroare la piese_laptop: {e}")

  try:
    importlib.reload(emag)
    specs.append(("eMAG", emag.scrape(client, part_number)))
  except Exception as e:
    print(f"Eroare la emag: {e}")

  try:
    importlib.reload(powerlaptop)
    specs.append(("Powerlaptop", powerlaptop.scrape(client, part_number)))
  except Exception as e:
    print(f"Eroare la powerlaptop: {e}")

  try:
    importlib.reload(onlaptop)
    specs.append(("OnLaptop", onlaptop.scrape(client, part_number)))
  except Exception as e:
    print(f"Eroare la onlaptop: {e}")

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