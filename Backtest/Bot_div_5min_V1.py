
# Author: Ahmed / Yasine
# 26/04/2022
# Function that eliminates crossed pics

# --- Import
import pandas as pd
import numpy as np
from binance.client import Client
import pandas_ta as pta
from numpy.core.fromnumeric import size
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import matplotlib.pyplot as plt
# import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from binance.enums import HistoricalKlinesType
import time
from datetime import datetime
from datetime import timedelta
import logging



# --- Sourcing functions
# exec(open("functions/get_data.py").read())
# exec(open("functions/math_tools.py").read())
# in the server:
exec(open("/home/ec2-user/Algo-Trading/functions/get_data.py").read())
exec(open("/home/ec2-user/Algo-Trading/functions/math_tools.py").read())


# --- API
api_key = 'vCvbNDYnP04sL3ZMGdGxY4QuEPEdotvw9JqBoM7cL9sSUol5m86EZwhy3JOI0kon'
api_secret = '9GZ3AlmbVHg0NawM1MYVIzNSjw7eh53f60TtETu7M5jcce1fRtnKzhVlMJbfT14y'
client = Client(api_key,api_secret)


# The argument "Window" is not being of use yet !

# logging system
# More on login system : https://algotrading101.com/learn/live-algo-trading-on-the-cloud-aws/
# https://docs.python.org/fr/3/howto/logging.html
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filename='events.log', filemode='a')


symbol = "WAVESUSDT"
window_div= 7
tolerance = 0.25
levier = 1
def div_5min(symbol = "WAVESUSDT", window_div= 7, tolerance = 0.25, levier = 1):

    while(True):

        # 0 --- traceback
        print("###### Iteration at: "+str(datetime.now())+" ######")
        logging.info("###### Iteration at: "+str(datetime.now())+" ######")

        # 1 --- Get data and transform it to HA
        try:
            df_5mn = getdata_min_ago(symbol, interval = "5m", lookback= str(13*60))
        except Exception as e:
            print(f'Problem in reading data, exception hya : {e}')
            logging.info(f'Problem in reading data, exception hya : {e}')
        global HAdf_5mn,RSI_stoch_k,RSI_stoch_d,RSI
        HAdf_5mn = HA_transformation(df_5mn)
        RSI_stoch_k = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSIk_14_14_3_3, 2)  # k = blue # ignore warning
        RSI_stoch_d = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSId_14_14_3_3, 2)
        RSI = round(pta.rsi(HAdf_5mn.Close, 14), 2)


        # 2 --- Verify if the stochastic is verified
        OB_or_OS = sum(HAdf_5mn.tail(3).iloc[[0, 1]].Open < HAdf_5mn.tail(3).iloc[[0, 1]].Close)
        if(not verify_stochastic_5min(OB_or_OS, RSI_stoch_d, RSI_stoch_k)):
            continue


        # 3 --- Verify condition 5 min
        if(not verify_condition_5min(OB_or_OS,HAdf_5mn)):
            continue

        # 4 --- Find divergence

        # 4 - a - Find local minima / maxima
        # short (maxima)
        if (OB_or_OS == 2):
            peaks, _ = find_peaks(HAdf_5mn.Close, distance=2)  # distance = minimum distance between two peaks
        # long (minima)
        else:
            peaks, _ = find_peaks(-HAdf_5mn.Close, distance=2)

        # 4 - b - Eliminate invalid last peaks (Stochastic + 3 candles verification)
        potential_pics = eliminate_last_pics_stocha_candles(OB_or_OS,peaks,HAdf_5mn,RSI_stoch_k)

        # ISSUE with find_peaks
        if (OB_or_OS == 2):
            # Issue: if last pic is the highest, this stupid function won't take it, we should add it!
            max_last_pic = np.where(HAdf_5mn.Close == max(HAdf_5mn.iloc[[-3, -2, -1]].Close))[0][-1] # [-1] to take the last maximum
            if(max_last_pic not in peaks):
                potential_pics = np.append(potential_pics,max_last_pic)
        # long (minima)
        else:
            # Issue: if last pic is the lowest, this stupid function won't take it, we should add it!
            min_last_pic = np.where(HAdf_5mn.Close == min(HAdf_5mn.iloc[[-3, -2, -1]].Close))[0][-1]
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
        Div = divergence_verificaiton(uncrossed_peaks_RSI,OB_or_OS,RSI,HAdf_5mn,currect_pic)


        # 5 --- buy or sell
        if(Div):
            print("Div = True")
            logging.info("Div = True")
            # Get usdt futurse balance
            try:
                balance = pd.DataFrame(client.futures_account_balance())
                balance_usdt = round(0.9 * float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0]), 4)
                precision = 1  # WAVES
                qty = round(levier * balance_usdt / HAdf_5mn.iloc[[-1]].Close[0], precision)
                # update leverage
                client.futures_change_leverage(symbol=symbol, leverage=round(levier))
                # position long
                order = client.futures_create_order(symbol=symbol, side='BUY' if (OB_or_OS == 0) else "SELL",
                                                    type='MARKET', quantity=qty)
                if (OB_or_OS == 0):
                    TP = HAdf_5mn.iloc[[-1]].Close[0] + 0.66 / 100 * HAdf_5mn.iloc[[-1]].Close[0]
                    SL = HAdf_5mn.iloc[[-1]].Close[0] - 0.59 / 100 * HAdf_5mn.iloc[[-1]].Close[0]
                else:
                    TP = HAdf_5mn.iloc[[-1]].Close[0] - 0.66 / 100 * HAdf_5mn.iloc[[-1]].Close[0]
                    SL = HAdf_5mn.iloc[[-1]].Close[0] + 0.59 / 100 * HAdf_5mn.iloc[[-1]].Close[0]
                order_tp = client.futures_create_order(symbol=symbol, side='BUY' if (OB_or_OS == 2) else "SELL",
                                                       type='LIMIT', quantity=qty, price=round(TP, 3),
                                                       timeInForce='GTC')
                order_sl = client.futures_create_order(symbol=symbol, side='BUY' if (OB_or_OS == 2) else "SELL",
                                                       type='STOP_MARKET', quantity=qty, stopPrice=round(SL, 3))
            except Exception as e:
                print(f'Problem in firing the order, exception hya : {e}')
                logging.info(f'Problem in firing the order, exception hya : {e}')

            try:
                a = pd.DataFrame(client.futures_position_information())
                a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            except Exception as e:
                print(f'Problem in futures_position_information, exception hya : {e}')
                logging.info((f'Problem in futures_position_information, exception hya : {e}'))

            while(len(a.index)>0):
                try:
                    print("Still in position, time = " + str(datetime.now()))
                    logging.info("Still in position, time = " + str(datetime.now()))
                    time.sleep(15)
                    a = pd.DataFrame(client.futures_position_information())
                    a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
                except Exception as e:
                    print(f'Problem in futures_position_information (inside the loop), exception hya : {e}')
                    logging.info(f'Problem in futures_position_information (inside the loop), exception hya : {e}')

            print("order (maybe) completed")
            logging.info("order (maybe) completed")
            # Cancel all open orders
            try:
                client.futures_cancel_all_open_orders(symbol= symbol)
            except Exception as e:
                print(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')
                logging.info(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')
        else:
            print("skip (no divergence detected)")
            logging.info("skip (no divergence detected)")
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




# https://docs.python.org/fr/3.5/tutorial/errors.html
# try:
#    print(df)
# except ValueError as v:
#     print(f'ValueError hya: : {v}')
# except NameError as n:
#     print(f'NameError hya: {n}')
# except Exception as e:
#        print(f'Exception hya: {e}')




import logging
