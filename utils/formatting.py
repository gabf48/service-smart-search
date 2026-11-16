import re

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