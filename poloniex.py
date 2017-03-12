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
A tool to parse a Poloniex trade history report and calculate net gain/loss
in USD.
'''
def main():
    pickles = glob('.*.pkl')
    if '.buys.pkl' not in pickles or '.sells.pkl' not in pickles:
        (token_buys, token_sells) = collectData('poloniex.csv')
    else:
        restart = raw_input('Looks like you have saved data. Use that? (1=yes 0=no) ')
        if restart == '1':
            token_buys = loadPickle('buys')
            token_sells = loadPickle('sells')
        else:
            (token_buys, token_sells) = collectData('poloniex.csv')
    # Calculate gain/loss
    print '\nYour gains and losses:'
    print '===================================='
    gain = 0
    for m in token_buys:
       if m in token_sells:
           print m
           coin_gain = calculateGainLoss(token_buys[m], token_sells[m])
           color = RED if coin_gain < 0 else GREEN
        #    print '%s: %s$%.2f'%(m, color, coin_gain) + END
           gain += coin_gain
    print '------------------------------------'
    color = RED if gain < 0 else GREEN
    print 'Total: %s$%.2f\n'%(color, gain) + END

'''
Get the data from a tradeHistory csv file.
@param {string} filename  - name of the file relative to this directory
@returns {tuple}          - (token_buys, token_sells), both lists of lists
                            containing [btc_amount, usd_price]
'''
def collectData(filename):
    with open(filename, 'rb') as f:
        # Dictionaries of lists of costs/revenues (in USD)
        token_buys = dict()
        token_sells = dict()
        # Read the csv file
        reader = csv.reader(f, delimiter=',')
        # Skip headers
        next(reader)
        rows = list(reversed(list(reader)))
        # Print a progress bar
        print 'Parsing trades and getting reference prices...'
        L = 100                         # Total size of the progress bar
        _i = int((len(rows) + 1) / L) # Size of each item in the bar
        sys.stdout.write("[%s]" % (" " * L))
        sys.stdout.flush()
        sys.stdout.write("\b" * (L+1))

        buy_ids = list()
        sell_ids = list()
        for i in xrange(len(rows)):
            row = rows[i]
            (market, btc_amount, price, ts, id) = parseOrder(row)
            if market is None:
                continue
            # For token sells
            if btc_amount > 0:
                if market not in token_sells:
                    token_sells[market] = [[btc_amount, price, ts, id]]
                elif id in sell_ids:
                    for i in range(len(token_sells[market])):
                        if token_sells[market][i][3] == id:
                            s = token_sells[market][i]
                            if s[0] + btc_amount > 0:
                                new_p = float(s[0] * s[1] + btc_amount*price)/(s[0] + btc_amount)
                                token_sells[market][i][0] += btc_amount
                                token_sells[market][i][1] = new_p
                else:
                    token_sells[market].append([btc_amount, price, ts, id])
                    sell_ids.append(id)
            # For token buys
            else:
                if market not in token_buys:
                    token_buys[market] = [[-btc_amount, price, ts, id]]
                elif id in buy_ids:
                    for i in range(len(token_buys[market])):
                        if token_buys[market][i][3] == id:
                            b = token_buys[market][i]
                            if b[0] + btc_amount > 0:
                                new_p = float(b[0] * b[1] + btc_amount*price)/(b[0] + btc_amount)
                                token_buys[market][i][0] += btc_amount
                                token_buys[market][i][1] = new_p
                else:
                    token_buys[market].append([-btc_amount, price, ts, id])
                    buy_ids.append(id)
            # Add to progress bar if needed
            if (i+1) % _i == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
        sys.stdout.write("\n")

        # Save the data
        savePickle(token_buys, 'buys')
        savePickle(token_sells, 'sells')
        return (token_buys, token_sells)

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
    buy_ts = buys[0][2]
    buy_id = buys[0][3]
    buys.pop(0)
    ts = 0
    sell_id = 0
    tmp_cost = 0
    for sell in sells:
        ts = sell[2]
        sell_id = sell[3]
        tmp_sell = [sell[0], sell[1]]
        while sell[0] > 0:
            tmp_cost += buy_p * buy_q
            # If we need to load up a new buy, pop the first item
            if buy_q == 0 and len(buys) > 0:
                buy_p = buys[0][1]
                buy_q = buys[0][0]
                buy_ts = buys[0][2]
                buy_id = buys[0][3]
                buys.pop(0)
                tmp_cost += buy_p * buy_q

            # Zero out either the sell or the buy
            q = min(sell[0], buy_q)
            # The price is positive for a gain
            p = sell[1] - buy_p

            gain += p * q
            buy_q -= q
            sell[0] -= q
            # Escape hatch
            if len(buys) == 0 and buy_q == 0:
                return gain
        # if datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") > datetime.strptime(buy_ts, "%Y-%m-%d %H:%M:%S"):
        print '(%s) %s Cost Basis: $%.2f'%(buy_ts, buy_id, tmp_cost)
        tmp_cost = 0
        print '(%s) %s Sell: $%.2f'%(ts, sell_id, tmp_sell[0]*tmp_sell[1])

    return gain

'''
Parse the order. It will be added to the appropriate stack.
@param {list} row    - The row from the csv file.
@returns {tuple}     - (string, number, bool) market, cost basis, and USD sell
'''
def parseOrder(row):
    market = parseMarket(row[1])
    # Get the timestamp
    ts = row[0]
    # Get the price of btc at the time
    price = float(getBtcQuote(ts))
    # Order Id (usually orders are split across many rows)
    id = row[8]
    # Row 9 is the cost basis. It is negative for token buys (i.e. selling BTC)
    # and positive for token sells (i.e. buying BTC)
    btc_amount = float(row[9])
    if not price:
        return (None, None, None, None, None)
    return (market, btc_amount, price, ts, id)


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
    except:
        # Occasionally, the request will fail. We will just retry.
        return getBtcQuote(ts)

'''
Get the token of the market (i.e. the numerator). If this is a non-BTC market,
notify the user and return nothing.
@param {string} m    - The market (e.g. ETH/BTC)
@returns {string}    - Can be None. String of the token symbol.
'''
def parseMarket(m):
    if m[4:] != 'BTC':
        # print 'WARNING: You have an order in a non-BTC market, but this tool does not support that yet.'
        return None
    else:
        return m[:3]


if __name__=="__main__":
  main()
