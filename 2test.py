import pandas as pd
#import pandas.io.data as web   # Package and modules for importing data; this code may change depending on pandas version
from pandas_datareader import data as web   # Package and modules for importing data; this code may change depending on pandas version
import datetime
import time

# We will look at stock prices over the past year, starting at January 1, 2016
start = datetime.datetime(2017,1,1)
end = datetime.date.today()

# Let's get Apple stock data; Apple's ticker symbol is AAPL
# First argument is the series we want, second is the source ("yahoo" for Yahoo! Finance), third is the start date, fourth is the end date
apple = web.DataReader("AAPL", "google", start, end)

print(type(apple))
print(apple.head())

import matplotlib.pyplot as plt   # Import matplotlib
# This line is necessary for the plot to appear in a Jupyter notebook 
#%matplotlib inline
# Control the default size of figures in this Jupyter notebook 
#%pylab inline
plt.rcParams['figure.figsize'] = (10, 6)   # Change the size of plots

apple["Close"].plot(grid = True) # Plot the adjusted closing price of AAPL
plt.show()
