# Author: Ahmed
# 22/01/2022
# hints: https://tradewithpython.com/constructing-heikin-ashi-candlesticks-using-python
# The goal is to display HA candles according to UTC-temara time!

import pandas as pd
import numpy as np
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import math
import plotly.graph_objects as go
import random
from plotly.subplots import make_subplots


# --- 1 API (Confidential) (Useless if we only want to read the data, only for order automation)
# api_key = 'YqtSwA9CkxTjBlx2f3NUnBTj7YwH8hj4OZq9USMb7YsRfH18UC3JFS39QL3JgxDy'
# api_secret = 'Ru1Drz8zalkBeTRShKKk8YEGsaeRh6YZ0lukwBZpGxClWiIfGBjB5MLoKd4zlgqw'
# client = Client(api_key,api_secret)
client = Client()

# --- 3 Data formatting function
# https://www.youtube.com/watch?v=_IV1qfSPPwI&ab_channel=Algovibes
# https://github.com/ahmedjoubest/Algo-Trading/blob/main/into_api_binance.ipynb

def getdata_date(symbol, interval, date1, date2):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, date1, date2))
    frame = frame.iloc[:,:6] # on s'arrête a la colonne 6
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float) # transform string to floats :
    # get only open/close prices
    frame = frame[['Open','Close','High','Low']]
    return frame
df_1mn = getdata_date(symbol = "WAVESUSDT", interval = "5m", date1= "16 Apr, 2022",date2= "17 Apr, 2022")

# --- 4 Transformation from normal candles to HA
def HA_transformation(DF):
    HAdf = DF[['Open', 'High', 'Low', 'Close']]
    HAdf['Close'] = (DF['Open'] + DF['Close'] + DF['Low'] + DF['High']) / 4 # ignore error, just warning
    for i in range(len(DF)):
        if i == 0:
            HAdf.iat[0, 0] = round(((DF['Open'].iloc[0] + DF['Close'].iloc[0]) / 2), 2)
        else:
            HAdf.iat[i, 0] = round(((HAdf.iat[i - 1, 0] + HAdf.iat[i - 1, 3]) / 2), 2)
    HAdf['High'] = HAdf.loc[:, ['Open', 'Close']].join(DF['High']).max(axis=1)
    HAdf['Low'] = HAdf.loc[:, ['Open', 'Close']].join(DF['Low']).min(axis=1)
    return(HAdf)

HAdf = HA_transformation(df_1mn)

# --- 5 plot
fig2 = go.Figure(data=[go.Candlestick(x=HAdf.index,
                open=HAdf.Open,
                high=HAdf.High,
                low=HAdf.Low,
                close=HAdf.Close)])
fig2.update_layout(yaxis_range = [14,16],
          title = 'Heikin Ashi Chart: Waves',
          xaxis_title = 'Date',
          yaxis_title = 'Price')
fig2.show()

# --- 6 Question: How far is the intracandles variation biasing the backtest

# --- 6.a Let's choose N random '5min' moments from the last 24h
N = 10
df_1mn = getdata_date(symbol = "WAVESUSDT", interval = "1m", date1= "2 Apr, 2022", date2 = "3 Apr, 2022")
index_5min = [idx for idx,element in enumerate(df_1mn.index.minute) if element % 5 == 0]
random_index_5min = random.choices(index_5min,k=N)

# --- 6.b Evaluate, for each moment, the intra 5min candle evolution (i.e: at 1h25 vs at 1h29)
for i in range(len(random_index_5min)):
    index = random_index_5min[i]

    # Build 5min HA candles from 1 min candles until 'index' moment
    df_1mn_index = df_1mn.iloc[list(range(0,index+5))] # + 1 for candles at +1mn
    df_5mn = df_1mn.iloc[[]]
    index_5min = list(range(0,index+1,5))
    for idx in index_5min:
        df_5mn =\
            pd.concat([df_5mn,
                       pd.DataFrame(np.array([[
                           float(df_1mn_index.iloc[[idx]].Open),
                           float(df_1mn_index.iloc[[idx+4]].Close),
                           float(df_1mn_index.iloc[list(range(idx,idx+5))].High.max()),
                           float(df_1mn_index.iloc[list(range(idx, idx + 5))].Low.min())
                       ]]), index=[df_1mn_index.index[idx]], columns=['Open', 'Close', 'High', 'Low'])
                       ])
    HAdf_5mn = HA_transformation(df_5mn)

    # Build 5min HA candles from 1 min candles until 'index' - 4 min moment (To see intra candle, real time)
    df_1mn_index_realtime = df_1mn.iloc[list(range(0, index + 1))]  # + 1 for candles at +1mn
    df_5mn_realtime = df_1mn.iloc[[]]
    index_5min = list(range(0, index + 1, 5))
    for idx in index_5min:
        # if last iteration, then don't take numbers out of boundries
        if index_5min[-1] == idx:
            boundries_correction = -4
        else :
            boundries_correction = 0
        df_5mn_realtime = \
            pd.concat([df_5mn_realtime,
                       pd.DataFrame(np.array([[
                           float(df_1mn_index_realtime.iloc[[idx]].Open),
                           float(df_1mn_index_realtime.iloc[[idx + 4 + boundries_correction]].Close),
                           float(df_1mn_index_realtime.iloc[list(range(idx, idx + 5 + boundries_correction))].High.max()),
                           float(df_1mn_index_realtime.iloc[list(range(idx, idx + 5 + boundries_correction))].Low.min())
                       ]]), index=[df_1mn_index_realtime.index[idx]], columns=['Open', 'Close', 'High', 'Low'])
                       ])
    HAdf_5mn_realtime = HA_transformation(df_5mn_realtime)

    # Let's plot to compare
    HAdf_5mn = HAdf_5mn.tail(10)
    HAdf_5mn_realtime = HAdf_5mn_realtime.tail(10)

    fig = make_subplots(rows=2, cols=1,vertical_spacing=0.25)
    fig.add_trace(
        go.Candlestick(x=HAdf_5mn_realtime.index,
                       open=HAdf_5mn_realtime.Open,
                       high=HAdf_5mn_realtime.High,
                       low=HAdf_5mn_realtime.Low,
                       close=HAdf_5mn_realtime.Close),
        row=1, col=1
    )
    fig.add_trace(
        go.Candlestick(x=HAdf_5mn.index,
                       open=HAdf_5mn.Open,
                       high=HAdf_5mn.High,
                       low=HAdf_5mn.Low,
                       close=HAdf_5mn.Close),
        row=2, col=1
    )
    fig.update_layout(yaxis_range=[HAdf_5mn_realtime.Low.min(), HAdf_5mn_realtime.High.max()],
                       title='Heikin Ashi Chart comparison between 1st and 5th minute (Realtime vs static)',
                       xaxis_title='Date',yaxis_title='Price',height=1500, width=1500)
    fig.show()

    input('Iteration number '+str(i)+'. Go to next iteration ?')



# --- 6.c Evaluate for a specific case (example 2 in: https://docs.google.com/document/d/135fNsknp0_VtwincMFlFIOuWrIKdN_cd9LXADyY0UQs/edit)
# 2 Apr 2022 at 1:25 UTC+4 = 21h25 UTC 1 apr

df_1mn = getdata_date(symbol = "WAVESUSDT", interval = "1m", date1= "31 Mar, 2022", date2 = "1 Apr, 2022")
index_5min = [idx for idx,element in enumerate(df_1mn.index.minute) if element % 5 == 0]

# --- 6.b Evaluate, for each moment, the intra 5min candle evolution (i.e: at 1h25 vs at 1h29)
index = [idx for idx,element in enumerate(df_1mn.index) if element == pd.to_datetime(['2022-03-31 23:45'])][0]

 # Build 5min HA candles from 1 min candles until 'index' moment
df_1mn_index = df_1mn.iloc[list(range(0,index+5))] # + 1 for candles at +1mn
df_5mn = df_1mn.iloc[[]]
index_5min = list(range(0,index+1,5))
for idx in index_5min:
    df_5mn =\
        pd.concat([df_5mn,
                    pd.DataFrame(np.array([[
                        float(df_1mn_index.iloc[[idx]].Open),
                        float(df_1mn_index.iloc[[idx+4]].Close),
                        float(df_1mn_index.iloc[list(range(idx,idx+5))].High.max()),
                        float(df_1mn_index.iloc[list(range(idx, idx + 5))].Low.min())
                    ]]), index=[df_1mn_index.index[idx]], columns=['Open', 'Close', 'High', 'Low'])
                    ])
HAdf_5mn = HA_transformation(df_5mn)

# Build 5min HA candles from 1 min candles until 'index' - 4 min moment (To see intra candle, real time)
df_1mn_index_realtime = df_1mn.iloc[list(range(0, index + 1))]  # + 1 for candles at +1mn
df_5mn_realtime = df_1mn.iloc[[]]
index_5min = list(range(0, index + 1, 5))
for idx in index_5min:
    # if last iteration, then don't take numbers out of boundries
    if index_5min[-1] == idx:
        boundries_correction = -4
    else :
        boundries_correction = 0
    df_5mn_realtime = \
        pd.concat([df_5mn_realtime,
                    pd.DataFrame(np.array([[
                        float(df_1mn_index_realtime.iloc[[idx]].Open),
                        float(df_1mn_index_realtime.iloc[[idx + 4 + boundries_correction]].Close),
                        float(df_1mn_index_realtime.iloc[list(range(idx, idx + 5 + boundries_correction))].High.max()),
                        float(df_1mn_index_realtime.iloc[list(range(idx, idx + 5 + boundries_correction))].Low.min())
                    ]]), index=[df_1mn_index_realtime.index[idx]], columns=['Open', 'Close', 'High', 'Low'])
                    ])
HAdf_5mn_realtime = HA_transformation(df_5mn_realtime)

# Let's plot to compare
HAdf_5mn = HAdf_5mn.tail(45)
HAdf_5mn_realtime = HAdf_5mn_realtime.tail(45)

fig = make_subplots(rows=2, cols=1,vertical_spacing=0.25)
fig.add_trace(
    go.Candlestick(x=HAdf_5mn_realtime.index,
                    open=HAdf_5mn_realtime.Open,
                    high=HAdf_5mn_realtime.High,
                    low=HAdf_5mn_realtime.Low,
                    close=HAdf_5mn_realtime.Close),
    row=1, col=1
)
fig.add_trace(
    go.Candlestick(x=HAdf_5mn.index,
                    open=HAdf_5mn.Open,
                    high=HAdf_5mn.High,
                    low=HAdf_5mn.Low,
                    close=HAdf_5mn.Close),
    row=2, col=1
)
fig.update_layout(yaxis_range=[HAdf_5mn_realtime.Low.min(), HAdf_5mn_realtime.High.max()],
                    title='Heikin Ashi Chart comparison between 1st and 5th minute (Realtime vs static)',
                    xaxis_title='Date',yaxis_title='Price',height=1500, width=1500)
fig.show()



# 1- ( à écrire dans la fin du fichier)
# 	kayn machakil f candles lwlin c'est pas très précis car O(i) = (O(i-1)+C(i-1)) / 2
# 	mais ça s'étenue très vite
# 	mafihahc mochkil car katban ghir f struggling candle (hmra blast mn khdra wla l3ks)
# 	w hna makantswqoch en général l lon dyal struggling candle ;) (wla we will)
#
# 2- des écarts (négligerable f lon dyal struggling candle) kaybano aussi 3la wed ma kan arondiwch
# 	donc on a juste moqarana m3a TV
# 		btw on peut corriger ça en arrondissant
#
# 3-