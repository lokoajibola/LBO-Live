# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 16:46:28 2024


@author: LK
"""

import pandas as pd
import MetaTrader5 as mt5
import numpy as np
import datetime
import pytz
import pandas_ta as ta
from time import sleep
import matplotlib.pyplot as plt


curr = 'XAUUSDm'
e_news = 'Non-Farm Employment Change'
# e_news = 'CPI y/y'

# SET THE NEWS TIME
news_min = 1
news_hour = 22
time_frame = 10
i = 0 

if time_frame == 15:
    time_frame2 = mt5.TIMEFRAME_M15
    i = i*3 # FVG in points
elif time_frame == 5:
    time_frame2 = mt5.TIMEFRAME_M5
    i = i*2 # FVG in points
elif time_frame == 10:
    time_frame2 = mt5.TIMEFRAME_M10
    i = i*2 # FVG in points
elif time_frame == 1:
    time_frame2 = mt5.TIMEFRAME_M1
    i = i*1 # FVG in points
elif time_frame == 30:
    time_frame2 = mt5.TIMEFRAME_M30
    i = i*4 # FVG in points
elif time_frame >= 59:
    time_frame2 = mt5.TIMEFRAME_H1
    i = i*5 # FVG in points

# GET THE ECONOMIC NEWS DATA AND DATETIME
df = pd.read_csv('news2.csv')

df['DATETIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])

# Filter the DataFrame for rows where 'news' column is "employment" and 'actual' > 'forecast'
df1 = df[(df['NEWS'] == e_news) & (df['ACTUAL'] > df['FORECAST'])]
# dff['DATETIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])


# LOGIN TO MT5
account = 187255335 #51610727
mt5.initialize("C:/Program Files/MetaTrader 5 EXNESS/terminal64.exe")
authorized=mt5.login(account, password="Yacht(1)", server = "Exness-MT5Real27")

if authorized:
    print("Connected: Connecting to MT5 Client")
    # sleep(3)
else:
    print("Failed to connect at account #{}, error code: {}"
          .format(account, mt5.last_error()))
   
# establish connection to MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =",mt5.last_error())
    mt5.shutdown()
    
tz = pytz.timezone("Europe/London")
mt5_now = datetime.datetime.fromtimestamp(mt5.symbol_info(curr).time)
news_time = datetime.datetime.now(tz).replace(hour=news_hour, minute=news_min, second =0)

prev_positions = 0

# ALL FUNCTIONS
def get_rates(curr_pair, rate_type, time_frame2, tz, df_datetime):
    
    # point = mt5.symbol_info(curr_pair).point
    if rate_type == 1:
    # RATES FOR 10% OF DAY TICKS #### BID ASK
        utc_to = datetime.datetime.fromtimestamp(mt5.symbol_info(curr_pair).time)
        utc_from = utc_to - datetime.timedelta(hours=0.1)
        rates = mt5.copy_ticks_range(curr_pair, utc_from, utc_to, mt5.COPY_TICKS_ALL) # COPY_TICKS_INFO
        rates_frame = pd.DataFrame(rates)
        rates_frame['close'] = (rates_frame['ask'] + rates_frame['bid'])/2

        rates_frame['times'] = pd.to_datetime(rates_frame['time'], unit='s')
        rates_frame['mins'] = rates_frame['times'].dt.minute
        rates_frame['hrs'] = rates_frame['times'].dt.hour
        return rates_frame
    
    if rate_type == 2:
    # RATES FOR LAST 1000 BARS # OHLC
        # rates = mt5.copy_rates_from_pos(curr_pair, mt5.TIMEFRAME_M1, 0, 500)
        # utc_to = datetime.datetime.fromtimestamp(mt5.symbol_info(curr_pair).time)
        # utc_from = utc_to - datetime.timedelta(hours=150000)
        
        # utc_from = datetime.datetime(2023, 1, 1, tzinfo=tz)
        # utc_to = datetime.datetime(2024, 1, 1, tzinfo=tz)
        # rates = mt5.copy_rates_range(curr_pair, time_frame2, utc_from, utc_to)
        
        utc_from = df_datetime
        # get 10 EURUSD H4 bars starting from 01.10.2020 in UTC time zone
        rates = mt5.copy_rates_from(curr_pair, time_frame2, utc_from, 70)
        
        rates_frame = pd.DataFrame(rates)
        # rates_frame['log_return'] = np.log(rates_frame['close']).diff()
        rates_frame['times'] = pd.to_datetime(rates_frame['time'], unit='s')
        rates_frame['mins'] = rates_frame['times'].dt.minute
        rates_frame['hrs'] = rates_frame['times'].dt.hour
        return rates_frame
    
    

cols2 = ['DATETIME'] + [i for i in range(0, 60)] # str(i)
df3 = pd.DataFrame(columns = cols2)

for idx, row in df1.iterrows():
    df_datetime = row['DATETIME']
    news = e_news #row['NEWS']
    
    df2 = get_rates(curr, 2, time_frame2, tz, df_datetime)
    # Find the index in df2 where datetime matches
    a1 = df2['close'].iloc[0:60]
    a1 = a1.to_frame()
   
    a1 = a1.T.reset_index(drop=True) 
    a1.insert(0, 'DATETIME', df_datetime)
    # row_df = pd.DataFrame([a1])
    df3 = pd.concat([df3, a1], ignore_index=True)
    
    # start_index = df2.index[df2['times'] == datetime].tolist()
    
    # if start_index:
    #     start_index = start_index[0]
        
    #     # Get the next 60 rows in df2 after the matching datetime
    #     next_60_rows = df2.iloc[start_index:start_index + 60]
        
    #     # Calculate pct_diff for each of the next 60 rows
    #     # pct_diff = ((next_60_rows['high'] - next_60_rows['low']) / next_60_rows['low']) * 100
    #     pct_diff = ((next_60_rows['close'] - next_60_rows['open']) / next_60_rows['open']) * 100
    #     pct_diff = next_60_rows['close']
    #     # Prepare the row to insert into df3
    #     row_data = [datetime, news] + pct_diff.tolist()
        
    #     # Add row to df3
    #     df3.loc[len(df3)] = row_data


# Set up the figure and axis for the plot
plt.figure(figsize=(12, 8))

# Plot each row (date) as a line
for idx, row in df3.iterrows():
    # Extract date for the label and pct_diff values for the line plot
    date_label = row['DATETIME'].strftime('%Y-%m-%d')
    pct_diff_values = row[[str(i) for i in range(0, 60)]]

    # Plot line with different color for each date and label it
    plt.plot(range(0, 60), pct_diff_values, label=date_label)

# Label axes
plt.xlabel('Values (1-60)')
plt.ylabel('Dates')
plt.title('Line Graph of pct_diff for Different Dates')
plt.legend(title="Date", loc='upper left', bbox_to_anchor=(1.05, 1), fontsize='small')