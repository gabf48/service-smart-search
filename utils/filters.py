import re


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
  if not title:
    return False
    
  t = title.lower()

  irrelevant_keywords = [
      "iphone",
      "smartphone",
      "telefon mobil",
      "telefon",
      "tab",
      "camera spate",     # Scris cu litere mici și fără diacritice
      "cameră spate",     # Cu diacritice, pentru siguranță
      "camera frontala",
      "cameră frontală",
      "camera selfie",
      "cameră selfie",
      "camera foto",
      "cameră foto",
      "husa",
      "husa iphone",
      "tableta",
      "ipad",
      "husa telefon",
      "folie protectie",
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