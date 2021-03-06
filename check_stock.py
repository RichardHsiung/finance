
import sys
import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
import talib as ta

from matplotlib.pylab import date2num
from multiprocessing import Pool
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc

def _get_stock_data(code, start_time, end_time, autype):

    stock_data = ts.get_k_data(code, start=start_time, end=end_time, autype=autype)
    stock_data.index = pd.to_datetime(stock_data.date)

    return stock_data.loc[:, ('open', 'close', 'high', 'low')]


def check_stock_data(code, start_time, end_time, operate_count, autype):

    success_count = 0
    failed_count = 0
    
    stock_data = _get_stock_data(code, start_time, end_time, autype)

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
            ma_len = stock_data_length
            
            # 在后面增加3列，分别是13-15列，对应的是 DIFF  DEA  DIFF-DEA
            # 2个数组
            # 1.DIFF、DEA均为正，DIFF向上突破DEA，买入信号。
            # 2.DIFF、DEA均为负，DIFF向下跌破DEA，卖出信号。
            if curdf.iat[(-1), macd_index] > 0:
                if (curdf.iat[(stock_data_length - 1), macd_signal_index] > 0 and
                            curdf.iat[(stock_data_length - 1), macd_index] > curdf.iat[(stock_data_length - 1), macd_signal_index] and
                            curdf.iat[(stock_data_length - 2), macd_index] <= curdf.iat[(stock_data_length - 2), macd_signal_index]):
                    operate = operate + 1
                    stock_data['macd_diff_dea'][stock_data_length - 1] = 1
            else:
                if (curdf.iat[(stock_data_length - 1), macd_signal_index] < 0 and
                            curdf.iat[(stock_data_length - 1), macd_index] == curdf.iat[(stock_data_length-2), macd_signal_index]):
                    operate = operate - 1
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
                        operate += 1
                        stock_data['macd_macd_self'][stock_data_length - 1] = 1
                        break
            # 由正变负，卖出信号
            if curdf.iat[(stock_data_length-1), macd_hist_index] < 0 and stock_data_length > 30 :
                for i in range(1, 26):
                    if curdf.iat[(stock_data_length - 1 - i), macd_hist_index] >= 0:#
                        operate += -1
                        stock_data['macd_macd_self'][stock_data_length - 1] = -1
                        break
                    
            stock_data['macd_sum'][stock_data_length - 1] = operate
        if stock_data['macd_sum'][stock_data_length - 1] >= operate_count:
            return code
        else:
            return


if __name__ == "__main__":
    start_time="2015-07-01"
    end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    all_stock = pd.read_csv('./stock_list.csv')
    all_stock = all_stock['code']
    autype = "qfq"

    operate_list = []
    calculate_rate = 0
    for code in all_stock:
        if calculate_rate % 5 == 0:
            sys.stdout.write('#')
            sys.stdout.flush()
        operate_list.append(check_stock_data(str(code), start_time, end_time, 2, autype))
        calculate_rate += 1
    print(operate_list)

