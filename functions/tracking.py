
# Author: Ahmed / Yasine
# 29/04/2022
# https://www.youtube.com/watch?v=ddf5Z0aQPzY&ab_channel=FrankMularcik
# limit api : 100 value per 100 second (read or update) according to the video
import time


def add_1rowDF_to_GS(df,sheet_name="tracking"):

    # establish connection
    scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']
    try: creds = ServiceAccountCredentials.from_json_keyfile_name('bot-tracking-348705-a840e831cb8c.json', scope)
    except Exception as e: print("I am on the server man")
    try: creds = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/ec2-user/Algo-Trading/Backtest/bot-tracking-348705-a840e831cb8c.json',
        scope)
    except Exception as e: print("I am NOT on the server man")
    client = gspread.authorize(creds)
    my_gs = client.open("Trades Analysis").worksheet(sheet_name) # or my_gs = client.open("Trades Analysis").sheet1

    time.sleep(1)
    my_gs.insert_rows(values=[list(df.iloc[0])], row=2)


    # Add a row : find the first empty row index
    # i = 1 # redha kber men 1 wla lqa chi tariqa hsn mn hadi a sat
    # while my_gs.cell(i,1).value is not None:
    #     i=i+1
    #    time.sleep(2) # must be optimized !
    #    # it will need sys.sleep with big amount of rows! (1 second dayr f lvidéo)
    # for j in range(1, 1 + len(df.count())):
    #    time.sleep(2)
    #    my_gs.update_cell(i,j,df.iloc[0,j-1])
    # it will need sys.sleep with big amount of rows & columns!

def get_dd_maxtp(df,price_entry,price_exit,time_entry, time_exit,win,position):
    time_entry = time_entry[0:16] + ':00'
    time_exit = time_exit[0:16] + ':59'
    time_exit = datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S')
    time_entry = datetime.strptime(time_entry, '%Y-%m-%d %H:%M:%S')
    if position == "long":
        if win:
            serie = df.Low[df.Low.index<=time_exit]
            minimum_price = serie[serie.index>=time_entry].min()
            DD = (price_entry-minimum_price)/price_entry
            maxtp = (price_exit - price_entry)/price_entry
        else:
            serie = df.High[df.High.index <= time_exit]
            maximum_price = serie[serie.index >= time_entry].max()
            maxtp = (maximum_price - price_entry) / price_entry
            DD = (price_entry - price_exit)/price_entry
    else:#
        if win:
            serie = df.High[df.High.index <= time_exit]
            maximum_price = serie[serie.index >= time_entry].max()
            DD = (maximum_price - price_entry) / price_entry
            maxtp = (price_entry - price_exit) / price_entry
        else:
            serie = df.Low[df.Low.index <= time_exit]
            minimum_price = serie[serie.index >= time_entry].min()
            maxtp = (price_entry - minimum_price) / price_entry
            DD = (price_exit - price_entry) / price_entry
    return (DD, maxtp)


def getdata_and_save_to_sheet(symbol, position, balance_usdt_t_final, balance_usdt_t0, order, order_tp, order_sl, breakout_level,df,sheet_name="tracking"):
    if (balance_usdt_t_final > balance_usdt_t0):
        win = True
        price_entry, time_entry = get_time_avgprice_order(order, symbol)
        price_exit, time_exit = get_time_avgprice_order(order_tp, symbol)
        print('TP reached')
        logging.info('TP reached')
        duration = \
            round(
                (datetime.strptime(time_exit, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_entry,
                                                                                       '%Y-%m-%d %H:%M:%S')).seconds / 60,
                1
            )
        Long_short = position
        # create data frame and save it in GS!
        DD, maxtp = get_dd_maxtp(df,price_entry,price_exit,time_entry, time_exit,win,position)
        df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
              "T_entry": [str(time_entry)],
              "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)], 'P_avg_exit': [str(price_exit)],
              'Balance': [str(balance_usdt_t_final)],
              'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)],
              'Support_level': [str(breakout_level)], 'DD': [str(DD)], 'TP_max': [str(maxtp)]
              }
        df = pd.DataFrame(df)
        add_1rowDF_to_GS(df, sheet_name=sheet_name)

    elif (balance_usdt_t_final < balance_usdt_t0):
        win = False
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
        Long_short = position
        # create data frame and save it in GS!
        DD, maxtp = get_dd_maxtp(df, price_entry, price_exit, time_entry, time_exit, win, position)
        df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
              "T_entry": [str(time_entry)],
              "P_avg_entry": [str(price_entry)], 'T_exit': [str(time_exit)], 'P_avg_exit': [str(price_exit)],
              'Balance': [str(balance_usdt_t_final)],
              'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str(duration)],
              'breakout_level': [str(breakout_level)], 'DD': [str(DD)], 'TP_max': [str(maxtp)]
              }
        df = pd.DataFrame(df)
        add_1rowDF_to_GS(df, sheet_name = sheet_name)
    else:
        print('(its a timeout case )')
        logging.info('(its a timeout case)')
        price_entry, time_entry = get_time_avgprice_order(order, symbol)
        Long_short = position
        # create data frame and save it in GS!
        df = {'Symbol': [str(symbol)], 'levier': [str(levier)], 'Direction': [str(Long_short)],
              "T_entry": [str(time_entry)],
              "P_avg_entry": [str(price_entry)], 'T_exit': [str('')], 'P_avg_exit': [str('')],
              'Balance': [str(balance_usdt_t_final)],
              'Balance_t0': [str(balance_usdt_t0)], 'Duration': [str('')],
              'breakout_level': [str(breakout_level)], 'DD': [str('')], 'TP_max': [str('')]
              }
        df = pd.DataFrame(df)
        add_1rowDF_to_GS(df, sheet_name=sheet_name)


print("'tracking.py' has been Sucessfully executed ")
