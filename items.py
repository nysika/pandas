import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Фиксируем seed для воспроизводимости
np.random.seed(42)
random.seed(42)

# ======================== 1. БАЗОВЫЕ ДАННЫЕ ========================
# Товары (20 различных позиций)
products = {
    101: {"name": "Кофеварка Philips HD7432", "category": "Бытовая техника", "base_price": 4500},
    102: {"name": "Смартфон Xiaomi Note 12", "category": "Электроника", "base_price": 18990},
    103: {"name": "Коврик для мыши", "category": "Аксессуары", "base_price": 350},
    104: {"name": "Ноутбук Lenovo IdeaPad", "category": "Электроника", "base_price": 54990},
    105: {"name": "Наушники JBL Tune", "category": "Аксессуары", "base_price": 3990},
    106: {"name": "Электрочайник Bosch TWK", "category": "Бытовая техника", "base_price": 3200},
    107: {"name": "Фитнес-браслет Mi Band", "category": "Электроника", "base_price": 2490},
    108: {"name": "Монитор Samsung 24\"", "category": "Электроника", "base_price": 15990},
    109: {"name": "Мышь Logitech M185", "category": "Аксессуары", "base_price": 1290},
    110: {"name": "Соковыжималка Braun", "category": "Бытовая техника", "base_price": 8900},
    111: {"name": "Планшет Huawei MatePad", "category": "Электроника", "base_price": 25990},
    112: {"name": "Клавиатура Logitech K380", "category": "Аксессуары", "base_price": 3490},
    113: {"name": "Робот-пылесос Xiaomi", "category": "Бытовая техника", "base_price": 18990},
    114: {"name": "Внешний SSD 1TB", "category": "Электроника", "base_price": 7990},
    115: {"name": "Подставка для ноутбука", "category": "Аксессуары", "base_price": 890},
    116: {"name": "Микроволновая печь Samsung", "category": "Бытовая техника", "base_price": 12990},
    117: {"name": "Смарт-часы Amazfit", "category": "Электроника", "base_price": 11990},
    118: {"name": "USB-хаб 4 порта", "category": "Аксессуары", "base_price": 590},
    119: {"name": "Холодильник LG", "category": "Бытовая техника", "base_price": 45990},
    120: {"name": "Стиральная машина Bosch", "category": "Бытовая техника", "base_price": 38990}
}

# Регионы с коэффициентом спроса
regions = {
    "Центр": {"demand_factor": 1.3, "premium_ratio": 0.35},
    "Северо-Запад": {"demand_factor": 1.1, "premium_ratio": 0.30},
    "Юг": {"demand_factor": 1.0, "premium_ratio": 0.25},
    "Поволжье": {"demand_factor": 0.9, "premium_ratio": 0.20},
    "Урал": {"demand_factor": 0.95, "premium_ratio": 0.22},
    "Сибирь": {"demand_factor": 0.85, "premium_ratio": 0.18},
    "Дальний Восток": {"demand_factor": 0.7, "premium_ratio": 0.15}
}

# Сегменты клиентов
segments = ["Эконом", "Стандарт", "Премиум"]

# ======================== 2. ГЕНЕРАЦИЯ ДАННЫХ ========================
records = []
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 3, 31)
date_range = (end_date - start_date).days

# Веса для регионов (сумма = 1)
region_weights = [0.25, 0.15, 0.15, 0.12, 0.12, 0.12, 0.09]
region_names = list(regions.keys())

for i in range(5000):
    # Выбор товара
    product_id = random.choice(list(products.keys()))
    product = products[product_id]
    
    # Выбор региона с весами
    region = np.random.choice(region_names, p=region_weights)
    region_data = regions[region]
    
    # Выбор сегмента с корректными вероятностями
    premium_prob = region_data["premium_ratio"]
    # Нормируем вероятности так, чтобы их сумма была = 1
    # Базовые вероятности: Эконом - 0.3, Стандарт - 0.5, Премиум - premium_prob
    # Но сумма может быть больше 1, поэтому нормируем
    raw_probs = [0.3, 0.5, premium_prob]
    probs = [p / sum(raw_probs) for p in raw_probs]
    
    segment = np.random.choice(segments, p=probs)
    
    # Базовое количество продаж (зависит от товара)
    if product_id in [103, 109, 112, 115, 118]:  # Дешёвые аксессуары
        base_qty = np.random.poisson(15)
    elif product_id in [102, 107, 111, 117]:  # Средняя электроника
        base_qty = np.random.poisson(8)
    elif product_id in [101, 106, 110, 113, 116]:  # Бытовая техника
        base_qty = np.random.poisson(5)
    else:  # Дорогие товары (104, 108, 114, 119, 120)
        base_qty = np.random.poisson(2)
    
    # Модификаторы
    region_modifier = region_data["demand_factor"]
    segment_modifier = {"Эконом": 0.7, "Стандарт": 1.0, "Премиум": 1.5}[segment]
    
    # Сезонность
    sale_date = start_date + timedelta(days=np.random.randint(0, date_range))
    month_factor = 0.9 if sale_date.month == 1 else (1.1 if sale_date.month == 3 else 1.0)
    
    # Итоговое количество (минимум 1)
    quantity = max(1, int(base_qty * region_modifier * segment_modifier * month_factor * np.random.uniform(0.7, 1.3)))
    
    # Скидка (зависит от сегмента и сезона)
    if segment == "Премиум":
        discount = np.random.uniform(0.05, 0.15)
    elif segment == "Стандарт":
        discount = np.random.uniform(0, 0.08)
    else:  # Эконом
        discount = np.random.uniform(0, 0.03)
    
    # Корректировка скидки в марте
    if sale_date.month == 3:
        discount += np.random.uniform(0, 0.05)
    
    discount = min(discount, 0.25)
    
    # Цена с возможной динамикой
    price_modifier = 1.0
    if sale_date.month == 3:
        price_modifier = np.random.uniform(0.95, 1.0)
    
    unit_price = round(product["base_price"] * price_modifier, 2)
    
    # Добавление записи
    records.append({
        "product_id": product_id,
        "product_name": product["name"],
        "category": product["category"],
        "unit_price": unit_price,
        "quantity_sold": quantity,
        "sale_date": sale_date.strftime("%Y-%m-%d"),
        "region": region,
        "customer_segment": segment,
        "discount": round(discount, 3)
    })

# ======================== 3. СОЗДАНИЕ DATAFRAME ========================
df = pd.DataFrame(records)
df = df.sort_values('sale_date').reset_index(drop=True)

# Добавляем случайный шум в цены
for idx in df.sample(frac=0.1).index:
    df.loc[idx, 'unit_price'] = round(df.loc[idx, 'unit_price'] * np.random.uniform(0.97, 1.03), 2)

# ======================== 4. СОХРАНЕНИЕ В CSV ========================
df.to_csv('sales_data.csv', index=False, encoding='utf-8')

# ======================== 5. СТАТИСТИКА ========================
print("=" * 60)
print("✅ Файл 'sales_data.csv' успешно создан!")
print("=" * 60)
print(f"\n📊 Статистика сгенерированных данных:")
print(f"   • Всего записей: {len(df):,}")
print(f"   • Уникальных товаров: {df['product_id'].nunique()}")
print(f"   • Период: {df['sale_date'].min()} → {df['sale_date'].max()}")
print(f"   • Регионов: {df['region'].nunique()}")
print(f"\n📈 Объёмы продаж по категориям:")
print(df.groupby('category')['quantity_sold'].sum().to_string())
print(f"\n💰 Выручка по сегментам:")
df['revenue'] = df['unit_price'] * df['quantity_sold'] * (1 - df['discount'])
print(df.groupby('customer_segment')['revenue'].sum().apply(lambda x: f"{x:,.0f} ₽").to_string())
print(f"\n🎯 Топ-5 товаров по количеству продаж:")
print(df.groupby('product_name')['quantity_sold'].sum().sort_values(ascending=False).head().to_string())
print(f"\n📅 Продажи по месяцам:")
df['month'] = pd.to_datetime(df['sale_date']).dt.month
print(df.groupby('month')['quantity_sold'].sum().to_string())
print("\n" + "=" * 60)

# Проверка данных
print("\n🔍 Проверка данных:")
print(f"   • Отрицательные скидки: {(df['discount'] < 0).sum()}")
print(f"   • Нулевые продажи: {(df['quantity_sold'] == 0).sum()}")
print(f"   • Пустые значения: {df.isnull().sum().sum()}")
print(f"   • Диапазон цен: {df['unit_price'].min():.0f} - {df['unit_price'].max():.0f} ₽")
print(f"   • Средняя скидка: {df['discount'].mean():.1%}")

# Дополнительная проверка распределения по сегментам
print(f"\n📊 Распределение по сегментам:")
print(df['customer_segment'].value_counts(normalize=True).apply(lambda x: f"{x:.1%}"))