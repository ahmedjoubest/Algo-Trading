
# Author: Ahmed / Yasine
# 26/04/2022

# --- 1 keep uncrossed preaks rpice
import math

import pandas_ta


def keep_uncrossed_peaks(close,open,peaks,tolerance,Short):

    uncrossed_peaks = []

    if(Short):
        # Short
        for peak in peaks:
            price_pic = close.iloc[[peak]]
            price_current = close.iloc[peaks[-1]]
            line = np.linspace(start=price_pic, stop=price_current, num = peaks[-1]-peak+1)
            # Create DataFrame
            df = pd.DataFrame({'Close': close.iloc[np.linspace(start = peak, stop = peaks[-1], num = peaks[-1]-peak+1)],
                               'Open': open.iloc[np.linspace(start = peak, stop = peaks[-1], num = peaks[-1]-peak+1)]})
            threshold = (1-tolerance)*abs(df.Close - df.Open) + df.min(axis=1)
            if(
                sum(np.array(sum(line.tolist(), [])) >= threshold) == len(np.array(sum(line.tolist(), [])) >= threshold)
            ):
                uncrossed_peaks.append(peak)
    else:
        # Long
        for peak in peaks:
            price_pic = close.iloc[[peak]]
            price_current = close.iloc[peaks[-1]]
            line = np.linspace(start=price_pic, stop=price_current, num=peaks[-1] - peak + 1)
            # Create DataFrame
            df = pd.DataFrame({'Close': close.iloc[np.linspace(start=peak, stop=peaks[-1], num=peaks[-1] - peak + 1)],
                               'Open': open.iloc[np.linspace(start=peak, stop=peaks[-1], num=peaks[-1] - peak + 1)]})
            threshold = (tolerance)*abs(df.Close - df.Open) + df.min(axis=1)
            if(
                sum(np.array(sum(line.tolist(), [])) <= threshold) == len(np.array(sum(line.tolist(), [])) <= threshold)
            ):
                uncrossed_peaks.append(peak)
    return(uncrossed_peaks)


# --- 2 keep uncrossed peaks rsi
def keep_uncrossed_peaks_RSI(RSI,peaks,Short):

    uncrossed_peaks = []

    if(Short):
        # Short
        for peak in peaks:
            rsi_pic = RSI.iloc[[peak]]
            rsi_current = RSI.iloc[[peaks[-1]]]
            line = np.linspace(start=rsi_pic, stop=rsi_current, num = peaks[-1]-peak+1)
            rsi = np.array(RSI.iloc[np.linspace(start = peak, stop = peaks[-1], num = peaks[-1]-peak+1)])
            if(
                sum(np.array(sum(line.tolist(), [])) >= rsi) == len(np.array(sum(line.tolist(), [])) >= rsi)
            ):
                uncrossed_peaks.append(peak)
    else:
        # Long
        for peak in peaks:
            rsi_pic = RSI.iloc[[peak]]
            rsi_current = RSI.iloc[[peaks[-1]]]
            line = np.linspace(start=rsi_pic, stop=rsi_current, num=peaks[-1] - peak + 1)
            rsi = np.array(RSI.iloc[np.linspace(start=peak, stop=peaks[-1], num=peaks[-1] - peak + 1)])
            if (
                    sum(np.array(sum(line.tolist(), [])) <= rsi) == len(np.array(sum(line.tolist(), [])) <= rsi)
            ):
                uncrossed_peaks.append(peak)
    return(uncrossed_peaks)

# --- 3 Transformation from normal candles to HA
def HA_transformation(DF):
    HAdf = DF[['Open', 'High', 'Low', 'Close']]
    HAdf['Close'] = (DF['Open'] + DF['Close'] + DF['Low'] + DF['High']) / 4 # ignore error, just warning
    for i in range(len(DF)):
        if i == 0:
            HAdf.iat[0, 0] = round(((DF['Open'].iloc[0] + DF['Close'].iloc[0]) / 2), 4)
        else:
            HAdf.iat[i, 0] = round(((HAdf.iat[i - 1, 0] + HAdf.iat[i - 1, 3]) / 2), 4)
    HAdf['High'] = HAdf.loc[:, ['Open', 'Close']].join(DF['High']).max(axis=1)
    HAdf['Low'] = HAdf.loc[:, ['Open', 'Close']].join(DF['Low']).min(axis=1)
    return(HAdf)

# --- 4 Verification stochastic 5min
def verify_stochastic_5min(OB_or_OS, RSI_stoch_d, RSI_stoch_k):
    if (OB_or_OS == 2):
        # last two candles are green
        if (((RSI_stoch_d.iloc[[-1]] >= 80) & (RSI_stoch_k.iloc[[-1]] >= 80))[0]):
            print("next steps: short (stochastic is verified)")
            logging.info("next steps: short (stochastic is verified)")
            return(True)
        else:
            print("skip: step 2 (stochastic not verified)")
            logging.info("skip: step 2 (stochastic not verified)")
            return(False)
    elif (OB_or_OS == 0):
        # last two candles are red
        if (((RSI_stoch_d.iloc[[-1]] <= 20) & (RSI_stoch_k.iloc[[-1]] <= 20))[0]):
            print("next steps: long (stochastic is verified)")
            logging.info("next steps: long (stochastic is verified)")
            return(True)
        else:
            print("skip: step 2 (stochastic not verified)")
            logging.info("skip: step 2 (stochastic not verified)")
            return(False)
    else:
        print("skip: last two candles are not in the same color!")
        logging.info("skip: last two candles are not in the same color!")
        return(False)

# --- 5 Verification condition 5 min
def verify_condition_5min(OB_or_OS,HAdf_5mn):
    # 3 - a - position short
    if (OB_or_OS == 2):
        # {High(t) - Low(t)} should be lower than {High(t-1) - Low(t-1)}
        if ((HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[1] <= (HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[0]):
            print("next steps (Short): Verify div (condition 5 min verified)")
            logging.info("next steps (Short): Verify div (condition 5 min verified)")
            return(True)
        else:
            print("skip (condition 5 min NOT verified)")
            logging.info("skip (condition 5 min NOT verified)")
            return(False)
    # 3 - b - position Long
    if (OB_or_OS == 0):
        # {High(t) - Low(t)} should be lower than {High(t-1) - Low(t-1)}
        if ((HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[1] <= (HAdf_5mn.tail(2).High - HAdf_5mn.tail(2).Low)[0]):
            print("next steps (Long): Verify div (condition 5 min verified)")
            logging.info("next steps (Long): Verify div (condition 5 min verified)")
            return(True)
        else:
            print("skip (condition 5 min NOT verified)")
            logging.info("skip (condition 5 min NOT verified)")
            return(False)

# --- 6 Function to eliminate invalid last peaks (Stochastic + 3 candles verification)
def eliminate_last_pics_stocha_candles(OB_or_OS,peaks,HAdf_5mn,RSI_stoch_k):
    if (OB_or_OS == 2):
        # short
        potential_pics = []
        for idx in peaks:
            if idx == peaks[-1]:
                potential_pics.append(idx)
                break
            # Stochastic must be verified
            if (((RSI_stoch_k.iloc[[idx]] >= 65))[0]):
                # At least 3 candles same color
                if (
                        sum(HAdf_5mn.iloc[[idx - 1, idx, idx + 1]].Close > HAdf_5mn.iloc[
                            [idx - 1, idx, idx + 1]].Open) == 3 or \
                        sum(HAdf_5mn.iloc[[idx - 2, idx - 1, idx]].Close > HAdf_5mn.iloc[
                            [idx - 2, idx - 1, idx]].Open) == 3 or \
                        sum(HAdf_5mn.iloc[[idx, idx + 1, idx + 2]].Close > HAdf_5mn.iloc[
                            [idx, idx + 1, idx + 2]].Open) == 3
                ):
                    potential_pics.append(idx)
                else:
                    continue
            else:
                continue
        return(potential_pics)
    else:
        # long
        potential_pics = []
        for idx in peaks:
            if idx == peaks[-1]:
                potential_pics.append(idx)
                break
            # Stochastic must be verified
            if (((RSI_stoch_k.iloc[[idx]] <= 35))[0]):
                # At least 3 candles
                if (
                        sum(HAdf_5mn.iloc[[idx - 1, idx, idx + 1]].Close < HAdf_5mn.iloc[
                            [idx - 1, idx, idx + 1]].Open) == 3 or \
                        sum(HAdf_5mn.iloc[[idx - 2, idx - 1, idx]].Close < HAdf_5mn.iloc[
                            [idx - 2, idx - 1, idx]].Open) == 3 or \
                        sum(HAdf_5mn.iloc[[idx, idx + 1, idx + 2]].Close < HAdf_5mn.iloc[
                            [idx, idx + 1, idx + 2]].Open) == 3
                ):
                    potential_pics.append(idx)
                else:
                    continue
            else:
                continue
        return (potential_pics)

# --- 7 Function to eliminate peaks without divergence (must be reviewed)
def divergence_verificaiton(uncrossed_peaks_RSI,OB_or_OS,RSI,HAdf_5mn,currect_pic):
    global H_R, distance_2peaks
    Div = False
    for peak in uncrossed_peaks_RSI:
        if (OB_or_OS == 2):
            # Short
            # Hidden divergence:
            if (32 < RSI[peak] < 68):
                if (HAdf_5mn.iloc[[peak]].Close[0] > HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                        RSI[peak] < RSI[currect_pic]):
                    Div = True
                    print("Hidden Div detected for 'Short' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    logging.info("Hidden Div detected for 'Short' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    H_R = "H"
                    distance_2peaks = (RSI.iloc[[currect_pic]].index - RSI.iloc[[peak]].index).seconds[0]/(60*60)
                    break
                else:
                    continue
            elif (RSI[peak] >= 68):
                # Regular divergence:
                if (HAdf_5mn.iloc[[peak]].Close[0] < HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                        RSI[peak] > RSI[currect_pic]):
                    Div = True
                    print("Regular Div detected for 'Short' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    logging.info("Regular Div detected for 'Short' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    H_R = "R"
                    distance_2peaks = (RSI.iloc[[currect_pic]].index - RSI.iloc[[peak]].index).seconds[0]/(60*60)
                    break
                else:
                    continue
        else:
            # Long
            # Hidden divergence:
            if (32 < RSI[peak] < 68):
                if (HAdf_5mn.iloc[[peak]].Close[0] < HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                        RSI[peak] > RSI[currect_pic]):
                    Div = True
                    print("Hidden Div detected for 'Long' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    logging.info("Hidden Div detected for 'Long' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    H_R = "H"
                    distance_2peaks = (RSI.iloc[[currect_pic]].index - RSI.iloc[[peak]].index).seconds[0]/(60*60)
                    break
                else:
                    continue
            elif (RSI[peak] <= 32):
                # Regular divergence:
                if (HAdf_5mn.iloc[[peak]].Close[0] > HAdf_5mn.iloc[[currect_pic]].Close[0] and \
                        RSI[peak] < RSI[currect_pic]):
                    Div = True
                    print("Regular Div detected for 'Long' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    logging.info("Regular Div detected for 'Long' in: " + str(HAdf_5mn.iloc[[peak]].index))
                    H_R = "R"
                    distance_2peaks = (RSI.iloc[[currect_pic]].index - RSI.iloc[[peak]].index).seconds[0]/(60*60)
                    break
                else:
                    continue
    return(Div)


# --- 8 ATR Support resistence
def supp_resis(df,length = 14,mult = 2,maLen = 14):

    ATR = pta.atr(df.High,df.Low, df.Close, length)
    dev = mult*ATR
    basis = pta.sma(df.Close,length)
    upper = basis + dev
    lower = basis - dev
    bbr = (df.Close - lower)/(upper - lower)
    bbe = pta.ema(bbr, maLen)
    up = []
    for idx, element in enumerate(bbe):
        if (bbe[idx - 1] > bbe[idx] and bbe[idx - 2] < bbe[idx - 1]):
            up.append(bbe[idx])
        else:
            up.append(float("NAN"))
    bt=[]
    for idx, element in enumerate(bbe):
        if (bbe[idx - 1] < bbe[idx] and bbe[idx - 2] > bbe[idx - 1]):
            bt.append(bbe[idx])
        else:
            bt.append(float("NAN"))
    up = pd.Series(up, index=bbe.index)
    bt = pd.Series(bt, index=bbe.index)
    topH = []
    for idx,element in enumerate(up):
        if(not math.isnan(element)):
            topH.append(max(df.High.iloc[idx],df.High.iloc[idx-1],df.High.iloc[idx-2]))
        else:
            topH.append(float("NAN"))
    topH = pd.Series(topH, index=bbe.index)
    bottomL = []
    for idx, element in enumerate(bt):
        if (not math.isnan(element)):
            bottomL.append(min(df.Low.iloc[idx], df.Low.iloc[idx - 1], df.Low.iloc[idx - 2]))
        else:
            bottomL.append(float("NAN"))
    bottomL = pd.Series(bottomL, index=bbe.index)
    tf = topH.fillna(method = "ffill").shift(-1)
    bf = bottomL.fillna(method = "ffill").shift(-1)

    tf[-1]= tf[-2]
    bf[-1]= bf[-2]

    return(tf,bf)


# --- detect RSI cross
def detect_RSI_cross(RSI,window=60,bottom_line_rsi=30 ,top_line_rsi = 70):
    if 30 < RSI[-1] < 70:
        top_line = pd.Series([top_line_rsi] * len(RSI))
        bottom_line = pd.Series([bottom_line_rsi] * len(RSI))
        top_line.index, bottom_line.index = RSI.index, RSI.index
        idx_cross_rsi_bottom = np.argwhere(np.diff(np.sign(bottom_line - RSI))).flatten()
        idx_cross_rsi_top = np.argwhere(np.diff(np.sign(top_line - RSI))).flatten()
        idx_cross_rsi_bottom = np.append(idx_cross_rsi_bottom, [0, 1]) if (
                len(idx_cross_rsi_bottom) == 0) else idx_cross_rsi_bottom
        idx_cross_rsi_top = np.append(idx_cross_rsi_top, [0, 1]) if (len(idx_cross_rsi_top) == 0) else idx_cross_rsi_top
        idx_cross_rsi_bottom = RSI.index[idx_cross_rsi_bottom + 1][-1]
        idx_cross_rsi_top = RSI.index[idx_cross_rsi_top + 1][-1]
        cross_time = idx_cross_rsi_top if (idx_cross_rsi_top > idx_cross_rsi_bottom) else idx_cross_rsi_bottom
        if(cross_time < (RSI.iloc[[-1]].index -timedelta(minutes = window))):
            print("RSI cross: TIMEOUT")
            logging.info("RSI cross: TIMEOUT")
            position = "nothing"
            cross_time = None
        else:
            position = "short" if (idx_cross_rsi_top > idx_cross_rsi_bottom) else "long"
            print(position + " position detected --- cross_time = "+str(cross_time))
            logging.info(position + " position detected --- cross_time = "+str(cross_time))
    else:
        print("RSI is still on OB or OS")
        logging.info("RSI is still on OB or OS")
        position = "nothing"
        cross_time = None
    return(position,cross_time)


# --- identify level breakout
def identify_breakout_level(position,tf,bf,price, moment):
    tf = tf[tf.index<=moment]
    bf = bf[bf.index<=moment]
    price = price[price.index<=moment]
    if position == "long":
        i = len(bf) - 1
        while (price[-1] >= bf[i]):
            i = i - 1
        level = bf[i]
        time_level = bf.index[i]
        print("support level = " + str(round(level, 4)))
        logging.info("support level = " + str(round(level, 4)))
        return(level,time_level)
    else:
        i = len(tf) - 1
        while (price[-1] <= tf[i]):
            i = i - 1
        level = tf[i]
        time_level = tf.index[i]
        print("resistence level = " + str(round(level, 4)))
        logging.info("resistence level = " + str(round(level, 4)))
        return (level,time_level)


# --- detect breakout cross
def detect_breakout(position,Hadf,level):
    if position=="long":
        if (abs(HAdf.Close[-1]-HAdf.Open[-1])/2)+min([HAdf.Close[-1],HAdf.Open[-1]]) >= level:
            if (abs(HAdf.Close[-2]-HAdf.Open[-2])/2)+min([HAdf.Close[-2],HAdf.Open[-2]]) >= level:
                print("Break out happened (too late to enter)")
                logging.info("Break out happened (too late to enter)")
                breakout = False
            else:
                breakout = True
                print("Break out position detected, entry!")
                logging.info("Break out position detected, entry!")
        else:
            breakout = False
            print("Break out coming (too early to enter)")
            logging.info("Break out coming (too early to enter)")
    else:
        if (abs(HAdf.Close[-1]-HAdf.Open[-1])/2)+min([HAdf.Close[-1],HAdf.Open[-1]]) <= level:
            if (abs(HAdf.Close[-2]-HAdf.Open[-2])/2)+min([HAdf.Close[-2],HAdf.Open[-2]]) <= level:
                print("Break out happened (too late to enter)")
                logging.info("Break out happened (too late to enter)")
                breakout = False
            else:
                breakout = True
                print("Break out position detected, entry!")
                logging.info("Break out position detected, entry!")
        else:
            breakout = False
            print("Break out coming (too early to enter)")
            logging.info("Break out coming (too early to enter)")
    return(breakout)

# fig = go.Figure(
#    data=[
    #        go.Candlestick(
    #            x=df.index,
    #          open=df.Open,
    #        high=df.High,
    #        low=df.Low,
    #       close=df.Close
    #   ),
    #  go.Scatter(
    #      x=bf.index,
    #       y=bf,
    #        mode = 'markers',
    #        line_color = "green"
    #   ),
    #   go.Scatter(
    #       x=tf.index,
    #       y=tf,
    #      mode = 'markers',
    #      line_color = "red"
    #   )
# ]
#)
#fig.show()



print("'math_tools.py' has been Sucessfully executed ")
