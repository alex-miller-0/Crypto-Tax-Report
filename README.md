# poloTaxReport
A tool for parsing a tradeHistory document from Poloniex and calculating gains/losses

## Usage

1. Download your trade history from Poloniex. You will get a file called `tradeHistory.csv`. Move that to this directory.
2. Run `python poloReport.py`

This may take several minutes (but there is a progress bar!) because each reference price (in USD) must be queried using Bitmex's API (throttled at 1 request/sec).

## Assumptions
* All trades are in BTC markets (those in other markets are thrown out)
* All trades are made in less than 1 year (i.e. subject to short term cap gains)
