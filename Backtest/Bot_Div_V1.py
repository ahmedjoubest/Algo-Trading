
# --- 0 Import
import pandas as pd
import numpy as np
from binance.client import Client
import sqlalchemy
from binance import BinanceSocketManager
import pandas_ta as pta
from sspipe import p, px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks



# 0 --- Arguments:
window_div = 7


# --- 1 API
client = Client()

# 1 --- Sourcing functions
execfile("functions/get_data.py")
execfile("functions/HA_calculation.py")
# execfile("functions/RSI_calculation.py") # We are using RSI

# 2 --- Get data and transform it to HA
df_5mn = getdata_date(symbol = "WAVESUSDT", interval = "5m", date1= "25 Apr", date2 = "26 Apr")
HAdf_5mn = HA_transformation(df_5mn)
RSI_stoch_k = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSIk_14_14_3_3,2) # k = blue # ignore warning
RSI_stoch_d = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSId_14_14_3_3,2)

# 3 --- indexing our test time frame (this part will be deleted)
index = [idx for idx,element in enumerate(HAdf_5mn.index) if (element >= pd.to_datetime(['2022-04-25 2:50'])) & (element <= pd.to_datetime(['2022-04-25 8:45']))]
HAdf_5mn = HAdf_5mn.iloc[index]
RSI_stoch_k = RSI_stoch_k.iloc[index]
RSI_stoch_d = RSI_stoch_d.iloc[index]

# 4 --- Verify if the stochastic is verified
OB_or_OS = sum(HAdf_5mn.tail(3).iloc[[0,1]].Open < HAdf_5mn.tail(3).iloc[[0,1]].Close)
if(OB_or_OS == 2):
    # last two candles are green
    if (((RSI_stoch_d.iloc[[-1]] >= 80) & (RSI_stoch_k.iloc[[-1]] >= 80))[0]):
        print("next steps: short")
    else:
        print("Continue ( = go next iteration boucle while)")
elif(OB_or_OS == 0):
    # last two candles are red
    if (((RSI_stoch_d.iloc[[-1]] <= 20) & (RSI_stoch_k.iloc[[-1]] <= 20))[0]):
        print("next steps: long")
    else:
        print("Continue")
else:
    print("Continue")

# 5 --- Verify condition 5 min
# 5 - a - position short
if(OB_or_OS == 2):
    # {High(t) - Low(t)} should be lower than {High(t-1) - Low(t-1)}
    if((HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[1] <= (HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[0]):
        print("next steps (Short): Verify div")
    elif:
        print("Continue")
# 5 - b - position Long
if(OB_or_OS == 0):
    # {High(t) - Low(t)} should be lower than {High(t-1) - Low(t-1)}
    if((HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[1] <= (HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[0]):
        print("next steps (Long): Verify div")
    elif:
        print("Continue")

# 6 --- Find divergence

# 6 - a - Find local minima / maxima
# short (maxima)
if(OB_or_OS == 2):
    peaks, _ = find_peaks(HAdf_5mn.Close, distance=3) # distance = minimum distance between two peaks
    # peaks = HAdf_5mn.iloc[peaks.tolist()].index
# long (minima)
elif(OB_or_OS == 0):
    peaks, _ = find_peaks(-HAdf_5mn.Close, distance=3)

# 6 - b - Eliminate invalid last peaks
# short
for idx in peaks:
    # Stochastic must be verified
    if(((RSI_stoch_d.iloc[[idx]] >= 65))[0]):
        if()
    elif:
        continue


peaks = HAdf_5mn.iloc[peaks.tolist()].index
plt.plot(x)
plt.plot(peaks, x[peaks], "x")
plt.show()









fig2 = go.Figure(data=[go.Candlestick(x=HAdf_5mn.index,
                open=HAdf_5mn.Open,
                high=HAdf_5mn.High,
                low=HAdf_5mn.Low,
                close=HAdf_5mn.Close)])
fig2.update_layout(yaxis_range = [HAdf_5mn.Low.min(),HAdf_5mn.High.max()],
          title = 'Heikin Ashi Chart: Waves',
          xaxis_title = 'Date',
          yaxis_title = 'Price')
fig2.show()