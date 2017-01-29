#!/bin/python
import csv
from datetime import datetime, timedelta
import requests
import time

'''
A tool to parse a Poloniex trade history report and calculate net gain/loss
'''
def main():
    with open('tradeHistory.csv', 'rb') as f:
        # Dictionaries of lists of costs/revenues (in USD)
        token_buys = dict()
        token_sells = dict()
        gains = dict()
        # Read the csv file
        reader = csv.reader(f, delimiter=',')
        # Skip headers
        next(reader)
        for row in reversed(list(reader)):
            (market, btc_amount, price) = parseOrder(row)
            if market is None:
                continue
            # For token sells
            if btc_amount > 0:
                if market not in token_sells:
                    token_sells[market] = [[btc_amount, price]]
                else:
                    token_sells[market].append([btc_amount, price])
            # For token buys
            else:
                if market not in token_buys:
                    token_buys[market] = [[btc_amount, price]]
                else:
                    token_buys[market].append([btc_amount, price])

        # Calculate gain/loss
        for m in token_buys:
            if m in token_sells:
                gains[m] = calculateGainLoss(token_buys[m], token_sells[m])
        print gains

'''
Calculate the gain or loss for a given market
@param {list} buys    - list of floats representing amounts (in USD)
@param {list} sells   - list of floats representing amounts (in USD)
@returns {float}      - in USD; positive for gain, negative for loss
'''
def calculateGainLoss(buys, sells):
    gain = 0
    current_buy = buys.pop(0)
    print current_buy
    for sell in sells:
        while sell[0] > 0 and buys:
            # Get the quantity and the price
            q_diff = min(sell[0], current_buy[0])
            p_diff = sell[1] - current_buy[0]
            gain += q_diff * p_diff
            # Subtract the quantities from both the buy and the sell
            current_buy[0] -= q_diff
            sell[0] -= q_diff
            # If the buy has run out, add a new one
            if current_buy[0] == 0:
                current_buy = buys.pop(0)
    return gain

'''
Parse the order. It will be added to the appropriate stack.
@param {list} row    - The row from the csv file.
@returns {tuple}     - (string, number, bool) market, cost basis, and USD sell
'''
def parseOrder(row):
    market = parseMarket(row[1])
    if market != 'AMP':
        return (None, None, None)

    # Row 9 is the cost basis. It is negative for token buys (i.e. selling BTC)
    # and positive for token sells (i.e. buying BTC)
    btc_amount = float(row[9])
    # Get the timestamp
    ts = row[0]
    # Get the price of btc at the time
    price = getBtcQuote(ts)
    if not price:
        return (None, None, None)
    return (market, btc_amount, price)


'''
Get a quote for BTC at the time of the event. This uses the bitmex API.
It will average the bid and ask prices for the time of the event.
@param {string} ts   - timestamp of the event
@returns {float}     - price at the time of the event

'''
def getBtcQuote(ts):
    # Throttle the requests
    time.sleep(1)
    req = 'https://www.bitmex.com/api/v1/quote?symbol=XBTUSD&count=1&reverse=false&'
    # We will look at a 1 minute interval (only getting 1 data point)
    _start = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    start = str(_start).replace(" ", "T").replace(":", "%3A")
    req += 'startTime=%s'%(start)
    # Make the request
    res = requests.get(req)
    j = res.json()
    if len(j) == 0:
        print 'WARNING: Response was empty.'
        return None
    return (float(j[0]['bidPrice']) + float(j[0]['askPrice'])) / 2.


'''
Get the token of the market (i.e. the numerator). If this is a non-BTC market,
notify the user and return nothing.
@param {string} m    - The market (e.g. ETH/BTC)
@returns {string}    - Can be None. String of the token symbol.
'''
def parseMarket(m):
    if m[4:] != 'BTC':
        print 'WARNING: You have an order in a non-BTC market, but this tool does not support that yet.'
        return None
    else:
        return m[:3]


if __name__=="__main__":
  main()
