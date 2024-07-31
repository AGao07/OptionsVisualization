import pandas as pd
import os
import GetInformation
import Greeks
import Graph
from datetime import datetime

# Simplifies the create optionsFile
def createOptionsFile(tick, finvizKey, fedKey, numFridays):
    # Input: Tick, Finviz Key, Saint Louis Federal Bank APi Key, and Number of fridays to record
    # Output: Downloads NumFridays # of csvs with greeks applied.
    # Purpose to create a viable storage for values to be visualized.

    tolerance = 1e-8 #Sigma tolerance for model difference
    maxIter = 1000 #Sigma max iterations
    historicalVolatility = GetInformation.getHistoricalVolatility(tick) # model volatility before sigma
    fedRate = GetInformation.getFedFundsRate(fedKey)  # Rate according to Saint Louis Federal Bank
    stockPrice = GetInformation.getCurrentPrice(tick)  # Get current price from Finviz Instrument API
    nextFridays = GetInformation.findNextFridays(numFridays)  # Array of Date-Time Objects

    # Arrays to accept once the the loops run
    paths = []
    expirations = []

    for i in range(numFridays):
        runningFriday = nextFridays[i]
        if isinstance(runningFriday, str):  # Ensure runningFriday is a datetime object
            runningFriday = datetime.strptime(runningFriday, "%Y-%m-%d")

        daysUntil = GetInformation.getDaysUntil(runningFriday)
        untilMaturity = daysUntil / 365  # Until Maturity for calculation
        expirations.append(untilMaturity) # Gets all the expirations

        pathToFile = GetInformation.getOptionChains(tick, runningFriday,
                                                    finvizKey)  # Downloads the export, returns the path
        paths.append(pathToFile)

        # Confirm file path
        print(f'File saved to: {pathToFile}')

        contracts = pd.read_csv(pathToFile)
        grouped = contracts.groupby('Type')

        # Separates into calls and puts.
        for type_name, group in grouped:
            output_file = os.path.join('data', f'{type_name}_{runningFriday.strftime("%Y-%m-%d")}.csv')
            group.to_csv(output_file, index=False)
            print(f'Saved {type_name} data to {output_file}')

        # Construct file paths for reading
        call_file = os.path.join('data', f'call_{runningFriday.strftime("%Y-%m-%d")}.csv')
        put_file = os.path.join('data', f'put_{runningFriday.strftime("%Y-%m-%d")}.csv')
        print(f'Reading files: {call_file}, {put_file}')

        # Check if the files exist before reading
        if os.path.exists(call_file):
            call = pd.read_csv(call_file)
        else:
            print(f'File not found: {call_file}')
            call = pd.DataFrame()  # Create an empty DataFrame to avoid further errors

        if os.path.exists(put_file):
            put = pd.read_csv(put_file)
        else:
            print(f'File not found: {put_file}')
            put = pd.DataFrame()  # Create an empty DataFrame to avoid further errors

        # Filter out rows with NaN values in crucial columns
        call = call.dropna()
        put = put.dropna()

        def safe_float_conversion(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return None  # or another default value

        # Convert variables safely
        stockPrice = safe_float_conversion(stockPrice)
        call['Strike'] = call['Strike'].apply(safe_float_conversion)
        put['Strike'] = put['Strike'].apply(safe_float_conversion)
        untilMaturity = safe_float_conversion(untilMaturity)
        fedRate = safe_float_conversion(fedRate)
        historicalVolatility = safe_float_conversion(historicalVolatility)

        # Check for None or NaN in the converted values
        if pd.isnull(stockPrice) or pd.isnull(untilMaturity) or pd.isnull(fedRate) or pd.isnull(historicalVolatility):
            print("One or more values could not be converted to float.")
            # Handle missing or invalid data as needed

        if call['Strike'].isna().any() or put['Strike'].isna().any():
            print("One or more strike prices could not be converted to float.")
            # Handle missing or invalid data as needed

        # Calculate stockCall and stockPut for each row
        call['StockPrice'] = call.apply(
            lambda row: Greeks.BS_CALL(stockPrice, row['Strike'], untilMaturity, fedRate, historicalVolatility), axis=1)
        put['StockPrice'] = put.apply(
            lambda row: Greeks.BS_PUT(stockPrice, row['Strike'], untilMaturity, fedRate, historicalVolatility), axis=1)

        # Proceed with calculations if DataFrames are not empty after filtering
        if not call.empty:
            # Add Greeks and perform calculations
            call['ImpliedVolatility'] = call.apply(
                lambda row: Greeks.sigmaCall(row['StockPrice'], stockPrice, row['Strike'], untilMaturity, fedRate,
                                             historicalVolatility, tolerance, maxIter), axis=1)
            call['Delta'] = call.apply(
                lambda row: Greeks.calculateDelta(stockPrice, row['Strike'], fedRate, untilMaturity,
                                                  row['ImpliedVolatility'], 'call'), axis=1)
            call['Vega'] = call.apply(
                lambda row: Greeks.calculateVega(stockPrice, row['Strike'], fedRate, untilMaturity,
                                                 row['ImpliedVolatility']), axis=1)
            call.to_csv(os.path.join('data', f'{tick}_call_with_greeks_{runningFriday.strftime("%Y-%m-%d")}.csv'),
                        index=False)
        else:
            print("No valid call options to process.")

        if not put.empty:
            put['ImpliedVolatility'] = put.apply(
                lambda row: Greeks.sigmaPut(row['StockPrice'], stockPrice, row['Strike'], untilMaturity, fedRate,
                                            historicalVolatility, tolerance, maxIter), axis=1)
            put['Delta'] = put.apply(
                lambda row: Greeks.calculateDelta(stockPrice, row['Strike'], fedRate, untilMaturity,
                                                  row['ImpliedVolatility'], 'put'), axis=1)
            put['Vega'] = put.apply(lambda row: Greeks.calculateVega(stockPrice, row['Strike'], fedRate, untilMaturity,
                                                                     row['ImpliedVolatility']), axis=1)
            put.to_csv(os.path.join('data', f'{tick}_put_with_greeks_{runningFriday.strftime("%Y-%m-%d")}.csv'),
                       index=False)
        else:
            print("No valid put options to process.")

numFridays=5
tick = 'DJT'
finvizKey = '#Fill This In According To README'  #Finviz Key - Refer to keys.txt doc or look at canvas
fedKey = '#Fill This In According To README'  # Fed key - Refer to keys.txt doc or look at canvas
createOptionsFile(tick, finvizKey, fedKey, numFridays)
Graph.createGraph(tick,numFridays)