
# Author: Ahmed
# 14/01/2022
# Tuto: https://www.youtube.com/watch?v=pB8eJwg7LJU&t=1838s&ab_channel=Algovibes
# The first goal is to apply this strategy (with small tweaks) to a Cryptocurrency with different timeframe
### Strategy:
# symbol = "BNBUSDT", interval = "1m", lookback = "24h", MA_n = 30, RSI_min = 35, RSI_max = 65
# Buy Signal: RSI < RSI_min and Price > MA_n
# sell signam: RSI > RSI_max

import pandas as pd
import numpy as np
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib.pyplot as plt

# --- 1 API (Confidential) (Useless if we only want to read the data, only for order automation)
# api_key = 'YqtSwA9CkxTjBlx2f3NUnBTj7YwH8hj4OZq9USMb7YsRfH18UC3JFS39QL3JgxDy'
# api_secret = 'Ru1Drz8zalkBeTRShKKk8YEGsaeRh6YZ0lukwBZpGxClWiIfGBjB5MLoKd4zlgqw'
# client = Client(api_key,api_secret)
client = Client()

# --- 2 read data
# for kline in client.get_historical_klines_generator("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 hours ago UTC"):
#   print(kline)

# --- 3 Data formatting function
# https://www.youtube.com/watch?v=_IV1qfSPPwI&ab_channel=Algovibes
# https://github.com/ahmedjoubest/Algo-Trading/blob/main/into_api_binance.ipynb
def getminutedata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback+" min ago UTC"))
    frame = frame.iloc[:,:6] # on s'arrête a la colonne 6
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float) # transform string to floats :
    # get only open/close prices
    frame = frame[['Open','Close']]
    return frame
# case of 23
# use :
# test = getminutedata("BNBUSDT","1m","5")
# test = getminutedata("BNBUSDT","1h","120")
# plt.plot(test)

# --- 4 RSI calculation function
def RSIcalc(symbol = "BNBUSDT", interval = "1m", lookback = str(60*24), MA_n = 60*4, RSI_min = 35, RSI_max = 65):
    df = getminutedata(symbol, interval, lookback) # Get data
    df['MA_n'] = df['Close'].rolling(window=MA_n).mean() # MA column (for the 1st condition backtest)
    df['price change'] = df['Close'].pct_change()
    df['Upmove'] = df['price change'].apply(lambda x: x if x>0 else 0)
    df['Downmove'] = df['price change'].apply(lambda x: abs(x) if x<0 else 0)
    df['avg Up'] = df['Upmove'].ewm(span=19).mean()
    df['avg Down'] = df['Downmove'].ewm(span=19).mean()
    df = df.dropna()
    df['RS'] = df['avg Up'] / df['avg Down']
    df['RSI'] = df['RS'].apply(lambda x: 100-(100/(x+1)))
    # Buy condition verified
    # df.loc[(df['Close']>df['MA_n']) & (df['RSI']<40), 'Buy'] = 'Yes'
    # MA maybe not adequate in minutes
    df.loc[(df['RSI']<40), 'Buy'] = 'Yes'
    # Buy condition not verified (NON A&B = NON A ou NON B)
    # df.loc[(df['Close']<df['MA_n']) | (df['RSI']>40), 'Buy'] = 'No'
    # df.loc[(df['RSI']>40), 'Buy'] = 'No'
    # Optimization for sql data base: drop useless columns
    return df[['Open','Close','MA_n','RSI','Buy']]

# --- 5 Visualization of RSI/Price
df = RSIcalc()
fig, axs = plt.subplots(2)
fig.suptitle('MA, Price and RSI')
axs[0].plot(df['Close'])
axs[0].plot(df['MA_n'])
axs[1].plot(df['RSI'])

# --- 6 Function to get signals
def getSignals(df):
    Buying_signals = []
    Selling_signals = []
    for i in range(len(df)):
        if "Yes" in df['Buy'].iloc[i]:
            Buying_signals.append(df.iloc[i+1].name) # +1 because we buy at the "NEXT" open price

    return Buying_signals, Selling_signals

a,b= getSignals(df)

