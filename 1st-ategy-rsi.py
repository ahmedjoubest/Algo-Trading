
# Author: Ahmed
# 14/01/2022
# Tuto: https://www.youtube.com/watch?v=pB8eJwg7LJU&t=1838s&ab_channel=Algovibes
# The first goal is to apply this strategy with Binance API (instead of stocks)
# for second timeframe

import pandas as pd
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib.pyplot as plt

# --- 1 API (Confidential)
api_key = 'YqtSwA9CkxTjBlx2f3NUnBTj7YwH8hj4OZq9USMb7YsRfH18UC3JFS39QL3JgxDy'
api_secret = 'Ru1Drz8zalkBeTRShKKk8YEGsaeRh6YZ0lukwBZpGxClWiIfGBjB5MLoKd4zlgqw'
client = Client(api_key,api_secret)

# --- 2 read data
# for kline in client.get_historical_klines_generator("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "24 hours ago UTC"):
#    print(kline)

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
    return frame