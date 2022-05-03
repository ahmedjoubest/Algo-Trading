
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





# Add and datetime.now().second > 50 !
# add time out not to miss opportuniutes f les crypto lokhrin

interval = "1m"
symbol = "WAVESUSDT"
timeout = 15

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

    if position == "nothing":
        continue

    if position == "long":

        # 1 --- Wait for the RSI cross
        while(RSI[-1]<30):

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
            print("waiting for the RSI cross")
        print("RSI crossed the position for "+ position)

        # 2 --- identify level of last support
        i = len(bf)-1
        while(HAdf.Close[-1] > bf[i]):
            i = i-1
        support_level = bf[i]
        print("support level = " + str(round(support_level,2)))

        # 3 --- Wait for the break out (or timeout, or RSI get back to OS)
        time_crossrsi = datetime.now()
        while(True): #

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
                break

            if(RSI[-1]<30):
                event = "RSI_anti_cross"
                print("RSI anti crossed")
                break

            # Verify break out code
            breakout = True if (abs(HAdf.Close[-1]-HAdf.Close[-1])/2)+min([HAdf.Close[-1],HAdf.Open[-1]]) > support_level else False
            if(breakout == True):
                print("Breakout detected, entry position : !" + position)
                event = "Entry"
                break

        # 4 --- Taking decision
        if(event=="timeout" or event=="RSI_anti_cross"):
            continue
        else:
            print("entry")
            # Entry position
            # code entry position





    if position == "short":

        # 1 --- Wait for the RSI cross
        while(RSI[-1]>70):

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
            print("waiting for the RSI cross")
        print("RSI crossed the position for "+ position)

        # 2 --- identify level of last support
        i = len(tf) - 1
        while (HAdf.Close[-1] < tf[i]):
            i = i - 1
        resistence_level = tf[i]
        print("resistence level = " + str(round(resistence_level,2)))

        # 3 --- Wait for the break out (or timeout, or RSI get back to OS)
        time_crossrsi = datetime.now()
        while(True):
            print("waiting for the breakout")
            dif = round((datetime.now() - time_crossrsi).seconds / 60, 2)
            if(dif>timeout):
                event = "timeout"
                print("Break out time out")
                break

            if(RSI[-1]>70):
                event = "RSI_anti_cross"
                print("RSI anti crossed")
                break

            # Verify break out code
            breakout = True if (abs(HAdf.Close[-1] - HAdf.Close[-1]) / 2) + min([HAdf.Close[-1], HAdf.Open[-1]]) < resistence_level else False
            breakout = False
            if(breakout == True):
                print("Breakout detected, entry position!" + position)
                event = "Entry"
                break

        # 4 --- Taking decision
        if(event=="timeout" or event=="RSI_anti_cross"):
            continue
        else:
            print("entry")
            # Entry position
            # code entry position


