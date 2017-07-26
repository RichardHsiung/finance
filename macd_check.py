
import sys
import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np

from matplotlib.pylab import date2num
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc

def _get_stock_data(code, start_time, end_time, autype):

    stock_data = ts.get_k_data(code, start=start_time, end=end_time, autype=autype)
    return stock_data


def macd_check(code, start_time, end_time, autype, short_day, long_day):
    sd = 0.05  #width of the region
    macd_all = _get_stock_data(code, start_time, end_time, autype)

    macd_all["short"] = np.round(macd_all["close"].rolling(window = int(short_day), center = False).mean(), 2)
    macd_all["long"] = np.round(macd_all["close"].rolling(window = int(long_day), center = False).mean(), 2)

    # s-l > long * sd  buy the stock
    macd_all["s-l"] = macd_all["short"] - macd_all["long"]
    macd_all['Regime'] = np.where(macd_all['s-l'] > macd_all["long"] * sd, 1, 0)
    print(macd_all['Regime'].value_counts())

    macd_all['Market'] = np.log(macd_all['close'] / macd_all['close'].shift(1))
    macd_all['Strategy'] = macd_all['Regime'].shift(1) * macd_all['Market']
    print(macd_all[['Market', 'Strategy', 'Regime']].tail())

    plt.rcParams['figure.figsize'] = (10, 6)  # Change the size of plots
    macd_all[['Market', 'Strategy']].cumsum().apply(np.exp).plot(grid=True)
    plt.show()

if __name__ == "__main__":
    start_time="2008-01-01"
    #end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    end_time = "2015-04-23"
    autype = None  #默认不复权
    code = sys.argv[1]
    mask = "000000"
    code = mask[len(code) - 1: -1] + code
    macd_check(code, start_time, end_time, autype, 20, 120)
