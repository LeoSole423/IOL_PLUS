import yfinance as yf
import pandas as pd

class MarketData:
    def __init__(self):
        self.tickers = {
            "SPY.BA": "S&P 500 CEDEAR",
            "GLD.BA": "Gold CEDEAR",
            "MELI.BA": "MercadoLibre CEDEAR",
            "GGAL.BA": "Grupo Galicia"
        }

    def get_global_context(self):
        """
        Fetches prices for key global assets to give context.
        """
        data = {}
        for ticker in self.tickers:
            try:
                # Fetch last closed price
                t = yf.Ticker(ticker)
                hist = t.history(period="1d")
                if not hist.empty:
                    data[ticker] = hist['Close'].iloc[-1]
                else:
                    data[ticker] = None
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                data[ticker] = None
        return data

    def get_asset_price(self, symbol):
        """
        Fetches current price for a specific asset.
        """
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="1d")
            if not hist.empty:
                return hist['Close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
        return 0.0

    def get_market_news(self):
        """
        Fetches recent news for key tickers to provide context.
        """
        news_summary = []
        # Key symbols to check for news (US and Argentina context)
        key_symbols = ["SPY", "MELI", "GGAL", "BTC-USD"]
        
        for symbol in key_symbols:
            try:
                t = yf.Ticker(symbol)
                news = t.news
                if news:
                    # Get top 2 news per symbol
                    for item in news[:2]:
                        title = item.get('title', 'No Title')
                        link = item.get('link', '')
                        news_summary.append(f"- [{symbol}] {title} ({link})")
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
                
        return news_summary
