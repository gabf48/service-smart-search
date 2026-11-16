import re


def classify_category(title: str) -> str:
  if not title:
    return "Piese / Altele"

  t = title.lower()

  # 1. Coolere & Sisteme de Răcire
  if any(kw in t for kw in ["cooler", "ventilator", "heatsink", "radiator"]):
    return "Coolere"

  # 2. Tastaturi
  if any(kw in t for kw in ["tastatura", "tastatură", "keyboard"]):
    return "Tastatură"

  # 3. Baterii
  if any(kw in t for kw in ["baterie", "acumulator", "battery"]):
    return "Baterie"

  # 4. Display-uri / Ecrane
  if any(kw in t for kw in ["display", "ecran", "matrice", "lcd", "led slim"]):
    return "Display"

  # 5. Încărcătoare / Alimentatoare
  if any(kw in t for kw in ["incarcator", "încărcător", "alimentator", "adaptor priza", "adapter"]):
    return "Încărcătoare"

  # 6. Stocare (SSD / HDD)
  if any(kw in t for kw in ["ssd", "hdd", "hard disk", "nvme", "m.2"]):
    return "Stocare"

  # 7. Memorie RAM ("ram" doar ca cuvânt întreg, ca să nu prindă "program", "frame" etc.)
  if re.search(r"\bram\b", t) or "memorie" in t:
    return "Memorie RAM"

  # 8. Elemente Carcase / Rame
  if any(kw in t for kw in ["balamale", "rama display", "ramă", "carcasa", "carcasă"]):
    return "Ramă Display"

  # 9. Mufe & Conectori
  if any(kw in t for kw in ["mufa", "mufă", "conector", "jack alimentare"]):
    return "Mufe & Conectori"

  # 10. Consumabile
  if any(kw in t for kw in ["pasta", "termoconductoare", "surub", "cablu flex"]):
    return "Consumabile"

  # 11. Laptopuri întregi
  if "laptop" in t and not any(p in t for p in [
      "piese", "baterie", "tastatura", "display", "cooler", "incarcator",
      "mufa", "ssd", "ram", "alimentator", "ventilator", "ecran"
  ]):
    return "Laptopuri"

  return "Piese / Altele"


# Alias arhitectural pentru compatibilitate totală în tot proiectul
get_product_tag = classify_category