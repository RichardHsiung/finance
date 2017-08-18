
import sys
import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
import time

from matplotlib.pylab import date2num
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc

def _get_stock_data(code, start_time, end_time, autype):

    stock_data = ts.get_k_data(code, start=start_time, end=end_time, autype=autype)
    if type(stock_data) == "DataFrame" and not stock_data.empty:
        stock_data.index = pd.to_datetime(stock_data.date)
    return stock_data

def macd_buy_sell_count(stock_data):
    pass
    


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

    df = pd.read_csv('./stock_list.csv')

    start_time="2016-01-01"
    end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    #end_time = "2015-04-23"
    #autype = None  #默认不复权
    autype = 'qfq'  #默认不复权
    #code = sys.argv[1]
    #mask = "000000"
    #code = mask[len(code) - 1: -1] + code
    good_codes = []
    for code in df['code']:
        code = str(code)
        if macd_check(code, start_time, end_time, autype, 5, 60, 0.12, 0.98):
            good_codes.append(code)
    print(sorted(good_codes))
