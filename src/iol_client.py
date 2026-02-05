import requests
import json
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class IOLClient:
    def __init__(self, username, password, base_url="https://api.invertironline.com", timeout=10):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.timeout = timeout
        self.session = self._create_session()
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0

    def _create_session(self):
        session = requests.Session()
        try:
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET", "POST"])
            )
        except TypeError:
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                method_whitelist=["GET", "POST"]
            )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def authenticate(self):
        """Obtains the access token using the credentials."""
        url = f"{self.base_url}/token"
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }
        
        # Note: IOL API sometimes requires standard form data for token
        response = self.session.post(url, data=data, timeout=self.timeout)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            # Set expiry time (usually expires_in is in seconds)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = time.time() + expires_in
            print("Authentication successful.")
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    def _ensure_token(self):
        """Checks if token is valid, if not, re-authenticates."""
        if not self.access_token or time.time() >= self.token_expiry:
            print("Token expired or missing, re-authenticating...")
            self.authenticate()

    def _get_headers(self):
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_portfolio(self, country="argentina"):
        """
        Fetches the portfolio for a specific country.
        Default is 'argentina'.
        """
        endpoint = f"/api/v2/portafolio/{country}"
        url = f"{self.base_url}{endpoint}"
        
        response = self.session.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get portfolio: {response.status_code} - {response.text}")

    def get_market_data(self, market="bcba", symbol="GGAL"):
        """
        Fetches market data for a specific symbol.
        """
        endpoint = f"/api/v2/{market}/titulos/{symbol}/cotizacion"
        url = f"{self.base_url}{endpoint}"
        
        response = self.session.get(url, headers=self._get_headers(), timeout=self.timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Warning: Could not fetch data for {symbol}: {response.text}")
            return None
