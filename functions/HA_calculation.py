
# Author: Ahmed
# 14/01/2022
# Defining functions to calculate HA candles from normal candles

# --- 4 Transformation from normal candles to HA
def HA_transformation(DF):
    HAdf = DF[['Open', 'High', 'Low', 'Close']]
    HAdf['Close'] = (DF['Open'] + DF['Close'] + DF['Low'] + DF['High']) / 4 # ignore error, just warning
    for i in range(len(DF)):
        if i == 0:
            HAdf.iat[0, 0] = round(((DF['Open'].iloc[0] + DF['Close'].iloc[0]) / 2), 2)
        else:
            HAdf.iat[i, 0] = round(((HAdf.iat[i - 1, 0] + HAdf.iat[i - 1, 3]) / 2), 2)
    HAdf['High'] = HAdf.loc[:, ['Open', 'Close']].join(DF['High']).max(axis=1)
    HAdf['Low'] = HAdf.loc[:, ['Open', 'Close']].join(DF['Low']).min(axis=1)
    return(HAdf)

print("'HA_calculation.py' has been Sucessfully executed ")
