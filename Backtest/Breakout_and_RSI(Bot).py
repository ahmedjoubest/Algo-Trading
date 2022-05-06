
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

# --- API
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


# logging system
# More on login system : https://algotrading101.com/learn/live-algo-trading-on-the-cloud-aws/
# https://docs.python.org/fr/3/howto/logging.html
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filename='events_breakout.log', filemode='a')


# add time out not to miss opportuniutes f les crypto lokhrin
# support wla resistence khass ykon mtraversyin l prix


timeout_entry_seconds = 180
tp = 0.57
sl = 1.4
interval = "1m"
symbol = "WAVESUSDT"
timeout = 60
levier = 10
incertitude = 0.08

while(True):

    # 0 --- Get data and transform it to HA
    try:
        df = getdata_min_ago(symbol, interval = interval, lookback= str(10*60))
    except Exception as e:
        print(f'Problem in reading data, exception hya : {e}')
        logging.info(f'Problem in reading data, exception hya : {e}')
    # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
    HAdf = HA_transformation(df)
    RSI = round(pta.rsi(HAdf.Close, 14), 2)
    tf,bf = supp_resis(HAdf,)

    # Detect RSI first signal (went on OB or OS)
    if(RSI[-1]<30):
        position = "long"
    elif(RSI[-1]>70):
        position = "short"
    else : position = "nothing"
    print("Position = "+ position)
    logging.info("Position = "+ position)

    if position == "nothing":
        continue

    if position == "long":

        # 1 --- Wait for the RSI cross
        while(RSI[-1]<30):
            if datetime.now().second > 40:
                print("waiting for the RSI cross")
                logging.info("waiting for the RSI cross")
                # Get data and transform it to HA
                try:
                    df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60))
                except Exception as e:
                    print(f'Problem in reading data, exception hya : {e}')
                    logging.info(f'Problem in reading data, exception hya : {e}')
                # global HAdf, RSI_stoch_k, RSI_stoch_d, RSI
                HAdf = HA_transformation(df)
                RSI = round(pta.rsi(HAdf.Close, 14), 2)
                tf, bf = supp_resis(HAdf, ) # bf for long (green one)
            else:
                time.sleep(1)
                continue
        print("RSI crossed the position for "+ position)
        logging.info("RSI crossed the position for "+ position)

        # 2 --- identify level of last support
        i = len(bf)-1
        while(HAdf.Close[-1] > bf[i]):
            i = i-1
        support_level = bf[i]
        print("support level = " + str(round(support_level,4)))
        logging.info("support level = " + str(round(support_level,4)))

        # 3 --- Wait for the break out (or timeout, or RSI get back to OS)
        time_crossrsi = datetime.now()
        while(True):

            if datetime.now().second > 40:
                print("waiting for the breakout")
                logging.info("waiting for the breakout")
                # read data
                try:
                    df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60))
                except Exception as e:
                    print(f'Problem in reading data, exception hya : {e}')
                    logging.info(f'Problem in reading data, exception hya : {e}')
                # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
                HAdf = HA_transformation(df)
                RSI = round(pta.rsi(HAdf.Close, 14), 2)

                dif = round((datetime.now() - time_crossrsi).seconds / 60, 2)
                if(dif>timeout):
                    event = "timeout"
                    print("Break out time out")
                    logging.info("Break out time out")
                    break

                if(RSI[-1]<30):
                    event = "RSI_anti_cross"
                    print("RSI anti crossed")
                    logging.info("RSI anti crossed")
                    break


                # Verify break out code
                breakout = True if (abs(HAdf.Close[-1]-HAdf.Close[-1])/2)+min([HAdf.Close[-1],HAdf.Open[-1]]) > support_level else False
                if(breakout):
                    print("Breakout detected, entry position : !" + position)
                    logging.info("Breakout detected, entry position : !" + position)
                    event = "Entry"
                    break
            else:
                time.sleep(1)
                continue

        # 4 --- Taking decision
        if(event=="timeout" or event=="RSI_anti_cross"):
            continue
        else:
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
                order = client.futures_create_order(symbol=symbol, side='BUY', type='LIMIT', quantity=qty,
                                                    timeInForce='GTC', price=calculated_price_entry)

                # Verify if the entry order limit is filled:
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
                        break

                if (len(a.index) > 0):
                    print("Order filled! Time = " + str(datetime.now()))
                    logging.info("Order filled! Time = " + str(datetime.now()))
                    TP = calculated_price_entry + tp / 100 * calculated_price_entry
                    SL = calculated_price_entry - sl / 100 * calculated_price_entry

                    # 0 --- Get data and transform it to HA
                    try:
                        df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60))
                    except Exception as e:
                        print(f'Problem in reading data, exception hya : {e}')
                        logging.info(f'Problem in reading data, exception hya : {e}')
                    # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
                    HAdf = HA_transformation(df)
                    RSI = round(pta.rsi(HAdf.Close, 14), 2)
                    tf, bf = supp_resis(HAdf, )
                    SL_support = bf[-1]
                    if(SL<=SL_support):
                        SL = SL_support - incertitude

                    order_tp = client.futures_create_order(symbol=symbol, side = "SELL", type='LIMIT', quantity=qty,
                                                           price=round(TP, 3), timeInForce='GTC')
                    order_sl = client.futures_create_order(symbol=symbol, side = "SELL", type='STOP_MARKET', quantity=qty,
                                                           stopPrice=round(SL, 3))
            except Exception as e:
                print(f'Problem in firing the order, exception hya : {e}')
                logging.info(f'Problem in firing the order, exception hya : {e}')

            try:
                a = pd.DataFrame(client.futures_position_information())
                a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            except Exception as e:
                print(f'Problem in futures_position_information, exception hya : {e}')
                logging.info((f'Problem in futures_position_information, exception hya : {e}'))

            while (len(a.index) > 0):
                try:
                    print("Still in position, time = " + str(datetime.now()))
                    logging.info("Still in position, time = " + str(datetime.now()))
                    time.sleep(3)
                    a = pd.DataFrame(client.futures_position_information())
                    a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
                except Exception as e:
                    print(
                        f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')
                    logging.info(
                        f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')

            # Cancel all open orders
            try:
                client.futures_cancel_all_open_orders(symbol=symbol)
            except Exception as e:
                print(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')
                logging.info(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')

            #####################
            #### Write into another script!
            # --- save data to GS
            balance = pd.DataFrame(client.futures_account_balance())
            balance_usdt_t_final = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])

            if (balance_usdt_t_final > balance_usdt_t0):
                price_entry, time_entry = get_time_avgprice_order(order, symbol)
                price_exit, time_exit = get_time_avgprice_order(order_tp, symbol)
                print('TP reached')
                logging.info('TP reached')
                duration = \
                    round(
                        (datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_entry,
                                                                                               '%Y-%m-%d %H:%M:%S')).seconds / 60,
                        1
                    )
                Long_short = position
                # create data frame and save it in GS!
                df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
                      "T_entry": [str(time_entry)],
                      "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)], 'P_avg_exit': [str(price_exit)],
                      'Balance': [str(balance_usdt_t_final)],
                      'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)],
                      'Support_level': [str(support_level)]
                      }
                df = pd.DataFrame(df)
                add_1rowDF_to_GS(df, sheet_name="tracking")

            elif (balance_usdt_t_final < balance_usdt_t0):
                price_entry, time_entry = get_time_avgprice_order(order, symbol)
                price_exit, time_exit = get_time_avgprice_order(order_sl, symbol)
                print('SL reached')
                logging.info('SL reached')
                duration = \
                    round(
                        (datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_entry,
                                                                                               '%Y-%m-%d %H:%M:%S')).seconds / 60,
                        1
                    )
                Long_short = position
                # create data frame and save it in GS!
                df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
                      "T_entry": [str(time_entry)],
                      "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)], 'P_avg_exit': [str(price_exit)],
                      'Balance': [str(balance_usdt_t_final)],
                      'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)],
                      'Support_level': [str(support_level)]
                      }
                df = pd.DataFrame(df)
                add_1rowDF_to_GS(df, sheet_name="tracking")
            else:
                print('(its a timeout case )')
                logging.info('(its a timeout case)')






































    if position == "short":

        # 1 --- Wait for the RSI cross
        while(RSI[-1]>70):
            if datetime.now().second > 40:
                print("waiting for the RSI cross")
                logging.info("waiting for the RSI cross")
                # Get data and transform it to HA
                try:
                    df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60))
                except Exception as e:
                    print(f'Problem in reading data, exception hya : {e}')
                    logging.info(f'Problem in reading data, exception hya : {e}')
                # global HAdf, RSI_stoch_k, RSI_stoch_d, RSI
                HAdf = HA_transformation(df)
                RSI = round(pta.rsi(HAdf.Close, 14), 2)
                tf, bf = supp_resis(HAdf, )
            else:
                time.sleep(1)
                continue
        print("RSI crossed the position for "+ position)
        logging.info("RSI crossed the position for "+ position)

        # 2 --- identify level of last support
        i = len(tf) - 1
        while (HAdf.Close[-1] < tf[i]):
            i = i - 1
        resistence_level = tf[i]
        print("resistence level = " + str(round(resistence_level,4)))
        logging.info("resistence level = " + str(round(resistence_level,4)))

        # 3 --- Wait for the break out (or timeout, or RSI get back to OS)
        time_crossrsi = datetime.now()
        while(True):
            if datetime.now().second > 40:
                print("waiting for the breakout")
                logging.info("waiting for the breakout")
                # read data
                try:
                    df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60))
                except Exception as e:
                    print(f'Problem in reading data, exception hya : {e}')
                    logging.info(f'Problem in reading data, exception hya : {e}')
                # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
                HAdf = HA_transformation(df)
                RSI = round(pta.rsi(HAdf.Close, 14), 2)

                dif = round((datetime.now() - time_crossrsi).seconds / 60, 2)
                if(dif>timeout):
                    event = "timeout"
                    print("Break out time out")
                    logging.info("Break out time out")
                    break

                if(RSI[-1]>70):
                    event = "RSI_anti_cross"
                    print("RSI anti crossed")
                    logging.info("RSI anti crossed")
                    break

                # Verify break out
                breakout = True if (abs(HAdf.Close[-1] - HAdf.Close[-1]) / 2) + min([HAdf.Close[-1], HAdf.Open[-1]]) < resistence_level else False
                if(breakout):
                    print("Breakout detected, entry position!" + position)
                    logging.info("Breakout detected, entry position!" + position)
                    event = "Entry"
                    break
            else:
                time.sleep(1)
                continue


        # 4 --- Taking decision
        if(event=="timeout" or event=="RSI_anti_cross"):
            continue
        else:
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
                order = client.futures_create_order(symbol=symbol, side='SELL', type='LIMIT', quantity=qty,
                                                    timeInForce='GTC', price=calculated_price_entry)
                # Verify if the entry order limit is filled:
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
                        break

                if (len(a.index) > 0):
                    print("Order filled! Time = " + str(datetime.now()))
                    logging.info("Order filled! Time = " + str(datetime.now()))
                    TP = calculated_price_entry - tp / 100 * calculated_price_entry
                    SL = calculated_price_entry + sl / 100 * calculated_price_entry

                    # 0 --- Get data and transform it to HA
                    try:
                        df = getdata_min_ago(symbol, interval=interval, lookback=str(10 * 60))
                    except Exception as e:
                        print(f'Problem in reading data, exception hya : {e}')
                        logging.info(f'Problem in reading data, exception hya : {e}')
                    # global HAdf,RSI_stoch_k,RSI_stoch_d,RSI
                    HAdf = HA_transformation(df)
                    RSI = round(pta.rsi(HAdf.Close, 14), 2)
                    tf, bf = supp_resis(HAdf, )
                    SL_support = tf[-1]
                    if (SL >= SL_support):
                        SL = SL_support + incertitude

                    order_tp = client.futures_create_order(symbol=symbol, side = "BUY", type='LIMIT', quantity=qty,
                                                           price=round(TP, 3), timeInForce='GTC')
                    order_sl = client.futures_create_order(symbol=symbol, side = "BUY", type='STOP_MARKET', quantity=qty,
                                                           stopPrice=round(SL, 3))
            except Exception as e:
                print(f'Problem in firing the order, exception hya : {e}')
                logging.info(f'Problem in firing the order, exception hya : {e}')

            try:
                a = pd.DataFrame(client.futures_position_information())
                a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
            except Exception as e:
                print(f'Problem in futures_position_information, exception hya : {e}')
                logging.info((f'Problem in futures_position_information, exception hya : {e}'))

            while (len(a.index) > 0):
                try:
                    print("Still in position, time = " + str(datetime.now()))
                    logging.info("Still in position, time = " + str(datetime.now()))
                    time.sleep(3)
                    a = pd.DataFrame(client.futures_position_information())
                    a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
                except Exception as e:
                    print(
                        f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')
                    logging.info(
                        f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')

            # Cancel all open orders
            try:
                client.futures_cancel_all_open_orders(symbol=symbol)
            except Exception as e:
                print(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')
                logging.info(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')

            #####################
            #### Write into another script!
            # --- save data to GS
            balance = pd.DataFrame(client.futures_account_balance())
            balance_usdt_t_final = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])

            if (balance_usdt_t_final > balance_usdt_t0):
                price_entry, time_entry = get_time_avgprice_order(order, symbol)
                price_exit, time_exit = get_time_avgprice_order(order_tp, symbol)
                print('TP reached')
                logging.info('TP reached')
                duration = \
                    round(
                        (datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_entry,
                                                                                               '%Y-%m-%d %H:%M:%S')).seconds / 60,
                        1
                    )
                Long_short = position
                # create data frame and save it in GS!
                df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
                      "T_entry": [str(time_entry)],
                      "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)], 'P_avg_exit': [str(price_exit)],
                      'Balance': [str(balance_usdt_t_final)],
                      'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)],
                      'Support_level': [str(resistence_level)]
                      }
                df = pd.DataFrame(df)
                add_1rowDF_to_GS(df, sheet_name="tracking")

            elif (balance_usdt_t_final < balance_usdt_t0):
                price_entry, time_entry = get_time_avgprice_order(order, symbol)
                price_exit, time_exit = get_time_avgprice_order(order_sl, symbol)
                print('SL reached')
                logging.info('SL reached')
                duration = \
                    round(
                        (datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_entry,
                                                                                               '%Y-%m-%d %H:%M:%S')).seconds / 60,
                        1
                    )
                Long_short = position
                # create data frame and save it in GS!
                df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
                      "T_entry": [str(time_entry)],
                      "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)], 'P_avg_exit': [str(price_exit)],
                      'Balance': [str(balance_usdt_t_final)],
                      'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)],
                      'Support_level': [str(resistence_level)]
                      }
                df = pd.DataFrame(df)
                add_1rowDF_to_GS(df, sheet_name="tracking")
            else:
                print('(its a timeout case )')
                logging.info('(its a timeout case)')


