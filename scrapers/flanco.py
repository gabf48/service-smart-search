import html
import re
import urllib.parse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def scrape(client, part_number: str):
    """Caută în Flanco.ro. Site-ul blochează httpx (403), deci folosim Playwright."""
    store_name = "Flanco"
    query_encoded = urllib.parse.quote(part_number)
    target_url = f"https://www.flanco.ro/catalogsearch/result/?q={query_encoded}"

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="ro-RO",
            )
            await page.goto(target_url, timeout=25000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            soup = BeautifulSoup(await page.content(), "html.parser")
            for card in soup.select(".product-item"):
                title_elem = card.select_one("h2")
                if not title_elem:
                    continue

                title = html.escape(" ".join(title_elem.get_text(" ", strip=True).split()))
                if len(title) < 5:
                    continue

                link = ""
                for anchor in card.select("a[href]"):
                    href = anchor.get("href", "")
                    if href and href != "#" and not href.startswith("javascript"):
                        link = href
                        break
                if link.startswith("//"):
                    link = "https:" + link
                elif link.startswith("/"):
                    link = "https://www.flanco.ro" + link
                if not link.startswith("http"):
                    continue

                price_elem = card.select_one(".special-price") or card.select_one(".price")
                price = (
                    html.escape(price_elem.get_text(" ", strip=True))
                    if price_elem
                    else "N/A"
                )

                image_url = ""
                img = card.select_one("img")
                if img:
                    image_url = (
                        img.get("data-src")
                        or (img.get("srcset") or "").split(",")[0].split(" ")[0]
                        or img.get("src")
                        or ""
                    ).strip()
                    if image_url.startswith("data:"):
                        image_url = ""
                    elif image_url.startswith("//"):
                        image_url = "https:" + image_url
                    elif image_url.startswith("/"):
                        image_url = "https://www.flanco.ro" + image_url

                results.append({
                    "Magazin": store_name,
                    "Produs": title[:95] + ("..." if len(title) > 95 else ""),
                    "Preț": price,
                    "Sursă / Link": link,
                    "Imagine": image_url,
                })
        except Exception as e:
            print(f"❌ [Flanco] Eroare: {e}")
        finally:
            await browser.close()

    return results
