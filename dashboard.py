import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.poster_api import PosterAPI
from core.weather_service import get_weather_history, get_weather_forecast
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from itertools import combinations
import random

# Page config
st.set_page_config(page_title="Poster Analytics Pro", layout="wide")

st.title("📊 Poster Analytics Dashboard")
st.markdown("---")

# Initialize API
@st.cache_resource
def get_api():
    return PosterAPI()

api = get_api()

# Global Blacklist
SKIP_CATS = ['13', '50', '17', '75', '140']
SKIP_KEYWORDS = ['стакан', 'контейнер', 'пакет', 'серветк', 'ложка', 'вилка', 'ніж', 'трубочк', 'кришка', 'стік цукру', 'вода', 'water', 'pepsi', 'пепсі', 'cola', 'кола', 'фанта', 'fanta', 'спрайт', 'sprite', 'бонаква', 'моршинськ']

def is_disposable(name, cat_id):
    if str(cat_id) in SKIP_CATS: return True
    name_low = name.lower()
    return any(k in name_low for k in SKIP_KEYWORDS)

# Sidebar for filters
st.sidebar.header("⚙️ Налаштування")
days_to_analyze = st.sidebar.slider("Період аналізу продажів (днів)", 1, 60, 30)
min_margin_threshold = st.sidebar.slider("Поріг націнки (%)", 5, 50, 20)

# ---------------------------------------------------------
# DATA LOADING FUNCTIONS
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def load_sales_data(days):
    date_to = datetime.now().strftime('%Y%m%d')
    date_from = (datetime.now() - timedelta(days=days-1)).strftime('%Y%m%d')
    transactions = api.get_transactions(date_from=date_from, date_to=date_to, status=2)
    if not transactions: return pd.DataFrame(), []
    sales_list = []
    tids = []
    for t in transactions:
        try:
            t_date = datetime.strptime(t.get('date_close_date'), '%Y-%m-%d %H:%M:%S')
            sales_list.append({"date": t_date, "revenue": float(t.get('payed_sum', 0)) / 100, "id": t.get('transaction_id'), "client_id": t.get('client_id')})
            if t.get('transaction_id'): tids.append(t.get('transaction_id'))
        except: continue
    df = pd.DataFrame(sales_list)
    if not df.empty: df['hour'] = df['date'].dt.hour
    return df, tids

@st.cache_data(ttl=3600)
def load_loyalty_data():
    now = datetime.now()
    date_to = now.strftime('%Y%m%d')
    date_from = (now - timedelta(days=89)).strftime('%Y%m%d')
    transactions = api.get_transactions(date_from=date_from, date_to=date_to, status=2)
    if not transactions: return pd.DataFrame()
    client_visits = {}
    for t in transactions:
        cid = t.get('client_id', '0')
        if cid != '0':
            try:
                t_date = datetime.strptime(t.get('date_close_date'), '%Y-%m-%d %H:%M:%S')
                if cid not in client_visits: client_visits[cid] = {"dates": [], "revenues": []}
                client_visits[cid]["dates"].append(t_date)
                client_visits[cid]["revenues"].append(float(t.get('payed_sum', 0)) / 100)
            except: continue
    client_data = api._make_request('clients.getClients')
    clients_map = {c['client_id']: f"{c['firstname']} {c['lastname']}".strip() or c['phone'] for c in client_data} if client_data else {}
    segments = []
    for cid, data in client_visits.items():
        last_visit = max(data["dates"])
        recency = (now - last_visit).days
        frequency = len(data["dates"])
        monetary = sum(data["revenues"])
        if recency <= 14 and frequency >= 3: seg = "🏆 Чемпіони"
        elif recency > 21: seg = "⚠️ Під ризиком"
        elif recency <= 21 and frequency == 1: seg = "🆕 Новачки"
        else: seg = "💤 Сплячі / Інші"
        segments.append({"Клієнт": clients_map.get(cid, f"ID:{cid}"), "Останній візит": last_visit.strftime('%Y-%m-%d'), "Днів тому": recency, "Візитів за 90д": frequency, "Сума (грн)": round(monetary, 0), "Сегмент": seg})
    return pd.DataFrame(segments)

@st.cache_data(ttl=600)
def load_product_and_basket_data(tids):
    if not tids: return [], pd.DataFrame()
    products_info = api._make_request('menu.getProducts')
    names_map = {p['product_id']: p['product_name'] for p in products_info}
    
    def get_price(p):
        price_data = p.get('price', '0')
        if isinstance(price_data, dict):
            return float(price_data.get('1', 0)) / 100
        return float(price_data) / 100

    prices_map = {p['product_id']: get_price(p) for p in products_info}
    cat_map = {p['product_id']: p.get('menu_category_id') for p in products_info}

    def fetch_transaction_products(tid):
        return api._make_request('dash.getTransactionProducts', {'transaction_id': tid})

    all_products_sold = []
    baskets = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(fetch_transaction_products, tids[:400])) 
        for res in results:
            if isinstance(res, list) and res:
                transaction_basket = []
                for p in res:
                    pid = p.get('product_id')
                    name = names_map.get(pid, "Unknown")
                    if is_disposable(name, cat_map.get(pid)): continue
                    all_products_sold.append({"product_name": name, "revenue": float(p.get('payed_sum', 0)) / 100})
                    transaction_basket.append(name)
                if len(transaction_basket) > 1: baskets.append(list(set(transaction_basket)))

    df_top = pd.DataFrame(all_products_sold).groupby('product_name').agg({'revenue': 'sum'}).reset_index().sort_values('revenue', ascending=False)
    pair_counts = Counter()
    for basket in baskets:
        for pair in combinations(sorted(basket), 2): pair_counts[pair] += 1
    common_pairs = []
    for (p1, p2), count in pair_counts.most_common(10):
        pr1 = next((prices_map[pid] for pid, name in names_map.items() if name == p1), 0)
        pr2 = next((prices_map[pid] for pid, name in names_map.items() if name == p2), 0)
        common_pairs.append({"Товар 1": p1, "Товар 2": p2, "Разом (раз)": count, "Стара ціна": pr1+pr2, "Акційна ціна": round((pr1+pr2)*0.85, 0)})
    return common_pairs, df_top

@st.cache_data(ttl=600)
def load_margin_data():
    products = api._make_request('menu.getProducts')
    if not products: return pd.DataFrame()
    data = []
    for p in products:
        name = p.get('product_name')
        if is_disposable(name, p.get('menu_category_id')): continue
        spot = p.get('spots', [{}])[0]
        price = float(spot.get('price', '0')) / 100
        profit = float(spot.get('profit', 0)) / 100
        if price > 0: data.append({"Товар": name, "Ціна": price, "Собівартість": round(price - profit, 2), "Прибуток": round(profit, 2), "Націнка %": round((profit/price*100), 1)})
    return pd.DataFrame(data)

@st.cache_data(ttl=600)
def load_smart_bundles():
    """Generates bundles based on inventory levels and corrected logic."""
    products = api._make_request('menu.getProducts')
    inventory = api._make_request('storage.getStorageLeftovers')
    if not products or not inventory: return []

    stock_map = {str(i['ingredient_id']): float(i['ingredient_left']) for i in inventory}
    
    cheeses = []
    drinks = []
    
    CHEESE_CATS = ['82', '6', '7', '12']
    # Filter for alcoholic drinks specifically for cheese sets
    WINE_ALCO_CATS = ['4', '20', '48', '83']

    for p in products:
        name = p['product_name']
        cat = str(p.get('menu_category_id'))
        
        # Determine price properly
        price_data = p.get('price', '0')
        if isinstance(price_data, dict):
            price = float(price_data.get('1', 0)) / 100
        else:
            price = float(price_data) / 100
            
        if price == 0 or is_disposable(name, cat): continue
        
        # Link by ingredient_id
        iid = str(p.get('ingredient_id'))
        stock = stock_map.get(iid, 0)
        
        item_data = {"name": name, "price": price, "stock": stock}
        if cat in CHEESE_CATS: cheeses.append(item_data)
        elif cat in WINE_ALCO_CATS: drinks.append(item_data)

    # Sort by stock to find overstock
    cheeses.sort(key=lambda x: x['stock'], reverse=True)
    drinks.sort(key=lambda x: x['stock'], reverse=True)

    bundles = []
    for i in range(min(8, len(cheeses), len(drinks))):
        c = cheeses[i]
        d = drinks[random.randint(0, min(5, len(drinks)-1))] # Add some variety
        
        # Avoid pairing very low stock items
        if c['stock'] < 0.5: continue 
        
        total = c['price'] + d['price']
        bundles.append({
            "Назва сету": f"💡 Сет: {c['name']} + {d['name']}",
            "Склад": f"{c['name']} (100г) + {d['name']} (порція)",
            "Стара ціна": f"{total} грн",
            "Акційна ціна": f"{round(total * 0.85, 0)} грн",
            "Обґрунтування": f"Високий запас: {c['name']} ({round(c['stock'], 1)})"
        })
    return bundles

# ---------------------------------------------------------
# EXECUTION
# ---------------------------------------------------------

if st.sidebar.button("🔄 Оновити всі дані"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Jarvis аналізує ваші дані..."):
    df_sales, tids = load_sales_data(days_to_analyze)
    df_clients = load_loyalty_data()
    common_pairs, df_top_prods = load_product_and_basket_data(tids)
    df_margin = load_margin_data()
    df_weather_hist = get_weather_history(days=days_to_analyze)
    forecast = get_weather_forecast()
    smart_bundles = load_smart_bundles()

# TABS
t1, t2, t3, t4, t5 = st.tabs(["📈 Продажі", "💎 Клієнти", "🛡 Margin Guard", "🌤 Погода", "🎁 Акції та Сети"])

with t1:
    if not df_sales.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Виручка", f"{round(df_sales['revenue'].sum(), 2)} грн")
        c2.metric("Середній чек", f"{round(df_sales['revenue'].mean(), 2)} грн")
        c3.metric("Чеки", f"{len(df_sales)}")
        st.plotly_chart(px.line(df_sales.groupby(df_sales['date'].dt.date)['revenue'].sum().reset_index(), x='date', y='revenue', markers=True), use_container_width=True)

with t2:
    if not df_clients.empty:
        st.plotly_chart(px.pie(df_clients['Сегмент'].value_counts().reset_index(), values='count', names='Сегмент', hole=.3), use_container_width=True)
        selected_seg = st.selectbox("Категорія:", options=["Всі"] + list(df_clients['Сегмент'].unique()))
        st.dataframe(df_clients[df_clients['Сегмент'] == selected_seg] if selected_seg != "Всі" else df_clients, use_container_width=True, hide_index=True)

with t3:
    if not df_margin.empty:
        low_m = df_margin[df_margin['Націнка %'] < min_margin_threshold].sort_values('Націнка %')
        st.dataframe(low_m, use_container_width=True, hide_index=True)

with t4:
    if forecast: st.success(f"🌡️ Прогноз: сьогодні {forecast['today_temp']}°C, завтра {forecast['tomorrow_temp']}°C.")
    if not df_weather_hist.empty and not df_sales.empty:
        daily_s = df_sales.groupby(df_sales['date'].dt.date)['revenue'].sum().reset_index()
        daily_s['date'] = pd.to_datetime(daily_s['date'])
        df_corr = pd.merge(daily_s, df_weather_hist, on='date', how='inner')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_corr['date'], y=df_corr['revenue'], name="Виручка"))
        fig.add_trace(go.Scatter(x=df_corr['date'], y=df_corr['temp_max'], name="Темп", yaxis="y2", line=dict(dash='dash')))
        fig.update_layout(yaxis=dict(title="Виручка"), yaxis2=dict(title="Темп", overlaying="y", side="right"))
        st.plotly_chart(fig, use_container_width=True)

with t5:
    st.markdown("### 🪄 Розумний конструктор дегустацій")
    st.write("Jarvis підібрав ідеальні пари: сири з великим залишком + популярні напої.")
    
    if smart_bundles:
        for bundle in smart_bundles:
            with st.expander(bundle['Назва сету']):
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.write(f"📋 **Склад:** {bundle['Склад']}")
                    st.write(f"💰 **Ціна:** ~~{bundle['Стара ціна']}~~ → **{bundle['Акційна ціна']} грн**")
                with col_b2:
                    st.success(f"💡 **Порада Оксані:** {bundle['Обґрунтування']}")
    else:
        st.warning("⚠️ Поки не вдалося знайти ідеальні пари. Перевірте, чи заповнені залишки (stock) для товарів у категоріях Сири та Алкоголь.")

    st.markdown("---")
    st.markdown("#### 🔥 Також популярні серед клієнтів (на основі чеків):")
    if common_pairs:
        st.dataframe(pd.DataFrame(common_pairs)[['Товар 1', 'Товар 2', 'Акційна ціна']], use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
st.sidebar.info("🦾 Poster AI: Smart Bundling v2")
