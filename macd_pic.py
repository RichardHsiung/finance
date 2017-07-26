
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
    stock_data.index = pd.to_datetime(stock_data.date)
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

            # Create empty data frame containing what will be plotted
            plotdat = pd.DataFrame({"open": [], "high": [], "low": [],
                                    "close": []})
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

        # Create empty data frame containing what will be plotted
        plotdat = pd.DataFrame(
            {"open": [], "high": [], "low": [], "close": []})

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

def get_moving_averages(code, start_time, end_time, autype):
    df = _get_stock_data(code, start_time, end_time, autype)
    df["5d"] = np.round(df["close"].rolling(window = 5, center = False).mean(), 2)
    df["10d"] = np.round(df["close"].rolling(window = 10, center = False).mean(), 2)
    df["20d"] = np.round(df["close"].rolling(window = 20, center = False).mean(), 2)
    df["60d"] = np.round(df["close"].rolling(window = 60, center = False).mean(), 2)
    df["120d"] = np.round(df["close"].rolling(window = 120, center = False).mean(), 2)

    pandas_candlestick_ohlc(df.loc[start_time:end_time,:],
                            otherseries=['5d','10d','20d','60d','120d'])


if __name__ == "__main__":
    start_time="2008-07-01"
    end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    autype = None
    code = sys.argv[1]
    mask = "000000"
    code = mask[len(code) - 1: -1] + code
    get_moving_averages(code, start_time, end_time, autype)
