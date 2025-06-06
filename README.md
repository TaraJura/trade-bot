# Binance Trading Bot

A cryptocurrency trading bot for the Binance exchange with automated trading strategies and a web-based control interface.

## Features

- **Automated Trading**: Execute trades based on technical indicators
- **Multiple Strategies**: SMA, RSI, Bollinger Bands, and Combined strategies
- **Risk Management**: Configurable stop-loss and take-profit levels
- **Web Interface**: Real-time monitoring and control dashboard
- **Test Mode**: Paper trading for safe strategy testing
- **Multiple Pairs**: Support for BTC, ETH, BNB, and other major cryptocurrencies

## Technologies

- **Backend**: Python 3.8+, Flask, python-binance
- **Frontend**: HTML/CSS/JavaScript, Chart.js
- **Analysis**: pandas, numpy, ta (Technical Analysis library)
- **Storage**: JSON-based state persistence

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd trade-bot
```

2. **Run the setup script**
```bash
python setup.py
```
This will create necessary directories and install dependencies.

3. **Configure API credentials**
Create a `.env` file in the project root:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
FLASK_SECRET_KEY=your_flask_secret_key
FLASK_PORT=5000
```

4. **Start the application**
```bash
python app.py
```

5. **Access the interface**
Navigate to `http://localhost:5000` in your browser.

## Usage

### Control Panel (/)
- Start/stop the trading bot
- Select trading strategy and pair
- Configure trading parameters
- View active positions

### Dashboard (/dashboard)
- Advanced analytics and charts
- Position management
- Trade history
- Performance statistics

## Trading Strategies

1. **Simple Moving Average (SMA)**
   - Uses 20 and 50 period moving average crossovers
   - Buy when fast MA crosses above slow MA
   - Sell when fast MA crosses below slow MA

2. **RSI Strategy**
   - Trades based on Relative Strength Index
   - Buy when RSI < 30 (oversold)
   - Sell when RSI > 70 (overbought)

3. **Bollinger Bands**
   - Trades when price touches the bands
   - Buy at lower band, sell at upper band

4. **Combined Strategy**
   - Requires confirmation from multiple indicators
   - Higher confidence trades with reduced frequency

## Configuration

### Trading Parameters
- **Interval**: 1m, 5m, 15m, 30m, 1h
- **Max Position Size**: 10% of account balance
- **Stop Loss**: 2% below entry price
- **Take Profit**: 3% above entry price
- **Minimum Order**: $10

### Risk Management
- Position size limits prevent over-leveraging
- Automatic stop-loss protection
- Real-time position monitoring
- Trade history tracking

## API Endpoints

- `GET /status` - Bot status and positions
- `POST /start` - Start the bot
- `POST /stop` - Stop the bot
- `POST /positions` - Create manual position
- `PUT /positions/<id>` - Update position
- `DELETE /positions/<id>` - Close position
- `GET /stats` - Trading statistics
- `GET /config` - Current configuration

## Safety Features

- **Test Mode**: Trade without real money
- **State Persistence**: Survives restarts
- **Error Handling**: Comprehensive exception management
- **Logging**: Detailed activity tracking
- **Validation**: Order parameter verification

## Requirements

- Python 3.8 or higher
- Binance account with API access
- API key with trading permissions

## License

This project is for educational purposes. Use at your own risk. Cryptocurrency trading involves substantial risk of loss.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Disclaimer

This bot is provided as-is with no guarantees. Always test strategies in test mode first. Never invest more than you can afford to lose.