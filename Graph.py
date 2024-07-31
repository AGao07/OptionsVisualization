import pandas as pd
from matplotlib.dates import date2num, DateFormatter
import GetInformation
from datetime import datetime
import os
import matplotlib.pyplot as plt

def createGraph(tick, numFridays):
    # Input: Tick stock tracker, and next friday arrays
    # Output: Graph with a unrefined candlestick, bollinger band, and SMA
    # The goal is to produce a graph that shows the trend in the past contracts

    # Get the next numFridays
    nextFridays = GetInformation.findNextFridays(numFridays)

    # Convert nextFridays to strings using strftime
    nextFridays_str = [date.strftime("%Y-%m-%d") if isinstance(date, datetime) else date for date in nextFridays]

    # Generate file paths for the CSV files
    file_paths = [os.path.join('data', f'{tick}_call_with_greeks_{date_str}.csv') for date_str in nextFridays_str]

    # Read and combine all CSV files on tick and in next fridays
    dfs = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            dfs.append(df)

    # Combine all DataFrames into one
    df = pd.concat(dfs, ignore_index=True)

    # Convert 'Last Trade' to datetime and 'Last Close' to numeric
    df['Date'] = pd.to_datetime(df['Last Trade'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce') # Date along x axis
    df['Close'] = pd.to_numeric(df['Last Close'], errors='coerce') # Last close baseline for y axis
    df['Open'] = df[['Bid', 'Ask']].mean(axis=1) # Counter part to close for candle
    df['High'] = df[['Bid', 'Ask']].max(axis=1) # Wick above candle to show peak optimism
    df['Low'] = df[['Bid', 'Ask']].min(axis=1) # Wick below candle to show peak pessimism

    # Drop rows with NaN values in 'Date' or numeric columns
    df.dropna(subset=['Date', 'Close', 'Open', 'High', 'Low'], inplace=True) # Drop NAN

    # Aggregate data by date
    df_agg = df.groupby('Date').agg({ #Group by date
        'Close': 'mean',
        'Open': 'mean',
        'High': 'max',
        'Low': 'min'
    }).reset_index()

    # Set 'Date' as index
    df_agg.set_index('Date', inplace=True)

    # Calculate SMA and Bollinger Bands on aggregated data
    df_agg['SMA'] = df_agg['Close'].rolling(window=20).mean()
    df_agg['Rolling Std'] = df_agg['Close'].rolling(window=20).std()
    df_agg['Upper Band'] = df_agg['SMA'] + (df_agg['Rolling Std'] * 2) # Two standard deviations from SMA above
    df_agg['Lower Band'] = df_agg['SMA'] - (df_agg['Rolling Std'] * 2) # Two standard deviations from SMA below

    # Drop rows with NaN values in SMA or Bands
    df_agg.dropna(subset=['SMA', 'Upper Band', 'Lower Band'], inplace=True)

    # Plot
    fig, ax = plt.subplots(figsize=(14, 7))

    # Candlestick chart with adjusted width
    candle_width = 0.05  # Adjust this value to make candlesticks narrower or wider
    for i in range(len(df_agg)): #Placing candle sticks individually
        color = 'green' if df_agg['Close'].iloc[i] > df_agg['Open'].iloc[i] else 'red'
        ax.plot([date2num(df_agg.index[i]), date2num(df_agg.index[i])], [df_agg['Low'].iloc[i], df_agg['High'].iloc[i]], color=color)
        ax.add_patch(plt.Rectangle((date2num(df_agg.index[i]) - candle_width / 2, min(df_agg['Open'].iloc[i], df_agg['Close'].iloc[i])), candle_width, abs(df_agg['Close'].iloc[i] - df_agg['Open'].iloc[i]), color=color))

    # Plot SMA
    ax.plot(df_agg.index, df_agg['SMA'], label='SMA', color='blue')

    # Plot Bollinger Bands
    ax.plot(df_agg.index, df_agg['Upper Band'], label='Upper Band', color='orange')
    ax.plot(df_agg.index, df_agg['Lower Band'], label='Lower Band', color='orange', linestyle='--')

    # Format x-axis for dates
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)

    # Add legend and labels
    plt.title('Candlestick Chart with Bollinger Bands and SMA')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.tight_layout()
    plt.show()
