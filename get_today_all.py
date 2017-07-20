import csv
import tushare as ts
import pandas as pd

all_data = ts.get_today_all()
df = pd.DataFrame(all_data)
df.to_csv('stock_list.csv')

