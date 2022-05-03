
# Author: Ahmed / Yasine
# 26/04/2022
# Bot div

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
interval = "1m"


def div_5min(symbol = "WAVESUSDT", window_div= 7, tolerance = 0.25, levier = 1, tp=0.66, sl=0.59, interval = "5m", timeout_entry_seconds = 155):

    print("\n\n\n\n\n\n\n")
    logging.info("\n\n\n\n\n\n\n")
    print("##################################################################")
    print("##################################################################")
    print("##################################################################")
    print("##################################################################")
    logging.info("##################################################################")
    logging.info("##################################################################")
    logging.info("##################################################################")
    logging.info("##################################################################")
    print("\n\n\n\n\n\n\n")
    logging.info("\n\n\n\n\n\n\n")
    while(True):

        # Cancel all open orders (this line is not mandatory but just in case!)
        try:
            client.futures_cancel_all_open_orders(symbol=symbol)
        except Exception as e:
            print(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')
            logging.info(f'Problem in futures_cancel_all_open_orders, exception hya : {e}')

        # 0 --- traceback
        print("\n\n"+"###### Iteration at: "+str(datetime.now())+" ######")
        logging.info("\n\n"+"###### Iteration at: "+str(datetime.now())+" ######")

        # 1 --- Get data and transform it to HA
        try:
            df_5mn = getdata_min_ago(symbol, interval = interval, lookback= str(17*60))
        except Exception as e:
            print(f'Problem in reading data, exception hya : {e}')
            logging.info(f'Problem in reading data, exception hya : {e}')
        global HAdf_5mn,RSI_stoch_k,RSI_stoch_d,RSI
        HAdf_5mn = HA_transformation(df_5mn)
        RSI_stoch_k = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSIk_14_14_3_3, 2)  # k = blue # ignore warning
        RSI_stoch_d = round(pta.stochrsi(HAdf_5mn['Close']).STOCHRSId_14_14_3_3, 2)
        RSI = round(pta.rsi(HAdf_5mn.Close, 14), 2)
        Ema = pta.ema(HAdf_5mn.Close,200)[-1] # Review : 1- calcul not exact 100% to Binance
        if(HAdf_5mn.Close[-1] > Ema): # Review : 2- better way to identify the trend!
            Ema = "UP"
        else:
            Ema = "DOWN"

        # Save HA data: Needed for any debug
        try: HAdf_5mn.to_csv('Last_HA.csv')
        except Exception as e: print("I'm on the server man")
        try: HAdf_5mn.to_csv('Last_HA.csv')
        except Exception as e: print("I'm Not on the server man")

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

        # ISSUE with find_peaks
        if (OB_or_OS == 2):
            # Issue: if last pic is the highest, this stupid function won't take it, we should add it!
            max_last_pic = np.where(HAdf_5mn.Close == max(HAdf_5mn.iloc[[-3, -2, -1]].Close))[0][-1]  # [-1] to take the last maximum
            if (max_last_pic not in peaks):
                peaks = np.append(peaks, max_last_pic)
        # long (minima)
        else:
            # Issue: if last pic is the lowest, this stupid function won't take it, we should add it!
            min_last_pic = np.where(HAdf_5mn.Close == min(HAdf_5mn.iloc[[-3, -2, -1]].Close))[0][-1]
            if (min_last_pic not in peaks):
                peaks = np.append(peaks, min_last_pic)


        # 4 - b - Eliminate invalid last peaks (Stochastic + 3 candles verification)
        potential_pics = eliminate_last_pics_stocha_candles(OB_or_OS,peaks,HAdf_5mn,RSI_stoch_k)

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

        # 5 --- buy or selll
        if(Div):
            print("Div = True")
            logging.info("Div = True")
            # Get usdt futurse balance
            try:
                balance = pd.DataFrame(client.futures_account_balance())
                balance_usdt_t0 = float(balance.loc[balance['asset'] == 'USDT', 'balance'].iloc[0])
                balance_usdt = round(0.9*balance_usdt_t0,4)
                precision = 1  # WAVES
                qty = round(levier * balance_usdt / HAdf_5mn.iloc[[-1]].Close[0], precision)
                # update leverage
                client.futures_change_leverage(symbol=symbol, leverage=levier)
                # entry position (limit)
                # calculated_price_entry = round(HAdf_5mn.iloc[-1].Low,3) if (OB_or_OS == 0) else round(HAdf_5mn.iloc[-1].High,3)
                calculated_price_entry = round(HAdf_5mn.iloc[-1].Close, 3)
                order = client.futures_create_order(symbol=symbol, side='BUY' if (OB_or_OS == 0) else "SELL",
                                                    type='LIMIT', quantity=qty, timeInForce='GTC',
                                                    price = calculated_price_entry)

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
                        logging.info(f'Problem in futures_position_information (inside the first while loop), exception hya : {e}')
                    if(dif >=timeout_entry_seconds):
                        print("Entry position : Time out! time = " + str(datetime.now()))
                        logging.info("Entry position : Time out! time = " + str(datetime.now()))
                        break

                if(len(a.index) > 0):
                    print("Order filled! Time = " + str(datetime.now()))
                    logging.info("Order filled! Time = " + str(datetime.now()))
                    if (OB_or_OS == 0):
                        TP = calculated_price_entry + tp / 100 * calculated_price_entry
                        SL = calculated_price_entry - sl / 100 * calculated_price_entry
                    else:
                        TP = calculated_price_entry - tp / 100 * calculated_price_entry
                        SL = calculated_price_entry + sl / 100 * calculated_price_entry
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
                    time.sleep(3)
                    a = pd.DataFrame(client.futures_position_information())
                    a = a.loc[pd.to_numeric(a.entryPrice) > 0,]
                except Exception as e:
                    print(f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')
                    logging.info(f'Problem in futures_position_information (inside the second while loop), exception hya : {e}')

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

            if(balance_usdt_t_final>balance_usdt_t0):
                price_entry, time_entry = get_time_avgprice_order(order, symbol)
                price_exit, time_exit = get_time_avgprice_order(order_tp,symbol)
                print('TP reached')
                logging.info('TP reached')
                duration = \
                    round(
                        (datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_entry,'%Y-%m-%d %H:%M:%S')).seconds / 60,
                        1
                    )
                Long_short = "S" if (OB_or_OS == 2) else "L"
                if(Long_short == "S"):
                    Ema = "With" if (Ema == "DOWN") else "Against"
                else:
                    Ema = "Against" if (Ema == "DOWN") else "With"
                # create data frame and save it in GS!
                df =  {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)], "T_entry":[str(time_entry)],
                       "P_avg_entry":[str(price_entry)], 'T_exit':[str(time_exit)], 'P_avg_exit':[str(price_exit)],'Balance':[str(balance_usdt_t_final)],
                       'Balance_t0':[str(balance_usdt_t0)], 'Duration': [str(duration)], 'Div_type':[str(H_R)], 'Window(h)':[str(distance_2peaks)],
                       'Trend': [str(Ema)]}
                df = pd.DataFrame(df)
                add_1rowDF_to_GS(df, sheet_name="tracking")


            elif(balance_usdt_t_final<balance_usdt_t0):
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
                Long_short = "S" if (OB_or_OS == 2) else "L"
                if (Long_short == "S"):
                    Ema = "With" if (Ema == "DOWN") else "Against"
                else:
                    Ema = "Against" if (Ema == "DOWN") else "With"
                # create data frame and save it in GS!
                df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
                      "T_entry": [str(time_entry)],
                      "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)],
                      'P_avg_exit': [str(price_exit)], 'Balance': [str(balance_usdt_t_final)],
                      'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)], 'Div_type': [str(H_R)],
                      'Window(h)': [str(distance_2peaks)],
                      'Trend': [str(Ema)]}
                df = pd.DataFrame(df)
                add_1rowDF_to_GS(df, sheet_name="tracking")
            else :
                print('(its a timeout case )')
                logging.info('(its a timeout case)')

        else:
            print("skip (no divergence detected)")
            logging.info("skip (no divergence detected)")
            continue




div_5min(levier = 3)


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





