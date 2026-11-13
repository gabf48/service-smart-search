import asyncio
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import httpx
from rich.console import Console
from rich.table import Table

console = Console()


async def fetch_page(client: httpx.AsyncClient, url: str):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    response = await client.get(
        url, headers=headers, timeout=6, follow_redirects=True
    )
    if response.status_code == 200:
      return url, response.text
  except Exception:
    pass
  return url, None


async def search_part_agent(part_number: str):
  console.print(
      f"\n[bold cyan]🔍 Agentul scanează web-ul pentru:[/bold cyan]"
      f" [yellow]{part_number}[/yellow]...\n"
  )

  query = f"{part_number} laptop"
  search_results = []

  # Căutare rapidă prin DuckDuckGo
  try:
    with DDGS() as ddgs:
      for r in ddgs.text(query, max_results=12):
        url = r.get("href", "")
        if url:
          search_results.append(url)
  except Exception as e:
    console.print(f"[bold red]Eroare la căutare: {e}[/bold red]")
    return

  if not search_results:
    console.print(
        "[bold red]Nu s-au găsit rezultate pe motoarele de căutare.[/bold red]"
    )
    return

  console.print(
      f"[dim]Am găsit {len(search_results)} pagini relevante. Se descarcă"
      " simultan...[/dim]\n"
  )

  # Preluare asincronă a paginilor
  async with httpx.AsyncClient() as client:
    tasks = [fetch_page(client, url) for url in search_results]
    pages = await asyncio.gather(*tasks)

  results_table = []
  for url, html in pages:
    if not html:
      continue
    soup = BeautifulSoup(html, "html.parser")

    # Extragere titlu
    title_tag = soup.find("h1")
    title = (
        title_tag.get_text(strip=True)
        if title_tag
        else soup.title.string.strip()
        if soup.title
        else "Produs"
    )

    # Căutare preț după elemente comune de e-commerce
    price = "N/A"
    price_tag = soup.select_one(
        "[class*='price'], [id*='price'], .current-price, span[content*='RON']"
    )
    if price_tag:
      price = price_tag.get_text(strip=True)

    results_table.append(
        {"url": url, "title": title[:50] + "...", "price": price}
    )

  if not results_table:
    console.print(
        "[yellow]Nu s-au putut extrage prețuri valide din paginile"
        " gasite.[/yellow]"
    )
    return

  # Afișare tabelară în terminal
  table = Table(
      title=f"Rezultate Piese pentru: {part_number}",
      show_header=True,
      header_style="bold magenta",
  )
  table.add_column("Sursă / Link", style="blue", overflow="fold", width=45)
  table.add_column("Produs Identificat", style="green", width=40)
  table.add_column("Preț Detectat", style="bold yellow", justify="right")

  for item in results_table:
    table.add_row(item["url"], item["title"], item["price"])

  console.print(table)


if __name__ == "__main__":
  pn = input("Introdu Part Number-ul sau modelul piesei (ex: B21N1818): ")
  if pn.strip():
    asyncio.run(search_part_agent(pn.strip()))