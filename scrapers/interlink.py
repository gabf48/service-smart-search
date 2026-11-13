import asyncio
import importlib
import json
import httpx


def load_stores():
  with open("websites.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    return data.get("stores", [])


async def search_single_store(store, client, part_number):
  module_name = store.get("module")
  if not module_name:
    return []

  try:
    # Importă dinamic modulul din folderul scrapers (ex: scrapers.interlink)
    scraper_module = importlib.import_module(f"scrapers.{module_name}")
    if hasattr(scraper_module, "scrape"):
      return await scraper_module.scrape(client, part_number)
  except Exception as e:
    print(f"Eroare la rularea scraperului pentru {store['name']}: {e}")

  return []


async def search_parts(part_number: str):
  stores = load_stores()

  # Setăm un Client HTTP global cu headere de browser standard
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  async with httpx.AsyncClient(
      headers=headers, follow_redirects=True, timeout=10
  ) as client:
    # Lansăm cererile în paralel pentru toate magazinele active
    tasks = [
        search_single_store(store, client, part_number) for store in stores
    ]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_results = []
    for res in results_nested:
      if isinstance(res, list):
        all_results.extend(res)

    return all_results