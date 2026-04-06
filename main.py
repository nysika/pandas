import pandas as pd
print(pd.__version__)
series = pd.Series([1, 2, 3, 4, 5])
new_series = series + 1
print(new_series)
shop_a = {'Яблоки': 10, 'Бананы': 5}
shop_b = {'Бананы': 8, 'Яблоки': 3}
shop_sum = pd.Series(shop_a) + pd.Series(shop_b)
print(shop_sum)

# Данные - продажи
sales = [150, 200, 100]

# Индекс - месяцы
months = ['Jan', 'Feb', 'Mar']

# Явное указание индекса
s = pd.Series(sales, index=months)

print(s)