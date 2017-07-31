import csv
import tushare as ts
import pandas as pd

#all_data = ts.get_today_all()
#df = pd.DataFrame(all_data)
#df.to_csv('stock_list.csv')

df = pd.read_csv('./stock_list.csv')
for one in df['code']:
    if one < 603416:
        print(one)


