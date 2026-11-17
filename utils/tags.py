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

  # 3. Baterii (inclusiv titluri fără cuvântul "baterie", dar cu capacitate în mAh)
  if any(kw in t for kw in ["baterie", "acumulator", "battery"]) or re.search(
      r"\b\d{3,6}\s*mah\b", t
  ):
    return "Baterie"

  # 4. Laptopuri întregi — se verifică ÎNAINTE de Stocare/RAM, altfel
  # specificațiile precum "256GB SSD" ar face un laptop complet să fie
  # clasificat greșit la "Stocare".
  part_markers = [
      "baterie", "battery", "acumulator", "incarcator", "încărcător",
      "charger", "adapter", "alimentator", "tastatura", "tastatură",
      "keyboard", "cooler", "ventilator", "fan ", "mufa", "mufă",
      "balamale", "hinge", "carcasa", "carcasă", "pasta", "surub", "șurub",
  ]
  # Titlurile care încep cu "Laptop" sunt aproape sigur laptopuri complete
  # (chiar dacă menționează ecran/display sau SSD în specificații).
  if t.startswith("laptop") and not any(kw in t for kw in part_markers):
    return "Laptopuri"

  # Laptopuri menționate în interiorul titlului (fără piese/accesorii)
  if "laptop" in t and not any(kw in t for kw in part_markers + [
      "piese", "display", "ecran", "screen",
  ]):
    return "Laptopuri"

  # 5. Display-uri / Ecrane
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

  # 10. Consumabile pentru imprimante (cartuse, toner, cerneala, maintenance box etc.)
  if any(kw in t for kw in [
      "cartus", "cartuș", "cartridge", "toner", "cerneala", "cerneală",
      "inkjet", "ink-jet", "maintenance box", "waste ink", "ink pad",
      "printhead", "print head", "cap de printare", "kit refill", "refill",
      "hartie foto", "hârtie foto", "etichete",
  ]):
    return "Consumabile Imprimante"

  # 11. Consumabile generale (pasta termica, suruburi etc.)
  if any(kw in t for kw in [
      "pasta", "termoconductoare", "surub", "cablu flex",
  ]):
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