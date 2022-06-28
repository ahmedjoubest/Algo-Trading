
# Author: Ahmed / Yasine
# 09/05/2022


# Author: Ahmed / Yasine
# 03/05/2022
# Bot breakout

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
from oauth2client.service_account import ServiceAccountCredentials
import gspread
# import datetime
import math
symbol = "WAVESUSDT"
interval = "30m"
timeout_entry_seconds = 180
tp = 0.57
window_rsi_minute = 60
levier = 1

api_key = 'vCvbNDYnP04sL3ZMGdGxY4QuEPEdotvw9JqBoM7cL9sSUol5m86EZwhy3JOI0kon'
api_secret = '9GZ3AlmbVHg0NawM1MYVIzNSjw7eh53f60TtETu7M5jcce1fRtnKzhVlMJbfT14y'
client = Client(api_key,api_secret)

# --- Sourcing functions
try:
    exec(open("functions/get_data.py").read())
    exec(open("functions/math_tools.py").read())
    exec(open("functions/tracking.py").read())
except Exception as e: print("I'm on the server man")
# in the server:
try:
    exec(open("/home/ec2-user/Algo-Trading/functions/get_data.py").read())
    exec(open("/home/ec2-user/Algo-Trading/functions/math_tools.py").read())
    exec(open("/home/ec2-user/Algo-Trading/functions/tracking.py").read())
except Exception as e: print("I'm NOT on the server man")

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filename='patterns.log')

while(True):
    try:
        df = getdata_min_ago(symbol, interval=interval,lookback=str(10 * 60))
    except Exception as e:
        print(f'Problem in reading data, exception hya : {e}')
        logging.info(f'Problem in reading data, exception hya : {e}')
    if(Close[-3]< Open[-3] and Close[-2]> Open[-2] and Low[-3]<Low[-2] and High[-3]<High[-2]):
        # --- Enter trade
        try:
            balance = pd.DataFrame(client.futures_account_balance())
            balance_usdt_t0 = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])
            balance_usdt = round(0.9 * balance_usdt_t0, 4)
            precision = 1  # WAVES
            qty = round(levier * balance_usdt / df.iloc[[-1]].Close[0], precision)
            # update leverage
            client.futures_change_leverage(symbol=symbol, leverage=levier)
            # entry position (limit)
            calculated_price_entry = round(min(Close[-2],Open[-2])+abs(df.iloc[-2].Close-df.iloc[-2].Open)/2, 3)
            order = client.futures_create_order(symbol=symbol, side='BUY' if position == "long" else "SELL",
                                                    type='LIMIT', quantity=qty,
                                                    timeInForce='GTC', price=calculated_price_entry)
            # 6 --- TP & SL
            if (len(a.index) > 0):
                print("Order filled! Time = " + str(datetime.now()))
                logging.info("Order filled! Time = " + str(datetime.now()))

                if position == 'long':
                    TP = calculated_price_entry + 0.45 / 100 * calculated_price_entry
                    SL = Low[-1]-df.Low[-1] *0.5/100
                else:
                    TP = calculated_price_entry - 0.45 / 100 * calculated_price_entry
                    SL = Open[-1]+df.High[-1] *0.5/100

                order_tp = client.futures_create_order(symbol=symbol, side='SELL' if position == "long" else "BUY",
                                                           type='LIMIT', quantity=qty,
                                                           price=round(TP, 3), timeInForce='GTC')
                order_sl = client.futures_create_order(symbol=symbol, side="SELL" if position == "long" else "BUY",
                                                           type='STOP_MARKET', quantity=qty,
                                                           stopPrice=round(SL, 3), timeInForce='GTE_GTC',
                                                           closePosition=True)
        except Exception as e:
            print(f'Problem in firing the true order, exception hya : {e}')
            logging.info(f'Problem in firing the true order, exception hya : {e}')