# Crypto Tax Report
A tool for parsing spreadsheets generated from cryptocurrency exchanges (GDAX and Poloniex at present) and calculating capital gains/losses for tax reporting purposes

## Poloniex

**Assumptions**

* All trades are in BTC markets (those in other markets are thrown out)
* All trades are made in less than 1 year (i.e. subject to short term cap gains)

**Usage**

1. Download your trade history from Poloniex. You will get a file called `tradeHistory.csv`. Move that to this directory.
2. Run `python poloReport.py`

This may take several minutes (but there is a progress bar!) because each reference price (in USD) must be queried using Bitmex's API (throttled at 1 request/sec).

## GDAX

