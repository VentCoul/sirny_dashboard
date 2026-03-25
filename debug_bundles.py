from poster_api import PosterAPI
import json

api = PosterAPI()
products = api._make_request('menu.getProducts')
inventory = api._make_request('storage.getStorageLeftovers')

# Sample some categories from products
cat_counts = {}
for p in products:
    cid = str(p.get('category_id'))
    cat_counts[cid] = cat_counts.get(cid, 0) + 1

print("Categories in products (ID: Count):")
print(cat_counts)

# Match inventory to products
stock_map = {i['ingredient_name'].lower(): float(i['ingredient_left']) for i in inventory}
match_count = 0
for p in products:
    if p['product_name'].lower() in stock_map:
        match_count += 1

print(f"\nExact matches between Product Name and Ingredient Name: {match_count}")
print(f"Total products: {len(products)}")
print(f"Total ingredients: {len(inventory)}")

# Print a few products from category 82 (Cheeses) and 22 (Drinks) if they exist
print("\nSample Products from known categories:")
target_cats = ['82', '6', '7', '12', '4', '20', '48', '83', '22', '141', '114']
for p in products:
    cid = str(p.get('category_id'))
    if cid in target_cats:
        print(f"Cat {cid}: {p['product_name']}")
        # Only print first 5
        target_cats.remove(cid) if cat_counts[cid] < 2 else None # stop after some
