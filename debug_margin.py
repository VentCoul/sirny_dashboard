from poster_api import PosterAPI
import json

api = PosterAPI()

# 1. Test menu.getProducts (to get price and current cost)
products = api._make_request('menu.getProducts')
print(f"Products count: {len(products) if products else 0}")
if products:
    print("Sample product:")
    # Extract only relevant fields for margin
    sample = {
        "name": products[0].get('product_name'),
        "price": products[0].get('price'), # sale price (usually dict or string)
        "cost": products[0].get('spots', [{}])[0].get('cost'), # prime cost from first spot
        "profit": products[0].get('spots', [{}])[0].get('profit')
    }
    print(json.dumps(sample, indent=2, ensure_ascii=False))

# 2. Test storage.getInvoices (to see cost changes from suppliers)
# This usually requires date filters
from datetime import datetime, timedelta
date_to = datetime.now().strftime('%Y%m%d')
date_from = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

invoices = api._make_request('storage.getInvoices', params={"date_from": date_from, "date_to": date_to})
print(f"\nInvoices in last 30 days: {len(invoices) if invoices else 0}")
if invoices and isinstance(invoices, list):
    print("Sample invoice:")
    print(json.dumps(invoices[0], indent=2, ensure_ascii=False))
