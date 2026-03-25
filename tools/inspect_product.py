from poster_api import PosterAPI
import json

api = PosterAPI()
products = api._make_request('menu.getProducts')
if products:
    print(json.dumps(products[0], indent=2, ensure_ascii=False))
