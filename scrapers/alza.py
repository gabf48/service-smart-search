import html
import re
import urllib.parse

from playwright.async_api import async_playwright


async def scrape(client, part_number: str):
  """Caută în Alza.ro.

 Magazinul e dezactivat implicit în websites.json: Cloudflare cere verificare
 umană, inclusiv pentru Chromium headless. Scraperul rămâne aici ca să poată fi
 activat pe o rețea/gazdă unde provocarea nu apare.
 """
  store_name = "Alza"
  query_encoded = urllib.parse.quote(part_number)
  target_url = f"https://www.alza.ro/search.htm?exps={query_encoded}"

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
      await page.goto(target_url, timeout=15000, wait_until="domcontentloaded")
      await page.wait_for_timeout(1500)

      if "confirm you are human" in (await page.inner_text("body")).lower():
        print("⚠️ [Alza] Cloudflare cere verificare umană — rezultate omitise.")
        return []

      cards = await page.locator(
          ".shopListBox, .product, .productBox, [class*='shopListBox']"
      ).all()
      for card in cards:
        link_tag = card.locator("h3 a, a.product, a[href*='.htm']").first
        if await link_tag.count() == 0:
          continue

        link = await link_tag.get_attribute("href") or ""
        if link.startswith("//"):
          link = "https:" + link
        elif link.startswith("/"):
          link = "https://www.alza.ro" + link
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
        price_match = re.search(r"([\d\s.,]+)\s*(lei|ron|kč)\b", card_text, re.I)
        price = html.escape(price_match.group(0)) if price_match else "N/A"

        image_url = ""
        img = card.locator("img").first
        if await img.count():
          image_url = (
              await img.get_attribute("data-src")
              or await img.get_attribute("src")
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
      print(f"❌ [Alza] Eroare: {e}")
    finally:
      await browser.close()

  return results
