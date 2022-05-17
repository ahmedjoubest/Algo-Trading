
# Author: Ahmed / Yasine
# 17/05/2022

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

df = pd.read_csv("Trades Analysis - Sheet7.csv")

f= open("pine_script.txt","w+")
f.write("//@version=5 \r\n")
f.write('indicator(title="Analysis", overlay=true)\r\n')

for i in range(len(df)):
     direction = df.Direction[[i]][i]
     winorloss = df.winorloss[[i]][i]
     t_entry = df.T_entry[[i]][i][0:16]
     if(winorloss=="W" and direction=="long"):
          f.write("lineDate_"+str(i)+" = timestamp('"+t_entry+"')\r\n")
          f.write("period_"+str(i)+" = time == lineDate_"+str(i)+"\r\n")
          f.write("label.new(lineDate_"+str(i)+", ta.valuewhen(period_"+str(i)+", low, 0), xloc=xloc.bar_time,  style = label.style_label_up, color=#00FF00,size= size.tiny)\r\n")
     elif(winorloss=="L" and direction=="long"):
          f.write("lineDate_" + str(i) + " = timestamp('" + t_entry + "')\r\n")
          f.write("period_" + str(i) + " = time == lineDate_" + str(i)+"\r\n")
          f.write("label.new(lineDate_" + str(i) + ", ta.valuewhen(period_" + str(i) + ", low, 0), xloc=xloc.bar_time,  style = label.style_label_up, color=#FFA07A,size= size.tiny)\r\n")
     elif(winorloss=="W" and direction=="short"):
          f.write("lineDate_"+str(i)+" = timestamp('"+t_entry+"')\r\n")
          f.write("period_"+str(i)+" = time == lineDate_"+str(i)+"\r\n")
          f.write("label.new(lineDate_"+str(i)+", ta.valuewhen(period_"+str(i)+", high, 0), xloc=xloc.bar_time,  style = label.style_label_down, color=#00FF00,size= size.tiny)\r\n")
     else:
          f.write("lineDate_" + str(i) + " = timestamp('" + t_entry + "')\r\n")
          f.write("period_" + str(i) + " = time == lineDate_" + str(i)+"\r\n")
          f.write("label.new(lineDate_" + str(i) + ", ta.valuewhen(period_" + str(i) + ", high, 0), xloc=xloc.bar_time,  style = label.style_label_down, color=#FFA07A,size= size.tiny)\r\n")
f.close()
