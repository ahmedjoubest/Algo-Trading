
# Author: Ahmed / Yasine
# 26/04/2022
# Function that eliminates crossed pics

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


# Uncrossed peaks for RSI
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

print("'math_tools.py' has been Sucessfully executed ")
