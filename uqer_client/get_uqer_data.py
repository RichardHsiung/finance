
import time
import sys
from uqer import Client


if __name__ == '__main__':
    username = '18511860769'
    password = 'hsiung@2015',
    token = '8EB19E2D2C668E72A2669E2D80572017'
    client = Client(username, password, token)

    if len(sys.argv[1]) < 1:
        print("Please enter the args")
        sys.exit()

    if sys.argv[1] == 'list':
        print(client.list_data())
    elif sys.argv[1] == 'factors':
        for x in client.list_data():
            num = int(x.split('_')[0])
            print(num)
            if x != 'stock_list.csv' and num >= 601199:
                client.download_data(x)
                time.sleep(4)
            else:
                continue
    elif sys.argv[1] == 'delete':
        for x in client.list_data():
            #time.sleep(1)
            if x != 'stock_list.csv':
                client.delete_data(x)
            
