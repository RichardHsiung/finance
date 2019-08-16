import csv
import tushare as ts
import pandas as pd

#all_data = ts.get_today_all()
#df_data = pd.DataFrame(all_data)


df_data = pd.read_csv('./stock_list.csv')
stock_data_length = df_data.shape[0]

for i in  range(stock_data_length):
    code = df_data.iloc[i].code
    code_path = './stock_price/' + code + '.csv'
    if os.path.exist(code_path):
        df = pd.read_csv(code_path)
        df.loc[df.shape[0] + 1] = {}
        pd.to_csv(code_path)
