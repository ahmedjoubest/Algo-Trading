
# Author: Ahmed
# 14/01/2022
# Tuto: https://www.youtube.com/watch?v=pB8eJwg7LJU&t=1838s&ab_channel=Algovibes
# The first goal is to apply this strategy (with small tweaks) to a Cryptocurrency with different timeframes
### Strategy:
# Buy Signal: RSI < RSI_min
# sell signam: RSI > RSI_max
### Critics/possible improvment:
# 1- no lags. The strategy buys/sells at the same closing price of the signal.
# Ideally, the actions should be triggered with a minimum of lag.
# For example, Buy/Sell with the open price of t+1, as it's done in the Youtube video.
    # Edited : this problem is now corrected
# 2- The program does not yet take the case where the last row is a Sell (t+1 opening price doesn't exist)
# 3- I keep using Python lists for calculation, numpy is maybe faster! (to verify)
# 4- *capital0/max(Buying_price) can be improved, right now it's just an approximation
# 5- (related to 4) Should take the profit of every day (or ideally every trade) in capital0

import pandas as pd
import numpy as np
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib.pyplot as plt
from datetime import timedelta

# --- 1 API (Confidential) (Useless if we only want to read the data, only for order automation)
# api_key = 'YqtSwA9CkxTjBlx2f3NUnBTj7YwH8hj4OZq9USMb7YsRfH18UC3JFS39QL3JgxDy'
# api_secret = 'Ru1Drz8zalkBeTRShKKk8YEGsaeRh6YZ0lukwBZpGxClWiIfGBjB5MLoKd4zlgqw'
# client = Client(api_key,api_secret)
client = Client()

# --- 2 read data
for kline in client.get_historical_klines_generator("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 hours ago UTC"):
    print(kline)


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
    frame = frame[['Open','Close']]
    return frame
# case of use :
# test = getdata("BNBUSDT","1m","5")
# test = getdata("BNBUSDT","1h","120")
# plt.plot(test)


# --- 4 RSI calculation function
def RSIcalc(symbol = "BNBUSDT", interval = "1m", lookback = str(60*24 + 4*60), MA_n = 60*4,
            n = 20):
    df = getdata(symbol, interval, lookback) # Get data
    df['MA_n'] = df['Close'].rolling(window=MA_n).mean() # MA column (for the 1st condition backtest)
    df['price change'] = df['Close'].pct_change()
    df['Upmove'] = df['price change'].apply(lambda x: x if x>0 else 0)
    df['Downmove'] = df['price change'].apply(lambda x: abs(x) if x<0 else 0)
    df['avg Up'] = df['Upmove'].ewm(span=n).mean()
    df['avg Down'] = df['Downmove'].ewm(span=n).mean()
    df = df.dropna()
    df['RS'] = df['avg Up'] / df['avg Down']
    df['RSI'] = df['RS'].apply(lambda x: 100-(100/(x+1)))
    # Optimization for sql data base: drop useless columns
    return df[['Open','Close','MA_n','RSI']]

# --- 5 Visualization of RSI/Price
df = RSIcalc(lookback = str(60*24*1 + 4*60), n=15)

# fig, axs = plt.subplots(2)
# fig.suptitle('MA, Price and RSI')
# axs[0].plot(df['Close'])
# axs[0].plot(df['MA_n'])
# axs[1].plot(df['RSI'])

# --- 6 Function to get signals
def getSignals(df, RSI_min = 35, RSI_max = 65):

    # df.loc[(df['Close']>df['MA_n']) & (df['RSI']<40), 'Buy'] = 'Yes'
    # df.loc[(df['Close']<df['MA_n']) | (df['RSI']>40), 'Buy'] = 'No'
    # MA is maybe not adequate with minutes timeframe, I will use only RSI

    # Buy condition verified
    df.loc[(df['RSI'] < RSI_min), 'Actions'] = 'Buy'
    # Sell condition verified
    df.loc[(df['RSI'] > RSI_max), 'Actions'] = 'Sell'
    # wait condition verified (NON A&B = NON A ou NON B)
    df.loc[(df['RSI'] < RSI_max) & (df['RSI'] > RSI_min), 'Actions'] = 'Wait'

    # Adapt Actions
    df['Actions_adapted'] = ["empty"] * len(df)
    i = 0
    next_move_is_buy = True  # if False, means sell
    while (i < len(df)):
        # print("While iteration number", i)
        # Identify next action
        if (next_move_is_buy):
            action = "Buy"
        else:
            action = "Sell"

        if "Wait" in df['Actions'].iloc[i]:
            df.iloc[i, len(df.columns) - 1] = "Wait"
            i += 1
            continue  # skip this iteration
        elif action in df['Actions'].iloc[i]:
            df.iloc[i, len(df.columns) - 1] = action
            next_move_is_buy = not next_move_is_buy
            i += 1
        else:
            df.iloc[i, len(df.columns) - 1] = "Wait"
            i += 1

    # Last action should be a "Sell"
    i = len(df)-1
    while (i >= 0):
        if "Sell" in df['Actions_adapted'].iloc[i]:
            print("Last element is a 'sell'")
            break
        if "Buy" in df['Actions_adapted'].iloc[i]:
            df.iloc[i, len(df.columns) - 1] = "Wait"
            print(i, " is a 'Buy' replaced by a 'Wait' ")
            break
        i -= 1

    return df

df= getSignals(df)

# --- 7 PNL function
def PNL(df,fees = 0.075/100, capital0=10000):
    Number_of_trades = sum(df['Actions_adapted'] == "Buy")
    Trades = list(["Trade: "+str(i+1) for i in list(range(Number_of_trades))])
    Buying_signals = list(df.index[df['Actions_adapted'] == "Buy"] + timedelta(minutes=1)) # buy at the t+1 opening price
    Selling_signals = list(df.index[df['Actions_adapted'] == "Sell"] + timedelta(minutes=1)) # buy at the t+1 opening price
    Buying_price = list(df.loc[(index in Buying_signals for index in df.index), 'Open']*(1+fees)*capital0/df['Open'].mean())
    Selling_price = list(df.loc[(index in Selling_signals for index in df.index), 'Open']*(1-fees)*capital0/df['Open'].mean())
    Profit = [sell - buy for buy, sell in zip(Buying_price, Selling_price)]
    profit_percent = [prof*100/buy for prof, buy in zip(Profit, Buying_price)]
    trade_duration = [int((t_buy - t_sell).total_seconds()/60) for t_buy, t_sell in zip(Selling_signals, Buying_signals)]
    df_PNL = {
        "Trades" : Trades,
        "Buying signals" : Buying_signals,
        "Selling signals": Selling_signals,
        "Buying price": Buying_price,
        "Selling price": Selling_price,
        "Profit": Profit,
        "percent-profit formatted" : profit_percent,
        "Trade duration (min)" : trade_duration
    }
    df_PNL = pd.DataFrame(df_PNL)

    # Summary
    df_PNL_Summary = {
        "Capital 0" :   [capital0] ,
        "Number of trades": [len(df_PNL)],
        "Total period (days)" : [(df.index[len(df)-1] - df.index[0]).total_seconds()/(60*60*24)],
        "Total profit (net)": [sum(df_PNL['Profit'])],
        "Total percent profit (net)": [sum(df_PNL['percent-profit formatted'])],
        "Avg percent profit per trade formatted (net)": [df_PNL['percent-profit formatted'].mean()],
        "Avg number of trades per day": [df_PNL.groupby(pd.Grouper(key='Selling signals',freq='D'))['Trades'].count().mean()],
        "Theoretical Profit": [(df.iloc[len(df) - 1, 0] - df.iloc[0, 0]) * capital0 / df['Open'].mean()]
    }
    df_PNL_Summary = pd.DataFrame(df_PNL_Summary)

    return(df_PNL,df_PNL_Summary)

df_PNL_01,df_PNL_Summary_01 = PNL(df, 0.1/100)


capital0 = 10000
fig, axs = plt.subplots(2)
fig.suptitle('MA, Price and RSI')
axs[0].scatter(df_PNL_01['Buying signals'], df_PNL_01['Buying price']/(capital0/df['Open'].mean()), marker='^', c='g', linewidths= 3)
axs[0].scatter(df_PNL_01['Selling signals'], df_PNL_01['Selling price']/(capital0/df['Open'].mean()), marker='^', c='r', linewidths= 3)
axs[0].plot(df['Open'], alpha = 0.5)
axs[1].plot(df['RSI'])





df_PNL_075,df_PNL_Summary_075 = PNL(df, 0.075/100)

