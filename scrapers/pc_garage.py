import html
import re
import urllib.parse
from bs4 import BeautifulSoup
import httpx


async def scrape(client: httpx.AsyncClient, part_number: str):
  store_name = "PC Garage"
  domain = "pcgarage.ro"

  query_encoded = urllib.parse.quote(part_number)
  target_url = f"https://www.{domain}/cautare/{query_encoded}"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
      "Referer": f"https://www.{domain}/",
  }

  try:
    response = await client.get(
        target_url, headers=headers, timeout=8, follow_redirects=True
    )
    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    # Țintim exact clasa .product_box identificată în inspector
    products = soup.select(".product_box, div[class*='product_box']")

    for prod in products:
      # Căutăm link-ul și titlul în structura exactă din HTML
      link_tag = prod.select_one("h2.my-0 a, .product_box_name a")
      if not link_tag:
        link_tag = prod.find("a", href=True)

      if not link_tag or not link_tag.has_attr("href"):
        continue

      link = link_tag["href"]
      if not link.startswith("http"):
        link = f"https://{domain}{link if link.startswith('/') else '/' + link}"

      # Luăm titlul preferențial din atributul 'title' sau din text
      raw_title = ""
      if link_tag.has_attr("title"):
        raw_title = link_tag["title"]
      else:
        raw_title = link_tag.get_text(" ", strip=True)

      title = html.escape(" ".join(raw_title.split()))
      if not title or len(title) < 3:
        continue

      # Extragere preț cu Regex din textul complet al cardului de produs
      price = "N/A"
      prod_text = prod.get_text(" ", strip=True)
      price_match = re.search(
          r"(\d+([.,]\d+)?)\s*(lei|ron)", prod_text, re.IGNORECASE
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