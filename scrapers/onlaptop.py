import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def scrape(client, query: str):
  results = []

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    )

    try:
      await page.goto("https://www.onlaptop.ro/", timeout=20000)

      search_input = await page.wait_for_selector(
          "input[name='s'], input.search-field, input[type='search']",
          timeout=10000,
      )
      if search_input:
        await search_input.fill(query)
        await search_input.press("Enter")
      else:
        await page.goto(
            f"https://www.onlaptop.ro/?s={query}&post_type=product",
            timeout=20000,
        )

      await page.wait_for_selector(
          "div.dfd-card, div.dfd-result-product, ul.products li.product,"
          " .product-small, .product",
          timeout=12000,
      )

      await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
      await page.wait_for_timeout(2000)

      products = await page.query_selector_all(
          "div.dfd-card, div.dfd-result-product, ul.products li.product,"
          " .product-small, .product"
      )

      for p in products:
        title_elem = await p.query_selector(
            ".dfd-card-title, h2.woocommerce-loop-product__title a,"
            " .box-text-products a, .name a, h3 a"
        )
        if not title_elem:
          continue

        title = await title_elem.inner_text()
        title = title.strip()
        if not title or len(title) < 5:
          continue

        link_elem = await p.query_selector("a[dfd-value-link], a[href]")
        link = ""
        if link_elem:
          link = (
              await link_elem.get_attribute("dfd-value-link")
              or await link_elem.get_attribute("href")
              or ""
          )

        lower_title = title.lower()
        if re.match(r"^\d+\s*products?$", lower_title):
          continue
        if any(
            kw in lower_title
            for kw in [
                "laptopuri refurbished",
                "laptopuri & componente",
                "componente & piese laptop",
                "shop now",
                "add to wishlist",
                "cos",
                "detalii",
                "wishlist",
                "021",
                "produse",
            ]
        ):
          continue

        if link and not link.startswith("http"):
          link = "https://www.onlaptop.ro" + link

        # Extragere preț corect (evitând suma economisită și prețul tăiat)
        price = "N/A"
        price_elem = await p.query_selector(
            ".dfd-card-price, .onl-sale-box-v2_new, .price ins, span.price"
        )
        
        if price_elem:
          raw_price_text = await price_elem.inner_text()
          cleaned_price_text = re.sub(r"<(del|s).*?>.*?</\1>", "", raw_price_text, flags=re.DOTALL | re.IGNORECASE)
          
          matches = re.findall(
              r"([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s*(?:lei|RON))",
              cleaned_price_text,
              re.IGNORECASE,
          )
          
          if matches:
            valid_prices = []
            for m in matches:
              num_str = re.sub(r"[^\d.,]", "", m)
              if "," in num_str and "." in num_str:
                if num_str.find(".") < num_str.find(","):
                  num_str = num_str.replace(".", "").replace(",", ".")
                else:
                  num_str = num_str.replace(",", "")
              else:
                num_str = num_str.replace(",", ".")
              
              try:
                val = float(num_str)
                if val > 5.0:
                  valid_prices.append((val, m))
              except ValueError:
                continue

            if valid_prices:
              valid_prices.sort(key=lambda x: x[0])
              price = valid_prices[0][1]

        if price == "N/A":
          card_html = await p.inner_html()
          cleaned_html = re.sub(r"<(del|s).*?>.*?</\1>", "", card_html, flags=re.DOTALL | re.IGNORECASE)
          temp_soup = BeautifulSoup(cleaned_html, "html.parser")
          for element in temp_soup.find_all(text=re.compile("Economisești", re.IGNORECASE)):
            element.extract()
          card_text = temp_soup.get_text()

          matches = re.findall(
              r"([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s*(?:lei|RON))",
              card_text,
              re.IGNORECASE,
          )
          if matches:
            valid_prices = []
            for m in matches:
              num_str = re.sub(r"[^\d.,]", "", m)
              num_str = num_str.replace(",", ".")
              try:
                val = float(num_str)
                if val > 50.0:
                  valid_prices.append((val, m))
              except ValueError:
                continue
            if valid_prices:
              valid_prices.sort(key=lambda x: x[0])
              price = valid_prices[0][1]

        if price == "N/A":
          continue

        image_url = ""
        img_elem = await p.query_selector("img")
        if img_elem:
          srcset = (
              await img_elem.get_attribute("data-srcset")
              or await img_elem.get_attribute("srcset")
              or ""
          )
          srcset_url = ""
          if srcset:
            srcset_url = srcset.split(",")[0].strip().split(" ")[0].strip()
          image_url = (
              await img_elem.get_attribute("data-src")
              or await img_elem.get_attribute("data-lazy-src")
              or await img_elem.get_attribute("data-original")
              or srcset_url
              or await img_elem.get_attribute("src")
              or ""
          )
          image_url = (image_url or "").strip()
          if image_url.startswith("data:"):
            image_url = ""
          if image_url.startswith("//"):
            image_url = "https:" + image_url
          elif image_url.startswith("/"):
            image_url = "https://www.onlaptop.ro" + image_url

        if link and not any(r["Sursă / Link"] == link for r in results):
          results.append({
              "Magazin": "OnLaptop",
              "Produs": title,
              "Preț": price,
              "Sursă / Link": link,
              "Imagine": image_url,
          })

    except Exception as e:
      print(f"❌ [OnLaptop Playwright] Eroare: {e}")
    finally:
      await browser.close()

  return results