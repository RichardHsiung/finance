#!/usr/bin/env python
#-*- coding:utf-8 -*-

import json
import tushare as ts
import pandas as pd
import datetime
import numpy as np


def _get_stock_data(code, start_time, end_time, autype):

    stock_data = ts.get_k_data(code, start=start_time, end=end_time, autype=autype)
    if type(stock_data) == "DataFrame" and not stock_data.empty:
        stock_data.index = pd.to_datetime(stock_data.date)
    return stock_data.loc[:, ('open', 'close', 'high', 'low')]

def macd_check(code, start_time, end_time, autype, short_day, long_day, rate, average_rate):
    sd = 0.05  #width of the region
    stock_data = _get_stock_data(code, start_time, end_time, autype)
    if type(stock_data.empty) == "NoneType" or stock_data.empty:
        return

    stock_data["short"] = np.round(stock_data["close"].rolling(window = int(short_day), center = False).mean(), 2)
    stock_data["long"] = np.round(stock_data["close"].rolling(window = int(long_day), center = False).mean(), 2)

    # s-l > long * sd  buy the stock
    stock_data["s-l"] = stock_data["short"] - stock_data["long"]
    stock_data['flag'] = np.where(stock_data['s-l'] > stock_data["long"] * sd, 1, 0)

    stock_data['Market'] = np.log(stock_data['close'] / stock_data['close'].shift(1))
    stock_data['Strategy'] = stock_data['flag'].shift(1) * stock_data['Market']

    stock_data['Market'] = stock_data[['Market']].cumsum().apply(np.exp)
    stock_data['Strategy'] = stock_data[['Strategy']].cumsum().apply(np.exp)
    stock_data['sum_ret'] = stock_data['Strategy'] - stock_data['Market']

    count = 0
    for item in stock_data['sum_ret']:
        if item > rate:
            count += 1
    if count/len(stock_data['sum_ret']) > average_rate:
        return True
    else:
        return False


if __name__ == "__main__":
    start_time = "2016-01-01"
    end_time = datetime.datetime.now().strftime('%Y-%m-%d')
    autype = "qfq"

    good_codes = []
    macd_data_path = '/Users/Richard/WorkSpace/finance'
    with open(macd_data_path + '/result_list.json', 'r') as f:
        ret_list = f.readlines()
    ret_json = json.loads(ret_list[-1])
    buy_list = ret_json['buy_list']
    sell_list = ret_json['sell_list']

    for code in buy_list:
        print(code)
        code = str(code)
        if macd_check(code, start_time, end_time, autype, 5, 60, 0.1, 0.9):
            good_codes.append(code)
    print(sorted(good_codes))
