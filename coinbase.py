#!/bin/python

# TODO Count up the tokens themselves. If the quantity bought exceeds the
#quantity sold, reduce the cost basis by the excess

import csv
from datetime import datetime, timedelta
import requests
import time
import sys
import pickle
from glob import glob
RED = '\x1b[0;31;40m'
GREEN = '\x1b[0;32;40m'
END = '\x1b[0m'
'''
A tool to parse a Coinbase trade history report and calculate net gain/loss
in USD.
'''
def main():
    pickles = glob('.*.pkl')
    if '.coinbase_buys.pkl' not in pickles or '.coinbase_sells.pkl' not in pickles:
        (btc_buys, btc_sells) = collectData('coinbase.csv')
    else:
        btc_buys = loadPickle('coinbase_buys')
        btc_sells = loadPickle('coinbase_sells')
    # Calculate gain/loss
    print '\nYour gains and losses:'
    print '===================================='
    gain = 0
    fiat_gain = calculateGainLoss(btc_buys, btc_sells)
    color = RED if fiat_gain < 0 else GREEN
    plus = 'gain' if fiat_gain > 0 else 'loss'
    print 'Coinbase %s from BTC wallet: %s$%.2f'%(plus, color, fiat_gain) + END
    print '------------------------------------'

'''
Get the data from a tradeHistory csv file.
@param {string} filename  - name of the file relative to this directory
@returns {tuple}          - (token_buys, token_sells), both lists of lists
                            containing [btc_amount, usd_price]
'''
def collectData(filename):
    with open(filename, 'rb') as f:
        # Dictionaries of lists of costs/revenues (in USD)
        btc_buys = list()
        btc_sells = list()
        # Read the csv file
        reader = csv.reader(f, delimiter=',')
        # Skip headers
        next(reader)
        # Read rows in reverse order
        rows = list(reversed(list(reader)))
        # Print a progress bar
        print 'Parsing trades and getting reference prices...'
        L = 100                         # Total size of the progress bar
        _i = int(round(L / float(len(rows) + 1))) # Size of each item in the bar
        sys.stdout.write("[%s]" % (" " * L))
        sys.stdout.flush()
        sys.stdout.write("\b" * (L+1))

        for i in xrange(len(rows)):
            row = rows[i]
            (btc_amount, price, ts) = parseOrder(row)
            # For token sells
            if btc_amount > 0:
                btc_sells.append([btc_amount, price, ts])
            # For token buys
            elif btc_amount < 0:
                btc_buys.append([-btc_amount, price, ts])
            # Add to progress bar if needed
            if (i+1) % _i == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
        sys.stdout.write("\n")
        # Save the data
        savePickle(btc_buys, 'coinbase_buys')
        savePickle(btc_sells, 'coinbase_sells')
        return (btc_buys, btc_sells)

'''
Save a pickle file with a dictionary
@param {dict} d       - dictionary with your data
@param {string} name  - name of the file you want to save (will be suffixed
                        with .pkl and will be a hidden file)
'''
def savePickle(d, name):
    with open('.%s.pkl'%name, 'wb') as handle:
        pickle.dump(d, handle, protocol=pickle.HIGHEST_PROTOCOL)

'''
Load a dictionary from a pickle file
@param {string} name   - filename of .pkl hidden file
@returns {dict}        - dictionary with your data
'''
def loadPickle(name):
    with open('.%s.pkl'%name, 'rb') as handle:
        b = pickle.load(handle)
        return b

'''
Calculate the gain or loss for a given market
@param {list} buys    - list of floats representing amounts (in USD)
@param {list} sells   - list of floats representing amounts (in USD)
@returns {float}      - in USD; positive for gain, negative for loss
'''
def calculateGainLoss(buys, sells):
    gain = 0
    # Calculated the weighted average price for buys
    buy_p = buys[0][1]
    buy_q = buys[0][0]
    buys.pop(0)
    for sell in sells:
        while sell[0] > 0:
            # If we need to load up a new buy, pop the first item
            if buy_q == 0 and len(buys) > 0:
                buy_p = buys[0][1]
                buy_q = buys[0][0]
                buys.pop(0)
            # Zero out either the sell or the buy
            q = min(sell[0], buy_q)
            # The price is positive for a gain
            p = sell[1] - buy_p
            gain += p * q
            buy_q -= q
            sell[0] -= q
    return gain

'''
Parse the order. It will be added to the appropriate stack.
@param {list} row    - The row from the csv file.
@returns {tuple}     - (number, number) delta BTC, price in USD
'''
def parseOrder(row):
    if len(row) < 4:
        return (0,0)
    if row[3] != 'BTC':
        return (0, 0)
    # Row 2 is the cost basis. It is negative for selling BTC and positive for buying
    btc_amount = float(row[2])
    # Get the timestamp
    ts = row[0]
    # Get the price of btc at the time
    price = getBtcQuote(ts)
    if not price:
        return (0, 0)
    return (btc_amount, price, ts)


'''
Get a quote for BTC at the time of the event. This uses the bitmex API.
It will average the bid and ask prices for the time of the event.
@param {string} ts   - timestamp of the event
@returns {float}     - price at the time of the event

'''
def getBtcQuote(ts):
    # Throttle the requests. Rate limit is 1/sec
    time.sleep(1.1)
    try:
        req = 'https://www.bitmex.com/api/v1/quote?symbol=XBTUSD&count=1&reverse=false&'
        # We will look at a 1 minute interval (only getting 1 data point)
        _start = datetime.strptime(ts[:-6], "%Y-%m-%d %H:%M:%S")
        start = str(_start).replace(" ", "T").replace(":", "%3A")
        req += 'startTime=%s'%(start)
        # Make the request
        res = requests.get(req)
        j = res.json()
        if len(j) == 0:
            print 'WARNING: Response was empty.'
            return None
        return (float(j[0]['bidPrice']) + float(j[0]['askPrice'])) / 2.
    except:
        # Occasionally, the request will fail. We will just retry.
        return getBtcQuote(ts)


if __name__=="__main__":
  main()
