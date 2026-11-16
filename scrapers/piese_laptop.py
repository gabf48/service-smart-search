import html
import re
import urllib.parse
from bs4 import BeautifulSoup
import httpx


async def scrape(client: httpx.AsyncClient, part_number: str):
  store_name = "Piese-Laptop"
  domain = "piese-laptop.ro"

  # Codificăm corect termenul de căutare pentru URL
  query_encoded = urllib.parse.quote(part_number)
  target_url = f"https://{domain}/cautare?q={query_encoded}"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  try:
    response = await client.get(
        target_url, headers=headers, timeout=8, follow_redirects=True
    )
    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    pn_clean = part_number.lower().strip()

    cards = soup.select(".card")
    if not cards:
      cards = soup.select(
          ".card-section, .product-item, div[class*='product']"
      )

    for card in cards:
      link_tag = card.find("a", href=True)
      if not link_tag and card.name == "a":
        link_tag = card

      if not link_tag:
        continue

      title_elem = card.select_one(".card-title")
      if not title_elem:
        title_elem = card.find(["h1", "h2", "h3", "h4"])

      raw_title = (
          title_elem.get_text(" ", strip=True)
          if title_elem
          else link_tag.get_text(" ", strip=True)
      )
      title = html.escape(" ".join(raw_title.split()))

      if not title or len(title) < 5:
        continue

      if pn_clean not in title.lower():
        continue

      # Extragere preț cu Regex
      price = "N/A"
      card_text = card.get_text(" ", strip=True)
      price_match = re.search(
          r"(\d+([.,]\d+)?)\s*(lei|ron)", card_text, re.IGNORECASE
      )
      if price_match:
        price = html.escape(price_match.group(0))

      image_url = ""
      img_tag = card.select_one("img")
      if img_tag:
        srcset = img_tag.get("data-srcset") or img_tag.get("srcset") or ""
        srcset_url = ""
        if srcset:
          srcset_url = srcset.split(",")[0].strip().split(" ")[0].strip()
        image_url = (
            img_tag.get("data-src")
            or img_tag.get("data-lazy-src")
            or img_tag.get("data-original")
            or srcset_url
            or img_tag.get("src")
            or ""
        ).strip()
        if image_url.startswith("data:"):
          image_url = ""
        if image_url.startswith("//"):
          image_url = "https:" + image_url
        elif image_url.startswith("/"):
          image_url = f"https://{domain}{image_url}"

      if not any(r["Sursă / Link"] == target_url for r in results):
        results.append({
            "Magazin": store_name,
            "Sursă / Link": target_url,
            "Produs": title[:95] + ("..." if len(title) > 95 else ""),
            "Preț": price,
            "Imagine": image_url,
        })

    return results
  except Exception:
    return []