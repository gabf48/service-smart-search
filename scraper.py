import asyncio
import importlib
import json
import os
from scrapers import emag, onlaptop, piese_laptop, powerlaptop
import httpx


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


async def search_parts(part_number: str):
  async with httpx.AsyncClient() as client:
    tasks = []

    # 1. Scraper Piese-Laptop
    try:
      importlib.reload(piese_laptop)
      tasks.append(piese_laptop.scrape(client, part_number))
    except Exception as e:
      print(f"Eroare la piese_laptop: {e}")

    # 2. Scraper eMAG
    try:
      importlib.reload(emag)
      tasks.append(emag.scrape(client, part_number))
    except Exception as e:
      print(f"Eroare la emag: {e}")

    # 3. Scraper Powerlaptop
    try:
      importlib.reload(powerlaptop)
      tasks.append(powerlaptop.scrape(client, part_number))
    except Exception as e:
      print(f"Eroare la powerlaptop: {e}")

    # 4. Scraper OnLaptop
    try:
      importlib.reload(onlaptop)
      tasks.append(onlaptop.scrape(client, part_number))
    except Exception as e:
      print(f"Eroare la onlaptop: {e}")

    if not tasks:
      return []

    responses = await asyncio.gather(*tasks)

    all_results = []
    for store_res in responses:
      all_results.extend(store_res)

  return all_results