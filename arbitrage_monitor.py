import requests
import time
import pandas as pd
from datetime import datetime
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage_monitor.log'),
        logging.StreamHandler()
    ]
)

class ArbitrageMonitor:
    def __init__(self, private_key_path='new-elections-key.txt'):
        self.private_key = self.load_private_key_from_file(private_key_path)
        self.kalshi_key_id = self.load_key_id_from_file('elections-key-id.txt')
        self.data = []
        
        self.df = pd.DataFrame({
            'timestamp': pd.Series(dtype='datetime64[ns]'),
            'kalshi_kamala_yes': pd.Series(dtype='float64'),
            'kalshi_kamala_no': pd.Series(dtype='float64'),
            'kalshi_trump_yes': pd.Series(dtype='float64'),
            'kalshi_trump_no': pd.Series(dtype='float64'),
            'polymarket_kamala_yes': pd.Series(dtype='float64'),
            'polymarket_kamala_no': pd.Series(dtype='float64'),
            'polymarket_trump_yes': pd.Series(dtype='float64'),
            'polymarket_trump_no': pd.Series(dtype='float64'),
            'arbitrage_no_spread_percent_return': pd.Series(dtype='float64'),
            'arbitrage_yes_no_spread_percent_return': pd.Series(dtype='float64')
        })

    def load_private_key_from_file(self, file_path):
        with open(file_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key

    def load_key_id_from_file(self, file_path):
        with open(file_path, "r") as file:
            return file.read().strip()

    def sign_pss_text(self, text: str) -> str:
        message = text.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

    def get_kalshi_data(self):
        current_time = datetime.now()
        timestamp = int(current_time.timestamp() * 1000)
        timestamp_str = str(timestamp)
        
        method = "GET"
        base_election_url = 'https://api.elections.kalshi.com'
        path = '/trade-api/v2/events/POPVOTE-24'
        
        msg_string = timestamp_str + method + path
        sig = self.sign_pss_text(msg_string)
        
        headers = {
            'KALSHI-ACCESS-KEY': self.kalshi_key_id,
            'KALSHI-ACCESS-SIGNATURE': sig,
            'KALSHI-ACCESS-TIMESTAMP': timestamp_str
        }
        
        response = requests.get(base_election_url + path, headers=headers)
        if response.status_code != 200:
            logging.error(f"Kalshi API error: {response.status_code}")
            return None
            
        return response.json()

    def get_polymarket_data(self):
        popular_vote_id = '903216'
        response = requests.get(f"https://gamma-api.polymarket.com/events/{popular_vote_id}")
        if response.status_code != 200:
            logging.error(f"Polymarket API error: {response.status_code}")
            return None
            
        return response.json()

    def calculate_arbitrage(self):
        try:
            # Get data from both platforms
            kalshi_data = self.get_kalshi_data()
            polymarket_data = self.get_polymarket_data()

            if not kalshi_data or not polymarket_data:
                logging.error("Failed to fetch data from one or both platforms")
                return

            # Extract Kalshi prices
            kalshi_kamala_market = next(m for m in kalshi_data['markets'] if m['ticker'] == 'POPVOTE-24-D')
            kalshi_trump_market = next(m for m in kalshi_data['markets'] if m['ticker'] == 'POPVOTE-24-R')

            kalshi_kamala_yes = kalshi_kamala_market['yes_ask'] / 100
            kalshi_kamala_no = kalshi_kamala_market['no_ask'] / 100
            kalshi_trump_yes = kalshi_trump_market['yes_ask'] / 100
            kalshi_trump_no = kalshi_trump_market['no_ask'] / 100

            # Extract Polymarket prices
            polymarket_kamala_market = next(m for m in polymarket_data['markets'] if 'Kamala Harris' in m['question'])
            polymarket_trump_market = next(m for m in polymarket_data['markets'] if 'Donald Trump' in m['question'])

            polymarket_kamala_yes, polymarket_kamala_no = map(
                lambda x: float(x.strip().strip('"')), 
                polymarket_kamala_market['outcomePrices'].strip('[]').split(',')
            )
            polymarket_trump_yes, polymarket_trump_no = map(
                lambda x: float(x.strip().strip('"')), 
                polymarket_trump_market['outcomePrices'].strip('[]').split(',')
            )


            # Calculate both arbitrage opportunities
            cost_no = polymarket_trump_no + kalshi_kamala_no
            arbitrage_no_spread_percent_return = round((1 - cost_no) / cost_no * 100, 2)

            cost_yes_no = polymarket_kamala_yes + kalshi_kamala_no
            arbitrage_yes_no_spread_percent_return = round((1 - cost_yes_no) / cost_yes_no * 100, 2)

            # Store data
            new_row = {
                'timestamp': datetime.now(),
                'kalshi_kamala_yes': kalshi_kamala_yes,
                'kalshi_kamala_no': kalshi_kamala_no,
                'kalshi_trump_yes': kalshi_trump_yes,
                'kalshi_trump_no': kalshi_trump_no,
                'polymarket_kamala_yes': polymarket_kamala_yes,
                'polymarket_kamala_no': polymarket_kamala_no,
                'polymarket_trump_yes': polymarket_trump_yes,
                'polymarket_trump_no': polymarket_trump_no,
                'arbitrage_no_spread_percent_return': arbitrage_no_spread_percent_return,
                'arbitrage_yes_no_spread_percent_return': arbitrage_yes_no_spread_percent_return
            }

            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            self.df.to_csv('arbitrage_data.csv', index=False)

            logging.info(f"Arbitrage No Spread (Trump/Kamala): {arbitrage_no_spread_percent_return}%")
            logging.info(f"Arbitrage Yes/No Spread (Kamala/Kamala): {arbitrage_yes_no_spread_percent_return}%")
            
        except Exception as e:
            logging.error(f"Error calculating arbitrage: {str(e)}")

    def monitor(self, interval_seconds=60):
        logging.info("Starting arbitrage monitoring...")
        while True:
            try:
                self.calculate_arbitrage()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor = ArbitrageMonitor()
    monitor.monitor()
