#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import json
import pandas as pd
import datetime
import numpy as np


def _macd_check(macd_data_path, code, short_day, long_day, rate, average_rate):

    sd = 0.05

    stock_data = pd.read_csv(macd_data_path + '/macd_data/' + code + '.csv')
    try:
       stock_data.empty
    except AttributeError as e:
        print(e)

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


def macd_check():

    buy_codes = []
    sell_codes = []
    buy_sell_result = {}

    calculate_rate = 0
    macd_data_path = '/Users/Richard/WorkSpace/finance'
    with open(macd_data_path + '/macd_data_ret.json', 'r') as f:
        ret_list = f.readlines()
    ret_json = json.loads(ret_list[-1])
    buy_list = ret_json['buy_list']
    sell_list = ret_json['sell_list']

    for code in buy_list:
        if _macd_check(macd_data_path, code, 5, 60, 0.1, 0.9):
            buy_codes.append(code)
        if calculate_rate % 5 == 0:
            sys.stdout.write('$')
            sys.stdout.flush()
        calculate_rate += 1
    print('')
    for code in sell_list:
        if _macd_check(macd_data_path, code, 5, 60, 0.1, 0.9):
            sell_codes.append(code)
        if calculate_rate % 5 == 0:
            sys.stdout.write('$')
            sys.stdout.flush()
        calculate_rate += 1

    print('')
    print(buy_codes)
    print()
    print(sell_codes)
    with open(macd_data_path + '/macd_data_ret_buy_sell.json', 'a') as f:
        buy_sell_result['data_time'] = str(datetime.datetime.now())
        buy_sell_result['buy_list'] = buy_codes
        buy_sell_result['sell_list'] = sell_codes

        f.write(json.dumps(buy_sell_result) + '\n\n\n')


if __name__ == "__main__":
    macd_check()
