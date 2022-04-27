
# Author: Ahmed / Yasine
# 26/04/2022
# Function that eliminates crossed pics

# --- 0 Import
import pandas as pd
import numpy as np
from binance.client import Client
import sqlalchemy
from binance import BinanceSocketManager
import pandas_ta as pta
from numpy.core.fromnumeric import size
from sspipe import p, px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks
from binance.enums import HistoricalKlinesType
import time
from datetime import datetime
from datetime import timedelta




# --- Sourcing functions
execfile("functions/get_data.py")
execfile("functions/HA_calculation.py")
# execfile("functions/RSI_calculation.py") # We are using RSI
execfile("functions/math_tools.py")

# --- API
api_key = 'vCvbNDYnP04sL3ZMGdGxY4QuEPEdotvw9JqBoM7cL9sSUol5m86EZwhy3JOI0kon'
api_secret = '9GZ3AlmbVHg0NawM1MYVIzNSjw7eh53f60TtETu7M5jcce1fRtnKzhVlMJbfT14y'
client = Client(api_key,api_secret)


# The argument "Window" is not being of use yet !


def div_5min(symbol = "WAVESUSDT", window_div= 7, tolerance = 0.25, levier = 1):
    while(True):

        # 1 --- Get data and transform it to HA
        df_5mn = getdata_min_ago(symbol, interval = "5m", lookback= str(13*60))
        HAdf_5mn = HA_transformation(df_5mn)
        RSI_stoch_k = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSIk_14_14_3_3, 2)  # k = blue # ignore warning
        RSI_stoch_d = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSId_14_14_3_3, 2)
        RSI = round(pta.rsi(HAdf_5mn.Close, 14), 2)

        # 2 --- Verify if the stochastic is verified
        OB_or_OS = sum(HAdf_5mn.tail(3).iloc[[0, 1]].Open < HAdf_5mn.tail(3).iloc[[0, 1]].Close)
        if (OB_or_OS == 2):
            # last two candles are green
            if (((RSI_stoch_d.iloc[[-1]] >= 80) & (RSI_stoch_k.iloc[[-1]] >= 80))[0]):
                print("next steps: short (stochastic is verified)")
            else:
                print("skip: step 2 (stochastic not verified)")
                continue
        elif (OB_or_OS == 0):
            # last two candles are red
            if (((RSI_stoch_d.iloc[[-1]] <= 20) & (RSI_stoch_k.iloc[[-1]] <= 20))[0]):
                print("next steps: long (stochastic is verified)")
            else:
                print("skip: step 2 (stochastic not verified)")
                continue
        else:
            print("skip: last two candles are not in the same color!")
            continue

        # 3 --- Verify condition 5 min
        # 3 - a - position short
        if (OB_or_OS == 2):
            # {High(t) - Low(t)} should be lower than {High(t-1) - Low(t-1)}
            if ((HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[1] <= (HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[0]):
                print("next steps (Short): Verify div (condition 5 min verified)")
            else:
                print("skip (condition 5 min NOT verified)")
                continue
        # 3 - b - position Long
        if (OB_or_OS == 0):
            # {High(t) - Low(t)} should be lower than {High(t-1) - Low(t-1)}
            if ((HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[1] <= (HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[0]):
                print("next steps (Long): Verify div (condition 5 min verified)")
            else:
                print("skip (condition 5 min NOT verified)")
                continue

        # 4 --- Find divergence

        # 4 - a - Find local minima / maxima
        # short (maxima)
        if (OB_or_OS == 2):
            peaks, _ = find_peaks(HAdf_5mn.Close, distance=2)  # distance = minimum distance between two peaks
        # long (minima)
        else:
            peaks, _ = find_peaks(-HAdf_5mn.Close, distance=2)

        # 4 - b - Eliminate invalid last peaks (Stochastic verification)
        if (OB_or_OS == 2):
            # short
            potential_pics = []
            for idx in peaks:
                # Stochastic must be verified
                if (((RSI_stoch_k.iloc[[idx]] >= 65))[0]):
                    # At least 3 candles same color
                    if (
                            sum(HAdf_5mn.iloc[[idx - 1, idx, idx + 1]].Close > HAdf_5mn.iloc[
                                [idx - 1, idx, idx + 1]].Open) == 3 or \
                            sum(HAdf_5mn.iloc[[idx - 2, idx - 1, idx]].Close > HAdf_5mn.iloc[
                                [idx - 2, idx - 1, idx]].Open) == 3 or \
                            sum(HAdf_5mn.iloc[[idx, idx + 1, idx + 2]].Close > HAdf_5mn.iloc[
                                [idx, idx + 1, idx + 2]].Open) == 3
                    ):
                        potential_pics.append(idx)
                    else:
                        continue
                else:
                    continue
        else:
            # long
            potential_pics = []
            for idx in peaks:
                # Stochastic must be verified
                if (((RSI_stoch_k.iloc[[idx]] <= 35))[0]):
                    # At least 3 candles
                    if (
                            sum(HAdf_5mn.iloc[[idx - 1, idx, idx + 1]].Close < HAdf_5mn.iloc[
                                [idx - 1, idx, idx + 1]].Open) == 3 or \
                            sum(HAdf_5mn.iloc[[idx - 2, idx - 1, idx]].Close < HAdf_5mn.iloc[
                                [idx - 2, idx - 1, idx]].Open) == 3 or \
                            sum(HAdf_5mn.iloc[[idx, idx + 1, idx + 2]].Close < HAdf_5mn.iloc[
                                [idx, idx + 1, idx + 2]].Open) == 3
                    ):
                        potential_pics.append(idx)
                    else:
                        continue
                else:
                    continue

        # ISSUE with find_peaks
        if (OB_or_OS == 2):
            # Issue: if last pic is the highest, this stupid function won't take it, we should add it!
            max_last_pic = np.where(HAdf_5mn.Close == max(HAdf_5mn.iloc[[-3, -2, -1]].Close))[0][0]
            if(max_last_pic not in peaks):
                potential_pics = np.append(potential_pics,max_last_pic)
        # long (minima)
        else:
            # Issue: if last pic is the lowest, this stupid function won't take it, we should add it!
            min_last_pic = np.where(HAdf_5mn.Close == min(HAdf_5mn.iloc[[-3, -2, -1]].Close))[0][0]
            if (min_last_pic not in peaks):
                potential_pics = np.append(potential_pics, min_last_pic)


        # 4 - c - Eliminate invalid last peaks (Uncross price verification)
        uncrossed_peaks_price = keep_uncrossed_peaks(close=HAdf_5mn.Close, open=HAdf_5mn.Open, peaks=potential_pics,
                                                     tolerance=tolerance, Short=(OB_or_OS == 2))
        # 4 - d - Eliminate invalid last peaks (Uncross RSI verification)
        uncrossed_peaks_RSI = keep_uncrossed_peaks_RSI(RSI=RSI, peaks=uncrossed_peaks_price, Short=(OB_or_OS == 2))

        # Current pic = last bigger pic
        currect_pic = uncrossed_peaks_RSI[-1]
        uncrossed_peaks_RSI.remove(uncrossed_peaks_RSI[-1])

        # Keep only peaks in the window
        uncrossed_peaks_RSI = [x for x in uncrossed_peaks_RSI if
                               HAdf_5mn.iloc[[x]].index > (datetime.now() - timedelta(hours=window_div))]

        # 4 - e - Eliminate peaks without divergence (must be reviewed)
        Div = False
        for peak in uncrossed_peaks_RSI:
            if (OB_or_OS == 2):
                # Short
                # Hidden divergence:
                if (32 < RSI[peak] < 68):
                    if (HAdf_5mn.iloc[[peak]].Close[0] > HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                            RSI[peak] < RSI[currect_pic]):
                        Div = True
                        print("Hidden Div detected for 'Short' in: " + str(HAdf_5mn.iloc[[peak]].index))
                        break
                    else:
                        continue
                elif (RSI[peak] >= 68):
                    # Hidden divergence:
                    if (HAdf_5mn.iloc[[peak]].Close[0] < HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                            RSI[peak] > RSI[currect_pic]):
                        Div = True
                        print("Regular Div detected for 'Short' in: " + str(HAdf_5mn.iloc[[peak]].index))
                        break
                    else:
                        continue
            else:
                # Long
                # Hidden divergence:
                if (32 < RSI[peak] < 68):
                    if (HAdf_5mn.iloc[[peak]].Close[0] < HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                            RSI[peak] > RSI[currect_pic]):
                        Div = True
                        print("Hidden Div detected for 'Long' in: " + str(HAdf_5mn.iloc[[peak]].index))
                        break
                    else:
                        continue
                elif (RSI[peak] <= 32):
                    # Hidden divergence:
                    if (HAdf_5mn.iloc[[peak]].Close[0] > HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                            RSI[peak] < RSI[currect_pic]):
                        Div = True
                        print("Regular Div detected for 'Long' in: " + str(HAdf_5mn.iloc[[peak]].index))
                        break
                    else:
                        continue

        # 5 --- buy or sell
        if(Div):
            print("Must buy or sell")
            # Get usdt futurse balance
            balance = pd.DataFrame(client.futures_account_balance())
            balance_usdt = round(0.9 * float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0]), 4)
            precision = 1 # WAVES
            qty = round(levier * balance_usdt / HAdf_5mn.iloc[[-1]].Close[0], precision)
            # update leverage
            client.futures_change_leverage(symbol= symbol, leverage=round(levier))
            # position long
            order = client.futures_create_order(symbol=symbol, side= 'BUY' if (OB_or_OS==0) else "SELL", type='MARKET', quantity=qty)
            if(OB_or_OS==0):
                TP = HAdf_5mn.iloc[[-1]].Close[0] + 0.66/100*HAdf_5mn.iloc[[-1]].Close[0]
                SL = HAdf_5mn.iloc[[-1]].Close[0] - 0.59/100*HAdf_5mn.iloc[[-1]].Close[0]
            else:
                TP = HAdf_5mn.iloc[[-1]].Close[0] - 0.66 / 100 * HAdf_5mn.iloc[[-1]].Close[0]
                SL = HAdf_5mn.iloc[[-1]].Close[0] + 0.59 / 100 * HAdf_5mn.iloc[[-1]].Close[0]
            order_tp = client.futures_create_order(symbol= symbol, side = 'BUY' if (OB_or_OS==2) else "SELL",
                                                   type='LIMIT', quantity=qty, price=round(TP,3), timeInForce='GTC')
            order_sl = client.futures_create_order(symbol= symbol, side='BUY' if (OB_or_OS==2) else "SELL",
                                                   type='STOP_MARKET', quantity= qty, stopPrice = round(SL,3))
            a = pd.DataFrame(client.futures_position_information())
            a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            while(len(a.index)>0):
                print("Still in position")
                time.sleep(15)
                print("time = " + str(datetime.now()))
                a = pd.DataFrame(client.futures_position_information())
                a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            print("order completed")
            # Cancel all open orders
            client.futures_cancel_all_open_orders(symbol= symbol)
        else:
            print("skip (no divergence detected)")
            continue




div_5min(symbol= "WAVESUSDT")


# cancel order
# client.futures_cancel_all_open_orders(symbol = 'WAVESUSDT')

# Get usdt futurse balance
# balance = pd.DataFrame(client.futures_account_balance())
# balance_usdt = round(0.9*float(balance.loc[balance['asset']=='USDT','balance'].iloc[0]),4)
# orders
# levier = 2
# qty: includes leverage!
# precision = 1
# qty = round(levier * balance_usdt / getdata_min_ago("WAVESUSDT", '1m', "1").Close[0],precision)
# update leverage
#client.futures_change_leverage(symbol="WAVESUSDT", leverage= round(levier))
# position long
# order = client.futures_create_order(symbol="WAVESUSDT", side='BUY', type='MARKET', quantity=qty)
# position end long
# order = client.futures_create_order(symbol="WAVESUSDT", side='SELL', type='MARKET', quantity= qty)
