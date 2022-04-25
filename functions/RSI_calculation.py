
# Author: Ahmed
# 14/01/2022
# Defining functions to calculate RSI's

# --- 1 RSI calculation function
def RSIcalc(symbol = "BNBUSDT", interval = "1m", lookback = str(60*24 + 4*60), MA_n = 60*4,
            n = 20):
    df = getdata(symbol, interval, lookback) # Get data
    df['MA_n'] = df['Close'].rolling(window=MA_n).mean() # MA column (for the 1st condition backtest)
    df['price change'] = df['Close'].pct_change()
    df['Upmove'] = df['price change'].apply(lambda x: x if x>0 else 0)
    df['Downmove'] = df['price change'].apply(lambda x: abs(x) if x<0 else 0)
    df['avg Up'] = df['Upmove'].ewm(span=n).mean()
    df['avg Down'] = df['Downmove'].ewm(span=n).mean()
    df = df.dropna()
    df['RS'] = df['avg Up'] / df['avg Down']
    df['RSI'] = df['RS'].apply(lambda x: 100-(100/(x+1)))
    # Optimization for sql data base: drop useless columns
    return df[['Open','Close','MA_n','RSI']]

print("'RSI_calculation.py' has been Sucessfully executed ")
