import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_last_close(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    if not hist.empty:
        return float(hist['Close'].iloc[-1])
    return None

@st.cache_data(ttl=600, show_spinner=False)
def _fetch_news(symbol):
    t = yf.Ticker(symbol)
    news = t.news or []
    result = []
    for item in news[:2]:
        title = item.get('title', 'No Title')
        link = item.get('link', '')
        result.append({"title": title, "link": link})
    return result

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
                data[ticker] = _fetch_last_close(ticker)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                data[ticker] = None
        return data

    def get_asset_price(self, symbol):
        """
        Fetches current price for a specific asset.
        """
        try:
            price = _fetch_last_close(symbol)
            if price is not None:
                return price
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
                items = _fetch_news(symbol)
                for item in items:
                    title = item.get('title', 'No Title')
                    link = item.get('link', '')
                    news_summary.append(f"- [{symbol}] {title} ({link})")
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
                
        return news_summary
