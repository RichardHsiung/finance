from CAL.PyCAL import Date
from CAL.PyCAL import Calendar
from CAL.PyCAL import BizDayConvention
start = '2015-01-01'                       # 回测起始时间
end = '2017-07-01'                         # 回测结束时间
benchmark = 'HS300'                        # 策略参考标准
universe = set_universe('HS300')           # 证券池，支持股票和基金
capital_base = 100000                      # 起始资金
freq = 'd'                                 # 策略类型，'d'表示日间策略使用日线回测，'m'表示日内策略使用分钟线回测
refresh_rate = 1                           # 调仓频率，表示执行handle_data的时间间隔，若freq = 'd'时间间隔的单位为交易日，若freq = 'm'时间间隔为分钟
commission = Commission(buycost=0.0003, sellcost=0.002, unit='perValue')

def initialize(account):                   # 初始化虚拟账户状态
    pass

def handle_data(account):                  # 每个交易日的买入卖出指令
    buylist=[]
    selist=[]
    dt = Date.fromDateTime(account.current_date) 
    cal = Calendar('China.SSE')
    lastTDay = cal.advanceDate(dt,'-1B',BizDayConvention.Preceding)
    current_date=dt.strftime('%Y%m%d')
    last_date=lastTDay.strftime('%Y%m%d')
    
    getData_current_date=DataAPI.MktStockFactorsOneDayGet(tradeDate=current_date,secID=account.universe,field=['secID','MA5','MA10','MA20','NetProfitGrowRate'],pandas="1")
    getData_current_date.set_index('secID',inplace=True)
    getData_current_date=getData_current_date[getData_current_date.NetProfitGrowRate>=1.0].dropna()
    getData_current_date=getData_current_date.sort(columns='NetProfitGrowRate',ascending=False)
    getData_current_date=getData_current_date.head(20)
    #print  account.current_date,getData_current_date

    getData_last_date=DataAPI.MktStockFactorsOneDayGet(tradeDate=last_date,secID=list(getData_current_date.index),field=['secID','MA5','MA10','MA20','NetProfitGrowRate'],pandas="1")
    getData_last_date.set_index('secID',inplace=True)
    
    for stock in list(getData_current_date.index):
        if((getData_current_date['MA5'][stock]>getData_current_date['MA10'][stock])&(getData_last_date['MA5'][stock]<=getData_last_date['MA10'][stock])):
            buylist.append(stock)
            
    for stock in list(getData_current_date.index):
        if((getData_current_date['MA5'][stock]<=getData_current_date['MA10'][stock])&(getData_last_date['MA5'][stock]>getData_last_date['MA10'][stock])):
            selist.append(stock)
    
    
    for stock in selist:
        if(stock in account.valid_secpos):
            order_to(stock,0)
        else:
            pass
    
    for stock in buylist:
        if(stock in account.valid_secpos):
            pass
        else:
            if(len(buylist)>=5):
                order(stock,account.cash/account.referencePrice[stock]/len(buylist))
            else:
                order(stock,account.cash/account.referencePrice[stock]/5)
            
    print "日期：",account.current_date,",持仓：",account.valid_secpos
