import numpy as np
from scipy.stats import norm

# Option Greeks refer to values that relate option relation to stock, inherent decline due to other variables.
# Used values:
# Delta refers to price increase when stock increase by $1
# Vega refers to price increase when stock increases in implied volatility
# Sigma refers to implied volatility. Historical volatility is general shift whereas implied volatility is based on current prices.

# Black Scholes Put and Call market price functions
def BS_CALL(S, K, T, r, sigma):
    # Input (in order): Stock price, Strike price, Lending rate, Until Maturity, Volatility
    # Output: Market price
    # Used to create a baseline market price and also used in Sigma to regress towards calculated volatility.
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    callPrice = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    # Using CDF to calculate market price according to Black-Scholes formula
    return callPrice

def BS_PUT(S, K, T, r, sigma):
    # Input (in order): Stock price, Strike price, Lending rate, Until Maturity, Volatility
    # Output: Market price
    # Used to create a baseline market price and also used in Sigma to regress towards calculated volatility.
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    putPrice = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    # Using CDF to calculate market price according to Black-Scholes formula
    return putPrice

# Sigma functions, trying to calculate volatility
def sigmaCall(callMarket, S, K, T, r, historical_volatility, tol, max_iterations):
    # Input (in order): Market price, Strike price, Lending rate, Until Maturity, Volatility, Tolerance, Max iterations
    # Output: Calculated Volatility
    # Tries to calculate the volatility between market price and model price
    sigma = historical_volatility  # Use historical volatility as initial guess
    for i in range(max_iterations):
        call = BS_CALL(S, K, T, r, sigma)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)  # Vega calculation
        price_diff = call - callMarket  # Difference between market price and model price
        if abs(price_diff) < tol:
            return sigma
        sigma -= price_diff / vega  # Newton-Raphson step
    return sigma  # Return the best estimate after max_iterations

def sigmaPut(putMarket, S, K, T, r, historical_volatility, tol, max_iterations):
    # Input (in order): Market price, Strike price, Lending rate, Until Maturity, Volatility, Tolerance, Max iterations
    # Output: Calculated Volatility
    # Tries to calculate the volatility between market price and model price
    sigma = historical_volatility  # Use historical volatility as initial guess
    for i in range(max_iterations):
        put = BS_PUT(S, K, T, r, sigma)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)  # Vega calculation
        price_diff = put - putMarket  # Difference between market price and model price
        if abs(price_diff) < tol:
            return sigma
        sigma -= price_diff / vega  # Newton-Raphson step
    return sigma  # Return the best estimate after max_iterations

def calculateDelta(stock_price, strike_price, risk_free_rate, time_to_expiration, volatility, option_type):
    # Input (in order): stock_price, strike_price, risk_free_rate, time_to_expiration, volatility, option_type
    # Output: Tries to calculate how much option value increases when stock price increase by $1
    # Calculates Delta using Black-Scholes
    d1 = (np.log(stock_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiration) / (
            volatility * np.sqrt(time_to_expiration))

    if option_type.lower() == 'call':
        # Delta for call option
        delta = norm.cdf(d1)
    elif option_type.lower() == 'put':
        # Delta for put option
        delta = norm.cdf(d1) - 1
    else:
        raise ValueError("Invalid option type. Use 'call' or 'put'.")

    return delta

def calculateVega(stock_price, strike_price, risk_free_rate, time_to_expiration, volatility):
    # Input (in order): stock_price, strike_price, risk_free_rate, time_to_expiration, volatility, option_type
    # Output: Tries to calculate how much option value increases when implied volatility increases
    # Calculates Vega using Black-Scholes

    d1 = (np.log(stock_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiration) / (
            volatility * np.sqrt(time_to_expiration))

    # Calculate vega
    vega = stock_price * np.sqrt(time_to_expiration) * norm.pdf(d1)

    return vega