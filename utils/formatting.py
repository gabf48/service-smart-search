import re


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