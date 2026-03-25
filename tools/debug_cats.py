from poster_api import PosterAPI
import json

api = PosterAPI()
cats = api._make_request('menu.getCategories')
for c in cats:
    print(f"ID: {c['category_id']}, Name: {c['category_name']}")
