import time
import logging
from datetime import datetime
from binance_api import BinanceAPI
from strategies import SimpleMAStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy
import json
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self, strategy='combined', test_mode=True):
        self.api = BinanceAPI()
        self.test_mode = test_mode
        self.is_running = False
        self.positions = {}
        self.trades_history = []
        
        if strategy == 'sma':
            self.strategy = SimpleMAStrategy()
        elif strategy == 'rsi':
            self.strategy = RSIStrategy()
        elif strategy == 'bollinger':
            self.strategy = BollingerBandsStrategy()
        else:
            self.strategy = CombinedStrategy()
        
        self.config = {
            'max_position_size': 0.1,
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.03,
            'min_order_amount': 10.0
        }
        
        self.load_state()
    
    def load_state(self):
        if os.path.exists('bot_state.json'):
            try:
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.trades_history = state.get('trades_history', [])
            except Exception as e:
                logger.error(f"Error loading bot state: {e}")
    
    def save_state(self):
        try:
            state = {
                'positions': self.positions,
                'trades_history': self.trades_history
            }
            with open('bot_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bot state: {e}")
    
    def start(self):
        self.is_running = True
        logger.info(f"Trading bot started in {'TEST' if self.test_mode else 'LIVE'} mode")
        logger.info(f"Using strategy: {self.strategy.name}")
    
    def stop(self):
        self.is_running = False
        logger.info("Trading bot stopped")
    
    def run_cycle(self, symbol='BTCUSDT', interval='15m'):
        if not self.is_running:
            return
        
        try:
            klines = self.api.get_klines(symbol, interval, limit=100)
            if not klines:
                logger.warning(f"No kline data received for {symbol}")
                return
            
            signal, confidence = self.strategy.analyze(klines)
            current_price = float(klines[-1][4])
            
            logger.info(f"{symbol} - Price: ${current_price:.2f}, Signal: {signal}, Confidence: {confidence:.2f}%")
            
            if signal != 'HOLD' and confidence > 50:
                self.execute_trade(symbol, signal, current_price, confidence)
            
            self.check_positions(symbol, current_price)
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    def create_position(self, symbol, quantity, entry_price):
        """Manually create a position"""
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': entry_price,
            'entry_time': datetime.now().isoformat(),
            'stop_loss': entry_price * (1 - self.config['stop_loss_percentage']),
            'take_profit': entry_price * (1 + self.config['take_profit_percentage'])
        }
        self.record_trade(symbol, 'BUY', entry_price, quantity, self.test_mode)
        self.save_state()
        logger.info(f"Manually created position: {quantity} {symbol} at ${entry_price:.2f}")
        return True
    
    def execute_trade(self, symbol, signal, price, confidence):
        if self.test_mode:
            logger.info(f"TEST MODE: Would execute {signal} order for {symbol} at ${price:.2f}")
            self.record_trade(symbol, signal, price, 0.001, self.test_mode)
            return
        
        try:
            balance = self.api.get_balance('USDT')
            
            if signal == 'BUY' and symbol not in self.positions:
                max_amount = balance * self.config['max_position_size']
                
                if max_amount < self.config['min_order_amount']:
                    logger.warning(f"Insufficient balance for {symbol}. Available: ${balance:.2f}")
                    return
                
                symbol_info = self.api.get_symbol_info(symbol)
                if not symbol_info:
                    return
                
                quantity = self.calculate_quantity(max_amount / price, symbol_info)
                
                if quantity > 0:
                    order = self.api.place_order(symbol, 'BUY', quantity)
                    if order:
                        self.positions[symbol] = {
                            'quantity': quantity,
                            'entry_price': price,
                            'entry_time': datetime.now().isoformat(),
                            'stop_loss': price * (1 - self.config['stop_loss_percentage']),
                            'take_profit': price * (1 + self.config['take_profit_percentage'])
                        }
                        self.record_trade(symbol, signal, price, quantity, self.test_mode)
                        self.save_state()
                        logger.info(f"Bought {quantity} {symbol} at ${price:.2f}")
            
            elif signal == 'SELL' and symbol in self.positions:
                position = self.positions[symbol]
                order = self.api.place_order(symbol, 'SELL', position['quantity'])
                if order:
                    profit = (price - position['entry_price']) * position['quantity']
                    del self.positions[symbol]
                    self.record_trade(symbol, signal, price, position['quantity'], self.test_mode, profit)
                    self.save_state()
                    logger.info(f"Sold {position['quantity']} {symbol} at ${price:.2f}, Profit: ${profit:.2f}")
                    
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    def check_positions(self, symbol, current_price):
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        if current_price <= position['stop_loss'] or current_price >= position['take_profit']:
            reason = 'Stop Loss' if current_price <= position['stop_loss'] else 'Take Profit'
            logger.info(f"{reason} triggered for {symbol} at ${current_price:.2f}")
            self.execute_trade(symbol, 'SELL', current_price, 100)
    
    def calculate_quantity(self, raw_quantity, symbol_info):
        filters = {f['filterType']: f for f in symbol_info['filters']}
        
        lot_size = filters.get('LOT_SIZE', {})
        min_qty = float(lot_size.get('minQty', 0))
        max_qty = float(lot_size.get('maxQty', 999999))
        step_size = float(lot_size.get('stepSize', 0))
        
        if step_size > 0:
            quantity = (raw_quantity // step_size) * step_size
        else:
            quantity = raw_quantity
        
        return max(min_qty, min(quantity, max_qty))
    
    def record_trade(self, symbol, action, price, quantity, test_mode, profit=None):
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'test_mode': test_mode,
            'profit': profit
        }
        self.trades_history.append(trade)
        
        if len(self.trades_history) > 1000:
            self.trades_history = self.trades_history[-1000:]
    
    def get_status(self):
        total_value = 0
        positions_data = []
        
        for symbol, position in self.positions.items():
            ticker = self.api.get_symbol_ticker(symbol)
            if ticker:
                current_price = float(ticker['price'])
                position_value = position['quantity'] * current_price
                total_value += position_value
                
                positions_data.append({
                    'symbol': symbol,
                    'quantity': position['quantity'],
                    'entry_price': position['entry_price'],
                    'current_price': current_price,
                    'value': position_value,
                    'pnl': (current_price - position['entry_price']) * position['quantity'],
                    'pnl_percentage': ((current_price - position['entry_price']) / position['entry_price']) * 100
                })
        
        usdt_balance = self.api.get_balance('USDT')
        total_value += usdt_balance
        
        return {
            'is_running': self.is_running,
            'test_mode': self.test_mode,
            'strategy': self.strategy.name,
            'usdt_balance': usdt_balance,
            'total_value': total_value,
            'positions': positions_data,
            'recent_trades': self.trades_history[-10:]
        }