# This is a sample Python script.

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# 2 "getdata" takes a long time for just 10 days back testing

import pandas as pd
import numpy as np
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import math

# --- 1 API (Confidential) (Useless if we only want to read the data, only for order automation)
# api_key = 'YqtSwA9CkxTjBlx2f3NUnBTj7YwH8hj4OZq9USMb7YsRfH18UC3JFS39QL3JgxDy'
# api_secret = 'Ru1Drz8zalkBeTRShKKk8YEGsaeRh6YZ0lukwBZpGxClWiIfGBjB5MLoKd4zlgqw'
# client = Client(api_key,api_secret)
client = Client()

# --- 3 Data formatting function
# https://www.youtube.com/watch?v=_IV1qfSPPwI&ab_channel=Algovibes
# https://github.com/ahmedjoubest/Algo-Trading/blob/main/into_api_binance.ipynb
def getdata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback+" min ago UTC"))
    frame = frame.iloc[:,:6] # on s'arrête a la colonne 6
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float) # transform string to floats :
    # get only open/close prices
    frame = frame[['Open','Close','High','Low']]
    return frame

# Get data
df_BTC = getdata(symbol = "BTCUSDT", interval = "5m", lookback = str(60*24))
df_DOGE = getdata(symbol = "DOGEUSDT", interval = "5m", lookback = str(60*24))

# Price
btc_change = df_BTC['Close'].pct_change()
doge_change = df_DOGE['Close'].pct_change()

plt.plot(btc_change.head(100))
plt.plot(doge_change.head(100))

plt.plot(doge_change.head(100)/btc_change.head(100))

fig, axs = plt.subplots(4)
axs[0].plot(doge_change.head(100)/btc_change.head(100))
axs[1].plot(df_DOGE['Close'].head(100))
axs[2].plot(df_BTC['Close'].head(100))
axs[3].plot(btc_change.head(100))
axs[3].plot(doge_change.head(100))


