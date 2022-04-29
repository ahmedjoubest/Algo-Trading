
# Author: Ahmed
# 17/04/2022
# Defining functions to retrieve data from Binance

def getdata_min_ago(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback+" min ago UTC", klines_type=HistoricalKlinesType.FUTURES))
    frame = frame.iloc[:,:6] # on s'arrête a la colonne 6
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float) # transform string to floats :
    # get only open/close prices
    frame = frame[['Open','Close','High','Low']]
    return frame

def getdata_date(symbol, interval, date1, date2):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, date1, date2, klines_type=HistoricalKlinesType.FUTURES))
    frame = frame.iloc[:,:6] # on s'arrête a la colonne 6
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float) # transform string to floats :
    # get only open/close prices
    frame = frame[['Open','Close','High','Low']]
    return frame

# Get time and avg price from order
def get_time_avgprice_order(order,symbol):
    last_5_orders = client.futures_get_all_orders(symbol = symbol,limit = 5)
    last_5_orders = pd.DataFrame(last_5_orders)
    last_5_orders = last_5_orders.loc[last_5_orders['orderId']==order['orderId']]
    price = float(last_5_orders.avgPrice.iloc[0])
    time = str(datetime.fromtimestamp(last_5_orders.time.iloc[0]/1000))[0:19]
    return(price,time)

print("'get_data.py' has been Sucessfully executed ")
