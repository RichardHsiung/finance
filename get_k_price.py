#!/usr/bin/env python
#-*- coding:utf-8 -*-


import tushare as ts
import pandas as pd
import datetime
import numpy as np
import talib as ta
import multiprocessing
import time


def _get_k_data(code, start_time, end_time, autype):

    stock_data = ts.get_k_data(code, start=start_time, end=end_time, autype=autype)
    if type(stock_data) == "DataFrame" and not stock_data.empty:
        stock_data.index = pd.to_datetime(stock_data.date)
    return stock_data.loc[:, ('date', 'open', 'close', 'high', 'low')]


def check_stock_data(code, start_time, end_time, autype):
    
    stock_data = _get_k_data(code, start_time, end_time, autype)
    return stock_data


def stock_price_data(code_str):
    start_time = "2015-01-01"
    end_time = datetime.datetime.now().strftime('%Y-%m-%d')
    autype = "qfq"
    stock_data = check_stock_data(code_str, start_time, end_time, autype)
    try:
        stock_data.empty
    except AttributeError as e:
        print(code_str)
        print(e)
    stock_data.to_csv('./stock_price/' + code_str + '.csv')


def stock_price_data_pool():
    all_stock = pd.read_csv('./stock_list.csv')
    all_stock_code = all_stock['code']

    stock_pool = multiprocessing.Pool(processes=1)

    try:
        for code in all_stock_code:
            code_str = str(code).zfill(6)
            stock_pool.apply_async(stock_price_data, args=(code_str, )) # 维持执行的进程总数为processes，当一个进程执行完毕后会添加新的进程进去
        stock_pool.close()
        stock_pool.join()  # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束
    except Exception as e:
        print(code_str)
        print(e)


if __name__ == "__main__":
    stock_price_data_pool()

