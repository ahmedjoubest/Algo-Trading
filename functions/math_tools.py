
# Author: Ahmed / Yasine
# 26/04/2022

# --- 1 keep uncrossed preaks rpice
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

print("'math_tools.py' has been Sucessfully executed ")
