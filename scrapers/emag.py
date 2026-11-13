import html
import re
import urllib.parse
from bs4 import BeautifulSoup
import httpx


async def scrape(client: httpx.AsyncClient, part_number: str):
  store_name = "eMAG"
  domain = "emag.ro"

  query_encoded = urllib.parse.quote(part_number)
  target_url = f"https://www.emag.ro/search/{query_encoded}"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
      ),
      "Referer": "https://www.emag.ro/",
  }

  try:
    response = await client.get(
        target_url, headers=headers, timeout=10, follow_redirects=True
    )
    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    keywords = [w.lower() for w in part_number.split() if len(w.strip()) > 1]

    cards = soup.select(
        ".card-item, .card-v2, div[data-id], .card-section,"
        " div[class*='card-item']"
    )
    if not cards:
      cards = soup.select("div[class*='product']")

    for card in cards:
      link_tag = card.find("a", href=True)
      if not link_tag and card.name == "a":
        link_tag = card

      if not link_tag or not link_tag.get("href"):
        continue

      link = link_tag["href"]
      if link in ["#", "/"] or link.startswith("javascript"):
        continue

      if not link.startswith("http"):
        link = f"https://www.{domain}{link if link.startswith('/') else '/' + link}"

      title_elem = card.select_one(
          ".card-title, h2 a, a.product-title-link, .title-ph, h2"
      )
      if not title_elem:
        title_elem = card.find(["h1", "h2", "h3", "h4", "a"])

      raw_title = (
          title_elem.get_text(" ", strip=True)
          if title_elem
          else link_tag.get_text(" ", strip=True)
      )
      title = html.escape(" ".join(raw_title.split()))

      if not title or len(title) < 5:
        continue

      title_lower = title.lower()
      link_lower = link.lower()
      if keywords:
        matches = sum(
            1 for kw in keywords if kw in title_lower or kw in link_lower
        )
        min_matches = len(keywords) if len(keywords) <= 2 else len(keywords) - 1
        if matches < min_matches:
          continue

      # Extragere preț corectată pentru structura eMAG
      price = "N/A"
      price_container = card.select_one(
          ".product-new-price, .default-price, p.product-new-price"
      )

      if price_container:
        # Curățăm textul din containerul de preț (ex: "849 99 Lei" devine "849.99 Lei")
        p_text = price_container.get_text(" ", strip=True)
        p_text = re.sub(
            r"(\d+)\s+(\d{2})\s*(lei|ron)",
            r"\1.\2 Lei",
            p_text,
            flags=re.IGNORECASE,
        )
        if "lei" in p_text.lower() or "ron" in p_text.lower():
          price = html.escape(p_text)
      else:
        # Fallback generalist dacă nu găsește containerul specific
        card_text = card.get_text(" ", strip=True)
        price_match = re.search(
            r"(\d+\s*\d*([.,]\d+)?)\s*(lei|ron)", card_text, re.IGNORECASE
        )
        if price_match:
          price = html.escape(price_match.group(0))

      if not any(r["Sursă / Link"] == link for r in results):
        results.append({
            "Magazin": store_name,
            "Sursă / Link": link,
            "Produs": title[:95] + ("..." if len(title) > 95 else ""),
            "Preț": price,
        })

    return results
  except Exception:
    return []