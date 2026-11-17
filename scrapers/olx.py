import html
import re
import urllib.parse

import httpx
from bs4 import BeautifulSoup


async def scrape(client: httpx.AsyncClient, part_number: str):
    """Caută anunțuri în OLX.ro (HTML static, fără JavaScript)."""
    store_name = "OLX"
    query_encoded = urllib.parse.quote(part_number)
    target_url = f"https://www.olx.ro/oferte/q-{query_encoded}/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = await client.get(
            target_url, headers=headers, timeout=10, follow_redirects=True
        )
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for card in soup.select('[data-testid="l-card"]'):
            title_elem = card.select_one('[data-testid="ad-card-title"]')
            link_elem = card.select_one('a[data-testid="card-title-link"]')
            if not title_elem or not link_elem:
                continue

            # OLX adaugă prețul la finalul titlului în card: „... 320 lei".
            raw_title = title_elem.get_text(" ", strip=True)
            raw_title = re.sub(
                r"\s+\d[\d\s.,]*\s*(?:lei|ron)\s*$", "", raw_title, flags=re.IGNORECASE
            )
            title = html.escape(" ".join(raw_title.split()))
            if len(title) < 5:
                continue

            link = link_elem.get("href", "")
            if link.startswith("//"):
                link = "https:" + link
            elif link.startswith("/"):
                link = "https://www.olx.ro" + link
            if not link.startswith("http"):
                continue

            price_elem = card.select_one('[data-testid="ad-price"]')
            price = (
                html.escape(price_elem.get_text(" ", strip=True))
                if price_elem
                else "N/A"
            )

            image_url = ""
            img = card.select_one("img")
            if img:
                image_url = (
                    img.get("src")
                    or img.get("data-src")
                    or (img.get("srcset") or "").split(",")[0].split(" ")[0]
                    or ""
                ).strip()
                if image_url.startswith("data:"):
                    image_url = ""
                elif image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = "https://www.olx.ro" + image_url

            results.append({
                "Magazin": store_name,
                "Produs": title[:95] + ("..." if len(title) > 95 else ""),
                "Preț": price,
                "Sursă / Link": link,
                "Imagine": image_url,
            })

        return results
    except Exception:
        return []
