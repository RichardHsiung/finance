# -*- coding: utf-8 -*-
from dataapiclient import Client
if __name__ == "__main__":
    try:
        client = Client()
        client.init('f0d4b9b58f55dead730820c0db538f5f2177da6ea9218b2ded348d242f10c509')
        #url1='/api/macro/getChinaDataGDP.csv?field=&indicID=M010000002&indicName=&beginDate=&endDate='
        url1='/api/market/getStockFactorsDateRange.json?field=&secID=&ticker=000001&beginDate=20170612&endDate=20170617'
        code, result = client.getData(url1)
        if code==200:
            print(result)
        else:
            print(code)
            print(result)
        url2='/api/subject/getThemesContent.csv?field=&themeID=&themeName=&isMain=1&themeSource='
        code, result = client.getData(url2)
        if(code==200):
            file_object = open('thefile.csv', 'w')
            file_object.write(result)
            file_object.close( )
        else:
            print(code)
            print(result) 
    except Exception as e:
        #traceback.print_exc()
        raise e
