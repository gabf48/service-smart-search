from bs4 import BeautifulSoup
import httpx


async def scrape(client: httpx.AsyncClient, query: str):
  results = []
  url = f"https://www.powerlaptop.ro/cauta/{query}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  try:
    response = await client.get(
        url, headers=headers, timeout=10.0, follow_redirects=True
    )
    if response.status_code != 200:
      return results

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("li.pl-product-card")

    for item in items:
      link_el = item.select_one("a")
      name_el = item.select_one(
          "[class*='name'], [class*='title'], h4, h3, h2"
      )

      if not name_el and link_el:
        name_el = link_el

      if name_el and link_el:
        title = name_el.get_text(strip=True)
        link = link_el.get("href", "")
        if link and not link.startswith("http"):
          link = "https://www.powerlaptop.ro" + link

        price_el = item.select_one(".price-new, .special-price, .current-price")
        if not price_el:
          price_el = item.select_one(
              "[class*='price'], .price, span.price, div.price"
          )

        price = price_el.get_text(" ", strip=True) if price_el else "N/A"

        if "Lei" in price and price.count("Lei") > 1:
          parts = [p.strip() for p in price.split("Lei") if p.strip()]
          if parts:
            price = parts[-1] + " Lei"
        elif "RON" in price and price.count("RON") > 1:
          parts = [p.strip() for p in price.split("RON") if p.strip()]
          if parts:
            price = parts[-1] + " RON"

        if len(title) > 3:
          results.append(
              {
                  "Magazin": "Powerlaptop",
                  "Produs": title,
                  "Preț": price,
                  "Sursă / Link": link,
              }
          )

  except Exception as e:
    print(f"Eroare completă la powerlaptop: {e}")

  return results