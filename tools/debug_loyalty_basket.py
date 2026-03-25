from poster_api import PosterAPI
import json
from datetime import datetime

api = PosterAPI()

# 1. Check client data
clients = api._make_request('clients.getClients')
print(f"Total clients: {len(clients) if clients else 0}")
if clients and len(clients) > 0:
    print("Sample client:")
    # We need last visit date or history
    print(json.dumps(clients[0], indent=2, ensure_ascii=False))

# 2. Check if we can get transactions with product details in bulk efficiently
# We already used dash.getTransactionProducts in a loop. 
# For basket analysis, we need many transactions.
