import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
#import pandas.io.data as web   # Package and modules for importing data; this code may change depending on pandas version
from pandas_datareader import data as web   # Package and modules for importing data; this code may change depending on pandas version
import datetime


def get_usstock_data(code, start, end):
    # We will look at stock prices over the past year, starting at January 1, 2016
    # Let's get Apple stock data; Apple's ticker symbol is AAPL
    # First argument is the series we want, second is the source ("yahoo" for Yahoo! Finance), third is the start date, fourth is the end date
    stock_data = web.DataReader(code, "yahoo", start, end)
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

if __name__ == "__main__":
    start_time = datetime.datetime(2018, 1, 1)
    end_time = datetime.date.today()
    start="2018-01-01"
    end=datetime.datetime.now().strftime('%Y-%m-%d')
    code = "APPL"
    df = get_usstock_data(code, start_time, end_time)
    pandas_candlestick_ohlc(df.loc[start:end,:])