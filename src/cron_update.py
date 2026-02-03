import os
import sys
from dotenv import load_dotenv
from iol_client import IOLClient
from portfolio_manager import PortfolioManager
import logging

# Setup basic logging
logging.basicConfig(
    filename='update.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_update():
    # Load env from the project root (assuming script runs from project root or finding .env explicitly)
    # We'll assume CWD is project root for simplicity, or find relative to file.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, '.env')
    
    load_dotenv(env_path)
    
    iol_username = os.getenv("IOL_USERNAME")
    iol_password = os.getenv("IOL_PASSWORD")
    
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
            iol = IOLClient(iol_username, iol_password)
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
