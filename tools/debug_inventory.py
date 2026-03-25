from poster_api import PosterAPI
import json

api = PosterAPI()
# Testing storage.getStorageLeftovers
data = api._make_request('storage.getStorageLeftovers')
print(f"Data type: {type(data)}")
if isinstance(data, list):
    print(f"Items count: {len(data)}")
    if data:
        print("First item sample:")
        print(json.dumps(data[0], indent=2))
elif isinstance(data, dict):
    print(f"Keys: {data.keys()}")
    if 'error' in data:
        print(f"Error: {data['error']}")
