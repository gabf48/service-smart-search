import html
import urllib.parse

from bs4 import BeautifulSoup


async def scrape(client, part_number: str):
  """Caută în Interlink.ro (OpenCart: /index.php?route=product/search)."""
  store_name = "Interlink"
  query_encoded = urllib.parse.quote(part_number)
  target_url = (
      "https://www.interlink.ro/index.php?route=product/search"
      f"&search={query_encoded}"
  )

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
      "Referer": "https://www.interlink.ro/",
  }

  results = []
  try:
    response = await client.get(
        target_url, headers=headers, timeout=12, follow_redirects=True
    )
    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select(".product-layout, .product-thumb")
    if not cards:
      cards = soup.select("[class*='product-layout']")

    for card in cards:
      name_el = card.select_one(".name a, h4 a, h3 a, h2 a")
      link_el = name_el or card.find("a", href=True)
      if not link_el or not link_el.get("href"):
        continue

      link = link_el["href"]
      if link.startswith("//"):
        link = "https:" + link
      elif link.startswith("/"):
        link = "https://www.interlink.ro" + link
      if not link.startswith("http"):
        continue

      raw_title = (
          name_el.get("title")
          if name_el and name_el.get("title")
          else link_el.get_text(" ", strip=True)
      )
      title = html.escape(" ".join(raw_title.split()))
      if len(title) < 5:
        continue

      # .price e elementul real; [class*='price'] prinde și wrapper-e care
      # conțin „0 opinii”, deci îl folosim doar ca fallback.
      price_el = card.select_one(".price, .price-new, .special-price")
      if not price_el:
        price_el = card.select_one("[class*='price']")
      price = html.escape(price_el.get_text(" ", strip=True)) if price_el else "N/A"

      image_url = ""
      img = card.select_one("img")
      if img:
        image_url = (
            img.get("data-src")
            or img.get("data-lazy-src")
            or (img.get("srcset") or "").split(",")[0].split(" ")[0]
            or img.get("src")
            or ""
        )
        if image_url.startswith("//"):
          image_url = "https:" + image_url
        elif image_url.startswith("/"):
          image_url = "https://www.interlink.ro" + image_url

      if not any(r["Sursă / Link"] == link for r in results):
        results.append({
            "Magazin": store_name,
            "Produs": title[:95] + ("..." if len(title) > 95 else ""),
            "Preț": price,
            "Sursă / Link": link,
            "Imagine": image_url,
        })
  except Exception as e:
    print(f"❌ [Interlink] Eroare: {e}")

  return results
