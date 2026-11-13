import re


def get_product_tag(title):
  t = title.lower()
  words = t.split()

  if any(x in t for x in ["cartus", "cartuş", "toner", "ink", "duza"]):
    return "🖨️ Consumabile"
  elif any(
      x in t
      for x in [
          "incarcator",
          "încărcător",
          "alimentator",
          "adaptor",
          "adapter",
          "power supply",
      ]
  ):
    return "⚡ Încărcătoare"
  elif any(
      x in t
      for x in [
          "cooler",
          "ventilator",
          "radiator",
          "heatsink",
          "cooler laptop",
      ]
  ):
    return "❄️ Coolere"
  elif any(
      x in t
      for x in [
          "mufa",
          "mufă",
          "jack",
          "conector",
          "dc-in",
          "dc in",
      ]
  ):
    return "🔌 Mufe & Conectori"
  elif any(x in t for x in ["baterie", "acumulator", "mah", "wh", "battery"]):
    return "🔋 Baterie"
  elif any(
      x in t
      for x in [
          "rama display",
          "ramă display",
          "bezel",
          "front cover",
          "lcd cover",
          "carcasa display",
          "carcasă display",
      ]
  ):
    return "🖼️ Ramă Display"
  elif any(x in t for x in ["tastatura", "tastatură", "keyboard", "palmrest"]):
    return "⌨️ Tastatură"
  elif any(
      w in words for w in ["ram", "ddr", "ddr3", "ddr4", "ddr5", "sodimm"]
  ) or "memorie" in t:
    return "🧠 Memorie RAM"
  elif any(x in t for x in ["ssd", "hdd", "hard", "stocare", "nvme", "m.2"]):
    return "💾 Stocare"
  elif any(
      x in t
      for x in ["display", "matrice", "ecran laptop", "lcd laptop", "panel"]
  ):
    return "🖥️ Display"
  elif any(x in t for x in ["laptop", "notebook", "macbook", "ultrabook"]):
    return "💻 Laptopuri"
  else:
    return "🔧 Piese / Altele"


def parse_price_for_sorting(price_str):
  if not price_str or price_str == "N/A":
    return float("inf")
  clean_str = re.sub(r"[^\d.,]", "", price_str)
  clean_str = clean_str.replace(",", ".")
  try:
    return float(clean_str)
  except ValueError:
    return float("inf")


def is_irrelevant_product(title, query=None):
  t = title.lower()

  irrelevant_keywords = [
      "iphone",
      "smartphone",
      "telefon mobil",
      "husa iphone",
      "husa telefon",
      "folie protectie iphone",
      "folie sticla iphone",
      "cablu lightning",
      "toaster",
      "prajitor",
      "prăjitor",
      "prajitor de paine",
      "prăjitor de pâine",
      "espressor",
      "cafetiera",
      "cafetieră",
      "cuptor",
      "aragaz",
      "pictura",
      "pictură",
      "tablou",
      "set pictura",
      "panza bumbac",
      "pânză bumbac",
      "uscator de par",
      "uscător de păr",
      "sampon",
      "șampon",
      "parfum",
      "cosmetice",
      "sezlong",
      "șezlong",
      "pisici",
      "caini",
      "câini",
      "hrana",
      "hrană",
      "jucarie",
      "jucărie",
      "haine",
      "pantofi",
      "aer conditionat",
      "aer condiționat",
      "masina de spalat",
      "mașină de spălat",
      "uscator de rufe",
      "uscător de rufe",
      "frigider",
      "congelator",
      "scaun",
  ]

  for kw in irrelevant_keywords:
    if kw in t:
      if query and kw in query.lower():
        return False
      return True

  return False


def highlight_search_terms(text, query):
  if not query or not query.strip():
    return text

  terms = [re.escape(word) for word in query.strip().split() if word]
  if not terms:
    return text

  pattern = re.compile(r"(" + "|".join(terms) + r")", re.IGNORECASE)

  highlighted = pattern.sub(
      r'<span style="background-color: rgba(210, 153, 34, 0.35); color:'
      r' #f0f6fc; padding: 1px 3px; border-radius: 3px; font-weight:'
      r' 600;">\1</span>',
      text,
  )
  return highlighted