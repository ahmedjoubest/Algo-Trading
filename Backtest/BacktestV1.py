
# --- 0 Import
import pandas as pd
import numpy as np
from binance.client import Client
import sqlalchemy
from binance import BinanceSocketManager
import pandas_ta as pta
from sspipe import p, px

# --- 1 API
client = Client()

# 1 --- Sourcing functions
execfile("functions/get_data.py")
execfile("functions/HA_calculation.py")
# execfile("functions/RSI_calculation.py") # We are using RSI

# 2 --- Get data and transform it to HA
df_5mn = getdata_date(symbol = "WAVESUSDT", interval = "5m", date1= "17 Apr, 2022", date2 = "18 Apr, 2022")
HAdf_5mn = HA_transformation(df_5mn)

# 3 --- RSI calculation
cRSI_stoch_k = pta.stochrsi(HAdf_5mn['Close']).STOCHRSIk_14_14_3_3 | p(round,2) # k = blue # ignore warning
RSI_stoch_d = pta.stochrsi(HAdf_5mn['Close']).STOCHRSId_14_14_3_3 | p(round,2)

