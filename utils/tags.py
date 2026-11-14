def get_product_tag(title):
  t = title.lower()
  words = t.split()

  if any(x in t for x in ["incarcator", "încărcător", "alimentator", "adaptor", "adapter", "power supply"]):
    return "⚡ Încărcătoare"
  elif any(x in t for x in ["baterie", "acumulator", "battery"]):
    return "🔋 Baterie"
  elif any(x in t for x in ["cartus", "cartuş", "toner", "ink", "duza"]):
    return "🖨️ Consumabile"
  elif any(x in t for x in ["tastatura", "tastatură", "keyboard", "palmrest"]):
    return "⌨️ Tastatură"
  elif any(x in t for x in ["display", "matrice", "ecran laptop", "lcd laptop", "panel"]):
    return "🖥️ Display"
  elif any(x in t for x in ["laptop", "notebook", "macbook", "ultrabook", "chromebook"]):
    return "💻 Laptopuri"
  elif any(x in t for x in ["cooler", "ventilator", "radiator", "heatsink"]):
    return "❄️ Coolere"
  elif any(x in t for x in ["mufa", "mufă", "jack", "conector", "dc-in", "dc in"]):
    return "🔌 Mufe & Conectori"
  elif any(x in t for x in ["rama display", "ramă display", "bezel", "front cover", "lcd cover", "carcasa display", "carcasă display"]):
    return "🖼️ Ramă Display"
  elif any(w in words for w in ["ram", "ddr", "ddr3", "ddr4", "ddr5", "sodimm"]) or "memorie" in t:
    return "🧠 Memorie RAM"
  elif any(x in t for x in ["ssd", "hdd", "hard", "stocare", "nvme", "m.2"]):
    return "💾 Stocare"
  else:
    return "🔧 Piese / Altele"