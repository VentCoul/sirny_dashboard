import pandas as pd
from datetime import datetime, timedelta
from poster_api import PosterAPI
import json

api = PosterAPI()
days = 60 # Look back further to find those who stopped coming
date_to = datetime.now().strftime('%Y%m%d')
date_from = (datetime.now() - timedelta(days=days-1)).strftime('%Y%m%d')

transactions = api.get_transactions(date_from=date_from, date_to=date_to, status=2)
client_visits = {}

if transactions:
    for t in transactions:
        cid = t.get('client_id', '0')
        if cid != '0':
            t_date = datetime.strptime(t.get('date_close_date'), '%Y-%m-%d %H:%M:%S')
            if cid not in client_visits: client_visits[cid] = []
            client_visits[cid].append(t_date)

now = datetime.now()
stats = []
for cid, dates in client_visits.items():
    last_visit = max(dates)
    recency = (now - last_visit).days
    stats.append({"cid": cid, "recency": recency, "freq": len(dates)})

df = pd.DataFrame(stats)
print(f"Total clients with visits in {days} days: {len(df)}")
if not df.empty:
    print("Recency distribution:")
    print(df['recency'].value_counts().sort_index().head(10))
    print("\nClients with recency > 21:")
    at_risk = df[(df['recency'] > 21) & (df['freq'] >= 2)]
    print(f"Count: {len(at_risk)}")
    if not at_risk.empty:
        print(at_risk.head())
else:
    print("No clients with ID found in transactions.")
