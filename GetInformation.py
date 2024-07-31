import requests
from datetime import datetime, timedelta
from fredapi import Fred
import pandas as pd
import numpy as np
import yfinance as yf
import os


def findNextFridays(num_fridays):
    #Input: # of Fridays from today
    #Output: Array of datetime objects that show Fridays since today
    #Purpose: Trading for options open on monday and close on Friday so expirations are on Fridays.

    current_date = datetime.today()# Get's today's date
    fridays_found = 0 # Counter
    next_fridays = [] # Array return variable

    while fridays_found < num_fridays: # While loop using counter to validate
        if current_date.weekday() == 4:  # 4 corresponds to Friday (0 is Monday, 6 is Sunday)
            next_fridays.append(current_date.strftime('%Y-%m-%d')) # Appends the datetime object
            fridays_found += 1 # Increments counter
        current_date += timedelta(days=1) #Since current_date is a date time object, you can't just add the integer 1.
    return next_fridays #Returns array

def getOptionChains(tick, expiration, key):
    # Input: Tick to track, expiration date for contract, and key to access API
    # Output: Downloads CSV to data directory, returns path for main
    # Purpose: This is my main API for getting option chains data.

    # Creates data folder
    if not os.path.exists('data'):
        os.makedirs('data')

    # Expiration date validation
    if isinstance(expiration, datetime):  # If datetime object, then set format for string
        expiration_str = expiration.strftime("%Y-%m-%d")  # This is what Finviz accepts
    elif isinstance(expiration, str):  # If object is string, then we can just use it likely due to coercion in main.
        expiration_str = expiration  #Set to expiration
    else:  #Exception thrown
        raise TypeError("expiration must be a string or datetime object")

    # Writing the path for ease of use and to set destination
    file_path = os.path.join('data', f"{tick}_{expiration_str}_export.csv")

    # Construct URL accepting parameters using format in Finviz API.
    URL = f"https://elite.finviz.com/export/options?t={tick}&ty=oc&e={expiration_str}&auth={key}"

    # Request form filled with URL and Response is what we get back.
    response = requests.get(URL)

    # Save the file
    with open(file_path, "wb") as file:  # Opens writing mode in binary
        file.write(response.content)  # Response gets data in CSV format according to documentation.

    return file_path #We return path as previously stated for ease of use in main.


def getFedFundsRate(api_key):
    # Input: Saint Louis Federal Bank API Key
    # Output: The Federal Funds Interest rate as used in Black Scholes formulas.
    # Purpose: I would use Yahoo Finance, but this is just for calculations in relation to Strike Price.
    fred = Fred(api_key=api_key) # Saint Louis Federal Bank API Object
    data = fred.get_series_latest_release('FEDFUNDS') #G Gets latest lending rates
    return data.iloc[-1] #Retrieves latest value

def getDaysUntil(targetDate):
    # Input: Target date
    # Output: Gets integer for days until Target Date
    # Purpose: This is the counterpart for next fridays function to get days until maturity or expiration.

    # Check if targetDate is already a datetime object
    if isinstance(targetDate, str):
        # If targetDate is a string, convert it to a datetime object
        target_date = datetime.strptime(targetDate, '%Y-%m-%d')
    elif isinstance(targetDate, datetime):
        # If targetDate is already a datetime object, use it directly
        target_date = targetDate
    else: # Exception throws
        raise TypeError("targetDate must be a string or datetime object")

    today = datetime.now()  # The current day
    days_until = (target_date - today).days  # Integer coercion into integer while using datetime objects for arithmetic.
    return days_until # Returns after making it integer.

def getCurrentPrice(tick):
    # Not written by me, Written by another student
    # Input: Stock ticker
    # Output: Most recent traded price
    # Purpose: This is just an attempt on using the Finviz Instrument API and can be adjusted to provide historical volume data.

    # Filter critera
    ticker = tick # Stock tracker
    time_frame = "i1" # Tracking interval i1 is every minute
    types = "stock" # Stock is underlying asset for option contracts

    URL = f"https://elite.finviz.com/api/quote.ashx"  # Base url for finviz screener.

    #Payload is request format and header is to show a real individual is trying to access the API.
    payload = {"instrument": types, "ticker": ticker, "timeframe": time_frame, "type": "new"}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Try throw exception,
    try:
        response = requests.get(URL, params=payload, headers=headers) # Request call made according to payload and header.
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

        json_response = response.json() # Converts the plain text json into a json file
        # Extract data assuming the response structure
        data_id = json_response.get("dataId", "") # Look for variable dataID
        if data_id: # data ID is a tuple for (id of last trade, last trade value)
            # Grab the last trade value and id is available but not used.
            id, last = data_id.split("|") # split by delimiter |
            return last
        else:
            print("dataId not found in the response.") # Error in Json

    # Exceptions
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except ValueError as e:
        print(f"Error processing the response: {e}")
    except KeyError as e:
        print(f"Missing key in the response: {e}")

def getHistoricalVolatility(ticker, days=30):
    # Input: tick for tracking and 30 days since current attempt is looking at monthly history.
    # Output: produces a running average volatility estimate
    # For greeks calculation, the baseline requires a volatility estimate from stock history or calculating it from other values.

    end_date = datetime.now() # 30 days until today
    start_date = end_date - timedelta(days=days * 1.5)  # Provide some buffer for weekends and holidays
    data = yf.download(ticker, start=start_date, end=end_date) # Downloads values from start date until today

    # I would have used Finviz Instrumental API, but adj close is calculated already in Yahoo Finance
    if len(data) < days: #Error in case the market data is lost or not available
        raise ValueError(f"Not enough data for the last {days} trading days.")

    # Calculation for close value change over each day
    data['Return'] = data['Adj Close'].pct_change()
    data.dropna(inplace=True)
    dailyVolatility = data['Return'].std() # Standard deviation which shows volatility between changes
    annualVolatility = dailyVolatility * np.sqrt(252)  # 252 trading days in a year

    return annualVolatility
