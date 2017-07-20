
import sys
import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
import talib as ta

from matplotlib.pylab import date2num
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from pandas_datareader import data as web   # Package and modules for importing data; this code may change depending on pandas version

from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc

def _get_stock_data(code, start_time, end_time):
    stock_data = ts.get_hist_data(code, start=start_time, end=end_time)
    stock_data = stock_data.sort_index(0)
    tmplist = []
    for onetime in stock_data.index:
        tmplist.append(datetime.datetime.strptime(onetime, '%Y-%m-%d'))
    stock_data.index = tmplist
    return stock_data


def pandas_candlestick_ohlc(dat, stick="day", otherseries=None):
    """
    :param dat: pandas DataFrame object with datetime64 index,
                and float columns "Open", "High", "Low", and "Close",
                likely created via DataReader from "yahoo"
    :param stick: A string or number indicating the period of
                  time covered by a single candlestick. Valid
                  string inputs include "day", "week", "month",
                  and "year", ("day" default),and any numeric
                  input indicates the number of trading days
                  included in a period.
    :param otherseries: An iterable that will be coerced into
                        a list, containing the columns of dat
                        that hold other series to be plotted
                        as lines.

    This will show a Japanese candlestick plot for stock data
    stored in dat, also plotting other series if passed.
    """
    mondays = WeekdayLocator(MONDAY)  # major ticks on the mondays
    alldays = DayLocator()  # minor ticks on the days
    dayFormatter = DateFormatter('%d')  # e.g., 12

    # Create a new DataFrame which includes OHLC data for each
    # period specified by stick input
    transdat = dat.loc[:, ["open", "high", "low", "close"]]
    if (type(stick) == str):
        if stick == "day":
            plotdat = transdat
            stick = 1  # Used for plotting
        elif stick in ["week", "month", "year"]:
            if stick == "week":
                transdat["week"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[1])  # Identify weeks
            elif stick == "month":
                transdat["month"] = pd.to_datetime(transdat.index).map(lambda x: x.month)  # Identify months
            transdat["year"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[0])  # Identify years
            grouped = transdat.groupby(list(set(["year", stick])))  # Group by year and other appropriate variable
            plotdat = pd.DataFrame({"open": [], "high": [], "low": [],
                                    "close": []})  # Create empty data frame containing what will be plotted
            for name, group in grouped:
                plotdat = plotdat.append(pd.DataFrame({"open": group.iloc[0, 0],
                                                       "high": max(group.High),
                                                       "low": min(group.Low),
                                                       "close": group.iloc[-1, 3]},
                                                      index=[group.index[0]]))
            if stick == "week":
                stick = 5
            elif stick == "month":
                stick = 30
            elif stick == "year":
                stick = 365

    elif (type(stick) == int and stick >= 1):
        transdat["stick"] = [np.floor(i / stick) for i in range(len(transdat.index))]
        grouped = transdat.groupby("stick")
        plotdat = pd.DataFrame(
            {"open": [], "high": [], "low": [], "close": []})  # Create empty data frame containing what will be plotted
        for name, group in grouped:
            plotdat = plotdat.append(pd.DataFrame({"open": group.iloc[0, 0],
                                                   "high": max(group.High),
                                                   "low": min(group.Low),
                                                   "close": group.iloc[-1, 3]},
                                                  index=[group.index[0]]))

    else:
        raise ValueError(
            'Valid inputs to argument "stick" include the strings "day", "week", "month", "year", or a positive integer')

    # Set plot parameters, including the axis object ax used for plotting
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)

    if plotdat.index[-1] - plotdat.index[0] < pd.Timedelta('730 days'):
        weekFormatter = DateFormatter('%b %d')  # e.g., Jan 12
        ax.xaxis.set_major_locator(mondays)
        ax.xaxis.set_minor_locator(alldays)
    else:
        weekFormatter = DateFormatter('%b %d, %Y')
    ax.xaxis.set_major_formatter(weekFormatter)

    ax.grid(True)

    # Create the candelstick chart
    candlestick_ohlc(ax, list(
        zip(list(date2num(plotdat.index.tolist())), plotdat["open"].tolist(), plotdat["high"].tolist(),
            plotdat["low"].tolist(), plotdat["close"].tolist())), colorup="red", colordown="black", width=stick * .4)

    # Plot other series (such as moving averages) as lines
    if otherseries != None:
        if type(otherseries) != list:
            otherseries = [otherseries]
        dat.loc[:, otherseries].plot(ax=ax, lw=1.3, grid=True)

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

    plt.show()

def get_moving_averages(code, start_time, end_time):
    df = _get_stock_data(code, start_time, end_time)
    df["5d"] = np.round(df["close"].rolling(window = 5, center = False).mean(), 2)
    df["10d"] = np.round(df["close"].rolling(window = 10, center = False).mean(), 2)
    df["20d"] = np.round(df["close"].rolling(window = 20, center = False).mean(), 2)
    df["60d"] = np.round(df["close"].rolling(window = 60, center = False).mean(), 2)
    df["120d"] = np.round(df["close"].rolling(window = 120, center = False).mean(), 2)
    df["240d"] = np.round(df["close"].rolling(window=240, center=False).mean(), 2)

    pandas_candlestick_ohlc(df.loc[start_time:end_time,:],
                            otherseries=['5d','10d','20d','60d','120d','240d'])
    

def get_macd(code, start_time, end_time):
    stock_data = _get_stock_data(code, start_time, end_time)
    stock_data_length = stock_data.shape[0]

    if stock_data_length > 35:
        stock_data['macd_diff_dea'] = pd.Series()
        stock_data['macd_dea_k'] = pd.Series()
        stock_data['macd_macd_self'] = pd.Series()
        stock_data['macd_sum'] = pd.Series()
        curdf = pd.DataFrame(stock_data[:stock_data_length])
        macd, macd_signal, macd_hist = ta.MACD(np.array(curdf['close']), 
                                     fastperiod = 12, slowperiod = 26, signalperiod = 9)

        signal_ma5 = ta.MA(macdsignal, timeperiod = 5, matype = 0)
        signal_ma10 = ta.MA(macdsignal, timeperiod = 10, matype = 0)
        signal_ma20 = ta.MA(macdsignal, timeperiod = 20, matype = 0)

        # 在后面增加3列，分别是13-15列，对应的是 DIFF  DEA  DIFF-DEA
        macd_index = stock_data.shape[1]
        curdf['macd'] = pd.Series(macd, index = curdf.index)  # DIFF
        macdsignal_index = stock_data.shape[1]
        curdf['macd_signal'] = pd.Series(macd_signal, index = curdf.index)  # DEA
        macdhist_index = stock_data.shape[1]
        curdf['macd_hist'] = pd.Series(macd_hist, index = curdf.index)  # DIFF-DEA
        ma_len = len(signal_ma5)
        
        if (stock_data.iat[(stock_data_length - 1), 13] > 0 and 
           stock_data.iat[(stock_data_length - 1), 14] > 0 and
           stock_data.iat[(stock_data_length - 1), 13] > stock_data.iat[( stock_data_length - 1), 14]):
            operate = operate + 1 #买入
        elif (stock_data.iat[(stock_data_length - 1), 14] < 0 and
             stock_data.iat[(stock_data_length - 1), 13] < 0 and
             stock_data.iat[(stock_data_length - 1), 13] < stock_data.iat[(stock_data_length - 1), 14]):
            operate = operate - 1 #卖出
        
        if (stock_data.iat[(stock_data_length - 1), 7] >= stock_data.iat[(stock_data_length - 1), 8] and 
           stock_data.iat[(stock_data_length - 1), 8] >= stock_data.iat[(stock_data_length - 1), 9] and #k线上涨 
           signal_ma5[ma_len - 1] <= signal_ma10[ma_len - 1] and signal_ma10[ma_len - 1] <= signal_ma20[ma_len-1]): #DEA下降
            operate = operate - 1
        elif (stock_data.iat[(stock_data_length - 1), 7] <= stock_data.iat[(stock_data_length - 1), 8] and
             stock_data.iat[(stock_data_length - 1), 8] <= stock_data.iat[(stock_data_length - 1), 9] and #k线下降
             signal_ma5[ma_len - 1] >= signal_ma10[ma_len - 1] and signal_ma10[ma_len - 1] >= signal_ma20[ma_len - 1]): #DEA上涨
             operate = operate + 1
            

if __name__ == "__main__":
    start_time="2015-07-01"
    end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    code = sys.argv[1]
    mask = "000000"
    code = mask[len(code) - 1: -1] + code
    get_macd(code, start_time, end_time)
    #getMovingAverages(code, start_time, end_time)
