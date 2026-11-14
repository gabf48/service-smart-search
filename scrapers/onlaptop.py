from bs4 import BeautifulSoup
import httpx
import re


async def scrape(client: httpx.AsyncClient, query: str):
  results = []
  url = f"https://www.onlaptop.ro/cautare?q={query}"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  try:
    response = await client.get(
        url, headers=headers, follow_redirects=True, timeout=12.0
    )
    if response.status_code != 200:
      return results

    soup = BeautifulSoup(response.text, "html.parser")

    # Selectăm toate elementele/cardurile de produs posibile pe structura lor
    products = soup.select(
        ".product-item, .product-layout, .item, div[class*='product']"
    )

    for p in products:
      title_elem = p.select_one(
          "h4 a, h3 a, h2 a, .product-item-link, a.product-item-link,"
          " .product-name a, a[title]"
      )
      if not title_elem:
        for a in p.find_all("app-link, a"):
          txt = a.get_text(strip=True)
          if txt and len(txt) > 5 and "lei" not in txt.lower():
            title_elem = a
            break

      if not title_elem:
        continue

      title = title_elem.get_text(strip=True)
      link = title_elem.get("href", "")

      # Filtrare anti-zgomot (evităm butoane, telefoane, texte generice)
      if not title or len(title) < 4:
        continue
      if any(
          j in title.lower()
          for j in [
              "shop now",
              "add to wishlist",
              "cos",
              "detalii",
              "wishlist",
              "021",
          ]
      ):
        continue

      if link and not link.startswith("http"):
        link = "https://www.onlaptop.ro" + link

      # Extragere preț
      price_elem = p.select_one(
          ".price, .price-new, span[data-price-amount], .price-box"
      )
      price = "N/A"
      if price_elem:
        raw_price = price_elem.get_text(strip=True)
        match = re.search(r"([\d\.,]+\s*lei)", raw_price, re.IGNORECASE)
        if match:
          price = match.group(1)
        else:
          price = raw_price

      if not any(r["Sursă / Link"] == link for r in results):
        results.append({
            "Magazin": "OnLaptop",
            "Produs": title,
            "Preț": price,
            "Sursă / Link": link,
        })

  except Exception as e:
    print(f"❌ [OnLaptop] Eroare: {e}")

  return results