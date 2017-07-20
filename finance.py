
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

    pandas_candlestick_ohlc(df.loc[start_time:end_time,:],
                            otherseries=['5d','10d','20d','60d','120d'])


def check_stock_data(code, start_time, end_time):

    success_count = 0
    failed_count = 0
    
    stock_data = _get_stock_data(code, start_time, end_time)
    stock_data_length = stock_data.shape[0]

    if stock_data_length > 35:
        last_operator_price_close = 0
        last_operator = 0
        stock_data['macd_diff_dea'] = pd.Series()
        stock_data['macd_dea_k'] = pd.Series()
        stock_data['macd_macd_self'] = pd.Series()
        stock_data['macd_sum'] = pd.Series()
        stock_data['macd_result'] = pd.Series()

        macd, macd_signal, macd_hist = ta.MACD(np.array(stock_data['close']), fastperiod = 12, slowperiod = 26, signalperiod = 9)

        macd_index = stock_data.shape[1]
        stock_data['macd'] = pd.Series(macd, index = stock_data.index) #DIFF
        macd_signal_index = stock_data.shape[1]
        stock_data['macd_signal'] = pd.Series(macd_signal, index = stock_data.index)#DEA
        macd_hist_index = stock_data.shape[1]
        stock_data['macd_hist'] = pd.Series(macd_hist, index = stock_data.index)#DIFF-DEA

        signal_ma5 = ta.MA(macd_signal, timeperiod = 5, matype = 0)
        signal_ma10 = ta.MA(macd_signal, timeperiod = 10, matype = 0)
        signal_ma20 = ta.MA(macd_signal, timeperiod = 20, matype = 0)

        for stock_data_length in range(36, stock_data.shape[0] + 1):
            curdf = pd.DataFrame(stock_data[:stock_data_length])
            operate = 0
            
            # 在后面增加3列，分别是13-15列，对应的是 DIFF  DEA  DIFF-DEA
            ma_len = stock_data_length
            # 2个数组
            # 1.DIFF、DEA均为正，DIFF向上突破DEA，买入信号。
            # 2.DIFF、DEA均为负，DIFF向下跌破DEA，卖出信号。
            # 待修改
            if curdf.iat[(-1), macd_index] > 0:
                if (curdf.iat[(stock_data_length - 1), macd_signal_index] > 0 and
                            curdf.iat[(stock_data_length - 1), macd_index] > curdf.iat[(stock_data_length - 1), macd_signal_index] and
                            curdf.iat[(stock_data_length - 2), macd_index] <= curdf.iat[(stock_data_length - 2), macd_signal_index]):
                    # operate = operate + 10#买入
                    stock_data['macd_diff_dea'][stock_data_length - 1] = 1
            else:
                if (curdf.iat[(stock_data_length - 1), macd_signal_index] < 0 and
                            curdf.iat[(stock_data_length - 1), macd_index] == curdf.iat[(stock_data_length-2), macd_signal_index]):
                    # operate = operate - 10#卖出
                    stock_data['macd_diff_dea'][stock_data_length - 1] = -1
            
            # 3.DEA线与K线发生背离，行情反转信号。
            if (curdf.iat[(stock_data_length - 1), 7] >= curdf.iat[(stock_data_length - 1), 8] and
                        curdf.iat[(stock_data_length-1), 8] >= curdf.iat[(stock_data_length-1),9]):#K线上涨
                if signal_ma5[ma_len - 1] <= signal_ma10[ma_len - 1] <= signal_ma20[ma_len - 1]: #DEA下降
                    operate += - 1
                    stock_data['macd_dea_k'][stock_data_length - 1] = 1
            elif (curdf.iat[(stock_data_length - 1), 7] <= curdf.iat[(stock_data_length - 1), 8] and
                          curdf.iat[(stock_data_length-1), 8] <= curdf.iat[(stock_data_length - 1), 9]):#K线下降
                if signal_ma5[ma_len - 1] >= signal_ma10[ma_len - 1] >= signal_ma20[ma_len - 1]: #DEA上涨
                    operate += 1
                    stock_data['macd_dea_k'][stock_data_length - 1] = -1
                       
               
            # 4.分析MACD柱状线，
            # 由负变正，买入信号。
            if curdf.iat[(stock_data_length - 1), macd_hist_index] > 0 and stock_data_length > 30 :
                for i in range(1, 26):
                    if curdf.iat[(stock_data_length - 1 - i), macd_hist_index] <= 0:
                        # operate += 5
                        stock_data['macd_macd_self'][stock_data_length - 1] = 1
                        break
            # 由正变负，卖出信号
            if curdf.iat[(stock_data_length-1), macd_hist_index] < 0 and stock_data_length > 30 :
                for i in range(1, 26):
                    if curdf.iat[(stock_data_length - 1 - i), macd_hist_index] >= 0:#
                        # operate += -5
                        stock_data['macd_macd_self'][stock_data_length - 1] = -1
                        break
                    
            if operate != 0:
                stock_data['macd_sum'][stock_data_length - 1] = operate
            
            if operate == 0:
                continue
            cur_operator_price_close = curdf['close'][stock_data_length - 1]
            if last_operator * operate > 0:
                continue
#            print code, name, 'operate=', operate, '  last_operator=', last_operator,
#            print '   cur_operator_price_close=', cur_operator_price_close,
#            print '   last_operator_price_close=', last_operator_price_close
            if operate > 0:
                # print 'operate=买入 price=',cur_operator_price_close
                pass
            else:
                #                print 'operate=卖出 ',
                #                print '   success=', (cur_operator_price_close > last_operator_price_close)
                #                print '   curprice=',cur_operator_price_close,
                #                print '   last_operator_price_close=', last_operator_price_close
                if last_operator_price_close != 0:
                    if cur_operator_price_close > last_operator_price_close:
                        success_count += 1
                        stock_data['macd_result'][stock_data_length - 1] = 1
                    else:
                        failed_count += 1
                        stock_data['macd_result'][stock_data_length - 1] = -1
                
            last_operator = operate
            last_operator_price_close = cur_operator_price_close
    stock_data.to_csv('./macd/' + code + '.csv')
    return success_count, failed_count


def check_stock_now(code, name):
    operate = 0
    last_operate = 0

    stock_data = _get_stock_data(code, start_time, end_time)
    stock_data_length = stock_data.shape[0]

    if stock_data_length > 35:
        last_operator_price_close = 0
        last_operator = 0
        stock_data['macd_diff_dea'] = pd.Series()
        stock_data['macd_dea_k'] = pd.Series()
        stock_data['macd_macd_self'] = pd.Series()
        stock_data['macd_sum'] = pd.Series()
        stock_data['macd_result'] = pd.Series()
        curdf = pd.DataFrame(stock_data[:stock_data_length])
        macd, macd_signal, macd_hist = ta.MACD(np.array(stock_data['close']), fastperiod=12, slowperiod=26,
                                               signalperiod=9)

        macd_index = stock_data.shape[1]
        stock_data['macd'] = pd.Series(macd, index=stock_data.index)  # DIFF
        macd_signal_index = stock_data.shape[1]
        stock_data['macd_signal'] = pd.Series(macd_signal, index=stock_data.index)  # DEA
        macd_hist_index = stock_data.shape[1]
        stock_data['macd_hist'] = pd.Series(macd_hist, index=stock_data.index)  # DIFF-DEA

        signal_ma5 = ta.MA(macd_signal, timeperiod=5, matype=0)
        signal_ma10 = ta.MA(macd_signal, timeperiod=10, matype=0)
        signal_ma20 = ta.MA(macd_signal, timeperiod=20, matype=0)


        # 在后面增加3列，分别是13-15列，对应的是 DIFF  DEA  DIFF-DEA
        ma_len = stock_data_length


        # 3.DEA线与K线发生背离，行情反转信号。
        if curdf.iat[(stock_data_length - 1), 7] >= curdf.iat[(stock_data_length - 1), 8] >= curdf.iat[(stock_data_length - 1), 9]:  # K线上涨
            if signal_ma5[ma_len - 1] <= signal_ma10[ma_len - 1] <= signal_ma20[ma_len - 1]:  # DEA下降
                operate += - 1
                stock_data['macd_dea_k'][stock_data_length - 1] = 1
        elif curdf.iat[(stock_data_length - 1), 7] <= curdf.iat[(stock_data_length - 1), 8] <= curdf.iat[(stock_data_length - 1), 9]:  # K线下降
            if signal_ma5[ma_len - 1] >= signal_ma10[ma_len - 1] >= signal_ma20[ma_len - 1]:  # DEA上涨
                operate += 1
                stock_data['macd_dea_k'][stock_data_length - 1] = -1

        last_operate = operate
        if operate == 0:
#            print code, '=', name, 'operate=0'
            for stock_data_length in range(36, stock_data_length - 1)[::-1]:
#                print dflen
                if curdf.iat[(stock_data_length - 1), 7] >= curdf.iat[(stock_data_length - 1), 8] >= curdf.iat[(stock_data_length - 1),9]:#K线上涨
                    if signal_ma5[stock_data_length - 1] <= signal_ma10[stock_data_length - 1] <= signal_ma20[stock_data_length - 1]: #DEA下降
                        last_operate = -1
                        stock_data['macd_dea_k'][stock_data_length - 1] = 1
                elif curdf.iat[(stock_data_length - 1), 7] <= curdf.iat[(stock_data_length - 1), 8] <= curdf.iat[(stock_data_length - 1),9]:#K线下降
                    if signal_ma5[stock_data_length - 1] >= signal_ma10[stock_data_length - 1] >= signal_ma20[stock_data_length - 1]: #DEA上涨
                        last_operate = 1
                        stock_data['macd_dea_k'][stock_data_length - 1] = -1
                if last_operate != 0:
                   break

        stock_data['macd_sum'][stock_data_length - 1] = operate

    return operate, last_operate


def check_stock_now_in_thread((index, row)):

    code = index
    name = row['name']
    code_str = str(code).zfill(6)
#    print code_str, '=', name
    operate, last_operate = check_stock_now(code, start_time, end_time)
    success_count = 0
    failed_count = 0
    if last_operate != 0:
        success_count,failed_count = check_stock_data(code, start_time, end_time)

    return index, code_str, name, operate, last_operate, success_count, failed_count

def chec_now():
    all_stock = getAllStock()

    pool = Pool(THREAD_POOL_SIZE)
    results = pool.map(checkStockNowInThread, all_stock.iterrows())
    pool.close()
    pool.join()

    for index,code_str,name,operate,last_operate,success_count,failed_count in results:
#        print index, success_count, failed_count
        all_stock.loc[index, 'operate'] = operate
        all_stock.loc[index, 'last_operate'] = last_operate
#        if (last_operate != 0):
        if True:
            all_stock.loc[index, 'macd_success'] = success_count
            all_stock.loc[index, 'macd_fail'] = failed_count
            if (success_count > 3) and (failed_count == 0):
                print code_str, name, '  operate=', operate,'  last_operate=', last_operate,
                print '  success_count=', success_count,'  failed_count=', failed_count


#    for index,row in all_stock.iterrows():
#        code = index
#        name = row['name']
#        code_str = str(code).zfill(6)
#        print code_str, '=', name
#        operate = check_stock_now(code_str, name)
#        all_stock.loc[index, 'operate'] = operate
#        if operate != 0:
#            success_count,failed_count = check_stock(code_str, name)
#            all_stock.loc[index, 'macd_success'] = success_count
#            all_stock.loc[index, 'macd_fail'] = failed_count
#            if (success_count >= 4):
#                print code_str, name, '  operate=', operate,
#                print '  success_count=', success_count,'  failed_count=', failed_count

    macddata = all_stock[all_stock.last_operate != 0].sort_values('macd_success', 0, False)
    macddata.to_csv('./output/macd/day/' + datetime.date.today().strftime('%Y-%m-%d') + '.csv')


if __name__ == "__main__":
    start_time="2015-07-01"
    end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    code = sys.argv[1]
    mask = "000000"
    code = mask[len(code) - 1: -1] + code
    #get_macd(code, start_time, end_time)
    #get_moving_averages(code, start_time, end_time)
    print(check_stock_data(code, start_time, end_time))

