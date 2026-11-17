import html
import re
import urllib.parse

from playwright.async_api import async_playwright


async def scrape(client, part_number: str):
  """Caută în PC Garage. Site-ul e protejat de Cloudflare, deci folosim Playwright."""
  store_name = "PC Garage"
  query_encoded = urllib.parse.quote(part_number)
  target_url = f"https://www.pcgarage.ro/cauta/?p=1&search={query_encoded}"

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

      cards = await page.locator(".product_box").all()
      for card in cards:
        link_tag = card.locator(
            ".product_box_image a, h2 a, .product_box_name a, a[title]"
        ).first
        if await link_tag.count() == 0:
          continue

        link = await link_tag.get_attribute("href") or ""
        if link.startswith("//"):
          link = "https:" + link
        elif link.startswith("/"):
          link = "https://www.pcgarage.ro" + link
        if not link.startswith("http"):
          continue

        raw_title = (
            await link_tag.get_attribute("title")
            or await link_tag.inner_text()
            or ""
        )
        title = html.escape(" ".join(raw_title.split()))
        if len(title) < 5:
          continue

        card_text = (await card.inner_text()).replace("\n", " ")
        price_match = re.search(
            r"(\d[\d\s.,]*)\s*(lei|ron)\b", card_text, re.IGNORECASE
        )
        price = html.escape(price_match.group(0)) if price_match else "N/A"

        image_url = ""
        img = card.locator("img").first
        if await img.count():
          image_url = (
              await img.get_attribute("src")
              or (await img.get_attribute("srcset") or "").split(",")[0].split(" ")[0]
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
      print(f"❌ [PC Garage] Eroare: {e}")
    finally:
      await browser.close()

  return results
