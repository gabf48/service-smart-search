import re


def parse_price_for_sorting(price_str):
  if not price_str or price_str == "N/A":
    return float("inf")
  # OpenCart/eMAG pot scrie "1.289 00 Lei" (miimi + zecimi separate prin spațiu).
  grouped = re.search(r"(\d{1,3}(?:[.\s]\d{3})+)[,\s]+(\d{2})(?!\d)", price_str)
  if grouped:
    try:
      return float(re.sub(r"\D", "", grouped.group(1)) + "." + grouped.group(2))
    except ValueError:
      return float("inf")

  clean_str = re.sub(r"[^\d.,]", "", price_str)
  # Handle both "1.299,99" and "1,299.99" style separators.
  if "," in clean_str and "." in clean_str:
    if clean_str.rfind(",") > clean_str.rfind("."):
      clean_str = clean_str.replace(".", "").replace(",", ".")
    else:
      clean_str = clean_str.replace(",", "")
  else:
    clean_str = clean_str.replace(",", ".")
  try:
    return float(clean_str)
  except ValueError:
    return float("inf")


def normalize_price_display(price_str):
  if not price_str or price_str == "N/A":
    return "N/A"

  match = re.search(r"([\d][\d\s.,]*)(?:\s*)(lei|ron)", price_str, re.IGNORECASE)
  if not match:
    return re.sub(r"\s+", " ", price_str).strip()

  raw_num = match.group(1)
  compact = re.sub(r"\s+", "", raw_num)

  # "1.289 00 Lei" / "1.289,99 Lei" -> 1289.00 / 1289.99
  grouped = re.search(
      r"(\d{1,3}(?:[.\s]\d{3})+)[,\s]+(\d{2})\s*(?:lei|ron)",
      price_str,
      re.IGNORECASE,
  )
  space_decimal = re.search(r"(\d+)\s+(\d{2})\s*(?:lei|ron)", price_str, re.IGNORECASE)
  if grouped:
    thousands = re.sub(r"\D", "", grouped.group(1))
    amount = float(f"{thousands}.{grouped.group(2)}")
  elif space_decimal and "." not in compact and "," not in compact:
    amount = float(f"{space_decimal.group(1)}.{space_decimal.group(2)}")
  else:
    amount = parse_price_for_sorting(raw_num)

  if amount == float("inf"):
    return re.sub(r"\s+", " ", price_str).strip()

  if amount.is_integer():
    formatted = f"{int(amount)}"
  else:
    formatted = f"{amount:.2f}".rstrip("0").rstrip(".")

  return f"{formatted} Lei"


def is_irrelevant_product(title, query=None):
  if not title:
    return False
    
  t = title.lower()

  irrelevant_keywords = [
      # Anvelope / pneuri (nu sunt piese de service IT)
      "anvelopa",
      "anvelopă",
      "anvelope",
      "pneu",
      "cauciuc auto",
      "cauciuc tractor",
      "iphone",
      "smartphone",
      "telefon mobil",
      "telefon",
      # Nu sunt piese de laptop (dar rămân permise dacă exact asta se caută).
      "baterie externa",
      "baterie externă",
      "powerbank",
      "second hand",
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
      # Șuruburi/consumabile de construcții sau tâmplărie (nu piese de laptop)
      "dulgherie",
      "autoforant",
      "diblu",
      "tija filetata",
      "tijă filetată",
      "ancora metalica",
      "ancoră metalică",
      # Veselă / articole de bucătărie
      "oala",
      "oale",
      "tigaie",
      "tigai",
      "termorezistent",
      "capac sticla",
      "capac sticlă",
      "capac de sticla",
      "capac de sticlă",
      "orificiu abur",
      "capac inox",
      "ceaun",
      "tefal",
      "inchidere ermetica",
      "închidere ermetică",
      "capac flexibil",
      "capace flexibile",
      "capac silicon",
      "capace silicon",
      "capac universal",
      "capace universale",
      "capac elastic",
      "capace elastice",
      "capac pliabil",
      "capace pliabile",
      "microunde",
      "capac termoizolant",
      "capace termoizolante",
      "aluminiu alimentar",
      "depozitare alimente",
      "tip capac",
      "vilde",
      "zilan",
      "boluri",
      "farfurii",
      "ventil de aburi",
      "ventil abur",
      "rama din otel inoxidabil",
      "ramă din oțel inoxidabil",
      "organizator",
      "suport organizator",
      "farfurie",
      "pahar",
      "cana",
      "bol ",
  ]

  for kw in irrelevant_keywords:
    if kw in t:
      if query and kw in query.lower():
        return False
      return True

  return False