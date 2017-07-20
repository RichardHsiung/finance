import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np

from matplotlib.pylab import date2num
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from pandas_datareader import data as web   # Package and modules for importing data; this code may change depending on pandas version

from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc



def pandas_candlestick_ohlc(dat, stick = "day", otherseries = None):
    """
    :param dat: pandas DataFrame object with datetime64 index, 
                and float columns "Open", "High", "Low", and "Close", 
                likely created via DataReader from "yahoo"
    :param stick: A string or number indicating the period of time covered by a single candlestick. 
                  Valid string inputs include "day", "week", "month", and "year", ("day" default), 
                  and any numeric input indicates the number of trading days included in a period
    :param otherseries: An iterable that will be coerced into a list, 
                        containing the columns of dat that hold other series to be plotted as lines

    This will show a Japanese candlestick plot for stock data stored in dat, also plotting other series if passed.
    """
    mondays = WeekdayLocator(MONDAY)        # major ticks on the mondays
    alldays = DayLocator()              # minor ticks on the days
    dayFormatter = DateFormatter('%d')      # e.g., 12

    # Create a new DataFrame which includes OHLC data for each period specified by stick input
    transdat = dat.loc[:,["open", "high", "low", "close"]]
    if (type(stick) == str):
        if stick == "day":
            plotdat = transdat
            stick = 1 # Used for plotting
        elif stick in ["week", "month", "year"]:
            if stick == "week":
                transdat["week"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[1]) # Identify weeks
            elif stick == "month":
                transdat["month"] = pd.to_datetime(transdat.index).map(lambda x: x.month) # Identify months
            transdat["year"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[0]) # Identify years
            grouped = transdat.groupby(list(set(["year",stick]))) # Group by year and other appropriate variable
            plotdat = pd.DataFrame({"open": [], "high": [], "low": [], "close": []}) # Create empty data frame containing what will be plotted
            for name, group in grouped:
                plotdat = plotdat.append(pd.DataFrame({"open": group.iloc[0,0],
                                            "high": max(group.High),
                                            "low": min(group.Low),
                                            "close": group.iloc[-1,3]},
                                           index = [group.index[0]]))
            if stick == "week": stick = 5
            elif stick == "month": stick = 30
            elif stick == "year": stick = 365

    elif (type(stick) == int and stick >= 1):
        transdat["stick"] = [np.floor(i / stick) for i in range(len(transdat.index))]
        grouped = transdat.groupby("stick")
        plotdat = pd.DataFrame({"open": [], "high": [], "low": [], "close": []}) # Create empty data frame containing what will be plotted
        for name, group in grouped:
            plotdat = plotdat.append(pd.DataFrame({"open": group.iloc[0,0],
                                        "high": max(group.High),
                                        "low": min(group.Low),
                                        "close": group.iloc[-1,3]},
                                       index = [group.index[0]]))

    else:
        raise ValueError('Valid inputs to argument "stick" include the strings "day", "week", "month", "year", or a positive integer')


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
    candlestick_ohlc(ax, list(zip(list(date2num(plotdat.index.tolist())), plotdat["open"].tolist(), plotdat["high"].tolist(), plotdat["low"].tolist(), plotdat["close"].tolist())), colorup = "black", colordown = "red", width = stick * .4)

    # Plot other series (such as moving averages) as lines
    if otherseries != None:
        if type(otherseries) != list:
            otherseries = [otherseries]
        dat.loc[:,otherseries].plot(ax = ax, lw = 1.3, grid = True)

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

    plt.show()


def _candlestick(ax, df, width=0.2, colorup='k', colordown='r', alpha=1.0):

    """
    Plot the time, open, high, low, close as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    df : pandas data from tushare
    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level
    ochl: bool
        argument to select between ochl and ohlc ordering of quotes

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """

    OFFSET = width / 2.0

    lines = []
    patches = []
    for date_string,row in df.iterrows():
        date_time = datetime.datetime.strptime(date_string,'%Y-%m-%d')
        t = date2num(date_time)
        open, high, close, low = row[:4]

        if close >= open:
            color = colorup
            lower = open
            height = close - open
        else:
            color = colordown
            lower = close
            height = open - close

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color=color,
            linewidth=0.5,
            antialiased=True,
        )

        rect = Rectangle(
            xy=(t - OFFSET, lower),
            width=width,
            height=height,
            facecolor=color,
            edgecolor=color,
        )
        rect.set_alpha(alpha)

        lines.append(vline)
        patches.append(rect)
        ax.add_line(vline)
        ax.add_patch(rect)
    ax.autoscale_view()

    return lines, patches


def drawPic(df, code, name):
    mondays = WeekdayLocator(MONDAY)            # 主要刻度
    alldays = DayLocator()                      # 次要刻度
    #weekFormatter = DateFormatter('%b %d')     # 如：Jan 12
    mondayFormatter = DateFormatter('%m-%d-%Y') # 如：2-29-2015
    dayFormatter = DateFormatter('%d')          # 如：12
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    ax.xaxis.set_major_locator(mondays)
    ax.xaxis.set_minor_locator(alldays)
    ax.xaxis.set_major_formatter(mondayFormatter)

    _candlestick(ax, df, width=0.6, colorup='r', colordown='g')

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')


    ax.grid(True)
    #plt.title(name + '  ' + code, fontproperties=zhfont)
    plt.title(name + '  ' + code)
    plt.show()


def getSinglePic(code, start_time, end_time, single_name="close"):
    df = ts.get_hist_data(code, start=start_time, end=end_time)
    df = df.sort_index(0)
    plt.rcParams['figure.figsize'] = (15, 9)
    df[single_name].plot(grid=True)
    plt.show()
    

def makePicture(code, name):
    begin_time="2016-12-1"
    end_time="2017-7-1"
    df = ts.get_hist_data(code, start=begin_time, end=end_time)
    df = df.sort_index(0)
    drawPic(df, code, name)

def getReturnPercent():
    begin_time="2016-12-1"
    end_time="2017-7-1"
    stock_dict = {"600848":"", "600300":"", "600200":""}
    for key in stock_dict.keys():
        tmp = ts.get_hist_data(key, start=begin_time, end=end_time)
        tmp = tmp.sort_index(0)
        stock_dict[key] = tmp['close']
    stocks = pd.DataFrame(stock_dict)
    stock_return = stocks.apply(lambda x: x/x[0])
    plt.rcParams['figure.figsize'] = (15, 9)
    stock_return.plot(grid=True).axhline(y = 1, color = "black", lw = 2)
    plt.show()


def getLogPic():
    begin_time="2016-12-1"
    end_time="2017-7-1"
    stock_dict = {"600848":"", "600300":"", "600200":""}
    for key in stock_dict.keys():
        tmp = ts.get_hist_data(key, start=begin_time, end=end_time)
        tmp = tmp.sort_index(0)
        stock_dict[key] = tmp['close']
    stocks = pd.DataFrame(stock_dict)
    stock_change = stocks.apply(lambda x: np.log(x) - np.log(x.shift(1)))
    plt.rcParams['figure.figsize'] = (15, 9)
    stock_change.plot(grid=True).axhline(y = 0, color = "black", lw = 2)
    plt.show()


def getMovingAverages(code, start_time, end_time):
    df = ts.get_hist_data(code, start=start_time, end=end_time)
    df = df.sort_index(0)
    df["5d"] = np.round(df["close"].rolling(window = 5, center = False).mean(), 2)
    df["20d"] = np.round(df["close"].rolling(window = 20, center = False).mean(), 2)
    df["20d"] = np.round(df["close"].rolling(window = 20, center = False).mean(), 2)
    df["40d"] = np.round(df["close"].rolling(window = 40, center = False).mean(), 2)
    df["200d"] = np.round(df["close"].rolling(window = 200, center = False).mean(), 2)
    tmplist = []
    for onetime in df.index:
        tmplist.append(datetime.datetime.strptime(onetime, '%Y-%m-%d'))
    df.index = tmplist
    pandas_candlestick_ohlc(df.loc[start_time:end_time,:], otherseries=['5d','20d','40d','200d'])

def getDiff5_20Day(code, start_time, end_time):
    df = ts.get_hist_data(code, start=start_time, end=end_time)
    df = df.sort_index(0)
    df["5d"] = np.round(df["close"].rolling(window = 5, center = False).mean(), 2)
    df["20d"] = np.round(df["close"].rolling(window = 20, center = False).mean(), 2)
    df['d5-20'] = df['5d'] - df ['20d']
    df['diff'] = np.sign(df['d5-20'])

    plt.rcParams['figure.figsize'] = (10, 6)   # Change the size of plots
    df['diff'].plot(ylim=(-2,2)).axhline(y=0, color='black', lw=2)
    plt.show()
   
def getSingal(code, start_time, end_time):
    df = ts.get_hist_data(code, start=start_time, end=end_time)
    df = df.sort_index(0)
    df["5d"] = np.round(df["close"].rolling(window = 5, center = False).mean(), 2)
    df["20d"] = np.round(df["close"].rolling(window = 20, center = False).mean(), 2)
    df['d5-20'] = df['5d'] - df ['20d']
    df['diff'] = np.sign(df['d5-20'])

    df['signal'] = np.sign(df['diff'] - df['diff'].shift(1))
    plt.rcParams['figure.figsize'] = (10, 6)   # Change the size of plots
    df['signal'].plot(ylim=(-2,2))
    plt.show()

def getBuyAndSell(code, start_time, end_time):
    df = ts.get_hist_data(code, start=start_time, end=end_time)
    df = df.sort_index(0)
    df["5d"] = np.round(df["close"].rolling(window = 5, center = False).mean(), 2)
    df["40d"] = np.round(df["close"].rolling(window = 40, center = False).mean(), 2)
    df['d5-40'] = df['5d'] - df ['40d']
    df['diff'] = np.sign(df['d5-40'])

    df['signal'] = np.sign(df['diff'] - df['diff'].shift(1))
    trade = pd.concat([
    pd.DataFrame({"price": df.loc[df["signal"] == 1, "close"],
                  "operation": "Buy"}),
    pd.DataFrame({"price": df.loc[df["signal"] == -1, "close"],
                  "operation": "Sell"})    
    ])
 
    trade.sort_index(inplace=True)
    print(trade)


if __name__ == "__main__":
    start_time="2015-01-01"
    end_time="2017-07-01"
    code = "000008"
    #getSinglePic("600200",start_time, end_time)
    #makePicture("600200", "nihao")
    #getReturnPercent()
    #getLogPic()
    getMovingAverages(code, start_time, end_time)
    #getDiff5_20Day(code, start_time, end_time)
    #getSingal(code, start_time, end_time)
    #getBuyAndSell(code, start_time, end_time)
