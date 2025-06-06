import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class BinanceAPI:
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
        
        self.client = Client(api_key, api_secret)
        
    def get_account_info(self):
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_balance(self, symbol='USDT'):
        try:
            balance = self.client.get_asset_balance(asset=symbol)
            return float(balance['free']) if balance else 0.0
        except BinanceAPIException as e:
            logger.error(f"Error getting balance for {symbol}: {e}")
            return 0.0
    
    def get_symbol_ticker(self, symbol):
        try:
            return self.client.get_symbol_ticker(symbol=symbol)
        except BinanceAPIException as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            return None
    
    def get_klines(self, symbol, interval, limit=100):
        try:
            return self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Error getting klines for {symbol}: {e}")
            return []
    
    def place_order(self, symbol, side, quantity, order_type='MARKET'):
        try:
            if order_type == 'MARKET':
                if side == 'BUY':
                    order = self.client.order_market_buy(symbol=symbol, quantity=quantity)
                else:
                    order = self.client.order_market_sell(symbol=symbol, quantity=quantity)
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing {side} order for {symbol}: {e}")
            return None
    
    def get_open_orders(self, symbol=None):
        try:
            if symbol:
                return self.client.get_open_orders(symbol=symbol)
            return self.client.get_open_orders()
        except BinanceAPIException as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def cancel_order(self, symbol, order_id):
        try:
            return self.client.cancel_order(symbol=symbol, orderId=order_id)
        except BinanceAPIException as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return None
    
    def get_exchange_info(self):
        try:
            return self.client.get_exchange_info()
        except BinanceAPIException as e:
            logger.error(f"Error getting exchange info: {e}")
            return None
    
    def get_symbol_info(self, symbol):
        try:
            exchange_info = self.get_exchange_info()
            if exchange_info:
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol:
                        return s
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None