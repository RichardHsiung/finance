
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

def _get_stock_data(code, start_time, end_time):

    stock_data = ts.get_hist_data(code, start=start_time, end=end_time)
    stock_data = stock_data.sort_index(0)
    tmplist = []
    for onetime in stock_data.index:
        tmplist.append(datetime.datetime.strptime(onetime, '%Y-%m-%d'))
    stock_data.index = tmplist
    return stock_data


def check_stock_data(code, start_time, end_time):

    print("check_stock_data")
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


def check_stock_now(code, start_time, end_time):

    print("check_stock_now")
    operate = 0
    last_operate = 0

    stock_data = _get_stock_data(code, start_time, end_time)
    stock_data_length = stock_data.shape[0]

    if stock_data_length > 35:
        stock_data['macd_diff_dea'] = pd.Series()
        stock_data['macd_dea_k'] = pd.Series()
        stock_data['macd_macd_self'] = pd.Series()
        stock_data['macd_sum'] = pd.Series()
        stock_data['macd_result'] = pd.Series()
        curdf = pd.DataFrame(stock_data[:stock_data_length])
        macd, macd_signal, macd_hist = ta.MACD(np.array(stock_data['close']), fastperiod=12, slowperiod=26,
                                               signalperiod=9)

        signal_ma5 = ta.MA(macd_signal, timeperiod=5, matype=0)
        signal_ma10 = ta.MA(macd_signal, timeperiod=10, matype=0)
        signal_ma20 = ta.MA(macd_signal, timeperiod=20, matype=0)


        # 在后面增加3列，分别是13-15列，对应的是 DIFF  DEA  DIFF-DEA
        stock_data['macd'] = pd.Series(macd, index = curdf.index)  # DIFF
        stock_data['macd_signal'] = pd.Series(macd_signal, index = curdf.index)  # DEA
        stock_data['macd_hist'] = pd.Series(macd_hist, index = curdf.index)  # DIFF-DEA

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


def check_stock_now_in_thread(code):

    start_time = "2015-07-01"
    end_time = datetime.datetime.now().strftime('%Y-%m-%d')

    index = code
    code_str = str(code).zfill(6)
    operate, last_operate = check_stock_now(code_str, start_time, end_time)
    print(code_str, ': ', operate, ' ', last_operate)
    # success_count = 0
    # failed_count = 0
    # if last_operate != 0:
    #success_count, failed_count = check_stock_data(code_str, start_time, end_time)

    # return index, code_str, success_count, failed_count


def check_now(thread_pool_size):
    all_stock = pd.read_csv('./stock_list.csv')
    all_stock = all_stock['code']
    # pool = Pool(thread_pool_size)
    # results = pool.map(check_stock_now_in_thread, all_stock)
    # pool.close()
    # pool.join()

    for index in all_stock:
        check_stock_now_in_thread(index)
        #index, code_str, success_count, failed_count = check_stock_now_in_thread(index)
        #print(code_str, ': ', success_count, ' ', failed_count )
        # all_stock.loc[index, 'macd_success'] = success_count
        # all_stock.loc[index, 'macd_fail'] = failed_count
        # if (success_count > 3) and (failed_count == 0):
        #     # print('%s operate=%s last_operate=%s' % (code_str, operate, last_operate))
        #     print('success_count=%s failed_count=%s' % (success_count, failed_count))


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

#    macddata = all_stock[all_stock.last_operate != 0].sort_values('macd_success', 0, False)
#    macddata.to_csv('./output/macd/day/' + datetime.date.today().strftime('%Y-%m-%d') + '.csv')


if __name__ == "__main__":
    start_time="2015-07-01"
    end_time=datetime.datetime.now().strftime('%Y-%m-%d')
    code = sys.argv[1]
    mask = "000000"
    code = mask[len(code) - 1: -1] + code
    #check_stock_data(code, start_time, end_time)
    #check_now(1)

