import os
import sys
import logging
from .iol_client import IOLClient
from ..data.portfolio_manager import PortfolioManager
from ..settings import get_settings, SettingsError

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('update.log')
    ]
)

def run_update():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    try:
        settings = get_settings()
    except SettingsError as exc:
        logging.error(str(exc))
        return

    iol_username = settings.IOL_USERNAME
    iol_password = settings.IOL_PASSWORD
    iol_base_url = settings.IOL_API_URL
    
    pm = PortfolioManager(db_path=os.path.join(project_root, "data", "inver.db"))
    
    logging.info("Starting portfolio update...")
    
    portfolio_data = []
    
    if not iol_username or not iol_password:
        logging.warning("No IOL credentials found. Using Simulation Mode logic (Mock Data).")
        # Same mock data as app.py
        portfolio_data = [
            {"Symbol": "SPY.BA", "Description": "S&P 500 ETF CEDEAR", "Quantity": 10, "Last Price": 52250.0, "Total Value": 522500.0, "Daily Var %": 0.5},
            {"Symbol": "GGAL.BA", "Description": "Grupo Financiero Galicia", "Quantity": 100, "Last Price": 8125.0, "Total Value": 812500.0, "Daily Var %": -1.2},
            {"Symbol": "MELI.BA", "Description": "MercadoLibre CEDEAR", "Quantity": 5, "Last Price": 26700.0, "Total Value": 133500.0, "Daily Var %": 2.1},
        ]
    else:
        try:
            iol = IOLClient(iol_username, iol_password, base_url=iol_base_url)
            iol.authenticate()
            raw_portfolio = iol.get_portfolio()
            
            if raw_portfolio and 'activos' in raw_portfolio:
                for asset in raw_portfolio['activos']:
                    symbol = asset.get('titulo', {}).get('simbolo', 'N/A')
                    desc = asset.get('titulo', {}).get('descripcion', '')
                    qty = asset.get('cantidad', 0)
                    last_price = asset.get('ultimoPrecio', 0.0)
                    total_val = asset.get('valorizado', 0.0)
                    daily_var = asset.get('variacionDiaria', 0.0)
                    
                    portfolio_data.append({
                        "Symbol": symbol,
                        "Description": desc,
                        "Quantity": qty,
                        "Last Price": last_price,
                        "Total Value": total_val,
                        "Daily Var %": daily_var
                    })
            logging.info("Successfully fetched data from IOL.")
            
        except Exception as e:
            logging.error(f"Failed to connect/fetch from IOL: {e}")
            return

    if portfolio_data:
        total_value = sum(item["Total Value"] for item in portfolio_data)
        try:
            pm.save_daily_snapshot(total_value, portfolio_data)
            logging.info(f"Snapshot saved. Total Value: ${total_value:,.2f}")
            print(f"Success. Total Value: ${total_value:,.2f}")
        except Exception as e:
            logging.error(f"Failed to save snapshot to DB: {e}")
    else:
        logging.warning("No portfolio data found to save.")

if __name__ == "__main__":
    run_update()
