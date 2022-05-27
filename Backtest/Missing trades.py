
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
interval = "1m"
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filename='missing_trades_dzps.log')

# incertitude = 0.062

while(True):
    Missing = False
    # --- avoid intra candles effect
    if(datetime.now().second < 50):
        continue

    print("----------------")
    logging.info('----------------')

    # 0 --- Get data and transform it to HA
    try:
        df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60)) # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
        HAdf = HA_transformation(df)
        RSI = round(pta.rsi(HAdf.Close, 14), 2)
        tf, bf = supp_resis(HAdf,length = 50, maLen = 30)
    except Exception as e:
        print(f'Problem in reading data, exception hya : {e}')
        logging.info(f'Problem in reading data, exception hya : {e}')
    incertitude = HAdf.Close[-1] *0.5/100
    print("incertitude = " + str(incertitude))
    logging.info("incertitude = " + str(incertitude))

    # 1 --- Detect last RSI cross
    position, RSI_cross_time = detect_RSI_cross(RSI, window=60, bottom_line_rsi=30, top_line_rsi=70)
    if position == "nothing":
        continue

    # 2 --- Identify level of breakout (at the RSI cross moment)
    breakout_level, time_level = identify_breakout_level(position, tf, bf, price = HAdf.Close, moment = RSI_cross_time)
    if (datetime.now() - time_level).seconds/60 > 60 :
        print("window of the breakout level is too big")
        logging.info("window of the breakout level is too big")
        continue

    # 3 --- Detect breakout
    breakout = detect_breakout(position,HAdf,level=breakout_level)
    if(not breakout):
        continue

    # 4 --- Enter trade
    try:
        balance = pd.DataFrame(client.futures_account_balance())
        balance_usdt_t0 = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])
        balance_usdt = round(0.9 * balance_usdt_t0, 4)
        precision = 1  # WAVES
        qty = round(levier * balance_usdt / HAdf.iloc[[-1]].Close[0], precision)
        # update leverage
        client.futures_change_leverage(symbol=symbol, leverage=levier)
        # entry position (limit)
        calculated_price_entry = round(HAdf.iloc[-1].Close, 3)
        order = client.futures_create_order(symbol=symbol, side= 'BUY' if position == "long" else "SELL", type='LIMIT', quantity=qty,
                                            timeInForce='GTC', price=calculated_price_entry)

        # 5 --- Verify if the entry order limit is filled:
        a = pd.DataFrame(client.futures_position_information())
        a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
        t = datetime.now()
        while (len(a.index) == 0):
            print("Waiting to fill the order, time = " + str(datetime.now()))
            logging.info("Waiting to fill the order, time = " + str(datetime.now()))
            time.sleep(3)
            dif = (datetime.now() - t).seconds
            try:
                a = pd.DataFrame(client.futures_position_information())
                a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            except Exception as e:
                print(f'Problem in futures_position_information (inside the first while loop), exception hya : {e}')
                logging.info(
                    f'Problem in futures_position_information (inside the first while loop), exception hya : {e}')
            if (dif >= timeout_entry_seconds):
                print("Entry position : Time out! time = " + str(datetime.now()))
                logging.info("Entry position : Time out! time = " + str(datetime.now()))
                # debug for this case : one the bot is deployed, the first position is a timeout one
                Missing= True
                order_tp = ""
                order_sl = ""
                break
        if (Missing==False and len(a.index)== 1):
            print("Fake position closed = " + str(datetime.now()))
            logging.info("Fake position closed = " + str(datetime.now()))
            # --- Cancel all positions #
            order_m4t = client.futures_create_order(symbol=symbol, side='SELL' if position == "long" else "BUY",
                                                    type='MARKET',quantity=qty)
    except Exception as e:
        print(f'Problem in firing the fake order, exception hya : {e}')
        logging.info(f'Problem in firing the fake order, exception hya : {e}')

    if(Missing):
        try:
            df = getdata_min_ago(symbol, interval=interval,
                                 lookback=str(10 * 60))  # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
            HAdf = HA_transformation(df)
        except Exception as e:
            print(f'Problem in reading data, exception hya : {e}')
            logging.info(f'Problem in reading data, exception hya : {e}')

        # 4 --- Enter trade
        try:
            balance = pd.DataFrame(client.futures_account_balance())
            balance_usdt_t0 = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])
            balance_usdt = round(0.9 * balance_usdt_t0, 4)
            precision = 1  # WAVES
            qty = round(levier * balance_usdt / HAdf.iloc[[-1]].Close[0], precision)
            # update leverage
            client.futures_change_leverage(symbol=symbol, leverage=levier)
            # entry position (limit)
            calculated_price_entry = round(HAdf.iloc[-1].Close, 3)
            order = client.futures_create_order(symbol=symbol, side='BUY' if position == "long" else "SELL",
                                                type='LIMIT', quantity=qty,
                                                timeInForce='GTC', price=calculated_price_entry)
            # 6 --- TP & SL
            if (len(a.index) > 0):
                print("Order filled! Time = " + str(datetime.now()))
                logging.info("Order filled! Time = " + str(datetime.now()))

                if position == 'long':
                    TP = calculated_price_entry + 0.45 / 100 * calculated_price_entry
                    SL = bf[-1]
                else:
                    TP = calculated_price_entry - 0.45 / 100 * calculated_price_entry
                    SL = tf[-1]

                order_tp = client.futures_create_order(symbol=symbol, side='SELL' if position == "long" else "BUY", type='LIMIT', quantity=qty,
                                                       price=round(TP, 3), timeInForce='GTC')
                order_sl = client.futures_create_order(symbol=symbol, side="SELL" if position == "long" else "BUY", type='STOP_MARKET', quantity=qty,
                                                       stopPrice=round(SL, 3), timeInForce='GTE_GTC', closePosition=True)
        except Exception as e:
            print(f'Problem in firing the true order, exception hya : {e}')
            logging.info(f'Problem in firing the true order, exception hya : {e}')
        # 7 --- waiting in the position
        try:
            a = pd.DataFrame(client.futures_position_information())
            a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
        except Exception as e:
            print(f'Problem in futures_position_information, exception hya : {e}')
            logging.info((f'Problem in futures_position_information, exception hya : {e}'))
        while (len(a.index) > 0):
            try:
                print("Still in reel position, time = " + str(datetime.now()))
                logging.info("Still in reel position, time = " + str(datetime.now()))
                time.sleep(3)
                a = pd.DataFrame(client.futures_position_information())
                a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            except Exception as e:
                print(f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')
                logging.info(
                    f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')

        # 9 --- save data to google sheet
        balance = pd.DataFrame(client.futures_account_balance())
        balance_usdt_t_final = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])
        print("sleeping (data saving to GS)")
        logging.info('sleeping (data saving to GS)')
        time.sleep(8)
        getdata_and_save_to_sheet(symbol, position, balance_usdt_t_final, balance_usdt_t0, order, order_tp, order_sl,
                                  breakout_level, HAdf, levier=levier,sheet_name='str(trades_Mi')

