from utils.tags import get_product_tag
from utils.filters import parse_price_for_sorting

def filter_and_sort_data(
    data,
    store_checkboxes,
    tag_checkboxes,
    sort_option,
    min_price,
    max_price,
):
  filtered_data = []
  hidden_by_store = 0
  hidden_by_tag = 0

  for item in data:
    if not store_checkboxes.get(item["Magazin"], True):
      hidden_by_store += 1
      continue

    tag_text = get_product_tag(item["Produs"])
    if not tag_checkboxes.get(tag_text, True):
      hidden_by_tag += 1
      continue

    p_val = parse_price_for_sorting(item["Preț"])
    if p_val == float("inf"):
      filtered_data.append(item)
      continue

    if min_price > 0 and p_val < min_price:
      continue
    if max_price > 0 and p_val > max_price:
      continue
    filtered_data.append(item)

  if sort_option == "Preț crescător 📈":
    filtered_data = sorted(
        filtered_data, key=lambda x: parse_price_for_sorting(x["Preț"])
    )
  elif sort_option == "Preț descrescător 📉":
    filtered_data = sorted(
        filtered_data,
        key=lambda x: parse_price_for_sorting(x["Preț"]),
        reverse=True,
    )

  return filtered_data, hidden_by_store, hidden_by_tag