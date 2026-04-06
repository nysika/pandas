import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# ======================== 1. ЗАГРУЗКА ДАННЫХ ========================
df = pd.read_csv('sales_data.csv', parse_dates=['sale_date'])

# Проверка на отрицательные скидки и некорректные значения
if (df['discount'] < 0).any() or (df['discount'] > 1).any():
    print("Предупреждение: обнаружены некорректные скидки (>1 или <0)")

# ======================== 2. РАСЧЁТ ФИНАНСОВЫХ ПОКАЗАТЕЛЕЙ ========================
df['revenue'] = df['unit_price'] * df['quantity_sold'] * (1 - df['discount'])
df['cost_price'] = df['unit_price'] * 0.6  # себестоимость 60% от цены
df['profit'] = df['revenue'] - (df['cost_price'] * df['quantity_sold'])

# ======================== 3. АГРЕГАЦИЯ ПО ТОВАРАМ ========================
products = df.groupby('product_id').agg({
    'product_name': 'first',
    'category': 'first',
    'unit_price': 'first',
    'quantity_sold': 'sum',
    'revenue': 'sum',
    'profit': 'sum',
    'discount': 'mean',
    'region': 'nunique',  # количество уникальных регионов
    'sale_date': 'nunique'  # частота продаж (дней)
}).rename(columns={
    'region': 'unique_regions',
    'sale_date': 'sales_frequency',
    'discount': 'avg_discount',
    'quantity_sold': 'total_quantity',
    'revenue': 'total_revenue',
    'profit': 'total_profit'
}).reset_index()

# Отметим неактивные товары (хотя в исходных данных все продавались)
products['status'] = 'active'

# ======================== 4. РЕГИОНАЛЬНЫЙ АНАЛИЗ ========================
# 4.1 Топ-2 товара по прибыли в каждом регионе
region_top_products = (df.groupby(['region', 'product_id', 'product_name'])['profit']
                       .sum()
                       .reset_index()
                       .sort_values(['region', 'profit'], ascending=[True, False])
                       .groupby('region')
                       .head(2)
                       .reset_index(drop=True))

# 4.2 Регионы, где доля Премиум > 40%
region_premium_share = df.groupby(['region', 'customer_segment'])['profit'].sum().unstack(fill_value=0)
region_premium_share['premium_share'] = region_premium_share['Премиум'] / region_premium_share.sum(axis=1)
high_value_regions = region_premium_share[region_premium_share['premium_share'] > 0.4].reset_index()[['region', 'premium_share']]

# ======================== 5. ПРОГНОЗ ПРОДАЖ НА 7 ДНЕЙ ========================
def forecast_sales(product_df, days_ahead=7):
    """
    Для одного товара строит прогноз на days_ahead дней.
    Если уникальных дней продаж >=3 - линейная регрессия,
    иначе - медиана продаж в день.
    """
    if len(product_df) < 3:
        # Недостаточно данных - используем медиану
        median_qty = product_df['quantity_sold'].median()
        return [max(0, int(median_qty))] * days_ahead
    else:
        # Подготовка данных для регрессии
        X = np.array((product_df['sale_date'] - product_df['sale_date'].min()).dt.days).reshape(-1, 1)
        y = product_df['quantity_sold'].values
        model = LinearRegression()
        model.fit(X, y)
        # Прогноз на следующие days_ahead дней
        future_days = np.array(range(X.max() + 1, X.max() + days_ahead + 1)).reshape(-1, 1)
        forecast = model.predict(future_days)
        # Округляем и не допускаем отрицательных значений
        return [max(0, int(round(val))) for val in forecast]

# Группируем исходные продажи по товарам для прогноза
sales_by_product = df.sort_values('sale_date').groupby('product_id')

forecast_dict = {}
for product_id, group in sales_by_product:
    forecast_dict[product_id] = forecast_sales(group)

# Добавляем прогноз в products (суммарный на 7 дней)
products['forecast_next_7days'] = products['product_id'].map(
    lambda pid: sum(forecast_dict.get(pid, [0]*7))
)

# ======================== 6. КЛАСТЕРИЗАЦИЯ ТОВАРОВ ========================
# Отбираем активные товары для кластеризации
cluster_df = products[products['status'] == 'active'].copy()

# Признаки для кластеризации
features = ['total_quantity', 'total_revenue', 'avg_discount', 'unique_regions', 'forecast_next_7days']
X_cluster = cluster_df[features]

# Масштабирование
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_cluster)

# Определение оптимального числа кластеров (метод локтя)
inertias = []
K_range = range(1, min(6, len(cluster_df)))
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Выбираем k = 3 (для демонстрации; в реальности анализируют график)
optimal_k = 3 if len(K_range) >= 3 else len(K_range)
kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
cluster_df['cluster_id'] = kmeans_final.fit_predict(X_scaled)

# Добавляем кластеры обратно в products
products = products.merge(cluster_df[['product_id', 'cluster_id']], on='product_id', how='left')
products['cluster_id'] = products['cluster_id'].fillna(-1).astype(int)  # -1 для неактивных

# ======================== 7. ФОРМИРОВАНИЕ РЕКОМЕНДАЦИЙ ПО КЛАСТЕРАМ ========================
cluster_stats = products[products['cluster_id'] >= 0].groupby('cluster_id')[features].mean().reset_index()

def get_strategy(row):
    if row['total_revenue'] > 50000 and row['unique_regions'] > 1:
        return "Увеличить закупки, расширить рекламу"
    elif row['avg_discount'] > 0.08:
        return "Снизить скидки, тестировать цену"
    elif row['forecast_next_7days'] > row['total_quantity'] * 0.5:
        return "Высокий прогноз — обеспечить складские запасы"
    else:
        return "Поддерживающий маркетинг"

cluster_stats['strategy'] = cluster_stats.apply(get_strategy, axis=1)
cluster_stats = cluster_stats[['cluster_id', 'strategy'] + features]

# ======================== 8. ЭКСПОРТ В EXCEL ========================
with pd.ExcelWriter('marketing_report.xlsx', engine='openpyxl') as writer:
    # Лист 1: Сводка по товарам
    products_report = products[[
        'product_id', 'product_name', 'category', 'total_quantity',
        'total_revenue', 'total_profit', 'avg_discount', 'unique_regions',
        'sales_frequency', 'forecast_next_7days', 'cluster_id', 'status'
    ]].copy()
    products_report.to_excel(writer, sheet_name='products_summary', index=False)
    
    # Лист 2: Прибыль по регионам и сегментам
    region_segment_profit = df.pivot_table(
        index='region', columns='customer_segment', values='profit', aggfunc='sum', fill_value=0
    ).reset_index()
    region_segment_profit.to_excel(writer, sheet_name='region_profit_analysis', index=False)
    
    # Лист 3: Высокомаржинальные регионы (Premium > 40%)
    high_value_regions.to_excel(writer, sheet_name='high_value_regions', index=False)
    
    # Лист 4: Рекомендации по кластерам
    cluster_stats.to_excel(writer, sheet_name='cluster_recommendations', index=False)
    
    # Доп. лист: Топ-2 товара по регионам
    region_top_products.to_excel(writer, sheet_name='top2_by_region', index=False)

print("✅ Отчёт 'marketing_report.xlsx' успешно создан!")
print(f"📊 Обработано товаров: {len(products)}")
print(f"🔍 Кластеров выделено: {optimal_k}")
print(f"📈 Прогноз построен для {len(forecast_dict)} товаров")