from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time
from trading_bot import TradingBot
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = None
bot_thread = None
running_cycles = {}


def run_bot_cycle(bot_instance, symbol, interval):
    while bot_instance.is_running and running_cycles.get(f"{symbol}_{interval}", False):
        bot_instance.run_cycle(symbol, interval)
        time.sleep(60)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    global bot
    if bot:
        return jsonify(bot.get_status())
    return jsonify({'is_running': False, 'message': 'Bot not initialized'})


@app.route('/api/start', methods=['POST'])
def start_bot():
    global bot, bot_thread, running_cycles
    
    data = request.json
    strategy = data.get('strategy', 'combined')
    test_mode = data.get('test_mode', True)
    symbol = data.get('symbol', 'BTCUSDT')
    interval = data.get('interval', '15m')
    
    try:
        if not bot:
            bot = TradingBot(strategy=strategy, test_mode=test_mode)
        
        if not bot.is_running:
            bot.start()
            
            cycle_key = f"{symbol}_{interval}"
            if cycle_key not in running_cycles or not running_cycles[cycle_key]:
                running_cycles[cycle_key] = True
                bot_thread = threading.Thread(
                    target=run_bot_cycle, 
                    args=(bot, symbol, interval),
                    daemon=True
                )
                bot_thread.start()
            
            return jsonify({'success': True, 'message': 'Bot started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Bot is already running'})
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global bot, running_cycles
    
    if bot and bot.is_running:
        bot.stop()
        running_cycles.clear()
        return jsonify({'success': True, 'message': 'Bot stopped successfully'})
    return jsonify({'success': False, 'message': 'Bot is not running'})


@app.route('/api/symbols')
def get_symbols():
    try:
        temp_api = BinanceAPI()
        exchange_info = temp_api.get_exchange_info()
        if exchange_info:
            symbols = [s['symbol'] for s in exchange_info['symbols'] 
                      if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT']
            return jsonify({'symbols': symbols[:50]})
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
    return jsonify({'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']})


@app.route('/api/balance')
def get_balance():
    try:
        temp_api = BinanceAPI()
        account = temp_api.get_account_info()
        if account:
            balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
            return jsonify({'balances': balances})
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
    return jsonify({'balances': []})


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    global bot
    
    if request.method == 'POST':
        if bot:
            data = request.json
            bot.config.update(data)
            bot.save_state()
            return jsonify({'success': True, 'message': 'Configuration updated'})
        return jsonify({'success': False, 'message': 'Bot not initialized'})
    
    else:
        if bot:
            return jsonify(bot.config)
        return jsonify({
            'max_position_size': 0.1,
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.03,
            'min_order_amount': 10.0
        })


@app.route('/api/positions')
def get_positions():
    global bot
    if bot:
        positions_data = []
        for symbol, position in bot.positions.items():
            ticker = bot.api.get_symbol_ticker(symbol)
            if ticker:
                current_price = float(ticker['price'])
                position_value = position['quantity'] * current_price
                positions_data.append({
                    'symbol': symbol,
                    'quantity': position['quantity'],
                    'entry_price': position['entry_price'],
                    'current_price': current_price,
                    'value': position_value,
                    'pnl': (current_price - position['entry_price']) * position['quantity'],
                    'pnl_percentage': ((current_price - position['entry_price']) / position['entry_price']) * 100,
                    'stop_loss': position.get('stop_loss', 0),
                    'take_profit': position.get('take_profit', 0),
                    'entry_time': position.get('entry_time', '')
                })
        return jsonify({'positions': positions_data})
    return jsonify({'positions': []})


@app.route('/api/positions/<symbol>', methods=['PUT'])
def update_position(symbol):
    global bot
    if not bot:
        return jsonify({'success': False, 'message': 'Bot not initialized'})
    
    if symbol not in bot.positions:
        return jsonify({'success': False, 'message': 'Position not found'})
    
    data = request.json
    position = bot.positions[symbol]
    
    if 'stop_loss' in data:
        position['stop_loss'] = float(data['stop_loss'])
    if 'take_profit' in data:
        position['take_profit'] = float(data['take_profit'])
    
    bot.save_state()
    return jsonify({'success': True, 'message': 'Position updated'})


@app.route('/api/positions', methods=['POST'])
def create_position():
    global bot
    if not bot:
        return jsonify({'success': False, 'message': 'Bot not initialized'})
    
    data = request.json
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    entry_price = data.get('entry_price')
    
    if not all([symbol, quantity, entry_price]):
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    try:
        if bot.create_position(symbol, float(quantity), float(entry_price)):
            return jsonify({'success': True, 'message': f'Position created for {symbol}'})
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/positions/<symbol>', methods=['DELETE'])
def close_position(symbol):
    global bot
    if not bot:
        return jsonify({'success': False, 'message': 'Bot not initialized'})
    
    if symbol not in bot.positions:
        return jsonify({'success': False, 'message': 'Position not found'})
    
    try:
        ticker = bot.api.get_symbol_ticker(symbol)
        if ticker:
            current_price = float(ticker['price'])
            bot.execute_trade(symbol, 'SELL', current_price, 100)
            return jsonify({'success': True, 'message': f'Position closed for {symbol}'})
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/statistics')
def get_statistics():
    global bot
    if not bot:
        return jsonify({
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'win_rate': 0,
            'average_profit': 0,
            'best_trade': 0,
            'worst_trade': 0
        })
    
    trades_with_profit = [t for t in bot.trades_history if t.get('profit') is not None]
    
    if not trades_with_profit:
        return jsonify({
            'total_trades': len(bot.trades_history),
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'win_rate': 0,
            'average_profit': 0,
            'best_trade': 0,
            'worst_trade': 0
        })
    
    profits = [t['profit'] for t in trades_with_profit]
    winning_trades = [p for p in profits if p > 0]
    losing_trades = [p for p in profits if p < 0]
    
    statistics = {
        'total_trades': len(trades_with_profit),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'total_profit': sum(profits),
        'win_rate': (len(winning_trades) / len(trades_with_profit) * 100) if trades_with_profit else 0,
        'average_profit': sum(profits) / len(profits) if profits else 0,
        'best_trade': max(profits) if profits else 0,
        'worst_trade': min(profits) if profits else 0,
        'total_volume': sum(t.get('quantity', 0) * t.get('price', 0) for t in bot.trades_history),
        'active_positions': len(bot.positions)
    }
    
    return jsonify(statistics)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    from binance_api import BinanceAPI
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=True, port=port, host='0.0.0.0')