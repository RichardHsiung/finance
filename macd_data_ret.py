#!/usr/bin/env python
#-*- coding:utf-8 -*-


import os
import json
import pandas as pd
import datetime


def macd_data_ret():
    buy_list = []
    sell_list = []
    macd_data_path = '/Users/Richard/WorkSpace/finance/macd_data'
    if os.path.isdir(macd_data_path):
        macd_files_list = os.listdir(macd_data_path)

    for file_name in macd_files_list:
        stock_data = pd.read_csv(macd_data_path + '/' + file_name)

        stock_data_length = stock_data.shape[0]
        if stock_data['macd_sum'][stock_data_length - 1] >= 2:
            buy_list.append(file_name.split('.')[0])
        if stock_data['macd_sum'][stock_data_length - 1] <= -1:
            sell_list.append(file_name.split('.')[0])

    with open('/Users/Richard/WorkSpace/finance/macd_data_ret.json', 'a') as f:
        result_list = {}
        result_list['data_time'] = str(datetime.datetime.now())
        result_list['buy_list'] = sorted(buy_list)
        result_list['sell_list'] = sorted(sell_list)
        f.write(json.dumps(result_list) + '\n')


if __name__ == '__main__':
    macd_data_ret()
