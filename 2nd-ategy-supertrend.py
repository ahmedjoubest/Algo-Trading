# Author: Ahmed
# 22/01/2022
# Tuto: https://medium.datadriveninvestor.com/the-supertrend-implementing-screening-backtesting-in-python-70e8f88f383d
# Apply this strategy (with small tweaks) to a Cryptocurrency with different timeframes
### Strategy:
# Enter when the price movement is in the uptrend and exit when the trend direction changes.
# Conditioned by MA
### Critics/possible improvment:
# 1 numpy (or pandas series) are not used everywhere = performance ? to check!
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
df = getdata(symbol = "BNBUSDT", interval = "1m", lookback = str(60*24*3))

# --- 4 Super trend calculation function
def Supertrend(df, atr_period = 10, multiplier = 3.0):
    # MA
    MA_20 = df['Close'].rolling(window=20).mean()
    MA_50 = df['Close'].rolling(window=50).mean()
    MA_100 = df['Close'].rolling(window=100).mean()
    MA_200 = df['Close'].rolling(window=200).mean()
    MA_400 = df['Close'].rolling(window=400).mean()

    high = df['High']
    low = df['Low']
    close = df['Close']

    # calculate ATR
    price_diffs = [high - low,
                   high - close.shift(),
                   close.shift() - low] # shifted because we're going to make decisions at t+1
    true_range = pd.concat(price_diffs, axis=1) # axis 0 = as index, axis 1 = as columns
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in super trend indicator
    atr = true_range.ewm(alpha=1 / atr_period, min_periods=atr_period).mean() # https://fr.wikipedia.org/wiki/Lissage_exponentiel
    # df['atr'] = df['tr'].rolling(atr_period).mean() -- simpler method to calculate ATR

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)

    # initialize Supertrend column to True
    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        curr, prev = i, i - 1

        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]

            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan

    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband,
        'MA_20' : MA_20,
        'MA_50': MA_50,
        'MA_100': MA_100,
        'MA_200': MA_200,
        'MA_400': MA_400
    }, index=df.index)
df = df.join(Supertrend(df, 20,3.5))

# --- 6 Get signals function
def getSignals(df):

    # Delete first positions Nan values
    df = df[~(df['Final Lowerband'].isna() & df['Final Upperband'].isna()) & ~df['MA_200'].isna()]

    is_uptrend = df['Supertrend']
    close = df['Close']

    # initial condition
    in_position = False
    # equity = investment
    # share = 0
    entry = []
    exit = []

    for i in range(0, len(df)):
        # if not in position & price is on uptrend -> buy
        if not in_position and is_uptrend[i] and df['Close'][i]<df['MA_200'][i]:
            # share = equity / close[i] * (1-fees)
            # equity -= share * close[i]
            entry.append((df.index[i], close[i]))
            in_position = True
            print(f'Buy at {round(close[i], 2)} on {df.index[i].strftime("%Y/%m/%d %Hh%Mmn")}')
        # if in position & price is not on uptrend -> sell
        elif in_position and not is_uptrend[i] and df['Close'][i]>df['MA_200'][i]:
            # equity += share * close[i] * (1-fees)
            exit.append((df.index[i], close[i]))
            in_position = False
            print(f'Sell at {round(close[i], 2)} on {df.index[i].strftime("%Y/%m/%d %Hh%Mmn")}')

    # if still in position -> sell all share
    if in_position:
        exit.append((df.index[i], close[i]))
        print(f'Sell at {round(close[i], 2)} on {df.index[i].strftime("%Y/%m/%d %Hh%Mmn")}')

    return entry, exit
entry, exit = getSignals(df)

# --- 7 P&L function / opinion: we really don't care about the capital for now.
def PNL(df,entry,exit ,fees= 0.075/100):
    Number_of_trades = len(entry)
    Trades = list(["Trade: "+str(i+1) for i in list(range(Number_of_trades))])
    Buying_signals = [entry[i][0] for i in range(0,len(entry))]
    Selling_signals = [exit[i][0] for i in range(0,len(entry))]
    Buying_price = [entry[i][1] for i in range(0,len(entry))]
    Selling_price = [exit[i][1] for i in range(0,len(entry))]
    net_ratio = [(sell*(1-fees) - buy*(1+fees))/buy*(1+fees) for buy,sell in zip(Buying_price, Selling_price)] # not sure
    trade_duration = [int((t_buy - t_sell).total_seconds()/60) for t_buy, t_sell in zip(Selling_signals, Buying_signals)]
    df_PNL = {
        "Trades" : Trades,
        "Buying signals" : Buying_signals,
        "Selling signals": Selling_signals,
        "Buying price": Buying_price,
        "Selling price": Selling_price,
        "Net profit ratio" : net_ratio,
        "Trade duration (min)" : trade_duration
    }
    df_PNL = pd.DataFrame(df_PNL)

    # Summary
    df_PNL_Summary = {
        "Number of trades": [len(df_PNL)],
        "Number of win": len(df_PNL[df_PNL['Net profit ratio'] >0]),
        "Number of loss": len(df_PNL[df_PNL['Net profit ratio'] < 0]),
        "Total period (days)" : [(df.index[len(df)-1] - df.index[0]).total_seconds()/(60*60*24)],
        "Total percent profit formatted (net)": [sum(df_PNL['Net profit ratio'])*100],
        "Avg percent profit per trade formatted (net)": [df_PNL['Net profit ratio'].mean()*100],
        "Avg number of trades per day": [df_PNL.groupby(pd.Grouper(key='Selling signals',freq='D'))['Trades'].count().mean()],
        "Theoretical Profit ratio": [(df['Close'][len(df)-1] - df['Close'][0])/df['Close'][0]],
    }
    df_PNL_Summary = pd.DataFrame(df_PNL_Summary)

    return(df_PNL,df_PNL_Summary)
df_PNL,df_PNL_Summary = PNL(df,entry,exit)

# plot
plt.scatter(df_PNL['Buying signals'], df_PNL['Buying price'], marker='^', c='g', linewidths= 3)
plt.scatter(df_PNL['Selling signals'], df_PNL['Selling price'], marker='^', c='r', linewidths= 3)
plt.plot(df['Close'], alpha = 0.5)
plt.plot(df['Final Lowerband'], 'g', label = 'Final Lowerband')
plt.plot(df['Final Upperband'], 'r', label = 'Final Upperband')
plt.plot(df['MA_50'], 'yellow', label = 'MA_50')
plt.plot(df['MA_200'], 'purple', label = 'MA_200')
plt.plot(df['MA_400'], 'grey', label = 'MA_400')

# ---9 optimization of parameters:
https://medium.datadriveninvestor.com/the-supertrend-implementing-screening-backtesting-in-python-70e8f88f383d