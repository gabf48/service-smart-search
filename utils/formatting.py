import re


def format_money(amount) -> str:
  """Formatare în Lei cu separator de mii și virgulă zecimală.

  ex. 1289.5 -> "1.289,50 Lei"; -120 -> "−120,00 Lei".
  """
  try:
    value = float(amount or 0)
  except (TypeError, ValueError):
    value = 0.0
  sign = "−" if value < 0 else ""
  text = f"{abs(value):,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
  return f"{sign}{text} Lei"


def highlight_search_terms(text: str, query: str) -> str:
  """Evidențiază termenul căutat în text (folosind Markdown bold sau formatare UI)."""
  if not query or not text:
    return text
    
  # Escapăm caracterele speciale din query pentru regex
  escaped_query = re.escape(query.strip())
  if not escaped_query:
    return text

  # Înlocuim case-insensitive termenul găsit cu text îngroșat (sau tag HTML de highlight)
  highlighted = re.sub(
      f"({escaped_query})",
      r"**\1**",
      text,
      flags=re.IGNORECASE
  )
  return highlighted