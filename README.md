# Crypto Tax Report
A tool for parsing spreadsheets generated from cryptocurrency exchanges (Coinbase/GDAX and Poloniex at present) and calculating capital gains/losses for tax reporting purposes.

Running these may take several minutes (but there is a progress bar!) because each reference price (in USD) must be queried using Bitmex's API (throttled at 1 request/sec).

## Poloniex

This assumes that all trades are in BTC markets (those in other markets are thrown out) and that all trades are made in less than 1 year (i.e. subject to short term cap gains).

**Usage**

1. Download your trade history from Poloniex. You will get a file called `tradeHistory.csv`.
2. Move that csv file to this directory and rename it to `poloniex.csv`
3. Run `python poloReport.py`

## Coinbase/GDAX

This assumes you downloaded a report for your BTC wallet and that all trades are in BTC. It also assumes all trades are made in less than 1 year (i.e. subject to short term cap gains).

**Usage**

1. Download your report from Coinbase. You will get a file with a long name called something like `Coinbase...csv`
2. Move that csv file to this directory and rename it `coinbase.csv`
3. Run `python coinbase.py`

