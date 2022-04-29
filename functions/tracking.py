
# Author: Ahmed / Yasine
# 29/04/2022
# https://www.youtube.com/watch?v=ddf5Z0aQPzY&ab_channel=FrankMularcik
# limit api : 100 value per 100 second (read or update) according to the video

from oauth2client.service_account import ServiceAccountCredentials
import gspread

def add_1rowDF_to_GS(df,sheet_name="tracking"):

    # establish connection
    scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']
    try: creds = ServiceAccountCredentials.from_json_keyfile_name('../Backtest/bot-tracking-348705-a840e831cb8c.json', scope)
    except Exception as e: print("I am on the server man")
    try: creds = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/ec2-user/Algo-Trading/Backtest/bot-tracking-348705-a840e831cb8c.json',
        scope)
    except Exception as e: print("I am NOT on the server man")
    client = gspread.authorize(creds)
    my_gs = client.open("Trades Analysis").worksheet(sheet_name) # or my_gs = client.open("Trades Analysis").sheet1

    # Add a row : find the first empty row index
    i = 1
    while my_gs.cell(i,1).value is not None:
        i=i+1
        # it will need sys.sleep with big amount of rows!
    for j in range(1, 1 + len(df.count())):
        my_gs.update_cell(i,j,df.iloc[0,j-1])
        # it will need sys.sleep with big amount of rows & columns!

print("'tracking.py' has been Sucessfully executed ")
