import html
import re
import urllib.parse

from bs4 import BeautifulSoup


async def scrape(client, part_number: str):
  """Caută în MediaTek.ro (WordPress/WooCommerce).

 Dezactivat implicit în websites.json: domeniul nu răspunde din mediul curent.
 """
  store_name = "MediaTek"
  query_encoded = urllib.parse.quote(part_number)
  target_url = f"https://www.mediatek.ro/?s={query_encoded}"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  results = []
  try:
    response = await client.get(
        target_url, headers=headers, timeout=10, follow_redirects=True
    )
    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select(
        ".product, .product-item, .woocommerce-loop-product__title, "
        "article, .post, [class*='product']"
    )

    for card in cards:
      title_el = card.select_one("h2 a, h3 a, .woocommerce-loop-product__title, a")
      if not title_el or not title_el.get("href"):
        continue

      link = title_el["href"]
      if link.startswith("//"):
        link = "https:" + link
      elif link.startswith("/"):
        link = "https://www.mediatek.ro" + link
      if not link.startswith("http"):
        continue

      title = html.escape(" ".join(title_el.get_text(" ", strip=True).split()))
      if len(title) < 5:
        continue

      card_text = card.get_text(" ", strip=True)
      price_match = re.search(r"([\d\s.,]+)\s*(lei|ron)\b", card_text, re.I)
      price = html.escape(price_match.group(0)) if price_match else "N/A"

      image_url = ""
      img = card.select_one("img")
      if img:
        image_url = (
            img.get("data-src")
            or (img.get("srcset") or "").split(",")[0].split(" ")[0]
            or img.get("src")
            or ""
        )
        if image_url.startswith("//"):
          image_url = "https:" + image_url

      if not any(r["Sursă / Link"] == link for r in results):
        results.append({
            "Magazin": store_name,
            "Produs": title[:95] + ("..." if len(title) > 95 else ""),
            "Preț": price,
            "Sursă / Link": link,
            "Imagine": image_url,
        })
  except Exception as e:
    print(f"❌ [MediaTek] Eroare: {e}")

  return results
